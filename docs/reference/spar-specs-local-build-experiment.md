# specs.md — Local-First Build Experiment

**Status:** Spar-artefact v0.1 — **D1 verplaatst** naar greenfield [Maestro'D ThreatModeling](../../specsrebuild.md)  
**Auteur:** Maestro (Cursor) + input LeadPM Dirk  
**Datum:** 2026-06-05  
**Doel:** Specificaties en werkwijze zo formuleren dat **lokale modellen** (LM Studio / Qwen) bounded bouw-taken kunnen uitvoeren — Cursor blijft orchestrator en gate.

---

## 1. Hypothese

> Een **local-first** threat modeling tool hoeft niet door één grote cloud-agent gebouwd te worden.  
> We kunnen **kleine, machine-leesbare specs** schrijven die een **lokaal model** uitvoert (via gecontroleerde agent-loop), terwijl **LeadPM + Maestro** scope, review en integratie houden.

**Experiment:** niet “kan Qwen alles?” maar “kan Qwen **één afgebakende increment** betrouwbaar bouwen als de spec dat toelaat?”

---

## 2. Wat bedoelen we met “herdoen”? (LeadPM kiest)

Drie mogelijke scopes — **niet alles tegelijk**:

| Optie | Beschrijving | Local-model haalbaarheid | Risico |
|-------|--------------|--------------------------|--------|
| **A — Proces-experiment** | Bestaande fork **niet** herschrijven; local model bouwt **één nieuw slice** (bijv. OWASP LLM Top 10 template-set, export-helper, kleine API-route) | ✅ Hoog — aanbevolen start | Laag |
| **B — Module-herbouw** | Eén module opnieuw (bijv. `workflow_threats` parsers, of mock-LLM-laag Sprint 9) met local model als primaire coder | ⚠️ Medium — met sterke specs + tests | Medium |
| **C — Greenfield rewrite** | Hele threat-designer opnieuw, local-only | ❌ Laag voor 27B alleen | Zeer hoog |

**Voorstel team:** start met **A**, slice grootte ≤ 1 PR, pytest/Playwright als harde gate.

---

## 3. Twee intelligenties (uitgebreid)

Bestaand model (`local-stack-owasped.md`) blijft, maar met een **derde rol**:

```
┌─────────────────────────────────────────────────────────────┐
│  LeadPM (Dirk)     — visie, go/no-go, gates                 │
│  Maestro (Cursor)  — specs, review, integratie, chirurgie   │
│  Local Builder     — implementatie van één spec-slice       │
│    (Qwen @ LM Studio via agent-loop / MCP / script)         │
└─────────────────────────────────────────────────────────────┘
```

| Rol | Doet wel | Doet niet |
|-----|----------|-----------|
| **LeadPM** | Scope kiezen, merge goedkeuren | Elke regel code reviewen |
| **Maestro** | `specs.md` + slice-specs schrijven, diff reviewen, fixen als local model faalt | Grote autonome rewrites zonder gate |
| **Local Builder** | Eén slice implementeren volgens spec | Architectuur wijzigen, scope uitbreiden |

**Product-LLM** (threat-designer agent) ≠ **Builder-LLM** — zelfde stack (LM Studio), andere prompts en tools.

---

## 4. Local-first spec-principes

Specs moeten **door een 27B-model** te volgen zijn zonder “impliciete” kennis.

### 4.1 Taal

- **SHALL** = verplicht  
- **MUST NOT** = verboden  
- **SHOULD** = aanbevolen; afwijken alleen met expliciete LeadPM-notitie  

### 4.2 Granulariteit

- **Één slice** = één mergebare PR  
- Max **~3 bestanden** gewijzigd per slice (tenzij LeadPM anders beslist)  
- Max **~150 regels** netto diff (richtlijn, geen dogma)  

### 4.3 Verplichte secties per slice-spec

Elke slice krijgt een eigen bestand: `docs/specs/slice-NNN-<naam>.md`

```markdown
# Slice NNN — <titel>

## Context
- Waarom (1 alinea)
- Bestaande bestanden (paden)

## Requirements
- R1: …
- R2: …

## Files
| Actie | Pad |
|-------|-----|
| CREATE / MODIFY / MUST NOT TOUCH | … |

## Interface contract
- Functie/signatuur, request/response, env vars

## Tests (Definition of Done)
- `pytest …` → verwacht: …
- Handmatig: …

## Out of scope
- Expliciet wat NIET mag

## Local Builder instructie
- Eén letterlijke opdracht voor het model (copy-paste ready)
```

### 4.4 Anti-patterns voor local models

| Vermijden | Waarom |
|-----------|--------|
| “Verbeter de codebase” | Te vaag |
| Meerdere concerns in één slice | Context + coherentie breken |
| Business logic refactoren “terwijl je bezig bent” | Scope creep |
| Nieuwe dependencies zonder expliciete ALLOW | Supply-chain + Docker rebuild |
| Auth, RDBMS, CI zonder gate | Vastgelegde projectregels |

---

## 5. Werkwijze — Local Build Loop

### Fase 0 — Voorbereiding (eenmalig)

1. LeadPM kiest scope **A/B/C** en eerste slice-onderwerp  
2. Maestro schrijft `docs/specs/slice-001-….md`  
3. DevOps: Builder-loop beschikbaar maken (zie §6)  
4. Baseline groen: `pytest test/` + `npm run test:e2e` (smoke)

### Fase 1 — Build (per slice)

```
Spec slice → Local Builder → diff/patch → Maestro review → pytest/e2e → LeadPM go → merge
```

| Stap | Wie | Output |
|------|-----|--------|
| 1. Spec goedkeuren | LeadPM | ✅ op slice-doc |
| 2. Builder run | Local model | patch of bestanden |
| 3. Kwaliteit | Maestro/QA | tests groen of BLOCKER |
| 4. Integratie | Maestro | minimale fix als model faalt |
| 5. Merge | LeadPM | commit/PR |

### Fase 2 — Leren

- Capture Builder I/O in `docs/qa/builder-slice-NNN.md` (zoals `partialexchangeqwen.md`)  
- Retro: wat werkte / faalde → volgende slice specs aanscherpen  

---

## 6. Builder-loop — technische opties (te kiezen)

| Optie | Beschrijving | Complexiteit |
|-------|--------------|--------------|
| **6a — Cursor + LM Studio split** | Maestro schrijft spec; jij plakt spec in LM Studio chat; copy-paste code terug | Laagst — geen nieuwe infra |
| **6b — Script + OpenAI API** | Klein Python-script: spec → `POST host.docker.internal:1234/v1` → schrijf files | Medium |
| **6c — MCP build server** | Local MCP tool `apply_spec_slice` met file-write + test-run | Hoger — herbruikbaar |
| **6d — Threat-designer agent hergebruiken** | Sentry/agent-patroon met “dev tools” (read_file, write_file, run_pytest) | Hoog — meta maar elegant |

**Voorstel:** **6a** voor slice 001 (leren), **6b** voor slice 002+ (reproduceerbaar).

---

## 7. Eerste kandidaat-slices (voorstel — geen go)

Gebaseerd op huidige stand (Sprint 8 open, `partialexchangeqwen.md` bewijs):

| # | Slice | Waarom geschikt voor local builder |
|---|-------|-------------------------------------|
| 001 | LangGraph pins committen + `requirements.txt` sync | Triviaal — warm-up / pipeline test |
| 002 | Playwright skeleton `lm-studio-full-scenario.spec.js` met `test.skip` | Sprint 8 L8-5; geen live LLM |
| 003 | OWASP LLM Top 10 — **één** STRIDE template JSON | Bounded, Sec-review door Maestro |
| 004 | Mock fixture `e2e/fixtures/llm/qwen/…` uit capture | Sprint 9 voorbereiding |

---

## 8. Succescriteria experiment

| Niveau | Criterium |
|--------|-----------|
| **Minimum** | Local Builder levert slice 001 met ≤ 2 Maestro-fixes |
| **Doel** | Slice 002–003 met tests groen, één capture-doc |
| **Stretch** | Builder-loop 6b scripted, reproduceerbaar door LeadPM zonder Cursor |

**Niet succes:** “local model bouwt hele fork” in één run.

---

## 9. Uitdaging — eerlijke inschatting (Maestro)

### Wat lokaal wél kan

- Bounded file edits met expliciete voor/na  
- Test-gedreven taken (pytest asserties in spec)  
- JSON/YAML/templates, routes, kleine services  
- Herhalen tot tests groen (met menselijke gate)

### Wat moeilijk blijft met 27B

- Multi-file coherentie zonder volledige repo-context  
- LangGraph/agent flows zonder regressie  
- “Begrijp de fork en migreer AWS” — te groot, te impliciet  
- Zelfstandig beoordelen wanneer klaar (stopconditie)  

### Jullie bewijs tot nu toe

`partialexchangeqwen.md` toont: **product-agent** (threat modeling) werkt **deels** met Qwen 3.6 27B — assets/flows verder dan threats, afgebroken bij catalog-cleanup. Dat is **hetzelfde model**, andere taak. Builder-taken zijn **eenvoudiger** dan volledige threat modeling — maar vereisen **betere specs** dan “bouwen zoals threat-designer”.

**Conclusie:** Ja, het is een **echte uitdaging** — en een **waardige** als we het als **experiment met kleine slices** framen, niet als vervanging van Maestro of LeadPM.

---

## 10. Open beslissingen (LeadPM)

| # | Vraag | Opties |
|---|-------|--------|
| D1 | Scope “herdoen”? | A / B / C (§2) |
| D2 | Eerste slice? | 001–004 (§7) of eigen idee |
| D3 | Builder-loop? | 6a / 6b / 6c / 6d (§6) |
| D4 | Waar specs? | `specs.md` (dit) + `docs/specs/slice-*.md` |
| D5 | Wanneer start? | Na Sprint 8-close of parallel als experiment |

---

## 11. Relatie bestaande docs

| Document | Rol |
|----------|-----|
| `sprints.md` | Officiële sprint-planning — blijft leidend voor delivery |
| `specs.md` (dit) | **Experiment** local-first build — aanvulling, geen vervanging |
| `src/projectgoal.md` | Productvisie OWASP / local |
| `docs/llm-assets-format-and-improvements.md` | LLM-gedrag product-agent |
| `docs/qa/partialexchangeqwen.md` | Bewijs + input voor fixtures |

---

*Volgende stap na LeadPM-go: eerste `docs/specs/slice-001-….md` schrijven en Builder-loop 6a of 6b proberen.*
