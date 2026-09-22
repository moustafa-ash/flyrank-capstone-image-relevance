from __future__ import annotations

import time
from pathlib import Path

from psycopg.types.json import Jsonb

from .config import settings
from .db import connection
from .provider import embed_text, vision_tags


ROOT = Path(__file__).resolve().parents[1]


def _cost(operation: str, job_id, tokens: dict[str, int]) -> float:
    # Conservative list-price estimate; free-tier estimate remains zero in the evidence log.
    return ((tokens.get("prompt_tokens", 0) + tokens.get("candidates_tokens", 0)) / 1_000_000) * 0.50


def _record_cost(conn, tenant_id: str, job_id, operation: str, model: str, tokens: dict[str, int]) -> None:
    conn.execute(
        """INSERT INTO cost_events(tenant_id,job_id,operation,provider,model,prompt_tokens,candidate_tokens,estimated_usd,list_price_estimate_usd)
           VALUES (%s,%s,%s,'gemini',%s,%s,%s,0,%s)""",
        (tenant_id, job_id, operation, model, tokens.get("prompt_tokens", 0), tokens.get("candidates_tokens", 0), _cost(operation, job_id, tokens)),
    )


def process_job(job: dict) -> None:
    job_id = job["id"]
    tenant_id = job["tenant_id"]
    with connection() as conn:
        conn.execute("UPDATE jobs SET status='running', attempts=attempts+1, updated_at=now() WHERE id=%s", (job_id,))
        images = conn.execute("SELECT * FROM images WHERE tenant_id=%s ORDER BY id", (tenant_id,)).fetchall()
        posts = conn.execute("SELECT * FROM posts WHERE tenant_id=%s ORDER BY slug", (tenant_id,)).fetchall()
        total = len(images) + len(posts)
        conn.execute("UPDATE jobs SET total=%s WHERE id=%s", (total, job_id))
        for image in images:
            calls = conn.execute("SELECT count(*) AS count FROM cost_events WHERE job_id=%s", (job_id,)).fetchone()["count"]
            if calls >= settings.ai_max_calls_per_job:
                raise RuntimeError("AI call budget exceeded")
            path = ROOT / "data" / "images" / f"{image['id']}.jpg"
            tags, tokens = vision_tags(image["id"], path)
            tag_status = "ready" if tags.confidence >= settings.vision_confidence_threshold else "flagged"
            conn.execute(
                """INSERT INTO image_tags(image_id,tenant_id,subject,category,attributes,caption,confidence,status,model)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (image_id) DO UPDATE SET subject=EXCLUDED.subject,category=EXCLUDED.category,attributes=EXCLUDED.attributes,caption=EXCLUDED.caption,confidence=EXCLUDED.confidence,status=EXCLUDED.status,model=EXCLUDED.model,updated_at=now()""",
                (image["id"], tenant_id, tags.subject, tags.category, Jsonb(tags.attributes), tags.caption, tags.confidence, tag_status, settings.vision_model),
            )
            _record_cost(conn, tenant_id, job_id, "vision", settings.vision_model, tokens)
            vector, tokens = embed_text(f"{tags.subject}. {tags.caption}. {' '.join(tags.attributes)}")
            conn.execute(
                """INSERT INTO embeddings(tenant_id,entity_type,entity_id,model,dimensions,embedding_values)
                   VALUES (%s,'image',%s,%s,%s,%s)
                   ON CONFLICT (tenant_id,entity_type,entity_id,model) DO UPDATE SET dimensions=EXCLUDED.dimensions,embedding_values=EXCLUDED.embedding_values,created_at=now()""",
                (tenant_id, image["id"], settings.embedding_model, len(vector), vector),
            )
            _record_cost(conn, tenant_id, job_id, "image_embedding", settings.embedding_model, tokens)
            conn.execute("UPDATE jobs SET processed=processed+1, updated_at=now() WHERE id=%s", (job_id,))
        for post in posts:
            calls = conn.execute("SELECT count(*) AS count FROM cost_events WHERE job_id=%s", (job_id,)).fetchone()["count"]
            if calls >= settings.ai_max_calls_per_job:
                raise RuntimeError("AI call budget exceeded")
            vector, tokens = embed_text(f"{post['subject']}. {post['title']}. {post['body']}")
            conn.execute(
                """INSERT INTO embeddings(tenant_id,entity_type,entity_id,model,dimensions,embedding_values)
                   VALUES (%s,'post',%s,%s,%s,%s)
                   ON CONFLICT (tenant_id,entity_type,entity_id,model) DO UPDATE SET dimensions=EXCLUDED.dimensions,embedding_values=EXCLUDED.embedding_values,created_at=now()""",
                (tenant_id, str(post["id"]), settings.embedding_model, len(vector), vector),
            )
            _record_cost(conn, tenant_id, job_id, "post_embedding", settings.embedding_model, tokens)
            conn.execute("UPDATE jobs SET processed=processed+1, updated_at=now() WHERE id=%s", (job_id,))
        conn.execute("UPDATE jobs SET status='completed', updated_at=now() WHERE id=%s", (job_id,))


def run_once() -> bool:
    with connection() as conn:
        job = conn.execute("""SELECT * FROM jobs WHERE status='queued' ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1""").fetchone()
        if not job:
            return False
    try:
        process_job(job)
    except Exception as exc:
        with connection() as conn:
            fresh = conn.execute("SELECT attempts FROM jobs WHERE id=%s", (job["id"],)).fetchone()
            attempts = fresh["attempts"] if fresh else 1
            status = "queued" if attempts < 3 else "failed"
            conn.execute("UPDATE jobs SET status=%s,last_error=%s,updated_at=now() WHERE id=%s", (status, str(exc)[:1000], job["id"]))
        print(f"job {job['id']} failed attempt: {exc}")
    return True


def main() -> None:
    while True:
        if not run_once():
            time.sleep(2)


if __name__ == "__main__":
    main()
