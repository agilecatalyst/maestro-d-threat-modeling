# Slice 004b1 — Agent LLM client + diagram loader

**Status:** READY_FOR_BUILDER  
**Depends on:** [slice-004a-invocations-stub.md](slice-004a-invocations-stub.md) `VERIFIED`  
**Next:** [slice-004b2-summary-worker.md](slice-004b2-summary-worker.md)

> **Klein slice** — geen LangGraph. Geen background task yet.

---

## Requirements

| ID | Requirement |
|----|-------------|
| **R1** | `llm.py` — `get_chat_model()` → `ChatOpenAI` via env `INFERENCE_BASE_URL`, `INFERENCE_API_KEY`, `LOCAL_MODEL` |
| **R2** | `diagram_loader.py` — `load_diagram_data_url(relative_path)` → `data:image/png;base64,...` from `DIAGRAM_STORAGE_PATH` |
| **R3** | `requirements.txt` — pins uit [dependencies.md](../dev/dependencies.md) § Slice 004b1 |
| **R4** | `docker-compose.yml` — tm-agent: `DIAGRAM_STORAGE_PATH=/data/diagrams` + volume `./data/diagrams:/data/diagrams` |
| **R5** | Flat imports. **MUST NOT** change `/ping`, `/inference/health`, `/invocations` logic |

---

## Files — ALLOWED

| Actie | Pad |
|-------|-----|
| **CREATE** | `backend/agent/llm.py` |
| **CREATE** | `backend/agent/diagram_loader.py` |
| **MODIFY** | `backend/agent/requirements.txt` |
| **MODIFY** | `docker-compose.yml` — tm-agent volume only |
| **MODIFY** | [slicedworkload.md](../../slicedworkload.md) |

**MUST NOT:** LangGraph, summary worker, invocations changes, api/, tests

---

## Definition of Done

```bash
docker compose up --build -d tm-agent
docker compose exec tm-agent python -c "from llm import get_chat_model; from diagram_loader import load_diagram_data_url; print(get_chat_model()); print(load_diagram_data_url('x.png')[:30] if False else 'import-ok')"
# → import ok, container starts
curl -sf http://localhost:8080/invocations -X OPTIONS
```

Manual: place a png in `data/diagrams/`, exec loader with real filename → data URL prefix `data:image/`

---

## Local Builder

Append only on existing files. ===FILE: first. Zero prose.
