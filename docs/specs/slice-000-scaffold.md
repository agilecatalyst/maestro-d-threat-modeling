# Slice 000 — Docker scaffold + health endpoints

**Status:** VERIFIED (slice 000 complete — see history in slicedworkload.md)  
**Owner review:** Maestro Data · **Gate:** Maître D  
**Workload tracker:** [slicedworkload.md](../../slicedworkload.md)

---

## Context

Maestro'D ThreatModeling greenfield. Planning docs (`specsrebuild.md`, `NOTICE`, `agents.md`) bestaan al.  
Jij (Local Builder / Gemma 4 12B) implementeert de **eerste runnable stack**: Compose + API stub + agent stub + Postgres container (nog geen migrations/ORM — dat is slice 001).

Referentie: [specsrebuild.md §5–§13](../../specsrebuild.md)

---

## Requirements

| ID | Requirement |
|----|-------------|
| **R1** | `docker-compose.yml` SHALL start `postgres`, `api`, `tm-agent` without error |
| **R2** | `api` SHALL expose `GET /health` → `200` + JSON `{"status":"healthy"}` |
| **R3** | `tm-agent` SHALL expose `GET /ping` → `200` + JSON `{"status":"Healthy"}` (upstream-convention) |
| **R4** | Postgres SHALL use a **named volume** `postgres_data` (data persists across restarts) |
| **R5** | Diagram volume SHALL mount `./data/diagrams` read-write into `api` at `/data/diagrams` |
| **R6** | Services SHALL load env from `.env` — ship `.env.example` already exists; document `cp .env.example .env` in compose comment or README one-liner |
| **R7** | `INFERENCE_BASE_URL` SHALL be passed to `tm-agent` env (no LLM call in this slice — env only) |
| **R8** | Python **3.12** slim images for `api` and `tm-agent` |

---

## Files — ALLOWED actions

| Actie | Pad |
|-------|-----|
| **CREATE** | `docker-compose.yml` |
| **CREATE** | `backend/api/Dockerfile` |
| **CREATE** | `backend/api/requirements.txt` |
| **CREATE** | `backend/api/main.py` |
| **CREATE** | `backend/agent/Dockerfile` |
| **CREATE** | `backend/agent/requirements.txt` |
| **CREATE** | `backend/agent/main.py` |
| **CREATE** | `test/test_health.py` (minimal — optional maar aanbevolen) |
| **MODIFY** | `README.md` — max **5 regels** “Quick start compose” |
| **MODIFY** | [slicedworkload.md](../../slicedworkload.md) — checklist + builder notes only |

---

## MUST NOT touch

- `specsrebuild.md`, `agents.md`, `NOTICE` (behalve slicedworkload)
- `docs/specs/slice-000-scaffold.md` (deze spec)
- `docs/reference/*`
- `frontend/` (slice 009)
- Geen MinIO, boto3, DynamoDB, Terraform
- Geen LangGraph in slice 000 — alleen FastAPI stubs
- Geen nieuwe dependencies buiten: `fastapi`, `uvicorn[standard]`, `pydantic` (api + agent)

---

## Interface contract

### `GET /health` (api, port 8000)

```json
{"status": "healthy", "service": "maestro-d-api"}
```

### `GET /ping` (tm-agent, port 8080)

```json
{"status": "Healthy", "service": "maestro-d-agent"}
```

### Compose ports (host)

| Service | Host port |
|---------|-----------|
| `api` | 8000 |
| `tm-agent` | 8080 |
| `postgres` | 5432 |

---

## docker-compose.yml — minimum shape

```yaml
# SHALL include:
services:
  postgres:   # image postgres:16, volume postgres_data, healthcheck
  api:        # build backend/api, ports 8000:8000, depends_on postgres healthy
  tm-agent:   # build backend/agent, ports 8080:8080, extra_hosts host.docker.internal
volumes:
  postgres_data:
```

`tm-agent` env SHALL include from `.env`: `INFERENCE_BASE_URL`, `INFERENCE_API_KEY`, `LOCAL_MODEL` (values from `.env.example`).

---

## Definition of Done (Builder claims done)

Maître D of Maestro voert uit na jouw `BUILDER_CLAIMS_DONE`:

```bash
cd maestro-d-threat-modeling
cp .env.example .env   # if .env missing
docker compose up --build -d
curl -sf http://localhost:8000/health
curl -sf http://localhost:8080/ping
docker compose ps    # all running
```

Optioneel:

```bash
pytest test/test_health.py -q
```

---

## Local Builder instructie (copy-paste)

```text
You are Local Builder for Maestro'D ThreatModeling (Gemma 4 12B).

Read in order:
1. specsrebuild.md (architecture only)
2. docs/specs/slice-000-scaffold.md (this slice — binding)
3. slicedworkload.md (update checklist as you go)

Implement ONLY slice 000. Follow every SHALL/MUST. Respect MUST NOT touch.
After each completed checklist item, update slicedworkload.md.
When all items are [x], set status to BUILDER_CLAIMS_DONE and stop.
Do not start slice 001.
```

---

## Out of scope (slice 001+)

- SQLAlchemy, Alembic, database tables
- Upload endpoints, LangGraph, Sentry
- Frontend, PDF export
