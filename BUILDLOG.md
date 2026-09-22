# Build log

This file records AI assistance and human decisions for the FlyRank capstone.

## Phase 1

- AI helped extract the PDF requirements, draft the architecture, and prepare the repository pack.
- The owner selected Gemini, a public repository, checkpointed phases, and a Pexels corpus.
- Dataset URLs are references only until the download script records SHA-256 values in `data/corpus.lock.json`.

Future entries will record incorrect suggestions, fixes, live provider runs, and evidence updates.

## Phase 2

- Added PostgreSQL migrations, API/worker/seed Compose services, idempotent catalog jobs, Pydantic vision validation, cost events, and a fixture provider.
- The worker uses PostgreSQL as the queue and retries failed jobs up to three attempts; no Redis or Celery was added.
- Docker Compose configuration validates locally. The daemon still needs to be started before live container evidence can be captured.
