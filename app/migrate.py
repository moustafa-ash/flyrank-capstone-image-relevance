from __future__ import annotations

from pathlib import Path

from .db import connection


def apply_migrations() -> None:
    root = Path(__file__).resolve().parents[1]
    with connection() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())")
        for path in sorted((root / "migrations").glob("*.sql")):
            version = path.name
            if conn.execute("SELECT 1 FROM schema_migrations WHERE version=%s", (version,)).fetchone():
                continue
            conn.execute(path.read_text(encoding="utf-8"))
            conn.execute("INSERT INTO schema_migrations(version) VALUES (%s)", (version,))
        conn.execute("INSERT INTO tenants(id, name) VALUES ('demo', 'Demo tenant') ON CONFLICT (id) DO NOTHING")


if __name__ == "__main__":
    apply_migrations()
    print("migrations applied")

