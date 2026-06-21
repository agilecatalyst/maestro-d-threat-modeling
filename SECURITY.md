# Security

Maestro'D Threat Modeling is designed **local-first** for personal or trusted-team use. Treat generated threat models as a **review starting point**, not as authoritative security sign-off.

## Scope

| Mode | Intended use |
|------|----------------|
| **Local dev** | Single developer, localhost, no auth (`LOCAL_USER` stub) |
| **Shared LAN / team** | Requires hardening below — not enabled by default |

## Threat model disclaimer

- LLM output may be incomplete, duplicated, or wrong for your context.
- Always validate threats, mitigations, and architecture assumptions with a human reviewer.
- Do not use exports as sole evidence for compliance or production approval.

## Deployment hardening checklist

### Network (P0)

- Default `docker-compose.yml` binds API to **127.0.0.1:8000** only; Postgres, agent, and Sentry have **no host ports**.
- For debugging, use `docker-compose.dev.yml` (still localhost-bound).
- Do not expose Postgres or the agent port to untrusted networks.

### Secrets (P0)

- Change defaults in `.env`: `POSTGRES_PASSWORD`, `INFERENCE_API_KEY`.
- Optionally set `INTERNAL_API_KEY` for Sentry → API mutation calls (Sentry sends `X-Internal-Key`).
- Never commit `.env` or diagram uploads.

### Application (P1)

- Uploads: PNG/JPEG only, 10 MB max, magic-byte validation.
- CORS: configure `CORS_ORIGINS` (comma-separated) — no wildcard on API or Sentry.
- Description field capped at **16,000 characters** (API + UI).
- In-memory rate limits (per client IP): upload 10/min, start job 5/min, flow scan 3/min, Sentry chat 10/min → HTTP 429. Disable in dev with `API_RATE_LIMIT_ENABLED=false`.
- **Audit log** (`audit_log` table): threat PATCH and flow-scan mutations recorded with action, threat names, and source IP.
- **Admin backup/restore** (`GET /admin/backup`, `POST /admin/restore`): localhost-trust only — no auth in v1; do not expose API to untrusted networks.

### LLM trust model (P1)

- User-supplied **description and diagram** are passed to the local LLM as prompt context. Treat them as untrusted input (prompt injection risk).
- The LLM may suggest incorrect threats or mitigations; human review is mandatory before acting on output.
- Sentry chat can mutate the threat catalog via internal API calls — keep `INTERNAL_API_KEY` set when Sentry is enabled on a shared network.
- Do not paste secrets, credentials, or PII into descriptions or chat; they may appear in logs or exports.

## Security audit

External review (2026-06-09): [docs/qa/security-audit-2026-06-09.md](docs/qa/security-audit-2026-06-09.md)  
Hardening work: [slice 018](docs/specs/slice-018-security-hardening-p0.md) (P0) → [slice 019](docs/specs/slice-019-security-hardening-p1.md) (P1) → [backlog](docs/backlog.md#p1--security-hardening-post-audit).

## Reporting vulnerabilities

If you find a security issue in this project, open a private advisory or contact the repository maintainers. Do not open public issues for exploitable vulnerabilities before coordinated disclosure.

## Dependencies

Run periodically:

```bash
pip-audit -r backend/api/requirements.txt
pip-audit -r backend/agent/requirements.txt
npm audit --prefix frontend
```

## OWASP alignment

This tool supports **security thinking acceleration** (STRIDE, DFD, mitigations). It does not replace threat modeling expertise, penetration testing, or formal AppSec review.
