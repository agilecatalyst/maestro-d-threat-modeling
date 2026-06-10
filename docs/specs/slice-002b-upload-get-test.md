# Slice 002b — Diagram GET metadata + pytest

**Status:** WAITING (after 002a VERIFIED)  
**Depends on:** [slice-002a-upload-post.md](slice-002a-upload-post.md) `VERIFIED`

> **Klein slice** — 2 files: route GET + test.

---

## Requirements

| ID | Requirement |
|----|-------------|
| **R1** | `GET /threat-designer/diagrams/{id}` → metadata JSON — **404** if missing |
| **R2** | Response includes: `id`, `owner`, `diagram_path`, `state`, `title` |
| **R3** | `test/test_upload.py` — POST then GET roundtrip (httpx of requests) |
| **R4** | `POST /health` unchanged; POST upload from 002a unchanged |

---

## Files — ALLOWED

| Actie | Pad |
|-------|-----|
| **MODIFY** | `backend/api/routes/diagrams.py` — add GET only |
| **CREATE** | `test/test_upload.py` |
| **MODIFY** | [slicedworkload.md](../../slicedworkload.md) |

---

## Definition of Done

```bash
pytest test/test_upload.py -q
curl -sf http://localhost:8000/threat-designer/diagrams/<id-from-post>
```
