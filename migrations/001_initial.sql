CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS tenants (id TEXT PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS images (
  id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL REFERENCES tenants(id), source_page TEXT NOT NULL, image_url TEXT NOT NULL,
  license TEXT NOT NULL, sha256 TEXT, status TEXT NOT NULL DEFAULT 'pending', last_error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE (tenant_id, sha256)
);
CREATE TABLE IF NOT EXISTS image_tags (
  image_id TEXT PRIMARY KEY REFERENCES images(id) ON DELETE CASCADE, tenant_id TEXT NOT NULL REFERENCES tenants(id),
  subject TEXT NOT NULL, category TEXT NOT NULL, attributes JSONB NOT NULL, caption TEXT NOT NULL,
  confidence DOUBLE PRECISION NOT NULL CHECK (confidence >= 0 AND confidence <= 1), status TEXT NOT NULL, model TEXT NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS posts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id TEXT NOT NULL REFERENCES tenants(id), slug TEXT NOT NULL,
  title TEXT NOT NULL, body TEXT NOT NULL, subject TEXT NOT NULL, category TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE (tenant_id, slug)
);
CREATE TABLE IF NOT EXISTS embeddings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id TEXT NOT NULL REFERENCES tenants(id), entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL, model TEXT NOT NULL, dimensions INTEGER NOT NULL, embedding_values REAL[] NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE (tenant_id, entity_type, entity_id, model)
);
CREATE TABLE IF NOT EXISTS jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id TEXT NOT NULL REFERENCES tenants(id), kind TEXT NOT NULL,
  idempotency_key TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'queued', attempts INTEGER NOT NULL DEFAULT 0,
  processed INTEGER NOT NULL DEFAULT 0, total INTEGER NOT NULL DEFAULT 0, last_error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, idempotency_key)
);
CREATE TABLE IF NOT EXISTS suggestions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id TEXT NOT NULL REFERENCES tenants(id), post_id UUID NOT NULL REFERENCES posts(id),
  image_id TEXT NOT NULL REFERENCES images(id), similarity DOUBLE PRECISION NOT NULL, decision TEXT NOT NULL,
  reasons JSONB NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS reviews (
  suggestion_id UUID PRIMARY KEY REFERENCES suggestions(id) ON DELETE CASCADE, tenant_id TEXT NOT NULL REFERENCES tenants(id),
  decision TEXT NOT NULL CHECK (decision IN ('approved','rejected')), note TEXT NOT NULL DEFAULT '', reviewed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS cost_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id TEXT NOT NULL REFERENCES tenants(id), job_id UUID REFERENCES jobs(id),
  operation TEXT NOT NULL, provider TEXT NOT NULL, model TEXT NOT NULL, prompt_tokens INTEGER NOT NULL DEFAULT 0,
  candidate_tokens INTEGER NOT NULL DEFAULT 0, estimated_usd DOUBLE PRECISION NOT NULL DEFAULT 0,
  list_price_estimate_usd DOUBLE PRECISION NOT NULL DEFAULT 0, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS images_tenant_status_idx ON images(tenant_id, status);
CREATE INDEX IF NOT EXISTS embeddings_lookup_idx ON embeddings(tenant_id, entity_type, entity_id);
CREATE INDEX IF NOT EXISTS jobs_queue_idx ON jobs(status, created_at);
CREATE INDEX IF NOT EXISTS suggestions_post_idx ON suggestions(tenant_id, post_id, created_at);
CREATE INDEX IF NOT EXISTS cost_events_job_idx ON cost_events(tenant_id, job_id);
