# Slice 001 — Postgres schema + Alembic + local-user

**Status:** READY_FOR_BUILDER  
**Owner review:** Maestro Data · **Gate:** Maître D  
**Workload tracker:** [slicedworkload.md](../../slicedworkload.md)  
**Depends on:** [slice-000-scaffold.md](slice-000-scaffold.md) `VERIFIED`

---

## Context

Slice 000 levert een runnable Compose-stack zonder database-logica.  
Slice 001 voegt **persistente metadata** toe in Postgres: SQLAlchemy models, Alembic migrations, DB-connectie in `api`, en de v1 **`local-user`** stub (geen auth — owner-kolom default).

Referentie architectuur: [specsrebuild.md §5, §12](../../specsrebuild.md)  
Upstream DynamoDB-concepten (vereenvoudigd): `threat_models` ≈ agent state, `job_status` ≈ processing state.

**Niet in deze slice:** diagram upload (002), LangGraph (003+), REST job-flow (008).

---

## Requirements

| ID | Requirement |
|----|-------------|
| **R1** | `api` SHALL connect to Postgres via `DATABASE_URL` env |
| **R2** | Alembic SHALL live under `backend/api/alembic/` with `alembic.ini` in `backend/api/` |
| **R3** | Initial migration SHALL create table `threat_models` (see schema below) |
| **R4** | Initial migration SHALL create table `job_status` (see schema below) |
| **R5** | `api` startup SHALL run `alembic upgrade head` before serving (lifespan or equivalent) |
| **R6** | `GET /health` SHALL remain `200` and **extend** JSON with `"database": "connected"` when DB OK |
| **R7** | `GET /health` SHALL return `"database": "disconnected"` and HTTP **503** if DB unreachable |
| **R8** | `LOCAL_USER` env (default `local-user`) SHALL be the default `owner` on new rows (helper/constant only — no auth) |
| **R9** | Dependency pins SHALL match [dependencies.md § Slice 001](../dev/dependencies.md) exactly |
| **R10** | `backend/agent/` SHALL NOT gain SQLAlchemy or DB code in this slice |

---

## Database schema (v1 minimal)

### `threat_models`

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | `gen_random_uuid()` default |
| `owner` | VARCHAR(255) NOT NULL | default `local-user` |
| `title` | VARCHAR(512) NULL | |
| `diagram_path` | VARCHAR(1024) NULL | slice 002 fills this |
| `application_type` | VARCHAR(128) NULL | |
| `created_at` | TIMESTAMPTZ NOT NULL | server default `now()` |
| `updated_at` | TIMESTAMPTZ NOT NULL | server default `now()` |

Index: `ix_threat_models_owner` on `owner`.

### `job_status`

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | FK → `threat_models.id` ON DELETE CASCADE |
| `state` | VARCHAR(32) NOT NULL | default `PENDING` |
| `detail` | TEXT NULL | |
| `retry_count` | INTEGER NOT NULL | default `0` |
| `updated_at` | TIMESTAMPTZ NOT NULL | server default `now()` |

Allowed `state` values (string, no PG enum yet):  
`PENDING`, `START`, `ASSETS`, `FLOW`, `THREAT`, `THREAT_RETRY`, `FINALIZE`, `COMPLETE`, `FAILED`.

---

## Files — ALLOWED actions

| Actie | Pad |
|-------|-----|
| **CREATE** | `backend/api/database.py` — engine, SessionLocal, `get_db()` |
| **CREATE** | `backend/api/models.py` — SQLAlchemy models |
| **CREATE** | `backend/api/alembic.ini` |
| **CREATE** | `backend/api/alembic/env.py` |
| **CREATE** | `backend/api/alembic/script.py.mako` |
| **CREATE** | `backend/api/alembic/versions/001_initial_schema.py` |
| **CREATE** | `test/test_db.py` |
| **MODIFY** | `backend/api/main.py` — lifespan migrate + health DB check |
| **MODIFY** | `backend/api/requirements.txt` — add SQLAlchemy pins |
| **MODIFY** | `backend/api/Dockerfile` — copy `alembic/` if needed |
| **MODIFY** | [slicedworkload.md](../../slicedworkload.md) — checklist + builder notes only |

---

## MUST NOT touch

- `specsrebuild.md`, `agents.md`, `NOTICE`, `docs/specs/slice-001-database.md`
- `backend/agent/*` (behalve als absoluut nodig — **niet nodig**)
- `docker-compose.yml` (postgres service al OK in slice 000)
- `frontend/`, LangGraph, upload endpoints, Sentry
- `scripts/local_builder.py`, `docs/dev/dependencies.md`
- Slice 002+ features

---

## Interface contract

### `GET /health` (extended)

DB OK:

```json
{"status": "healthy", "service": "maestro-d-api", "database": "connected"}
```

DB down:

```json
{"status": "healthy", "service": "maestro-d-api", "database": "disconnected"}
```

HTTP status: **503** when `database` is `disconnected`.

### Env (already in `.env.example`)

| Var | Default |
|-----|---------|
| `DATABASE_URL` | `postgresql://maestro:maestro@postgres:5432/maestro_d` |
| `LOCAL_USER` | `local-user` |

---

## `backend/api/database.py` — minimum shape

```python
# SHALL expose:
# - engine from DATABASE_URL
# - SessionLocal
# - get_db() generator for FastAPI Depends (optional in 001 — tests may use SessionLocal direct)
# - run_migrations() calling alembic upgrade head
```

---

## Definition of Done (Builder claims done)

Maître D of Maestro voert uit na `BUILDER_CLAIMS_DONE`:

```bash
cd maestro-d-threat-modeling
docker compose up --build -d
# wait for api healthy
curl -sf http://localhost:8000/health | grep '"database":"connected"'
docker compose exec api alembic current   # shows head revision
pytest test/test_db.py -q
```

`test/test_db.py` SHALL (minimaal):

1. Assert `threat_models` and `job_status` tables exist (via SQLAlchemy inspector of raw SQL).
2. Insert one `threat_models` row with `owner=LOCAL_USER`, link one `job_status` row `state=PENDING`, commit, read back.

Tests run **against running stack** (`localhost:8000` health) **or** direct `DATABASE_URL` to `localhost:5432` — kies één pad en documenteer in test file comment. Voorkeur: direct Postgres op host `:5432` (compose exposed).

---

## Local Builder instructie (copy-paste)

```text
You are Local Builder for Maestro'D ThreatModeling (Gemma 4 12B).

Read in order:
1. specsrebuild.md (§5 storage, §12 slice 001)
2. docs/dev/dependencies.md (Slice 001 pins — exact)
3. docs/specs/slice-001-database.md (this slice — binding)
4. slicedworkload.md (update checklist as you go)

Implement ONLY slice 001. Follow every SHALL/MUST. Respect MUST NOT touch.
Use dependency pins exactly from dependencies.md.
After each completed checklist item, update slicedworkload.md.
When all items are [x], set status to BUILDER_CLAIMS_DONE and stop.
Do not start slice 002.
```

---

## Out of scope (slice 002+)

- `POST` upload, `StorageBackend`, file writes to volume
- API routes `/threat-designer/*`
- Agent DB access
- PDF, frontend, Sentry
