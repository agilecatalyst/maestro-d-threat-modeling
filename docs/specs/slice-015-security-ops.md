# Slice 015 — Security ops (rate limits, audit, input caps, dependency CI)

**Status:** READY_FOR_REVIEW  
**Owner review:** Maestro Data · **Gate:** Maître D  
**Workload tracker:** [slicedworkload.md](../../slicedworkload.md)  
**Depends on:** [slice-013](slice-000-scaffold.md) hardening, [slice-014](../SECURITY.md) license

---

## Context

Post-MVP hardening for **team-ready** local deploy (not full auth). Closes gaps from DevSecOps review:

- No rate limiting → LLM/upload abuse
- No audit trail on threat mutations
- Unbounded description → token abuse
- No automated dependency scanning in CI

**Niet in deze slice:** full OAuth/Cognito auth (post-MVP), encryption at rest, WAF.

---

## Requirements

| ID | Requirement |
|----|-------------|
| **R1** | `POST /threat-designer/diagrams` SHALL reject `description`-less uploads as today; `POST /threat-designer` description SHALL max **16_000** chars |
| **R2** | Rate limit (in-memory v1): upload **10/min**, start job **5/min**, scan-flow **3/min**, Sentry `/invocations` **10/min** per client IP |
| **R3** | Exceeding rate limit → HTTP **429** with `Retry-After` header |
| **R4** | Table `audit_log`: `id`, `threat_model_id`, `action`, `detail` (JSON), `source_ip`, `created_at` |
| **R5** | Audit entries on: `PATCH /threats`, `POST /scan-flow`, Sentry tool mutations (via API) |
| **R6** | GitHub Action `.github/workflows/security.yml`: `pip-audit` (api, agent, sentry) + `npm audit --omit=dev` on PR |
| **R7** | `SECURITY.md` SHALL document prompt-injection / LLM output trust model |
| **R8** | Optional: `API_RATE_LIMIT_ENABLED=false` env to disable limits in dev tests |

---

## Design notes

### Rate limiting

- Use `slowapi` or lightweight middleware (KISS — no Redis v1)
- Key: client IP from `X-Forwarded-For` or `request.client.host`
- Agent internal calls (tm-agent → self) exempt via Docker network or no public port

### Audit log

```sql
CREATE TABLE audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  threat_model_id UUID REFERENCES threat_models(id) ON DELETE CASCADE,
  action VARCHAR(64) NOT NULL,  -- threat_add, threat_update, threat_delete, scan_flow
  detail JSONB,
  source_ip VARCHAR(64),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

No UI v1 — query via SQL or future admin endpoint.

### Description cap

- Pydantic `max_length=16000` on `StartThreatModelRequest.description`
- Frontend textarea `maxLength={16000}` + counter optional

### CI

```yaml
# .github/workflows/security.yml
- pip install pip-audit
- pip-audit -r backend/api/requirements.txt
- pip-audit -r backend/agent/requirements.txt
- pip-audit -r backend/sentry/requirements.txt
- npm ci --prefix frontend && npm audit --omit=dev
```

Fail on HIGH/CRITICAL only (configurable).

---

## Files (expected)

| Action | Path |
|--------|------|
| CREATE | `backend/api/alembic/versions/002_audit_log.py` |
| CREATE | `backend/api/middleware/rate_limit.py` |
| CREATE | `backend/api/services/audit_log.py` |
| MODIFY | `backend/api/main.py` — register rate limit |
| MODIFY | `backend/api/routes/threat_models.py` — audit calls |
| MODIFY | `backend/api/routes/diagrams.py` — rate limit |
| MODIFY | `backend/api/schemas.py` — description max_length |
| MODIFY | `backend/sentry/main.py` — rate limit |
| MODIFY | `SECURITY.md` — LLM section |
| CREATE | `.github/workflows/security.yml` |
| MODIFY | `frontend/src/pages/WizardPage.tsx` — maxLength |
| CREATE | `test/test_rate_limit.py` (optional smoke) |

---

## Definition of Done

- [x] Description >16k → 422
- [x] 11th upload in 1 min → 429
- [x] Threat PATCH creates `audit_log` row
- [x] GitHub Action green on main
- [x] `SECURITY.md` updated
- [x] `slicedworkload.md` → 015 IMPLEMENTED

---

## Test plan

```bash
# Description cap
curl -X POST .../threat-designer -d '{"description":"'$(python -c 'print("x"*16001)')'"}'  → 422

# Audit
PATCH /threats → psql SELECT count(*) FROM audit_log WHERE action='threat_add';

# CI
gh workflow run security.yml
```

---

## Effort

~4–6 uur (Dev + DevOps). Can split:

- **015a** — description cap + audit log + CI  
- **015b** — rate limits + SECURITY.md LLM section
