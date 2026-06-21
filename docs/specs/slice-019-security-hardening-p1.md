# Slice 019 — Security hardening P1 (boundary)

**Status:** READY_FOR_REVIEW  
**Depends on:** 018 VERIFIED  
**Source:** [security-audit-2026-06-09.md](../qa/security-audit-2026-06-09.md) — Phase 1  
**Gate:** Maître D go · required before **shared LAN / team** deployment

---

## Scope

| ID | Item |
|----|------|
| R1 | **Admin shared secret** — `ADMIN_API_KEY` env; `GET /admin/backup` + `POST /admin/restore` require `X-Admin-Key` when set; document in SECURITY.md |
| R2 | **Mutation auth model** — stop shipping `VITE_INTERNAL_API_KEY`; UI mutations via session cookie or dedicated local-only BFF; Sentry keeps server-side `INTERNAL_API_KEY` only |
| R3 | **Internal service auth** — agent `/invocations` + `/scan-flow` require `X-Internal-Key` when `INTERNAL_API_KEY` set; Sentry `/invocations` same or mTLS stub |
| R4 | **Owner consistency** — `GET /diagrams/{id}` filter on `LOCAL_USER` like `/file` |
| R5 | **Env example hygiene** — `.env.example` uses placeholders (`change-me-…`); no real-looking API keys in repo |

## MUST NOT

- Full OAuth (→ backlog P2)
- Public internet deployment guide

## Definition of Done

- [ ] Admin routes protected when `ADMIN_API_KEY` set
- [ ] No secret in frontend bundle for API mutations
- [ ] Agent rejects unauthenticated invocation when key configured
- [ ] SECURITY.md updated with deployment tiers (localhost / LAN / team)
- [ ] `verify-pass` green

## Addresses audit findings

C2, H2, H3, C3, M3, M5
