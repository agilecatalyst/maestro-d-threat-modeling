# Slice 004c — Summary pipeline pytest

**Status:** VERIFIED  
**Depends on:** [slice-004b2-summary-worker.md](slice-004b2-summary-worker.md) `VERIFIED`

> **Klein slice** — tests only.

---

## Requirements

| ID | Requirement |
|----|-------------|
| **R1** | `test/test_summary.py` — upload → invocations → poll `job_status` |
| **R2** | Assert `state=SUMMARIZED`, `detail.summary` length > 20 |
| **R3** | Skip if api/agent unreachable (not if LLM offline — fallback OK) |
| **R4** | Fixture `test/fixtures/sample.png` + vaste description |
| **R5** | Geen assert op exact LLM wording |

---

## Definition of Done

```bash
docker compose up -d
pytest test/test_summary.py -q
```
