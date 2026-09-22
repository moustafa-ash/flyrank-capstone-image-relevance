# FlyRank Image-Relevance Engine

An AI image understanding and semantic article-matching API. It tags a small Pexels image library with validated structured vision output, embeds image descriptions and article text, ranks candidates, and refuses wrong matches with an explanation.

## Status

Phase 1 design and repository pack are committed. Live Gemini and PostgreSQL evidence is added phase by phase.

## Architecture

```text
images --batch worker--> Gemini Flash-Lite --> validated tags --> image embeddings
posts -----------------> Gemini Embedding 2 ------------------> post embeddings
post + vectors --> cosine ranking --> mismatch guard --> suggestion/review
```

## Run

1. Copy `.env.example` to `.env` and set `GEMINI_API_KEY` for live mode, or leave `AI_MODE=fixture` for deterministic tests.
2. Start the stack: `docker compose up --build`.
3. Seed manifest records and labeled posts: `docker compose run --rm seed`.
4. Enqueue catalog processing with `POST /v1/jobs/catalog` and `Idempotency-Key: demo-catalog-v1`.

The final README will contain the measured top-1 precision, tuned thresholds, curl probes, and limitations after live verification.

## Attribution

The corpus manifest records Pexels source pages and direct image URLs. Downloaded images are intentionally excluded from Git; the seed/download step records their SHA-256 lock file locally.

