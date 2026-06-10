# Slice 002a — Diagram POST upload only

**Status:** READY_FOR_BUILDER  
**Owner review:** Maestro Data (tech lead) · **Gate:** Maître D  
**Workload tracker:** [slicedworkload.md](../../slicedworkload.md)  
**Depends on:** [slice-001-database.md](slice-001-database.md) `VERIFIED`  
**Next:** [slice-002b-upload-get-test.md](slice-002b-upload-get-test.md)

> **Klein slice** — max 3 code-files. Geen GET, geen pytest in deze slice.

---

## Context

Bob run 1 leverde partial code (`storage.py`, `routes/diagrams.py`, `main.py`).  
Deze slice: **alleen POST upload** werkend maken — fix imports, UUID, `JobStatus` insert.

`test/fixtures/sample.png` wordt door **tech lead** geleverd — Builder genereert geen binary.

---

## Requirements

| ID | Requirement |
|----|-------------|
| **R1** | `POST /threat-designer/diagrams` — `multipart/form-data`, field `file` |
| **R2** | MIME: `image/png`, `image/jpeg` only — else **400** |
| **R3** | Max **10 MB** — else **413** |
| **R4** | Save to `DIAGRAM_STORAGE_PATH` as `{uuid}.{ext}` |
| **R5** | Insert `threat_models` + `job_status` (`id` = same UUID FK, `state=PENDING`) |
| **R6** | `diagram_path` = relative filename in DB |
| **R7** | Response **200**: `{"id","diagram_path","owner","state":"PENDING"}` |
| **R8** | Imports: `from database import get_db, LOCAL_USER` — `from models import ThreatModel, JobStatus` |
| **R9** | `GET /health` unchanged |
| **R10** | `python-multipart` in requirements (pin dependencies.md § Slice 002) |

---

## Files — ALLOWED (max 3 code files)

| Actie | Pad |
|-------|-----|
| **CREATE/MODIFY** | `backend/api/storage.py` |
| **CREATE/MODIFY** | `backend/api/routes/diagrams.py` — **POST only** (geen GET) |
| **MODIFY** | `backend/api/main.py` — router mount |
| **MODIFY** | `backend/api/requirements.txt` — `python-multipart` |
| **MODIFY** | [slicedworkload.md](../../slicedworkload.md) |

**MUST NOT:** `test/test_upload.py`, GET route, `backend/agent/*`, alembic, compose

---

## Definition of Done

```bash
docker compose up --build -d api
curl -sf http://localhost:8000/health | grep connected
curl -sf -X POST http://localhost:8000/threat-designer/diagrams \
  -F "file=@test/fixtures/sample.png"
ls data/diagrams/*.png
```

---

## Builder instructie

```text
Slice 002a ONLY. POST upload. Fix partial code from run 1.
Imports: database + models (flat, no backend.api.db).
JobStatus.id = ThreatModel.id (UUID). Minimal prose. ===FILE=== blocks only.
No GET endpoint. No test files. BUILDER_CLAIMS_DONE when DoD ready.
```
