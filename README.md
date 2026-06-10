# Maestro'D ThreatModeling

Local-first AI threat modeling — local-first reimplementation inspired by [AWS Threat Designer](https://github.com/awslabs/threat-designer), zonder cloud lock-in.

## License

Licensed under the [Apache License 2.0](LICENSE). See [NOTICE](NOTICE) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for attribution.

## Credits

Inspired by AWS Threat Designer · Envisioned by **Maître D** ·  
Designed & architected with Lead Architect **Maestro Data** (Cursor) ·  
Local inference — weapon of choice: **Gemma 4 12B** (coding & modeling)

See [NOTICE](NOTICE) for formal attribution. AWS Threat Designer is a trademark of Amazon.com, Inc.; this project is not affiliated with AWS.

## Status

**MVP 000–016** — zie [slicedworkload.md](slicedworkload.md), [SECURITY.md](SECURITY.md), [docs/backlog.md](docs/backlog.md).

## Quick start

```bash
cp .env.example .env
# Hardened (localhost API only):
docker compose --profile full up -d --build
# Dev (expose postgres :5432, agent :8080, sentry :8090 on localhost):
docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile full up -d --build

cd frontend && npm install && npm run dev
```

Open http://localhost:5173 — API at http://127.0.0.1:8000

```bash
# Smoke (API up, catalog responds)
bash scripts/smoke.sh
# or from frontend/: npm run smoke
```

## Referentie-fork

Bewijs, QA-captures en pipeline-kennis: [`../threat-designer-owasped`](../threat-designer-owasped)  
→ [docs/reference/README.md](docs/reference/README.md)

## Stack (target)

| Component | Keuze |
|-----------|--------|
| Backend | Python / FastAPI |
| Data | PostgreSQL (persistent) |
| Diagrammen | Local filesystem volume (geen MinIO/S3) |
| LLM | Host endpoint only (`INFERENCE_BASE_URL`) — LM Studio / oMLX |
| Frontend | Vite + React (analoog upstream UX) |
| Sentry | Optioneel — sparring-assistent |
| Export | **PDF** (must), JSON (should), DOCX (could) |
