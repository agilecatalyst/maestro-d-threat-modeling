# specsrebuild.md — Maestro'D ThreatModeling

**Status:** v1.0 — LeadPM go (Maître D) — 2026-06-05  
**Scope:** D1 greenfield rebuild — volwaardige analog AWS Threat Designer, local-first  
**Bouw:** Maître D + Composer (spec/bouw primair) · Local Builder Gemma 4 12B @ oMLX (optioneel) — zie [docs/governance.md](docs/governance.md)

---

## Credits

Inspired by AWS Threat Designer · Envisioned by **Maître D** ·  
Designed & architected with Lead Architect **Maestro Data** (Cursor) ·  
Local inference — weapon of choice: **Gemma 4 12B** (coding & modeling)

Formal: [NOTICE](NOTICE)

---

## 1. Visie

**Maestro'D ThreatModeling** is een volledig lokale, containerized AI threat modeling tool:

- **Input:** architectuurtekening (visual) + beschrijving + aannames
- **Output:** STRIDE threat catalog, dashboards, **PDF-rapport** (must), JSON export
- **Inference:** uitsluitend lokaal model op host — Docker Compose heeft **één externe dependency**: `INFERENCE_BASE_URL`
- **Sentry:** optionele sparring-assistent over het threat model
- **Geen** AWS Cognito, Bedrock, Lambda, DynamoDB, S3/MinIO in v1

Referentie-implementatie en bewijs: [`../threat-designer-owasped`](../threat-designer-owasped)  
Pipeline-capture: [`partialexchangeqwen.md`](../threat-designer-owasped/docs/qa/partialexchangeqwen.md)

---

## 2. Niet-doelen (v1)

| Uitgesloten | Reden |
|-------------|--------|
| MinIO / S3 / boto3 file storage | Te AWS-shaped — zie §5 |
| DynamoDB Local | In-memory; vervangen door Postgres |
| Terraform / `infra/` AWS | Niet local-first |
| Cognito / JWT auth | Later; v1 = `local-user` stub |
| Cloud LLM in productpad | Privacy & OWASP-verhaal |
| Volledige upstream feature-pariteit dag 1 | Slices; zie §12 |

---

## 3. Feature-pariteit (t.o.v. AWS Threat Designer)

### Must (MVP)

| Feature | Beschrijving |
|---------|--------------|
| **Diagram upload** | PNG/JPG (PDF pagina later) — persistent op volume |
| **Threat modeling wizard** | Beschrijving, aannames, application type, start job |
| **Pipeline fasen 0–5** | Zie §6 |
| **Threat catalog UI** | Bekijken, filteren, bewerken (basis) |
| **Job status / polling** | Processing → resultaat |
| **Export PDF** | Mooi rapport — **must** (upstream-kwaliteit als streven) |
| **Export JSON** | Volledige threat model state |
| **Local LLM** | OpenAI-compat endpoint op host |
| **Persistent data** | Postgres + diagram volume overleeft `compose down` |

### Should (MVP of v1.1)

| Feature | Beschrijving |
|---------|--------------|
| Threat catalog replay / refine | `iteration`, `instructions`, `replay` |
| Attack tree | Na stabiele core pipeline |
| **Sentry** assistent | Chat over threat model; compose profile `full` |
| Export DOCX | Zelfde template-bron als PDF |

### Could (backlog)

| Feature | Beschrijving |
|---------|--------------|
| OWASP LLM Top 10 templates | Na stabiele STRIDE basis |
| Multi-user / auth | Post-MVP |
| Collaboration / locks | Port van upstream concepten |

---

## 4. Local-first spec-principes (voor Builder)

Zie ook [agents.md](agents.md).

- **SHALL** / **MUST NOT** taal in slice-specs (`docs/specs/slice-NNN-*.md`)
- Max **3 bestanden** per slice (richtlijn)
- **pytest** of API-test als DoD
- Builder rules-pack bij elke slice
- Maestro Data review vóór merge

### Builder stack

| Rol | Model | Runtime |
|-----|-------|---------|
| **Local Builder** | Gemma 4 12B | **oMLX** (MLX, SSD KV-cache) |
| **Product LLM** | Qwen 3.6 / Gemma 4 | LM Studio of oMLX (`LOCAL_MODEL` env) |

---

## 5. Architectuur

```mermaid
flowchart TB
  subgraph host [Host Mac — enige externe deps]
    LLM["INFERENCE_BASE_URL\nLM Studio :1234 of oMLX :8002"]
    OLMX["oMLX — Builder only\nGemma 4 12B"]
  end
  subgraph compose [docker-compose]
    UI[frontend :5173]
    API[api :8000 FastAPI]
    AGENT[tm-agent :8080]
    PG[(postgres)]
    VOL["/data/diagrams volume"]
    SEN[sentry :8090\nprofile full optional]
  end
  UI --> API
  API --> AGENT
  API --> PG
  API --> VOL
  AGENT --> LLM
  AGENT --> PG
  SEN --> LLM
  SEN --> PG
```

### Services

| Service | Poort | Taak |
|---------|-------|------|
| `postgres` | 5432 | Alle metadata, job state, threat catalog |
| `api` | 8000 | REST API, upload, catalog, export trigger |
| `tm-agent` | 8080 | LangGraph `/invocations` |
| `frontend` | 5173 | Vite dev (niet in compose prod; wel dev workflow) |
| `sentry` | 8090 | Optioneel — profile `full` |

### Opslag (geen MinIO)

| Data | Opslag |
|------|--------|
| Diagrambestanden | Bind mount `./data/diagrams/{id}.{ext}` |
| Metadata | Postgres kolom `diagram_path` (of `storage_uri` `file://…`) |
| Agent state / trail | Postgres tabellen (niet DynamoDB-shaped tenzij bewezen nodig) |

**Storage interface:** `StorageBackend` — v1 alleen `LocalFileStorage`; geen S3.

### Compose env (minimum)

```env
# Enige “cloud” = host LLM
INFERENCE_BASE_URL=http://host.docker.internal:1234/v1
INFERENCE_API_KEY=local
MODEL_PROVIDER=ollama
LOCAL_MODEL=qwen/qwen3.6-27b

DATABASE_URL=postgresql://maestro:maestro@postgres:5432/maestro_d
DIAGRAM_STORAGE_PATH=/data/diagrams
LOCAL_USER=local-user
```

---

## 6. Threat modeling pipeline (functionele contract)

Gebaseerd op [threat-modeling-llm-pipeline.md](../threat-designer-owasped/docs/threat-modeling-llm-pipeline.md) en [partialexchangeqwen.md](../threat-designer-owasped/docs/qa/partialexchangeqwen.md).

| Fase | Naam | LLM-actie | Tools / schema |
|------|------|-----------|----------------|
| **0** | Init | Load diagram (base64), description, assumptions, application_type, instructions | — |
| **1** | Summary | Multimodale interpretatie tekening | `summary` prompt |
| **2** | Assets | Componenten, entities, criticality | `AssetsList` |
| **3** | Flows | Data flows, trust boundaries, threat actors | `FlowsList` |
| **4** | Threats (agentic) | generate → audit → fix loop | `add_threats`, `delete_threats`, `gap_analysis` |
| **4b** | Threats (traditional) | Optioneel bij `iteration > 0` | structured threats prompt |
| **5** | Finalize | Persist catalog, job COMPLETE | — |

### Agent workflow (threats fase)

```
Work in a generate → audit → fix loop until gap_analysis returns STOP.
```

- `add_threats` — batch threat objects (STRIDE, threat grammar)
- `gap_analysis` — CONTINUE of STOP
- Threat grammar: `[source] [prerequisites] can [action] which leads to [impact], negatively impacting [target]`

### Model-rollen (product)

| Rol | Gebruik |
|-----|---------|
| `summary_model` | Fase 1 |
| `assets_model` | Fase 2 |
| `flows_model` | Fase 3 |
| `threats_agent_model` | Fase 4 agentic + tools |
| `gaps_model` | gap_analysis backing |

Alle via `ChatOpenAI` + `INFERENCE_BASE_URL` (zelfde patroon als owasped).

### Parser-fallbacks (must port concept)

Van owasped — nodig voor lokale modellen:

- Plain-text asset blocks → `AssetsList`
- `[TOOL_REQUEST]` + JSON wrapper (Gemma)
- `tool_request_markers` / `structured_tool_json`
- `add_threats` schema coercion + max schema errors env

Referentie: [`docs/llm-assets-format-and-improvements.md`](../threat-designer-owasped/docs/llm-assets-format-and-improvements.md)

---

## 7. API surface (analoog)

| Method | Route | Doel |
|--------|-------|------|
| GET | `/threat-designer/all` | Catalog list |
| POST | `/threat-designer` | Start job |
| GET | `/threat-designer/{id}` | Status + result |
| GET | `/threat-designer/{id}/export/pdf` | **PDF download** |
| GET | `/threat-designer/{id}/export/json` | JSON export |
| POST | `/invocations` | Agent (internal tm-agent) |

Exacte paths mogen tijdens slice 001–003 worden vastgelegd; **semantiek** blijft analoog upstream.

---

## 8. PDF export (must)

| Aspect | Specificatie |
|--------|--------------|
| **Inhoud** | Summary, assets, flows, threat catalog (STRIDE), metadata, **credits colofon** |
| **Kwaliteit** | Professioneel layout — streven naar upstream Threat Designer PDF-niveau |
| **Techniek** | Python: Jinja2/HTML template → **WeasyPrint** (voorkeur) of reportlab |
| **Colofon** | NOTICE credits + threat model id + datum |
| **Trigger** | API endpoint + knop in UI |

Slice: **slice-010-pdf-export** (na catalog UI werkt).

---

## 9. Sentry (optioneel)

| Aspect | Keuze |
|--------|--------|
| Activeer | `docker compose --profile full` |
| Poort | 8090 |
| LLM | Zelfde `INFERENCE_BASE_URL` |
| UI | `VITE_SENTRY_ENABLED` + `VITE_SENTRY_BASE_URL` |
| Scope v1 | Chat over threat model; geen Tavily verplicht |

Referentie: [sentry_design.md](../threat-designer-owasped/docs/sentry_design.md)

---

## 10. Frontend (analoog)

Mag sterk lijken op upstream UX; **geen** Amplify/Cognito.

| Scherm | Functie |
|--------|---------|
| Landing / catalog | Threat models overzicht |
| Wizard | Upload, beschrijving, start |
| Processing | Poll status |
| Results | Tabs: summary, assets, flows, threats, charts |
| Export | PDF, JSON |
| Sentry drawer | Optioneel |

Tech: Vite + React (zoals owasped na Sprint 4).

---

## 11. Tech stack samenvatting

| Laag | Technologie |
|------|-------------|
| API | FastAPI, uvicorn, pydantic, sqlalchemy |
| Agent | LangGraph, langchain-openai, httpx |
| DB | PostgreSQL 16 |
| Files | Local volume |
| PDF | WeasyPrint + Jinja2 |
| Tests | pytest, Playwright (smoke later) |
| Compose | 1 file `docker-compose.yml` |

**LangGraph pins:** `langgraph==1.0.10`, `langgraph-prebuilt==1.0.8` (les uit owasped).

---

## 12. Slice roadmap

| Slice | Doel | DoD |
|-------|------|-----|
| **000** | Repo scaffold, NOTICE, compose skeleton, health | `compose up` groen |
| **001** | Postgres + migrations + `local-user` | pytest db |
| **002a** | Diagram POST upload → volume + DB rows | curl POST 200 |
| **002b** | Diagram GET metadata + pytest | pytest upload |
| **003** | `tm-agent` health + `INFERENCE_BASE_URL` ping | models list OK |
| **003a** | `GET /inference/health` endpoint | curl 200/503 |
| **003b** | pytest inference | pytest green |
| **004a** | `/invocations` stub (202, geen LLM) | curl POST 202 |
| **004b** | Summary node + LangGraph (oMLX Gemma multimodal) | job summary in DB |
| **004c** | pytest summary golden | pytest skip if LLM down |
| **005a** | Assets parsers (`AssetsList` + fallbacks) | pytest parsers |
| **005b** | Assets worker (pipeline after summary) | ASSETS_DONE in DB |
| **006** | Flows `FlowsList` | pytest |
| **007a–d** | Threats + agent loop + COMPLETE | pytest + e2e |
| **008** | API job flow + polling + LangGraph | pytest + e2e via API |
| **009** | Frontend wizard + results shell | npm build + manual |
| **010** | **PDF export** | PDF opens, colofon OK |
| **011** | **JSON export** | schema stable |
| **012** | Sentry profile `full` | `/ping` healthy |

Local Builder (Gemma @ oMLX) bouwt slices **000–003** eerst; Maestro Data review.

---

## 13. Projectstructuur (target)

```
maestro-d-threat-modeling/
├── NOTICE
├── README.md
├── agents.md
├── specsrebuild.md          ← dit document
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── api/                 # FastAPI
│   ├── agent/               # LangGraph tm-agent
│   └── sentry/              # optioneel
├── frontend/
├── data/diagrams/           # volume (gitignored)
├── docs/
│   ├── reference/
│   └── specs/               # slice-NNN-*.md
└── test/
```

---

## 14. Relatie threat-designer-owasped

| owasped | Maestro'D |
|---------|-----------|
| Migratie fork | **Greenfield** |
| DynamoDB + MinIO | Postgres + filesystem |
| Sprint 8/9 | Nieuwe slice-planning hier |
| `specs.md` experiment | Vervangen door `specsrebuild.md` voor dit product |

Owasped blijft open voor experimenten en QA-captures.

---

## 15. Open punten (Maître D)

| # | Vraag | Default in deze spec |
|---|-------|----------------------|
| O1 | oMLX poort builder | 8002 (api compose blijft 8000) |
| O2 | Product model default | Qwen 3.6 op LM Studio; builder Gemma op oMLX |
| O3 | Git init in sibling | Maître D init + eerste commit wanneer gewenst |
| O4 | Attack tree in MVP? | **Should** — na slice 010 |

---

*Engage. Volgende stap: `docs/specs/slice-000-scaffold.md` + `docker-compose.yml` skeleton — op go Maître D.*
