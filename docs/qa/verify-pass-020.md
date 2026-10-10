# Verify pass — slice 020 (Pluggable LLM providers)

**Date:** 2026-10-10  
**Runner:** Junie (coding agent, offline sandbox)  
**Command:** standalone assertion runner — `bash scripts/verify-pass.sh` **not** executable here

## Environment constraint

The sandbox has **no PyPI/npm network access**: `pytest`, the backend wheels and
`frontend/node_modules` could not be installed, and Docker images could not be
built. The provider registry and the role resolver were therefore verified with
a standalone Python script that mirrors the new pytest assertions one-for-one.

## Results

| Suite | Result |
|-------|--------|
| Provider registry (4 kinds, unknown kind, missing base_url, missing SDK) | **passed** (standalone) |
| Legacy env path + `MODEL_PROVIDER` → `kind` mapping (6 cases) | **passed** (standalone) |
| Role resolution: DB override, role separation, TTL cache, fallback | **passed** (standalone) |
| `api_key_env` allowlist (`INFERENCE_API_KEY`, `LLM_*` vs `POSTGRES_PASSWORD`, `PATH`) | **passed** (standalone) |
| API CRUD / roles / test endpoint (`test/test_llm_provider_api.py`) | **not run** — needs Postgres + FastAPI |
| `test/test_inference.py` payload update | **not run** — needs running tm-agent |
| Frontend `tsc --noEmit` | **not run** — no `node_modules` |

## Slice 020 changes to re-verify on a networked machine

- `langchain-anthropic` / `langchain-google-genai` are **commented out** in both
  `requirements.txt` with band pins (`>=1.3,<2` / `>=3,<5`). Resolve exact pins
  with `pip-audit` and move them to `docs/dev/dependencies.md` as hard pins if
  the cloud providers become part of the default image.
- Alembic `003_llm_providers` upgrade/downgrade against a real Postgres
  (uses `gen_random_uuid()` — requires `pgcrypto` or PG13+).
- `POST /admin/llm-providers/{id}/test` against a live LM Studio / cloud key.

## Re-run

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml build api tm-agent
bash scripts/verify-pass.sh
cd frontend && npm ci && npx tsc --noEmit
```
