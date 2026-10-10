# Dev endpoints — lokaal LLM

> Twee lanes: **Builder** (local script → oMLX) vs **Product** (Docker tm-agent).  
> Niet door elkaar halen. Cursor Override URL op localhost werkt meestal niet — zie [cursor-local-limitations.md](cursor-local-limitations.md).

---

## 1. Local Builder — oMLX + Gemma 4 12B (8-bit)

Gebruik **`scripts/local_builder.py`** (zie [builder-session.md](../builder-session.md)).

| Env / flag | Waarde |
|------------|--------|
| `OMLX_BASE_URL` / `--base-url` | `http://127.0.0.1:8002/v1` |
| `--api-key` | `Mikey` (hardcoded in `scripts/local_builder.py`) |
| `OMLX_MODEL` / `--model` | id uit `GET /v1/models` (auto-detect als leeg) |

```bash
python scripts/local_builder.py --verify
python scripts/local_builder.py
```

~~Cursor Override URL~~ — experimenteel; requests gaan via Cursor cloud → localhost faalt.

### Verify oMLX

```bash
curl -s http://127.0.0.1:8002/v1/models | python3 -m json.tool
```

Noteer de `"id"` van je geladen model — die plak je in Cursor als modelnaam.

### Aanbevolen model (Builder)

| Model | Type | RAM (richtlijn) |
|-------|------|-----------------|
| `mlx-community/gemma-4-12B-8bit` (of IT-variant) | **Dense ~12B** | ~13 GB (8-bit) |
| `google/gemma-4-12B-it` | Dense unified | hoger in 16-bit |

**Weapon of choice** in credits: Gemma 4 12B — 8-bit MLX is prima voor Builder.

---

## 2. oMLX toont “3.4B params” bij `gemma-4-12B-8bit`?

**Ja — dat is een display-typo / tellingsartefact in oMLX (of HF metadata), geen verkeerd model.**

| Check | Verwacht voor **echte 12B 8-bit** |
|-------|-----------------------------------|
| Model-id | `mlx-community/gemma-4-12B-8bit` |
| Architectuur | `Gemma4Unified` — **48 layers**, `hidden_size` 3840 |
| RAM bij load | **~13 GB** (Google: 12B @ 8-bit ≈ 13,4 GB) — geen 3B-footprint |
| Google spec | **~11,95B dense** parameters (geen MoE) |

De **3.4B** in de UI lijkt **niet** op “je hebt per ongeluk E4B/26B-A4B” als de id **`gemma-4-12B-8bit`** is — vertrouw de **model-id + RAM**, niet alleen het params-label.

MoE zou **`26b-a4b`** in de id hebben (~4B active / 26B totaal) — dat is iets anders.

```bash
curl -s http://127.0.0.1:8002/v1/models
# id moet "12B" bevatten, niet "26b-a4b" of "E4B"
```

---

## 3. Product LLM — threat pipeline (Docker)

**Voorlopig default: oMLX + Gemma 4 12B** — zelfde instance als Builder.

| Veld | Default (oMLX) |
|------|----------------|
| `INFERENCE_BASE_URL` | `http://host.docker.internal:8002/v1` |
| `INFERENCE_API_KEY` | `Mikey` |
| `LOCAL_MODEL` | id uit `GET :8002/v1/models` (bv. `gemma-4-12B-it-8bit`) |

**Alternatief** (groter model, apart proces):

| Veld | LM Studio |
|------|-----------|
| `INFERENCE_BASE_URL` | `http://host.docker.internal:1234/v1` |
| `LOCAL_MODEL` | `qwen/qwen3.6-27b` |

### Eén GPU, twee rollen

| Rol | Wanneer |
|-----|---------|
| Builder (Bob) | `python scripts/local_builder.py` |
| Product (pipeline) | `POST /invocations` → summary/assets/… |

**Regel:** niet tegelijk zware Builder-run + pipeline op dezelfde oMLX load — wissel af. Eén geladen Gemma 12B dekt **beide** voor dev.

Zie [.env.example](../../.env.example).

---

## 4. Poorten overzicht

| Poort | Service |
|-------|---------|
| **8002** | oMLX — **Cursor Builder** (`127.0.0.1`) |
| **1234** | LM Studio — **Product** LLM (host → Docker) |
| **8000** | Maestro'D `api` (compose, later slice 000) |
| **8080** | Maestro'D `tm-agent` (compose) |
| **5432** | Postgres (compose) |

---

## 5. Copy-paste checklist Maître D

- [ ] oMLX server op **8002**
- [ ] Model = **Gemma 4 12B 8-bit** (id bevestigd via `/v1/models`)
- [ ] `pip install -r scripts/requirements.txt`
- [ ] `python scripts/local_builder.py --verify`
- [ ] `python scripts/local_builder.py` (actieve slice uit [slicedworkload.md](../../slicedworkload.md))

---

## 6. Provider configuratie (slice 020)

Vanaf slice 020 is de inference-backend **pluggable**. De `api` service beheert
provider profielen; `tm-agent` leest ze direct uit Postgres, `sentry` haalt ze
op via `THREAT_API_URL`. Zonder profielen valt alles terug op het bestaande
`INFERENCE_BASE_URL` / `LOCAL_MODEL` / `INFERENCE_API_KEY` blok.

### Routes (`api`, poort 8000)

| Methode | Pad | Doel |
|---------|-----|------|
| `GET` | `/admin/llm-providers` | Alle profielen (zonder secrets) |
| `POST` | `/admin/llm-providers` | Profiel aanmaken — `X-Internal-Key` vereist |
| `PUT` | `/admin/llm-providers/{id}` | Profiel wijzigen — `X-Internal-Key` vereist |
| `DELETE` | `/admin/llm-providers/{id}` | Verwijderen; **409** als het aan een rol hangt |
| `GET` | `/admin/llm-providers/roles` | Huidige binding per rol |
| `PUT` | `/admin/llm-providers/roles/{role}` | Rol (`threats` \| `sentry`) aan profiel koppelen |
| `GET` | `/admin/llm-providers/resolved/{role}` | Effectieve config (`source: db` of `env`) |
| `POST` | `/admin/llm-providers/{id}/test` | Live round trip → `{ok, latency_ms, detail\|error}` |

### Provider kinds

| `kind` | Verplicht | Voorbeeld |
|--------|-----------|-----------|
| `openai_compatible` | `base_url`, `model` | LM Studio, oMLX, Ollama `/v1`, vLLM, OpenRouter |
| `openai` | `model`, `api_key_env` | `gpt-4o-mini` |
| `anthropic` | `model`, `api_key_env` | `claude-sonnet-4` |
| `gemini` | `model`, `api_key_env` | `gemini-2.5-pro` |

### Secrets by reference

Een profiel bewaart **nooit** een sleutel, alleen `api_key_env`: de *naam* van
een environment variabele. De resolver doet `os.getenv(naam)` achter een
allowlist `^(INFERENCE_API_KEY|LLM_[A-Z0-9_]+)$`, zodat een geprepareerd profiel
geen `POSTGRES_PASSWORD` kan uitlezen. API responses tonen alleen `api_key_env`
plus een boolean `key_present`. De tabellen zitten niet in backup export/restore.

### Health

`GET /inference/health` (tm-agent, poort 8080) rapporteert nu ook
`provider_kind` en `config_source` (`db` of `env`), en gebruikt een probe die
bij het provider type past in plaats van altijd `GET {base_url}/models`.
