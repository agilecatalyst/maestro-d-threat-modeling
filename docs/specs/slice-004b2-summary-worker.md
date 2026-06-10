# Slice 004b2 — Summary background worker

**Status:** WAITING (after 004b1 VERIFIED)  
**Depends on:** [slice-004b1-agent-llm-base.md](slice-004b1-agent-llm-base.md) `VERIFIED`  
**Next:** [slice-004c-summary-test.md](slice-004c-summary-test.md)

> **Klein slice** — BackgroundTasks, geen LangGraph. Persist summary in `job_status.detail`.

---

## Requirements

| ID | Requirement |
|----|-------------|
| **R1** | `summary_worker.py` — async fn: load diagram, multimodal LLM call, text fallback if image fails |
| **R2** | Prompt: architecture summary, max ~150 words, plain text response |
| **R3** | `db.py` — `update_job_summary(job_id, summary, state="SUMMARIZED")` via SQLAlchemy + `DATABASE_URL` |
| **R4** | `detail` JSON: `{"summary":"<text>"}` |
| **R5** | `invocations.py` — `BackgroundTasks.add_task(run_summary, ...)` after 202; echo job_id unchanged |
| **R6** | On error: `state=FAILED`, `detail={"error":"..."}` |
| **R7** | `/ping`, `/inference/health`, OPTIONS unchanged |

---

## Files — ALLOWED (max 3 code)

| Actie | Pad |
|-------|-----|
| **CREATE** | `backend/agent/summary_worker.py` |
| **CREATE** | `backend/agent/db.py` |
| **MODIFY** | `backend/agent/routes/invocations.py` — ADD BackgroundTasks only |

**MUST NOT:** LangGraph, api/, alembic, requirements (done in 004b1)

---

## Definition of Done

```bash
# upload first
curl -sf -X POST http://localhost:8000/threat-designer/diagrams/ -F "file=@test/fixtures/sample.png"
# note id + diagram_path from response
curl -sf -X POST http://localhost:8080/invocations -H 'Content-Type: application/json' \
  -d '{"input":{"id":"<id>","diagram_path":"<path>","description":"test arch"}}'
sleep 30
# psql or api: job_status.detail has summary (004c pytest later)
docker compose exec postgres psql -U maestro -d maestro_d -c "SELECT state, detail FROM job_status ORDER BY updated_at DESC LIMIT 1;"
```

Skip LLM assert if oMLX offline — worker should set FAILED with error in detail.

---

## Multimodal fallback (R1)

Try `HumanMessage` with `image_url` content block. On exception → text-only with description + diagram_path note.
