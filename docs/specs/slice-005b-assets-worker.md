# Slice 005b — Assets worker (after summary)

**Status:** READY_FOR_BUILDER  
**Depends on:** [slice-005a-assets-parser.md](slice-005a-assets-parser.md) `VERIFIED`

> Chain after summary. Text LLM + parser fallback. **Max 3 code files.**

---

## Requirements

| ID | Requirement |
|----|-------------|
| **R1** | `pipeline_worker.py` — `run_pipeline(job_id, diagram_path, description, application_type)` calls `run_summary` then `run_assets` |
| **R2** | `assets_worker.py` — read summary from DB detail; LLM text prompt; `parse_assets_list_from_text`; store `assets` in detail JSON |
| **R3** | `db.py` — ADD `merge_job_detail(job_id, state, **fields)` — merge into existing detail dict |
| **R4** | `invocations.py` — swap `run_summary` → `run_pipeline` in BackgroundTasks only |
| **R5** | Final state `ASSETS_DONE` when assets parsed; `FAILED` on error; min 1 asset or fallback stub asset from description |
| **R6** | Flat imports. MUST NOT replace `/ping`, `/inference/health`, 202 contract |

---

## Files — ALLOWED

| Actie | Pad |
|-------|-----|
| **CREATE** | `backend/agent/pipeline_worker.py` |
| **CREATE** | `backend/agent/assets_worker.py` |
| **MODIFY** | `backend/agent/db.py` — ADD merge only |
| **MODIFY** | `backend/agent/routes/invocations.py` — task name only |

**MUST NOT:** parser files, requirements, compose, api/

---

## DoD

```bash
docker compose up --build -d tm-agent
pytest test/test_summary.py -q   # still passes; may take longer
# job_status.detail has summary + assets list
```

---

## Builder

Append only. ===FILE: first. Use `parse_assets_list_from_text` from asset_text_parser.
