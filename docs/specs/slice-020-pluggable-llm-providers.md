# Slice 020 — Pluggable LLM providers

**Status:** READY_FOR_REVIEW  
**Depends on:** 019 (admin auth surface — nieuwe admin routes hergebruiken `require_internal_key`)  
**Gate:** Maître D go

---

## Doel

De inference-backend is niet langer vastgeklonken aan één host endpoint
(LM Studio / oMLX). Operators kunnen provider profielen beheren in de UI,
per rol toewijzen en cloud API's gebruiken — zonder dat er ooit een sleutel
in Postgres belandt.

## Scope

| ID | Item |
|----|------|
| R1 | Provider registry met vier kinds: `openai_compatible`, `openai`, `anthropic`, `gemini` (cloud SDK's lazy geïmporteerd) |
| R2 | Tabellen `llm_provider_profiles` + `llm_role_bindings` (migratie `003_llm_providers`) |
| R3 | `/admin/llm-providers` CRUD, rolbinding, `resolved/{role}` en `POST /{id}/test` |
| R4 | `tm-agent` resolvet via raw SQL, `sentry` via `THREAT_API_URL`; beide met 30 s TTL cache en env fallback |
| R5 | `api_key_env` allowlist `^(INFERENCE_API_KEY\|LLM_[A-Z0-9_]+)$`, gevalideerd bij write én bij resolve |
| R6 | `/inference/health` rapporteert `provider_kind` en `config_source` |
| R7 | Frontend `/settings`: profiel CRUD, rolkeuze, Test connection |
| R8 | Provider tabellen buiten backup export/restore |

## Allowed files

```
backend/agent/llm.py, llm_providers.py, llm_settings.py, inference.py
backend/sentry/llm.py, llm_providers.py, llm_settings.py, chat.py
backend/api/models.py, schemas.py, main.py
backend/api/routes/llm_providers.py
backend/api/services/llm_provider_service.py, backup_service.py
backend/api/alembic/versions/003_llm_providers.py
backend/{agent,sentry}/requirements.txt
frontend/src/pages/SettingsPage.tsx, App.tsx, types.ts
frontend/src/api/client.ts, components/Layout.tsx
test/test_llm_providers.py, test_llm_provider_api.py,
test/test_llm_settings_resolution.py, test_inference.py
.env.example, docker-compose.yml, README.md,
docs/dev/endpoints.md, docs/dev/dependencies.md, docs/backlog.md,
slicedworkload.md, docs/qa/verify-pass-020.md
```

## MUST NOT

- Sleutels opslaan in de database of teruggeven in een API response
- Model-discovery dropdowns (model id wordt getypt)
- Per-pipeline-stage modellen (alleen de rollen `threats` en `sentry`)
- Bestaande tabellen hernoemen of het backup payload formaat wijzigen

## Definition of Done

- [x] Lege tabellen → exact het huidige env-gedrag (regressie guard in tests)
- [x] Elk `kind` bouwt het verwachte chat-model met model/temperature/timeout
- [x] `GET` toont nooit een secret, alleen `api_key_env` + `key_present`
- [x] `DELETE` van een gebonden profiel geeft 409
- [x] `api_key_env` buiten de allowlist → 422 bij write, genegeerd bij resolve
- [x] Store/transport failure → warning + env fallback, pipeline en chat blijven werken
- [x] `/settings` biedt CRUD, rolkeuze en Test connection
- [ ] `verify-pass` groen op een machine met netwerk (zie `docs/qa/verify-pass-020.md`)
