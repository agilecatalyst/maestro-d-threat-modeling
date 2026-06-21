# Slice 018 — Security hardening P0 (post-audit)

**Status:** VERIFIED  
**Depends on:** 017 VERIFIED  
**Source:** [security-audit-2026-06-09.md](../qa/security-audit-2026-06-09.md) — Phase 0  
**Gate:** Maître D go before implement · green `verify-pass` + pip-audit before VERIFIED

---

## Scope (max ~8 code files)

| ID | Item |
|----|------|
| R1 | **Dependency bumps** — `python-multipart` ≥0.0.31, `weasyprint` ≥68.0, `langchain-core` / `langchain-openai` to fix versions from pip-audit |
| R2 | **Agent diagram path hardening** — shared `_safe_path()` (or copy from API `storage.py`); reject `..` and absolute paths; validate `diagram_path` on restore |
| R3 | **Restore limits and validation** — max JSON body size (e.g. 32 MB), max rows per table (e.g. 10_000), validate `job_status.state` against allowlist, cap `detail` string length |

## MUST NOT

- OAuth / multi-user (→ slice 019 / backlog P2)
- Admin shared secret (→ slice 019)
- Redis rate limits

## Definition of Done

- [x] pip-audit clean (or documented exceptions) on API + agent requirements
- [x] Agent path traversal test (e.g. `../../etc/passwd` rejected)
- [x] Restore rejects oversized payload / invalid state
- [x] `bash scripts/verify-pass.sh` green
- [x] ≤8 production code files changed

## Addresses audit findings

H1, H4, M1, M2
