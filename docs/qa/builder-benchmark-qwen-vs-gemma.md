# Builder benchmark — Qwen 3.6 27B vs Gemma 4 12B

**Status:** `DRAFT` — **awaiting Maître D go** (no runs until explicit approval)  
**ADR:** [002-builder-model-sizing-vs-correction-budget.md](../adr/002-builder-model-sizing-vs-correction-budget.md)  
**Hardware target:** Mac M4 Pro, 48 GB unified memory

---

## Purpose

Empirically answer:

> Does a **larger local builder** (Qwen ~27B) reduce total effort on **complex slices** enough to justify slower inference — compared to Gemma 12B + BLOCKERS loops?

This is **not** a product-LLM test (threat pipeline stays on Gemma unless separately decided).

---

## Scope

| In | Out |
|----|-----|
| 2–3 **historical** slice-specs (re-run in scratch / reread-only) | New product features |
| `scripts/local_builder.py` + Caveman-lite | Cursor Composer as builder |
| Metrics table + short conclusion | Full CI matrix |
| Optional: one “integration” slice pick by Maître D | Benchmarking cloud models |

---

## Models & endpoints

| Role | Model (target) | Endpoint | Notes |
|------|----------------|----------|-------|
| **A — baseline** | Gemma 4 12B IT 8-bit | `http://127.0.0.1:8002/v1` (oMLX) | Current builder default |
| **B — candidate** | Qwen 3.6 27B (quantized) | `http://127.0.0.1:1234/v1` (LM Studio) | Per [endpoints.md](../dev/endpoints.md) |

**Rule:** Do not run heavy pipeline (`tm-agent` full job) during builder benchmark runs — unload conflicting loads if RAM tight.

Verify before each session:

```bash
curl -s http://127.0.0.1:8002/v1/models   # Gemma id
curl -s http://127.0.0.1:1234/v1/models    # Qwen id
python scripts/local_builder.py --verify --base-url http://127.0.0.1:8002/v1
python scripts/local_builder.py --verify --base-url http://127.0.0.1:1234/v1 --model <qwen-id>
```

---

## Slice selection (pick 2–3 at go-time)

Choose slices where Gemma historically hurt — **integration > parser-only**.

| Candidate | Why | Complexity |
|-----------|-----|------------|
| **004b2** summary worker | multimodal + fallback, agent-only | medium |
| **001** database + Alembic | migrations, lifespan | high |
| **012** threat mutations (subset) | API + frontend touch | high — use 012a spec split if exists, else skip |
| **005b** assets worker | LangGraph wiring | medium |

Maître D picks **exactly 2** at **go** (one medium + one high recommended).

**Method:** Re-run Local Builder against **frozen slice-spec**; apply output to a **git worktree or branch** (`benchmark/qwen-vs-gemma`); never commit benchmark dumps to `main` without review.

---

## Procedure (per slice, per model)

1. Maestro/Composer prepares **BLOCKERS-free** slice-spec + source files list (review only).
2. Run Local Builder:

```bash
# Gemma
python scripts/local_builder.py --slice <NNN> --base-url http://127.0.0.1:8002/v1

# Qwen (after go)
python scripts/local_builder.py --slice <NNN> --base-url http://127.0.0.1:1234/v1 --model <qwen-id>
```

3. If output wrong: **BLOCKERS telegram** → max **2** extra turns (same model) — record each turn.
4. Apply files; run **slice-relevant pytest** (not full verify-pass unless slice demands).
5. Fill metrics row below.

**Patience contract:** Wall-clock includes all turns. Do not abort Qwen run early for “feels slow” unless GPU/RAM failure.

---

## Metrics (fill after runs)

| Slice | Model | Turn 1 pytest | Total turns | Wall-clock (min) | Manual fix lines | Caveman prose (chars) | Notes |
|-------|-------|---------------|-------------|------------------|------------------|----------------------|-------|
| | Gemma | | | | | | |
| | Qwen | | | | | | |
| | Gemma | | | | | | |
| | Qwen | | | | | | |

### Derived scores

- **First-pass rate:** pytest green on turn 1 without manual edit (Y/N)
- **Time-to-green:** wall-clock until slice pytest green (all turns)
- **Human edit burden:** lines changed by Maestro/LeadPM outside builder output

---

## Success criteria (decision at review)

| Outcome | Condition |
|---------|-----------|
| **Qwen wins builder lane** | Qwen **time-to-green** ≤ Gemma **and** fewer turns on ≥2/2 slices |
| **Gemma + patience wins** | Gemma time-to-green lower when correction budget used; Qwen not worth RAM/speed cost |
| **Composer stays default** | Both local models lose on integration slices vs Composer baseline (subjective + metrics) |
| **Hybrid** | Qwen for agent/API slices; Gemma for parsers; Composer for >10 files |

Update ADR-002 status to **Accepted** with chosen row.

---

## Risks

| Risk | Mitigation |
|------|------------|
| LeadPM impatience skews results | Patience contract; benchmark in dedicated session |
| RAM pressure (48 GB) | One model loaded; close Docker if needed |
| Apples-to-oranges (different day, tired reviewer) | Same specs, same pytest commands, same reviewer |
| Benchmark branch merges by accident | Worktree only; no merge without ADR update |

---

## Gate

| Step | Owner | Status |
|------|-------|--------|
| This spec reviewed | Maître D | pending |
| **Go** to run benchmark | Maître D | **waiting** |
| Runs executed | Local Builder + Maître D | — |
| ADR-002 finalized | Maître D + Composer | — |

---

## After benchmark (optional doc updates)

- [ ] `docs/dev/endpoints.md` — default builder model if Qwen wins
- [ ] `scripts/local_builder.py` — document `--model` / `--base-url` examples
- [ ] `agents.md` — three-lane table (Composer / Qwen builder / Gemma product)
