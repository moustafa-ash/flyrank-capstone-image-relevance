# Evidence

Phase 1 repository gate is complete. Runtime and acceptance evidence will be pasted here as each phase is verified.

## Phase 2 deterministic checks

```text
compileall=ok
4 passed in 0.28s
docker compose config --quiet -> exit 0
```

These are local fixture/configuration checks, not live Gemini or PostgreSQL acceptance evidence.

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
