# ADR-001: Composer as primary builder

**Status:** Accepted  
**Date:** 2026-06-09  
**Deciders:** Maître D

### Context

Original model: Cursor (Maestro) specs/reviews; Gemma 4 12B @ oMLX (Local Builder) implements slices. During MVP finish (012–016), Gemma was slow and required many correction passes; LeadPM prioritized shipping.

### Decision

**Cursor Composer** is the **primary builder** after explicit Maître D **go** on a slice-spec. Local Builder remains optional for experiments and offline LLM-only workflows.

### Consequences

- **Positive:** Faster integration, fewer BLOCKERS loops, single session for spec + code + tests.
- **Negative:** Larger diffs risk; must enforce slice size and verify gates (see [governance.md](../governance.md)).
- **Follow-up:** `scripts/verify-pass.sh`; IMPLEMENTED ≠ VERIFIED; [ADR process](README.md).
