# Backlog — extra scope (post-MVP)

Items bewust **niet** in slice 016. Prioriteit voor volgende slices.

**Security audit (2026-06-09):** [docs/qa/security-audit-2026-06-09.md](qa/security-audit-2026-06-09.md)

---

## P0 — Security hardening (post-audit) — **done in slice 018**

| Item | Spec | Status |
|------|------|--------|
| Dependency bumps | [slice-018](specs/slice-018-security-hardening-p0.md) | VERIFIED |
| Agent diagram path traversal fix | [slice-018](specs/slice-018-security-hardening-p0.md) | VERIFIED |
| Restore body/row limits + validation | [slice-018](specs/slice-018-security-hardening-p0.md) | VERIFIED |

---

## P1 — Security hardening (post-audit) — before LAN/team ← **next**

| Item | Spec | Audit IDs |
|------|------|-----------|
| Admin backup/restore shared secret (`ADMIN_API_KEY`) | [slice-019](specs/slice-019-security-hardening-p1.md) | C2 |
| Mutation auth — remove `VITE_INTERNAL_API_KEY` from browser | [slice-019](specs/slice-019-security-hardening-p1.md) | H2, H3 |
| Agent + Sentry invocation auth when key set | [slice-019](specs/slice-019-security-hardening-p1.md) | C3 |
| Owner filter on diagram metadata GET | [slice-019](specs/slice-019-security-hardening-p1.md) | M3 |
| `.env.example` placeholder hygiene | [slice-019](specs/slice-019-security-hardening-p1.md) | M5 |
| Audit log: delete, backup, restore, pipeline start | backlog (no spec yet) | L3 |
| Trusted proxy config for `X-Forwarded-For` | backlog (no spec yet) | M4 |

---

## P1 — Data portability

| Item | Beschrijving | Motivatie |
|------|--------------|-----------|
| **DB JSON export** | `GET /admin/backup` → alle `threat_models` + `job_status` + `audit_log` als één JSON snapshot | **Done in slice 017** |
| **DB JSON import** | `POST /admin/restore` — merge or replace | **Done in slice 017** |
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
