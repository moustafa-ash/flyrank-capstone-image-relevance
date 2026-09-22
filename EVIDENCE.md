# Evidence

Phase 1 repository gate is complete. Runtime and acceptance evidence will be pasted here as each phase is verified.

## Phase 2 deterministic checks

```text
compileall=ok
4 passed in 0.28s
docker compose config --quiet -> exit 0
```

These are local fixture/configuration checks, not live Gemini or PostgreSQL acceptance evidence.

## Evidence policy

- Every claim must include a fresh command, test name, curl transcript, or database output.
- Fixture-provider output is labeled deterministic and is never presented as Gemini quality evidence.
- Secrets and `.env` contents are never pasted here.
