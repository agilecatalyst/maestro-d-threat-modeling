# Slice 007 — Threats (agentic) — schets

**Status:** READY_FOR_REVIEW — **Gate:** Maître D  
**Owner:** Maestro Data (tech lead + senior dev)  
**Depends on:** slice 006 `VERIFIED`  
**Referentie:** [partialexchangeqwen.md](../../threat-designer-owasped/docs/qa/partialexchangeqwen.md) · owasped `workflow_threats.py`

> Bob/Gemma **buiten** 007 — te veel integratie-risico. Senior dev bouwt; parsers eerst (port), loop daarna.

---

## Waar we staan

```
POST /invocations
  → summary   (detail.summary)
  → assets    (detail.assets)
  → flows     (detail.flows)
  → state: FLOWS_DONE
```

**007** voegt toe: **threat catalog** in `job_status.detail.threats` → `THREATS_DONE` → (008) `COMPLETE`.

---

## Design-keuzes (voorstel)

| # | Beslissing | Motivatie |
|---|------------|-----------|
| D1 | **Geen LangGraph in 007a/b** | KISS — Python `while`-loop i.p.v. subgraph tot loop stabiel is |
| D2 | **007b = one-shot threats eerst** | Werkende catalog vóór generate→audit→fix |
| D3 | **007c = agentic loop** | `add_threats` + `gap_analysis`, max **3 iteraties** (env) |
| D4 | **Parsers vóór LLM** | Zelfde les als assets/flows — lokale modellen → JSON/text fallback |
| D5 | **Context uit detail JSON** | Geen diagram in threats-fase; summary+assets+flows volstaan |
| D6 | **Fallback stub threats** | 3 STRIDE threats uit asset-namen als LLM faalt (nooit FAILED) |

LangGraph **optioneel later** (007c+ of 008) als pure-Python loop te krap wordt.

---

## Slice-split (iets groter, coherent per slice)

### 007a — Threat schema + parsers · **~1 slice, Maestro port**

| Deliverable | Pad |
|-------------|-----|
| Pydantic | `threats_schema.py` — `Threat`, `ThreatsList` (STRIDE enum, threat grammar velden) |
| JSON/tool wrapper | hergebruik `structured_tool_json.py`; `[TOOL_REQUEST]` marker parse (Gemma) |
| Plain-text fallback | `threats_text_parser.py` — minimaal JSON `{"name":"ThreatsList","arguments":{...}}` |
| Tests | `test/test_threats_parser.py` — fixtures uit capture (ingekort) |

**DoD:** `pytest test/test_threats_parser.py -q`

**MUST NOT:** LLM, pipeline wijziging, LangGraph

---

### 007b — One-shot threats worker · **1 slice, senior dev**

| Deliverable | Pad |
|-------------|-----|
| Worker | `threats_worker.py` — leest detail, 1× LLM prompt, parse, merge |
| Pipeline | `pipeline_worker.py` — append `run_threats()` |
| State | `THREATS_DONE`; `detail.threats: [{name, stride_category, ...}]` |

**Prompt-contract (kort):**
- Input: summary + asset names + flow descriptions + threat_sources
- Output: 5–10 threats, STRIDE verdeeld, threat grammar in `description`
- Parse via `parse_threats_list_from_text`

**DoD:**
```bash
pytest test/test_summary.py -q   # poll → THREATS_DONE, len(threats) >= 3
```

---

### 007c — Agentic loop (generate → audit → fix) · **1 slice, senior dev**

Geen volledige owasped-pariteit dag 1 — **verkleinde loop**:

```
catalog = []
for i in range(MAX_ITER):          # default 3
    LLM + tools (add_threats batch)
    merge catalog
    gap = gap_analysis(catalog, context)
    if gap.stop: break
    else: fix prompt with gap.findings
state THREATS_DONE (or COMPLETE in 007d)
```

| Component | Pad |
|-----------|-----|
| Catalog in-memory | `threat_catalog.py` — add/remove/list |
| Tools (Python) | `threat_tools.py` — `add_threats`, `gap_analysis` (geen LangGraph ToolNode) |
| Orchestrator | `threats_agent.py` — while-loop, bind_tools **of** text-tool fallback |
| Coercion | port concept `add_threats_tool_args` (schema errors cap) |

**Env:**
```env
THREAT_AGENT_MAX_ITERATIONS=3
THREAT_AGENT_MAX_ADD_THREATS_SCHEMA_ERRORS=3
```

**DoD:**
- Handmatig: 1 job → ≥8 threats, ≥3 STRIDE categories
- Optioneel: replay **1** turn uit `partialexchangeqwen.md` door parser + mock catalog

**Risico:** oMLX Gemma/Qwen tool_calls inconsistent → **text fallback verplicht** in spec

---

### 007d — Finalize + pytest · **klein slice**

| Deliverable | |
|-------------|--|
| `run_finalize(job_id)` | state → `COMPLETE`, detail metadata (counts, stride distribution) |
| `test/test_threats_pipeline.py` | upload → invocations → poll `COMPLETE` |
| `test_summary.py` | terminal state `COMPLETE` i.p.v. `FLOWS_DONE` |

---

## Data contract — `job_status.detail` (target na 007d)

```json
{
  "summary": "...",
  "assets": [...],
  "flows": {
    "data_flows": [...],
    "trust_boundaries": [...],
    "threat_sources": [...]
  },
  "threats": [
    {
      "name": "SQL injection via API",
      "stride_category": "Tampering",
      "description": "[External attacker] [API access] can ...",
      "target": "Database",
      "source": "External Threat Actors",
      "likelihood": "Medium",
      "impact": "High",
      "mitigations": ["Parameterized queries"],
      "prerequisites": ["Network access"],
      "vector": "HTTP API"
    }
  ],
  "meta": {
    "threat_count": 8,
    "stride_counts": {"Tampering": 2, "...": "..."}
  }
}
```

---

## Threat model — `Threat` (minimaal MVP)

| Veld | Vereist 007b |
|------|----------------|
| `name` | ✅ |
| `stride_category` | ✅ (6 STRIDE waarden) |
| `description` | ✅ (grammar) |
| `target` | ✅ (asset name) |
| `source` | ✅ (threat_sources category) |
| `likelihood` | ✅ Low/Medium/High |
| `impact` | ✅ string |
| `mitigations` | ✅ list, min 1 |
| `prerequisites` | ✅ list |
| `vector` | ✅ string |
| `starred`, `notes` | ❌ later |

---

## Wat we **niet** in 007 doen

- `delete_threats` in loop (007c v2 of 008) — eerst add + gap alleen
- Attack tree, PDF export (010), API polling (008)
- DynamoDB-shaped storage — blijft Postgres JSON in `detail` (tijdelijk; normalize later)
- Volledige LangGraph port `workflow_threats.py` (484 regels)

---

## Volgorde & effort (inschatting)

| Slice | Wie | Inschatting |
|-------|-----|-------------|
| **007a** parsers | Maestro | ~2u |
| **007b** one-shot worker | Maestro | ~2u |
| **007c** agentic loop | Maestro | ~4–6u (grootste brok) |
| **007d** finalize + e2e | Maestro | ~1u |

**Totaal:** ~1–2 sessies senior dev; Bob pas weer voor kleine append-slices (008 API routes).

---

## Open punten voor Maître D

| # | Vraag | Voorstel |
|---|-------|----------|
| O1 | 007b one-shot **vóór** 007c loop? | **Ja** — increment bewijs |
| O2 | Max iteraties loop | **3** (dev); later env |
| O3 | `detail` JSON vs aparte `threats` tabel | **JSON in detail** voor MVP (008 kan migreren) |
| O4 | Capture replay verplicht in DoD? | **Optioneel** 007c — parser golden verplicht in 007a |

---

## Go / no-go

| Akkoord | Actie |
|---------|--------|
| **Go 007a** | Maestro bouwt parsers + pytest |
| **Go 007a–b** | + one-shot worker, pipeline `THREATS_DONE` |
| **Go full 007** | t/m 007d `COMPLETE` |

---

*Na go: `slicedworkload.md` → active slice 007a. Bob blijft ziek.*
