# Backlog — extra scope (post-MVP)

Items bewust **niet** in slice 016. Prioriteit voor volgende slices.

---

## P1 — Data portability

| Item | Beschrijving | Motivatie |
|------|--------------|-----------|
| **DB JSON export** | `GET /admin/backup` → alle `threat_models` + `job_status` + `audit_log` als één JSON snapshot | Disaster recovery als Postgres volume weg is |
| **DB JSON import** | `POST /admin/restore` — idempotent merge of replace; diagram files mee of apart zip | “Import/export” zonder handmatig psql |
| **Diagram archive** | Backup zip: JSON + `data/diagrams/` files | Compleet herstel op nieuwe machine |

*Note:* Per-model JSON export bestaat al (`/export/json`). Backlog = **bulk** backup van de hele catalog.

---

## P2 — Product

| Item | Beschrijving |
|------|--------------|
| OAuth / multi-user | Vervang `LOCAL_USER` stub |
| Model duplicate | Clone COMPLETE model als nieuw id |
| Sentry chat history | Persist messages per session (nu stub `[]`) |
| Audit log UI | Read-only view op `audit_log` |
| DOCX export | README “could” |

---

## P3 — Ops / scale

| Item | Beschrijving |
|------|--------------|
| Redis rate limits | Vervang in-memory buckets voor multi-instance |
| pip-audit in pre-commit | Optioneel naast GitHub Action |

---

## P4 — LLM quality

| Item | Beschrijving |
|------|--------------|
| Structured output enforcement | Minder parser fallbacks in agent |
| Model selector in UI | Kies inference model per run |
