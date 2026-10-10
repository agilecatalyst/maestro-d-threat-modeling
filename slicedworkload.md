# Sliced workload — Maestro'D ThreatModeling

**Governance:** [docs/governance.md](docs/governance.md) (Composer-Builder, verify-gates)  
**Verify:** [docs/qa/verify-pass-012-018.md](docs/qa/verify-pass-012-018.md) — 51 passed, 1 skipped (2026-06-09)  
**Verify (020):** [docs/qa/verify-pass-020.md](docs/qa/verify-pass-020.md) — offline sandbox; API/DB suites still to run on a networked machine

---

## Stand van zaken

| Slice | Status |
|-------|--------|
| 000–009 | VERIFIED |
| **010–011** | **VERIFIED** — PDF + JSON export |
| **012** | **VERIFIED** — threat edit, flow scan, Sentry |
| **013** | **VERIFIED** — DevSecOps hardening |
| **014** | **VERIFIED** — License & attribution |
| **015** | **VERIFIED** — Security ops |
| **016** | **VERIFIED** — MVP polish |
| **017** | **VERIFIED** — DB backup/restore JSON |
| **018** | **VERIFIED** — Security hardening P0 |
| **019** | PENDING — Security hardening P1 |
| **020** | READY_FOR_REVIEW — [Pluggable LLM providers](docs/specs/slice-020-pluggable-llm-providers.md) |

MVP core **complete** · security audit: [docs/qa/security-audit-2026-06-09.md](docs/qa/security-audit-2026-06-09.md)

---

## Active slice

| Veld | Waarde |
|------|--------|
| **Slice** | **020** Pluggable LLM providers |
| **Status** | 020 implemented, await verify · [019 P1 hardening](docs/specs/slice-019-security-hardening-p1.md) still open (admin auth surface) |

---

## History

| Slice | Date |
|-------|--------|
| 020 Pluggable LLM providers | 2026-10-10 |
| 018 Security hardening P0 | 2026-06-09 |
| Security audit + hardening specs 018/019 | 2026-06-09 |
| 017 DB backup/restore | 2026-06-09 |
| Verify pass 010–016 | 2026-06-09 |
| Governance + co-creatie contract | 2026-06-09 |
