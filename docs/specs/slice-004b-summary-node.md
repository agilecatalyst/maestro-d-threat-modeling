# Slice 004b — Summary node (multimodal, LangGraph start)

**Status:** WAITING (after 004a VERIFIED)  
**Depends on:** [slice-004a-invocations-stub.md](slice-004a-invocations-stub.md) `VERIFIED`

> **Medium slice** — LangGraph deps + één node. Product-LLM via **oMLX Gemma 4 12B** (multimodal IT).

---

## Context

Fase 1 pipeline: lees diagram van disk (`diagram_path`), base64 → multimodal message → LLM summary → persist in Postgres (kolom TBD of JSON trail table — **tech lead beslist in review 004a**).

Referentie gedrag: owasped `SummaryService` + `MessageBuilder.create_summary_message`.

---

## Requirements (draft — detail na 004a go)

| ID | Requirement |
|----|-------------|
| **R1** | `langgraph`, `langgraph-prebuilt`, `langchain-openai` pins uit [dependencies.md](../dev/dependencies.md) § Slice 004 |
| **R2** | `ChatOpenAI` → `INFERENCE_BASE_URL` + `LOCAL_MODEL` (oMLX Gemma) |
| **R3** | Summary node: diagram PNG/JPG als `image_url` base64 + description/assumptions text |
| **R4** | Structured output: `summary` string (Pydantic `SummaryState` of equivalent) |
| **R5** | `POST /invocations` start **async** background task → run summary only → update `job_status` |
| **R6** | Fallback: als multimodal faalt → text-only summary met description (log warning) |

---

## Files — ALLOWED (indicatief, max 3 per builder run)

| Actie | Pad |
|-------|-----|
| **MODIFY** | `backend/agent/requirements.txt` |
| **CREATE** | `backend/agent/nodes/summary.py` |
| **CREATE** | `backend/agent/graph.py` — minimal 1-node graph |
| **MODIFY** | `backend/agent/routes/invocations.py` — wire background task |

**Split indien te groot:** 004b1 = deps + graph shell · 004b2 = summary node + wire

---

## Definition of Done (draft)

```bash
# oMLX Gemma geladen, .env → :8002
docker compose up --build -d tm-agent
curl -X POST .../invocations -d '{"input":{"id":"<existing-tm-id>","diagram_path":"..."}}'
# poll job_status → summary populated (slice 004c pytest)
```

---

## Risico — multimodal op oMLX

Verify vóór BUILDER start:

```bash
curl -s http://host.docker.internal:8002/v1/models   # from container perspective via tm-agent /inference/health
# Manual: chat completion with image_url against oMLX — Maître D or QA once
```

Als oMLX geen vision: tijdelijk text-only summary (R6) tot vision werkt.
