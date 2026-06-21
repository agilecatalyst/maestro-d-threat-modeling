# Slice 017 — DB backup & restore (JSON)

**Status:** VERIFIED  
**Depends on:** 016 VERIFIED  
**Source:** [backlog.md](../backlog.md) P1

---

## Scope (max ~8 code files)

| ID | Item |
|----|------|
| R1 | `GET /admin/backup` → JSON snapshot: `threat_models`, `job_status`, `audit_log` (+ schema version) |
| R2 | `POST /admin/restore` — merge or replace mode; validate schema version |
| R3 | Optional: include diagram file paths in snapshot (files copied separately in v1) |
| R4 | `scripts/verify-pass.sh` in DoD; **no IMPLEMENTED without green verify** |

## MUST NOT

- OAuth / multi-user
- Zip archive (defer to 017b)
- Frontend UI (CLI/curl only in 017)

## Definition of Done

- [x] Backup returns all rows for local user
- [x] Restore recreates models after empty DB
- [x] pytest for backup/restore roundtrip
- [x] `bash scripts/verify-pass.sh` green
- [x] ≤8 production code files changed

## Gate

Maître D **go** — 2026-06-09 · **verified** 2026-06-09
