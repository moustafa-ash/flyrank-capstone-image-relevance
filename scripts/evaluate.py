from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.config import settings
from app.db import connection
from app.guard import canonical, cosine


ROOT = Path(__file__).resolve().parents[1]


def _rows():
    with connection() as conn:
        posts = conn.execute("SELECT * FROM posts WHERE tenant_id='demo' ORDER BY slug").fetchall()
        images = conn.execute(
            """SELECT i.id, t.subject, t.confidence, e.embedding_values
               FROM images i JOIN image_tags t ON t.image_id=i.id
               JOIN embeddings e ON e.entity_id=i.id AND e.entity_type='image' AND e.tenant_id='demo'
               WHERE i.tenant_id='demo'"""
        ).fetchall()
        post_vectors = {
            str(row["id"]): conn.execute("SELECT embedding_values FROM embeddings WHERE entity_type='post' AND entity_id=%s AND tenant_id='demo' ORDER BY created_at DESC LIMIT 1", (str(row["id"]),)).fetchone()
            for row in posts
        }
    return posts, images, post_vectors


def evaluate(similarity_threshold: float) -> dict:
    labels = {row["post_slug"]: row["expected_subject"] for row in json.loads((ROOT / "data" / "eval.json").read_text(encoding="utf-8"))}
    posts, images, post_vectors = _rows()
    top1_correct = 0
    accepted = 0
    rows = []
    for post in posts:
        if post["slug"] not in labels or not post_vectors.get(str(post["id"])):
            continue
        vector = post_vectors[str(post["id"])] ["embedding_values"]
        # ponytail: linear scan is intentional for ~50 images; use pgvector when corpus latency requires it.
        candidates = []
        for image in images:
            score = cosine(list(vector), list(image["embedding_values"]))
            if canonical(image["subject"]) == canonical(post["subject"]) and image["confidence"] >= settings.vision_confidence_threshold and score >= similarity_threshold:
                candidates.append((score, image["subject"], image["id"]))
        candidates.sort(reverse=True)
        if candidates:
            accepted += 1
            correct = canonical(candidates[0][1]) == canonical(labels[post["slug"]])
            top1_correct += int(correct)
            rows.append({"post": post["slug"], "top1": candidates[0][2], "score": round(candidates[0][0], 6), "correct": correct})
    return {"posts": len(rows), "accepted": accepted, "top1_correct": top1_correct, "top1_precision": round(top1_correct / len(rows), 4) if rows else 0.0, "similarity_threshold": similarity_threshold, "rows": rows}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-thresholds", action="store_true")
    args = parser.parse_args()
    results = [evaluate(round(value, 2)) for value in [0.50 + i * 0.05 for i in range(10)]]
    chosen = next((row for row in results if row["posts"] and row["top1_precision"] == 1.0), results[0])
    output = {"chosen": chosen, "grid": results}
    if args.write_thresholds:
        thresholds = json.loads((ROOT / "config" / "thresholds.json").read_text(encoding="utf-8"))
        thresholds.update({"similarity_threshold": chosen["similarity_threshold"], "status": "measured from live evaluation"})
        (ROOT / "config" / "thresholds.json").write_text(json.dumps(thresholds, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
