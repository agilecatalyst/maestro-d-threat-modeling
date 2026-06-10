# Slice 002 — Diagram upload (volume + DB row)

**Status:** SUPERSEDED — split into [slice-002a-upload-post.md](slice-002a-upload-post.md) + [slice-002b-upload-get-test.md](slice-002b-upload-get-test.md)  
**Owner review:** Maestro Data · **Gate:** Maître D  
**Workload tracker:** [slicedworkload.md](../../slicedworkload.md)  
**Depends on:** [slice-001-database.md](slice-001-database.md) `VERIFIED`

---

## Context

Slice 001 levert Postgres-tabellen `threat_models` + `job_status`.  
Slice 002 voegt **directe diagram-upload** toe — geen S3/presigned URL (Maestro'D local-first).

Flow: client uploadt PNG/JPG → API schrijft bestand naar volume → DB-row met `diagram_path`.

Referentie: [specsrebuild.md §5 Opslag](../../specsrebuild.md) · upstream upload-concept (zonder MinIO).

---

## Requirements

| ID | Requirement |
|----|-------------|
| **R1** | `POST /threat-designer/diagrams` SHALL accept `multipart/form-data` with field `file` |
| **R2** | Allowed MIME types: `image/png`, `image/jpeg` — else **400** |
| **R3** | Max file size **10 MB** — else **413** |
| **R4** | API SHALL write file to `DIAGRAM_STORAGE_PATH` env (default `/data/diagrams`) as `{uuid}.{ext}` |
| **R5** | API SHALL insert `threat_models` row (`owner=LOCAL_USER`) + linked `job_status` (`state=PENDING`) |
| **R6** | `threat_models.diagram_path` SHALL store relative path e.g. `{uuid}.png` (not absolute host path) |
| **R7** | Response **200** JSON: `{"id":"<uuid>","diagram_path":"<filename>","owner":"<LOCAL_USER>","state":"PENDING"}` |
| **R8** | `GET /threat-designer/diagrams/{id}` SHALL return metadata JSON (id, owner, diagram_path, state, title if set) — **404** if missing |
| **R9** | `GET /health` behaviour from slice 001 SHALL remain unchanged |
| **R10** | Dependency: add `python-multipart` per [dependencies.md § Slice 002](../dev/dependencies.md) |
| **R11** | `backend/agent/` SHALL NOT be modified |

---

## Files — ALLOWED actions

| Actie | Pad |
|-------|-----|
| **CREATE** | `backend/api/storage.py` — `LocalFileStorage` (save, resolve path) |
| **CREATE** | `backend/api/routes/diagrams.py` — upload + get routes |
| **CREATE** | `test/test_upload.py` — upload roundtrip (pytest) |
| **MODIFY** | `backend/api/main.py` — mount router, keep `/health` |
| **MODIFY** | `backend/api/requirements.txt` — add `python-multipart` |
| **MODIFY** | [slicedworkload.md](../../slicedworkload.md) — checklist + builder notes only |

---

## MUST NOT touch

- `specsrebuild.md`, `agents.md`, `NOTICE`, deze spec
- `backend/agent/*`, `docker-compose.yml` (volume al OK)
- Alembic migrations (schema heeft al `diagram_path`)
- LangGraph, LLM calls, PDF, frontend, Sentry
- `scripts/local_builder.py`, `docs/dev/dependencies.md`

---

## Interface contract

### `POST /threat-designer/diagrams`

```bash
curl -sf -X POST http://localhost:8000/threat-designer/diagrams \
  -F "file=@/path/to/diagram.png"
```

Response `200`:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "diagram_path": "550e8400-e29b-41d4-a716-446655440000.png",
  "owner": "local-user",
  "state": "PENDING"
}
```

### `GET /threat-designer/diagrams/{id}`

Response `200`:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "owner": "local-user",
  "diagram_path": "550e8400-e29b-41d4-a716-446655440000.png",
  "state": "PENDING",
  "title": null
}
```

---

## `LocalFileStorage` — minimum shape

```python
# storage.py SHALL expose:
# - save_upload(file_bytes, filename_hint) -> relative_path str
# - full_path(relative_path) -> Path under DIAGRAM_STORAGE_PATH
```

---

## Definition of Done (Builder claims done)

```bash
cd maestro-d-threat-modeling
docker compose up --build -d
curl -sf http://localhost:8000/health | grep '"database":"connected"'
# gebruik een echte png/jpg, bijv. docs/samples of assets:
curl -sf -X POST http://localhost:8000/threat-designer/diagrams -F "file=@test/fixtures/sample.png"
# noteer id uit response, dan:
curl -sf http://localhost:8000/threat-designer/diagrams/<id>
ls -la data/diagrams/   # bestand aanwezig
docker compose run --rm -v "$PWD/test:/test:ro" -e DATABASE_URL=postgresql://maestro:maestro@postgres:5432/maestro_d api sh -c 'pip install -q pytest httpx && PYTHONPATH=/app pytest /test/test_upload.py -q'
```

Als geen `test/fixtures/sample.png`: Builder SHALL create minimal 1×1 PNG in `test/fixtures/sample.png`.

---

## Local Builder instructie (copy-paste)

```text
You are Local Builder for Maestro'D ThreatModeling (Gemma 4 12B).

Read in order:
1. specsrebuild.md (§5 storage)
2. docs/dev/dependencies.md (Slice 002 pin)
3. docs/specs/slice-002-diagram-upload.md (binding)
4. slicedworkload.md

Implement ONLY slice 002. Respect MUST NOT touch.
Use existing database.py, models.py patterns from slice 001.
When done: BUILDER_CLAIMS_DONE. Do not start slice 003.
```

---

## Out of scope (slice 003+)

- Presigned URLs, boto3, MinIO
- Start threat-modeling job / tm-agent invoke
- Image processing beyond save
