# Slice 016 — MVP polish (UX + resilience)

**Status:** IMPLEMENTED  
**Depends on:** 015

---

## In scope (016)

| ID | Item |
|----|------|
| R1 | FAILED state shows `error` from API + **Retry pipeline** (re-POST with stored description) |
| R2 | `GET /threat-designer/diagrams/{id}/file` — serve diagram bytes; thumbnail on results |
| R3 | Catalog: `updated_at`, `threat_count`; delete model (`DELETE /threat-designer/{id}`) |
| R4 | STRIDE filter chips on threats tab (frontend only) |
| R5 | Partial results during pipeline poll (`status.detail`) |
| R6 | Summary worker: text-only LLM retry when multimodal fails (not stub string) |
| R7 | Footer stack health (`/health`) |
| R8 | README + `.env.example` sync; `scripts/smoke.sh` + `npm run smoke` |

---

## Extra scope (backlog — not in 016)

See [docs/backlog.md](../backlog.md):

- Full **DB backup/restore** (JSON export/import of all models + diagrams)
- OAuth / multi-user auth
- Redis-backed rate limits
- DOCX export
- Sentry chat history persistence
- Model duplicate / versioning
- Audit log UI

---

## Definition of Done

- [x] All R1–R8 implemented
- [x] `slicedworkload.md` updated
- [x] `docs/backlog.md` created with extra scope
