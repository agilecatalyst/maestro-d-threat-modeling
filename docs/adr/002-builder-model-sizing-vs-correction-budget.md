# ADR-002: Builder model sizing vs correction budget

**Status:** Proposed (awaiting benchmark — see [builder-benchmark-qwen-vs-gemma.md](../qa/builder-benchmark-qwen-vs-gemma.md))  
**Date:** 2026-06-09  
**Deciders:** Maître D (go pending)

### Context

We validated that **orchestrator + local small agent** can work (Caveman-lite, slice specs, Local Builder script). In practice, **Gemma 4 12B @ oMLX** often needed many BLOCKERS correction passes on integration-heavy slices. LeadPM impatience compressed the intended loop (`spec → builder → BLOCKERS → builder → verify`) into Composer-as-builder (ADR-001).

Two levers exist — not mutually exclusive:

| Lever | Effect |
|-------|--------|
| **Larger builder model** (e.g. Qwen 3.6 27B) | Fewer correction rounds; slower tokens |
| **Smaller slices + correction budget** | More turns; LeadPM must accept wall-clock |

Hardware: **M4 Pro, 48 GB unified memory** — sufficient for 27B quantized (4-bit/8-bit MLX/LM Studio) if product and builder are not both loaded heavy at once.

Maître D insight (paraphrased): *the same impatience may return with 27B — but for speed, not quality. We should still test Qwen on a few slices to see if it handles complex code better than Gemma.*

### Decision (proposed — not final until benchmark)

**Orchestrator + local builder remains a valid path** when **either**:

1. **Model capacity:** builder model ≥ ~27B class (quantized) on host, **or**
2. **Process capacity:** LeadPM accepts **correction budget** (≥2 builder turns, small slices) without pulling Composer into the pan

Until benchmark completes: **Composer stays primary builder** (ADR-001). Qwen 27B is a **candidate**, not a default.

### Consequences

- **Positive:** Empirical choice between speed (Composer), quality-per-turn (Qwen), and cost (Gemma + patience).
- **Negative:** Dual inference setup (oMLX :8002 product vs LM Studio :1234 builder test) adds ops complexity.
- **Follow-up:** Run bounded benchmark; update this ADR to **Accepted** or **Rejected** with numbers; optional ADR-003 if Qwen wins builder lane only.

### Relationship to other ADRs

| ADR | Role |
|-----|------|
| [001](001-composer-primary-builder.md) | Current default — unchanged until benchmark go + results |
| 002 (this) | When local two-intelligence is worth retrying |

### LeadPM patience contract (benchmark only)

During the benchmark window, success is measured by **time-to-VERIFIED** (including correction rounds), not **time-to-first-token**. Impatience during a 27B run invalidates the experiment.
