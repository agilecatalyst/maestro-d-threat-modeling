# Slice 004a — `/invocations` stub (geen LangGraph)

**Status:** VERIFIED — 2026-06-09  
**Owner review:** Maestro Data · **Gate:** Maître D ✅  
**Workload tracker:** [slicedworkload.md](../../slicedworkload.md)  
**Depends on:** [slice-003b-inference-test.md](slice-003b-inference-test.md) `VERIFIED`  
**Next:** [slice-004b-summary-node.md](slice-004b-summary-node.md)

> **Klein slice** — max **3 code-files**. Stub only — **geen** LLM-call, **geen** LangGraph.

---

## Context

De API (slice 008) roept later `POST {tm-agent}/invocations` aan — zelfde contract als upstream Threat Designer.  
Nu: endpoint accepteert payload, valideert minimum, antwoordt **202 Accepted**. Worker-logica komt in **004b**.

**Product-LLM (voorlopig):** zelfde **oMLX + Gemma 4 12B** op `:8002` — geen LM Studio verplicht. Zie § Product LLM hieronder.

---

## Product LLM — oMLX + Gemma (default voor dev)

| Vraag | Antwoord |
|-------|----------|
| Kan product via oMLX? | **Ja** — OpenAI-compat `INFERENCE_BASE_URL` |
| Zelfde model als Builder? | **Ja, voorlopig** — één Gemma 12B geladen op `:8002` |
| Caveat | **Niet tegelijk** Builder-run + pipeline-test op zware load — wissel af of wacht tot Bob klaar is |
| Multimodal (004b) | Gemma 4 **IT/unified** ondersteunt beeld — oMLX moet `image_url` in chat accepteren (verify in 004b DoD) |

**`.env` voor Docker tm-agent:**

```env
INFERENCE_BASE_URL=http://host.docker.internal:8002/v1
INFERENCE_API_KEY=Mikey
LOCAL_MODEL=<exact id uit curl :8002/v1/models>
```

LM Studio (:1234) blijft **alternatief** voor grotere modellen (Qwen 27B) later.

---

## Requirements

| ID | Requirement |
|----|-------------|
| **R1** | `OPTIONS /invocations` → `200` + `{"message":"OK"}` |
| **R2** | `POST /invocations` — body shape upstream-compat: `{"input": { ... }}` |
| **R3** | `input.id` **required** (UUID string) — anders **422** |
| **R4** | **202** response: `{"statusCode":202,"body":{"message":"accepted","job_id":"<echo input.id>"}}` — **MUST echo** caller's `input.id`, **never** generate or hardcode a fixed UUID |
| **R5** | Stub logt `"invocation accepted"` + `job_id` (print of logging) — **geen** background worker |
| **R6** | `GET /ping` + `GET /inference/health` **ongewijzigd** |
| **R7** | Flat imports — `from routes.invocations import router` (geen package-relative) |

---

## Files — ALLOWED (max 3 code files)

| Actie | Pad |
|-------|-----|
| **CREATE** | `backend/agent/schemas.py` — `InvocationRequest`, `InvocationInput` (Pydantic v2) |
| **CREATE** | `backend/agent/routes/invocations.py` — OPTIONS + POST |
| **MODIFY** | `backend/agent/main.py` — **ADD** `include_router` only |
| **MODIFY** | [slicedworkload.md](../../slicedworkload.md) |

**MUST NOT:** LangGraph, langchain, LLM calls, `backend/api/*`, compose, requirements (geen nieuwe deps), tests (004c)

---

## Existing `main.py` — DO NOT REPLACE

```python
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from inference import check_inference

app = FastAPI(title="Maestro'D Agent")

@app.get("/ping")
async def ping():
    return {"status": "Healthy", "service": "maestro-d-agent"}

@app.get("/inference/health")
async def inference_health():
    result = check_inference()
    if result["status"] == "disconnected":
        return JSONResponse(status_code=503, content=result)
    return result
```

**SHALL append** router mount — niet herschrijven.

**Routes:** `@router.post("/invocations")` — geen `prefix="/invocations"` + `"/"` (307 redirect breekt `curl -sf`).

---

## POST body (minimum contract)

Caller (later: API) levert **`input.id`** = bestaand `threat_models.id` uit Postgres (zelfde UUID als upload 002a). Agent **echoot** die id terug als `job_id` — geen eigen id-fabriek in 004a.

```json
{
  "input": {
    "id": "<uuid-from-api-or-upload>",
    "description": "optional",
    "assumptions": [],
    "application_type": "Web App",
    "diagram_path": "abc.png"
  }
}
```

Extra velden **allowed** (Pydantic `model_config = ConfigDict(extra="allow")`).

---

## Definition of Done

```bash
docker compose up --build -d tm-agent
curl -sf http://localhost:8080/ping
curl -sf -X OPTIONS http://localhost:8080/invocations

JOB_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')
curl -sf -X POST http://localhost:8080/invocations \
  -H 'Content-Type: application/json' \
  -d "{\"input\":{\"id\":\"$JOB_ID\"}}" | grep -F "$JOB_ID"
# → statusCode 202, body.job_id == $JOB_ID (echo, not hardcoded)

curl -sf -X POST http://localhost:8080/invocations \
  -H 'Content-Type: application/json' \
  -d '{"input":{}}'
# → 422
```

---

## Local Builder instructie

```text
Create schemas.py + routes/invocations.py. Append router to main.py.
DO NOT replace /ping or /inference/health. No LangGraph. No LLM.
job_id in response MUST equal request input.id — never hardcode a UUID.
Emit ===FILE=== blocks only.
```

---

## Open voor Maître D (review)

| # | Beslissing | Voorstel Maestro |
|---|------------|------------------|
| D1 | Product LLM = oMLX Gemma | **Go** — update `.env.example` |
| D2 | LangGraph pas in 004b | **Go** — 004a blijft dun |
| D3 | `routes/` subfolder vs flat `invocations.py` | **routes/** — schaalt voor 004b+ |
