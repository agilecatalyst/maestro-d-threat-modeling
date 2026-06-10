# Slice 003b — pytest inference health

**Status:** WAITING (after 003a VERIFIED)  
**Depends on:** [slice-003a-inference-health.md](slice-003a-inference-health.md) `VERIFIED`

> **Klein slice** — 1 test-file.

---

## Requirements

| ID | Requirement |
|----|-------------|
| **R1** | `test/test_inference.py` — `GET /ping` unchanged contract |
| **R2** | `GET /inference/health` — assert JSON keys; **skip** test if status 503 (LLM offline) |
| **R3** | Als 200: assert `status=="connected"`, `model_loaded` is bool |
| **R4** | Geen wijzigingen aan agent code tenzij BLOCKERS |

---

## Files — ALLOWED

| Actie | Pad |
|-------|-----|
| **CREATE** | `test/test_inference.py` |
| **MODIFY** | [slicedworkload.md](../../slicedworkload.md) |

**MUST NOT:** `backend/agent/main.py` (tenzij BLOCKER), `backend/api/*`

---

## Definition of Done

```bash
pytest test/test_inference.py -q
```
