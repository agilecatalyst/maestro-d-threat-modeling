# Builder session — lokaal Gemma (Gemma 4 12B @ oMLX)

> **Primary build path (herzien 2026-06-08):** lokaal script of oMLX/Claude Code — **niet** Cursor Override URL op localhost.  
> Zie [cursor-local-limitations.md](dev/cursor-local-limitations.md).  
> Product threat-modeling LLM (in de app) is een **andere** lane — zie `INFERENCE_BASE_URL` in compose.

---

## Drie modi in Cursor

| Modus | Model in Cursor | Doet wat |
|-------|-----------------|----------|
| **Spec** | Default (Maestro / Composer) | `specsrebuild.md`, slice-specs, `slicedworkload.md` template |
| **Build** | **Gemma 4 12B** via lokaal endpoint | Implementeert actieve slice |
| **Review** | Default (Maestro) | Leest `slicedworkload.md`, draait DoD, zet `VERIFIED` |

**Niet Auto** — kies het model handmatig per sessie.

---

## 1. oMLX voorbereiden (eenmalig)

1. Installeer [oMLX](https://omlx.ai/) (menu bar app)
2. Laad **Gemma 4 12B** (MLX) in oMLX admin
3. Start server op poort **8002** (niet 8000 — reserved voor Maestro'D `api`)
4. Verify:

```bash
curl -sf http://localhost:8002/v1/models | head -c 200
```

Alternatief Builder-endpoint: LM Studio `:1234` met `google/gemma-4-12b` — zelfde workflow.

---

## 2. Builder — aanbevolen pad (Plan A)

**Cursor `localhost:8002` werkt meestal niet** (requests via Cursor cloud). Gebruik:

| Stap | Actie |
|------|--------|
| 1 | oMLX draait op `:8002`, model `mlx-community/gemma-4-12B-it-8bit` geladen |
| 2 | `python scripts/local_builder.py` — zie §2b (~5 min budget) |
| 3 | Of: oMLX **Admin Chat** `http://127.0.0.1:8002/admin/chat` + slice-spec plakken |
| 4 | Review met **Maestro Data** (Cursor, default model) |

### Cursor alleen voor spec + review

| Modus | Model in Cursor |
|-------|-----------------|
| Spec / review | **Composer 2.5** (Maestro Data) — cloud |
| ~~Build via Override URL~~ | ~~localhost~~ — **niet betrouwbaar** |

Details: [cursor-local-limitations.md](dev/cursor-local-limitations.md)

### oMLX verify

```bash
curl -s http://127.0.0.1:8002/v1/models
```

### 2b. Local Builder script (Plan A)

Eenmalig:

```bash
cd maestro-d-threat-modeling
python3 -m venv .venv
source .venv/bin/activate
pip install -r scripts/requirements.txt
```

Verify oMLX:

```bash
python scripts/local_builder.py --verify
```

Build actieve slice:

```bash
python scripts/local_builder.py
# Caveman-lite default: sources inline, spec cap, zero prose
# slim prompt auto als ## BLOCKERS in slicedworkload
# --max-tokens 4500 (~5 min)
```

| Default | Waarde |
|---------|--------|
| `CAVEMAN_LITE` | **True** — append-guard + stille output |
| `max_tokens` | 4500 |
| Prompt | slim als `## BLOCKERS` in slicedworkload |
| Live log | `tail -f scripts/last_builder_response_turn1.md` |
| Metriek | stdout: `Prompt size`, `Caveman prose (non-file)` |

Maestro = tech lead. Gemma = code. Zie [agents.md § Caveman-lite](../agents.md).

---

## 3. Build session starten (fallback: oMLX Admin Chat)

1. Open project: `maestro-d-threat-modeling/`
2. Model = **Gemma** (lokaal)
3. Plak prompt:

```text
You are Local Builder for Maestro'D ThreatModeling.

Read in order:
1. specsrebuild.md
2. docs/specs/slice-000-scaffold.md
3. slicedworkload.md

Implement ONLY the active slice. Update slicedworkload.md after each checklist [x].
Respect MUST NOT touch in the slice spec.
When done, set status BUILDER_CLAIMS_DONE and stop.
```

4. Laat Gemma werken tot `BUILDER_CLAIMS_DONE`

---

## 4. Switch terug — Review session (sous-chef, geen line cook)

> Fair play: zie [agents.md § Keuken-metafoor](../agents.md). Maestro **herschrijft geen** Builder-code.

1. **Nieuw chat** of switch model → **default (Maestro)**
2. Prompt:

```text
Review slicedworkload.md for the active slice.
Run Definition of Done from the active slice spec.
Update Review section in slicedworkload.md.

If DoD fails: IN_PROGRESS + concrete BLOCKERS for Local Builder.
Do NOT rewrite Builder files. Max micro-fix ~5 lines if DoD physically blocked — document it.
If DoD passes on Builder output: VERIFIED.
```

3. Bij BLOCKERS → tweede `python scripts/local_builder.py` met BLOCKERS, niet Maestro-refactor
4. Maestro draait `scripts/audit_deps.sh` (pip-audit, Python 3.12)
5. **Maître D** merge go als `VERIFIED`

---

## 5. slicedworkload.md regels

| Regel | Reden |
|-------|--------|
| Eén actieve slice | Geen parallel scope |
| Alleen Builder vult checklist `[x]` | Traceerbaarheid |
| Alleen Maestro zet `VERIFIED` | Kwaliteitsgate — **na** Builder DoD, niet na grote herschrijf |
| BLOCKERS → Builder rerun | Fair play; sous-chef kookt niet zelf |
| Builder notes bij blockers | Maître D kan helpen zonder thread |

---

## 6. Troubleshooting

| Probleem | Fix |
|----------|-----|
| Cursor geen verbinding oMLX | Server status menu bar; poort 8002 |
| Model hallucineert extra files | Herinner aan MUST NOT + max scope |
| `compose up` faalt | Builder notes → switch Review → Maestro chirurgie |
| Poort 8000 bezet | `docker compose down` in owasped fork |

---

## 7. vs product LLM

| | Builder (deze doc) | Product (tm-agent in app) |
|--|-------------------|---------------------------|
| Doel | Code schrijven | Threat modeling pipeline |
| Tool | `local_builder.py` + Gemma | LangGraph in container (004b+) |
| Endpoint | oMLX `:8002` | oMLX `:8002` via `host.docker.internal` (default) |
| Model | Gemma 4 12B 8-bit | Zelfde Gemma voorlopig — wissel af met Builder |
| Spec | slice-NNN.md | prompts + tools in agent |

**Regel:** niet tegelijk zware Builder-run + pipeline op één GPU-load.

---

*Weapon of choice: Gemma 4 12B — French Fries approved.*
