from __future__ import annotations

from uuid import UUID

from fastapi import FastAPI, Header, HTTPException, Query
from psycopg.types.json import Jsonb

from .config import settings
from .db import connection
from .guard import cosine, evaluate_candidate
from .schemas import ImageTags, JobResponse, PostCreate, ReviewCreate


app = FastAPI(title="FlyRank Image-Relevance Engine", version="0.1.0")


def tenant(value: str | None) -> str:
    return value or "demo"


def _job(row: dict) -> JobResponse:
    return JobResponse(id=row["id"], status=row["status"], attempts=row["attempts"], processed=row["processed"], total=row["total"])


@app.get("/health")
def health() -> dict[str, str]:
    try:
        with connection() as conn:
            conn.execute("SELECT 1")
        return {"status": "ok"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="database unavailable") from exc


@app.post("/v1/jobs/catalog", response_model=JobResponse, status_code=202)
def enqueue_catalog(x_tenant_id: str | None = Header(None, alias="X-Tenant-ID"), idempotency_key: str | None = Header(None, alias="Idempotency-Key")) -> JobResponse:
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key header is required")
    tenant_id = tenant(x_tenant_id)
    with connection() as conn:
        row = conn.execute(
            """INSERT INTO jobs(tenant_id,kind,idempotency_key,total)
               VALUES (%s,'catalog',%s,(SELECT count(*) FROM images WHERE tenant_id=%s)+(SELECT count(*) FROM posts WHERE tenant_id=%s))
               ON CONFLICT (tenant_id,idempotency_key) DO UPDATE SET idempotency_key=EXCLUDED.idempotency_key
               RETURNING *""",
            (tenant_id, idempotency_key, tenant_id, tenant_id),
        ).fetchone()
    return _job(row)


@app.get("/v1/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: UUID, x_tenant_id: str | None = Header(None, alias="X-Tenant-ID")) -> JobResponse:
    with connection() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id=%s AND tenant_id=%s", (job_id, tenant(x_tenant_id))).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="job not found")
    return _job(row)


@app.post("/v1/posts", status_code=201)
def create_post(payload: PostCreate, x_tenant_id: str | None = Header(None, alias="X-Tenant-ID")) -> dict:
    tenant_id = tenant(x_tenant_id)
    with connection() as conn:
        row = conn.execute(
            """INSERT INTO posts(tenant_id,slug,title,body,subject,category) VALUES (%s,%s,%s,%s,%s,%s)
               ON CONFLICT (tenant_id,slug) DO UPDATE SET title=EXCLUDED.title,body=EXCLUDED.body,subject=EXCLUDED.subject,category=EXCLUDED.category
               RETURNING id,slug,title,body,subject,category""",
            (tenant_id, payload.slug, payload.title, payload.body, payload.subject, payload.category),
        ).fetchone()
    return dict(row)


@app.get("/v1/posts/{post_id}/images")
def rank_images(post_id: UUID, limit: int = Query(5, ge=1, le=20), x_tenant_id: str | None = Header(None, alias="X-Tenant-ID")) -> dict:
    tenant_id = tenant(x_tenant_id)
    with connection() as conn:
        post = conn.execute("SELECT * FROM posts WHERE id=%s AND tenant_id=%s", (post_id, tenant_id)).fetchone()
        if not post:
            raise HTTPException(status_code=404, detail="post not found")
        post_embedding = conn.execute("SELECT embedding_values FROM embeddings WHERE tenant_id=%s AND entity_type='post' AND entity_id=%s ORDER BY created_at DESC LIMIT 1", (tenant_id, str(post_id))).fetchone()
        if not post_embedding:
            raise HTTPException(status_code=409, detail="post has not been embedded; run the catalog job")
        rows = conn.execute(
            """SELECT i.*, t.subject, t.category, t.attributes, t.caption, t.confidence, t.status AS tag_status, e.embedding_values
               FROM images i JOIN image_tags t ON t.image_id=i.id AND t.tenant_id=i.tenant_id
               JOIN embeddings e ON e.entity_id=i.id AND e.entity_type='image' AND e.tenant_id=i.tenant_id
               WHERE i.tenant_id=%s""",
            (tenant_id,),
        ).fetchall()
        ranked = []
        for row in rows:
            similarity = cosine(list(post_embedding["embedding_values"]), list(row["embedding_values"]))
            decision = evaluate_candidate(dict(post), {"tag_status": row["tag_status"], "tags": {"subject": row["subject"], "confidence": row["confidence"]}}, similarity, settings.vision_confidence_threshold, settings.match_similarity_threshold)
            suggestion = conn.execute(
                """INSERT INTO suggestions(tenant_id,post_id,image_id,similarity,decision,reasons) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id""",
                (tenant_id, post_id, row["id"], similarity, decision["decision"], Jsonb(decision["reasons"])),
            ).fetchone()
            ranked.append({"suggestion_id": suggestion["id"], "image_id": row["id"], "subject": row["subject"], **decision})
    ranked.sort(key=lambda item: item["similarity"], reverse=True)
    accepted = [item for item in ranked if item["accepted"]]
    return {"post_id": post_id, "status": "matched" if accepted else "no_confident_match", "suggestions": ranked[:limit], "reasons": [] if accepted else [reason for item in ranked[:limit] for reason in item["reasons"]]}


@app.get("/v1/suggestions/{suggestion_id}")
def get_suggestion(suggestion_id: UUID, x_tenant_id: str | None = Header(None, alias="X-Tenant-ID")) -> dict:
    with connection() as conn:
        row = conn.execute(
            """SELECT s.*, r.decision AS review_decision, r.note AS review_note, r.reviewed_at
               FROM suggestions s LEFT JOIN reviews r ON r.suggestion_id=s.id
               WHERE s.id=%s AND s.tenant_id=%s""",
            (suggestion_id, tenant(x_tenant_id)),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="suggestion not found")
    return dict(row)


@app.put("/v1/suggestions/{suggestion_id}/review")
def review_suggestion(suggestion_id: UUID, payload: ReviewCreate, x_tenant_id: str | None = Header(None, alias="X-Tenant-ID")) -> dict:
    tenant_id = tenant(x_tenant_id)
    with connection() as conn:
        if not conn.execute("SELECT 1 FROM suggestions WHERE id=%s AND tenant_id=%s", (suggestion_id, tenant_id)).fetchone():
            raise HTTPException(status_code=404, detail="suggestion not found")
        existing = conn.execute("SELECT * FROM reviews WHERE suggestion_id=%s AND tenant_id=%s", (suggestion_id, tenant_id)).fetchone()
        if existing and existing["decision"] != payload.decision:
            raise HTTPException(status_code=409, detail="review decision is already final")
        row = conn.execute(
            """INSERT INTO reviews(suggestion_id,tenant_id,decision,note) VALUES (%s,%s,%s,%s)
               ON CONFLICT (suggestion_id) DO UPDATE SET note=EXCLUDED.note,reviewed_at=now() RETURNING *""",
            (suggestion_id, tenant_id, payload.decision, payload.note),
        ).fetchone()
    return dict(row)


@app.get("/v1/costs")
def costs(job_id: UUID | None = None, x_tenant_id: str | None = Header(None, alias="X-Tenant-ID")) -> dict:
    with connection() as conn:
        rows = conn.execute("SELECT * FROM cost_events WHERE tenant_id=%s AND (%s IS NULL OR job_id=%s) ORDER BY created_at", (tenant(x_tenant_id), job_id, job_id)).fetchall()
    return {"events": [dict(row) for row in rows], "total_list_price_estimate_usd": round(sum(row["list_price_estimate_usd"] for row in rows), 8)}
