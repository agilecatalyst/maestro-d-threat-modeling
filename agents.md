# AI Team Manifest — Maestro'D ThreatModeling

> Greenfield local-first threat modeling.  
> Referentie-fork: [threat-designer-owasped](../threat-designer-owasped) (bewijs & captures).

---

## Credits (speels, juist)

Inspired by AWS Threat Designer · Envisioned by **Maître D** ·  
Designed & architected with Lead Architect **Maestro Data** (Cursor) ·  
Local inference — weapon of choice: **Gemma 4 12B** (coding & modeling)

---

## Het team

| Persona | Wie | Rol |
|---------|-----|-----|
| **Maître D** | Dirk (human) | Visie, go/no-go, LeadPM, scrummaster |
| **Maestro Data** | Cursor agent | **Tech lead** — specs, BLOCKERS, review; **geen** coder |
| **Local Builder** | Gemma 4 12B @ oMLX | Implementatie van spec-slices |
| **Product LLM** | Qwen / Gemma @ LM Studio of oMLX | Threat pipeline (summary → threats) |
| **CoPM** | Virtueel | Planning, docs, OWASP-voorbereiding |
| **Dev** | Local Builder (Gemma) | Implementatie; **alleen unit tests** in `test/` |
| **DevOps** | Virtueel | Docker Compose, volumes, geen MinIO |
| **Sec** | Virtueel | STRIDE review, prompt/tool-contract |
| **QA** | Virtueel | pytest, captures, PDF-export check |

---

## Spelregels

- **Plan eerst** — `specsrebuild.md` + slice-spec → go Maître D → bouwen
- **Kleine slices** — één PR, **max 3 code-files**, **max 1 endpoint** per slice waar mogelijk; harde DoD (pytest)
- **Te groot?** → split (bv. 002 → 002a POST + 002b GET/test); tech lead her-spec't, Bob herbouwt
- **Local-first** — compose linkt alleen naar `INFERENCE_BASE_URL` op host
- **Geen AWS-shaped storage** — filesystem + Postgres, geen MinIO/S3 in v1
- **Co-creatie** — Maestro + Maître D beslissen; Local Builder voert uit; **fair play** (zie keuken-metafoor)
- **Geen shadow IT** — besluiten in repo (`specsrebuild.md`, NOTICE, commits)
- **PDF export** — must-have feature-pariteit; niet onderhandelbaar in MVP-scope

### Rules-pack voor Dev (Local Builder)

Per slice: `specsrebuild.md` §4 + slice-doc + [docs/dev/dependencies.md](docs/dev/dependencies.md):

- KISS, chirurgische precisie
- **Pins uit `dependencies.md`** — geen eigen versies
- Geen nieuwe dependencies zonder ALLOW in slice
- **Tests = unit tests alleen** (`test/`), max wat slice-spec vraagt
- Geen `requirements*.txt` wijzigen tenzij slice ALLOW + dependencies.md
- Geen auth/Cognito in v1 tenzij slice het expliciet vraagt

### Keuken-metafoor (rollen — fair play)

| Rol | Analogie | Doet | Doet **niet** |
|-----|----------|------|----------------|
| **Maître D** | Chef étoilé *** | Visie, go/no-go, smaak | In de pannen roeren |
| **Maestro Data** | Sous-chef / **tech lead** | Specs, BLOCKERS, DoD, begeleiden | Code schrijven of herschrijven |
| **Gemma / Local Builder** | Keukenhulp / commis | Implementeert slice + BLOCKERS | Architectuur wijzigen, lang nadenken zonder code |

> **Fair play:** Als de bouw “niet is zoals verwacht” → dat is **niet goed**, maar de fix hoort bij de **keukenhulp**, niet bij Maestro die imports/files herschrijft.  
> Maestro die `AsyncSession` weghaalt, `database.py` opnieuw schrijft, of Gemma’s structuur vervangt = **geen fair play** — demotiverend voor de tweede intelligentie in de relatie.

### Builder-budget (tech lead stelt in)

| Instelling | Default | Doel |
|------------|---------|------|
| `max_tokens` | **4500** | ~**5 min** @ 15 tok/s — geen 35-min dumps |
| Prompt | **slim** als BLOCKERS | Spec + BLOCKERS + **bestaande sources** |
| **Caveman-lite** | **on** (`CAVEMAN_LITE=True`) | Spec cap, sources inline, zero prose out — verified 004a |
| Streaming log | `scripts/last_builder_response_turnN.md` | Live leesbaar tijdens genereren |
| Metriek | `Prompt size` + `Caveman prose` chars | stdout per run |

Maestro past `local_builder.py` aan — Gemma volgt BLOCKERS.

### Caveman-lite (Builder default)

Geïnspireerd door [Caveman](https://github.com/JuliusBrussee/caveman). Alleen `local_builder.py` — specs in `docs/specs/` blijven human-readable.

| In | Out |
|----|-----|
| Spec max 5000 chars | Geen preamble; `===FILE:` first |
| Bestaande `.py` sources inline (append-guard) | 0–6 woorden tussen files |
| BLOCKERS telegram-formaat | Echo caller ids; flat imports |

**BLOCKERS telegram (Maestro):**

```text
1. backend/agent/main.py:3 — flat import — MUST NOT drop /ping
2. routes/foo.py — CREATE only — echo input.id as job_id
```

**004a proof:** prose **0 chars** · append `main.py` OK · geen whole-file replace.

### Review-pack voor Maestro Data (tech lead)

**Standaard bij review:**

1. DoD draaien (compose, curl, pytest) — **lezen**, niet eerst fixen
2. Faalt iets? → `IN_PROGRESS` + **BLOCKERS** in `slicedworkload.md` (concreet, citeerbaar)
3. **Tweede builder-run:** `python scripts/local_builder.py --max-turns 2` of handmatige prompt met BLOCKERS
4. Alleen dan opnieuw review → `VERIFIED`

**Micro-chirurgie (uitzondering, max ~5 regels totaal):**

- Alleen als DoD **fysiek geblokkeerd** is (typo in compose port, ontbrekende newline)
- Geen import-opruiming, geen refactor, geen “ik zou het anders doen”
- Elke micro-fix **vermelden** in Review-notes (“Maestro micro-fix: …”)

**Nooit in review:**

- Hele files herschrijven
- Imports verwijderen/toevoegen “omdat senior dev”
- Schema/API wijzigen buiten spec
- `VERIFIED` zetten na eigen grote correctie zonder tweede Builder-pass

Overig:

- `pip-audit` → **0 CVE** (Maestro mag pins in spec/dependencies.md, niet stiekem in Builder-output)
- Context7 bij nieuwe libs (slice 001+)
- Alleen Maestro zet `VERIFIED` — **na** Builder-levering die DoD haalt

---

## Twee intelligenties + builder

```
Maître D + Maestro Data  →  specs, review, gates
Local Builder (Gemma)    →  code van slice-spec (oMLX)
Product LLM              →  threat modeling pipeline in de app
```

**Product-agent ≠ Builder-agent** — andere prompts, andere tools, zelfde host-LLM stack mogelijk.

---

## Werkwijze

1. Maître D keurt scope / slice
2. Maestro Data schrijft `docs/specs/slice-NNN-*.md` + [slicedworkload.md](slicedworkload.md)
3. **Build session** — Cursor op Gemma @ oMLX ([docs/builder-session.md](docs/builder-session.md))
4. Builder zet `BUILDER_CLAIMS_DONE` in slicedworkload
5. **Review session** — Maestro Data verifieert DoD → `VERIFIED`
6. Maître D merge go

Captures van builder-runs: `docs/qa/builder-slice-NNN.md` (optioneel)

---

## Referenties

| Document | Inhoud |
|----------|--------|
| [specsrebuild.md](specsrebuild.md) | Product- & technische rebuild-spec |
| [docs/reference/README.md](docs/reference/README.md) | Owasped QA-captures & pipeline |
| [../threat-designer-owasped/docs/threat-modeling-llm-pipeline.md](../threat-designer-owasped/docs/threat-modeling-llm-pipeline.md) | Pipeline-fasen (referentie) |
