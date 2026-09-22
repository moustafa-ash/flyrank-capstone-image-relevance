from __future__ import annotations

import json
from pathlib import Path

from .db import connection


def seed() -> None:
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / "data" / "corpus.json").read_text(encoding="utf-8"))
    posts = json.loads((root / "data" / "posts.json").read_text(encoding="utf-8"))
    with connection() as conn:
        conn.execute("INSERT INTO tenants(id, name) VALUES ('demo', 'Demo tenant') ON CONFLICT (id) DO NOTHING")
        for image in manifest["images"]:
            conn.execute(
                """INSERT INTO images(id, tenant_id, source_page, image_url, license, sha256)
                   VALUES (%s,'demo',%s,%s,%s,%s)
                   ON CONFLICT (id) DO UPDATE SET source_page=EXCLUDED.source_page, image_url=EXCLUDED.image_url, license=EXCLUDED.license""",
                (image["id"], image["source_page"], image["image_url"], image["license"], image.get("sha256")),
            )
        for post in posts:
            conn.execute(
                """INSERT INTO posts(tenant_id, slug, title, body, subject, category)
                   VALUES ('demo',%s,%s,%s,%s,%s)
                   ON CONFLICT (tenant_id, slug) DO UPDATE SET title=EXCLUDED.title, body=EXCLUDED.body, subject=EXCLUDED.subject, category=EXCLUDED.category""",
                (post["slug"], post["title"], post["body"], post["subject"], post["category"]),
            )
    print(f"seeded {len(manifest['images'])} images and {len(posts)} posts")


if __name__ == "__main__":
    seed()

