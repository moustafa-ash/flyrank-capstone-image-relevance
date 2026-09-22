# FlyRank Image-Relevance Engine

An AI image understanding and semantic article-matching API. It tags a small Pexels image library with validated structured vision output, embeds image descriptions and article text, ranks candidates, and refuses wrong matches with an explanation.

## Status

Phases 1–4 implementation and documentation are committed. Deterministic checks pass; live Gemini and PostgreSQL evidence is added after Docker is started with a configured key.

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
4. Download the licensed corpus locally: `python scripts/fetch_corpus.py`.
5. Enqueue catalog processing with `POST /v1/jobs/catalog` and `Idempotency-Key: demo-catalog-v1`.

The final measured top-1 precision and tuned thresholds are intentionally not fabricated: they are written after live verification.

After the worker completes, run `python scripts/evaluate.py --write-thresholds`. The command evaluates the ten labeled posts across a similarity-threshold grid and writes the selected threshold plus the manifest digest to `config/thresholds.json`.

Use `python scripts/probe.py` for the health, idempotent catalog, and clean-error smoke probes. Live provider calls require `AI_MODE=gemini`; the default fixture mode is deterministic and offline.

## Limitations

Tenant IDs are trusted request headers because authentication is outside this capstone's required scope. Vectors use PostgreSQL arrays and a linear scan, which is appropriate for the 50-image corpus but should become pgvector or a dedicated index as the corpus grows. Live precision and threshold values are recorded only after a real Gemini catalog run.

## Deterministic verification

The fixture provider is used for offline tests and never claimed as Gemini quality evidence. Run `uv run --no-project --with pytest --with pydantic pytest -q tests` for the current four core guard checks.

## Attribution

The corpus manifest records Pexels source pages and direct image URLs. Downloaded images are intentionally excluded from Git; the seed/download step records their SHA-256 lock file locally.
