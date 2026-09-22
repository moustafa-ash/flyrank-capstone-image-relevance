# Evidence

Phase 1 repository gate is complete. Runtime and acceptance evidence will be pasted here as each phase is verified.

## Phase 2 deterministic checks

```text
compileall=ok
4 passed in 0.28s
docker compose config --quiet -> exit 0
```

These are local fixture/configuration checks, not live Gemini or PostgreSQL acceptance evidence.

## Live local-stack evidence (fixture provider)

Captured 2026-09-23 with Docker Desktop running and `AI_MODE=fixture`:

```text
docker compose ps -> db healthy, api up :8000, worker up
seeded 50 images and 11 posts
catalog job -> status=completed, attempts=1, processed=61, total=61
image_tags -> tagged=50, flagged=5
embeddings -> embedded=61
cost_events -> vision=100, image_embedding=100, post_embedding=22
GET /health -> 200 {"status":"ok"}
GET wildlife-without-match/images -> status=no_confident_match
GET red-fox-behavior/images -> top subject=red fox
PostgreSQL fox probe -> gray wolf, decision=rejected, reason=category_mismatch
Conflicting review decision -> HTTP 409
scripts/evaluate.py -> fixture top1_precision=1.0, chosen similarity_threshold=0.5
Idempotent catalog replay -> same completed job id
```

This is live PostgreSQL/API/worker evidence, but fixture-provider output is not Gemini quality evidence. The Gemini acceptance boxes remain pending until provider quota permits processing the 50 downloaded images with `AI_MODE=gemini`.

## Gemini provider attempt

The configured local key was used without being printed. The worker reached Google, but the live batch received `429 RESOURCE_EXHAUSTED` on all three retry attempts before any image was processed (`processed=0`). This records provider availability/quota evidence only; no Gemini quality or precision claim is made.

## Phase 3/4 acceptance checklist

- [ ] Batch run: all 50 images have schema-valid tags and at least one low-confidence image is flagged.
- [ ] Red-fox article ranks a red-fox image first; wolf and dog rank lower.
- [ ] Forced wolf candidate is rejected with `category_mismatch`.
- [ ] Unmatched article returns `no_confident_match` with reasons.
- [ ] `scripts/evaluate.py` output and README precision agree.
- [ ] Every vision and embedding call appears in `cost_events` with a budget check.
- [ ] Review approval/rejection and tenant-isolation transcripts captured from PostgreSQL-backed API.

These boxes remain intentionally unchecked until Docker and the Gemini key are available for live verification.

## Evidence policy

- Every claim must include a fresh command, test name, curl transcript, or database output.
- Fixture-provider output is labeled deterministic and is never presented as Gemini quality evidence.
- Secrets and `.env` contents are never pasted here.
