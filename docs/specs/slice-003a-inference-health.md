# Slice 003a — tm-agent inference health endpoint

**Status:** READY_FOR_BUILDER  
**Owner review:** Maestro Data · **Gate:** Maître D  
**Workload tracker:** [slicedworkload.md](../../slicedworkload.md)  
**Depends on:** [slice-002b-upload-get-test.md](slice-002b-upload-get-test.md) `VERIFIED`  
**Next:** [slice-003b-inference-test.md](slice-003b-inference-test.md)

> **Klein slice** — 2 code-files. **Append only** — `/ping` blijft exact zoals hij is.

---

## Context

`tm-agent` is een FastAPI stub met `GET /ping`. Product-LLM draait op host via `INFERENCE_BASE_URL` (LM Studio :1234 of oMLX).  
Deze slice: **één nieuwe route** die vanuit de container `GET {INFERENCE_BASE_URL}/models` probeert.

---

## Requirements

| ID | Requirement |
|----|-------------|
| **R1** | `GET /inference/health` op `tm-agent` (:8080) |
| **R2** | Leest env: `INFERENCE_BASE_URL`, `INFERENCE_API_KEY`, `LOCAL_MODEL` |
| **R3** | Roept `GET {INFERENCE_BASE_URL}/models` aan via **httpx** (sync, timeout 5s) |
| **R4** | **200** als bereikbaar: `{"status":"connected","service":"maestro-d-agent","inference_base_url","local_model","models_count","model_loaded":bool}` |
| **R5** | **503** als niet bereikbaar: `{"status":"disconnected",...,"error":"..."}` |
| **R6** | `model_loaded` = true als `LOCAL_MODEL` voorkomt in `/models` response `data[].id` (substring match ok) |
| **R7** | `GET /ping` **ongewijzigd** — exact zelfde response als slice 000 |

---

## Files — ALLOWED (max 2 code files)

| Actie | Pad |
|-------|-----|
| **CREATE** | `backend/agent/inference.py` — `check_inference()` helper |
| **MODIFY** | `backend/agent/main.py` — **ADD** route + import; **behoud** `/ping` |
| **MODIFY** | [slicedworkload.md](../../slicedworkload.md) |

**MUST NOT:** `backend/api/*`, compose, requirements (httpx staat al), tests (003b), LangGraph

---

## Existing `main.py` — DO NOT REPLACE

```python
from fastapi import FastAPI

app = FastAPI(title="Maestro'D Agent")

@app.get("/ping")
async def ping():
    return {"status": "Healthy", "service": "maestro-d-agent"}
```

**SHALL append** new imports + `@app.get("/inference/health")` — niet herschrijven.

**Imports:** flat only — `from inference import check_inference` (geen `from .inference` — uvicorn `main:app`).

---

## Definition of Done

```bash
docker compose up --build -d tm-agent
curl -sf http://localhost:8080/ping
curl -s http://localhost:8080/inference/health   # 200 if LLM up, 503 if down — both OK for smoke
```

---

## Local Builder instructie

```text
Append GET /inference/health to tm-agent. Create inference.py.
DO NOT replace or delete /ping. DO NOT touch api/.
Emit ===FILE=== blocks only.
```
