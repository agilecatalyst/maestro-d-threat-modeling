# Slice 006 — Flows (parser + worker + pipeline)

**Status:** VERIFIED  
**Owner:** Maestro senior dev (Bob offline)  
**Depends on:** 005b

Single slice — parsers port + `flows_worker` + pipeline chain.

## DoD

```bash
pytest test/test_flows_parser.py test/test_summary.py -q
```

Pipeline states: `SUMMARIZED` → `ASSETS_DONE` → `FLOWS_DONE`
