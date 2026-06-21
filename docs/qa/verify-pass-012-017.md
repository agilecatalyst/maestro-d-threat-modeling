# Verify pass — slices 010–017

**Date:** 2026-06-09  
**Runner:** Composer (Maestro Data) · **Sign-off gate:** pytest + smoke **before** VERIFIED  
**Command:** `bash scripts/verify-pass.sh`

## Prerequisites

- Docker Desktop running
- `docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile full up -d postgres api tm-agent`

## Results

| Suite | Result |
|-------|--------|
| Host: `test_health`, `test_inference`, `test_upload` | **5 passed, 1 skipped** |
| API container (job, mutations, audit, rate limit, export, db, backup, …) | **27 passed** |
| Agent container (parsers, workflow graph) | **11 passed** |
| `scripts/smoke.sh` | **OK** |

**Total: 43 passed, 1 skipped, 0 failed**

### Skipped

- `test_inference` — skipped when host LLM (oMLX) not reachable (expected in CI/local without inference)

### Not in automated pass

- `test/test_summary.py` — requires live LLM + full pipeline (manual E2E)
- Frontend build — run separately: `cd frontend && npm run build`

## Fixes applied during pass

- Repaired Alembic stamp without schema (local Postgres had head stamp but no tables)
- `test/test_db.py` — re-migrate when other tests' `drop_all` left Alembic stamp orphaned
- `scripts/verify-pass.sh` — post-API-test schema repair before smoke (pytest `drop_all` teardown)
- `backup_service.py` — restore insert order + explicit catalog cleanup (FK-safe)
- `test/test_backup_restore.py` — row cleanup instead of `drop_all` in fixture teardown

## Slices verified

| Slice | Scope | Status after pass |
|-------|--------|-------------------|
| 010–011 | PDF + JSON export | **VERIFIED** |
| 012 | Threat edit, flow scan, Sentry | **VERIFIED** |
| 013 | DevSecOps hardening | **VERIFIED** |
| 014 | License & attribution | **VERIFIED** |
| 015 | Security ops | **VERIFIED** |
| 016 | MVP polish | **VERIFIED** |
| 017 | DB backup/restore JSON | **VERIFIED** |

*Slices 000–009 were VERIFIED in earlier builder/review cycles.*

## Re-run

```bash
bash scripts/verify-pass.sh
```
