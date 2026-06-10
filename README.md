# Maestro'D ThreatModeling

Local-first AI threat modeling — volwaardige analog van [AWS Threat Designer](https://github.com/awslabs/threat-designer), zonder cloud lock-in.

## Credits

Inspired by AWS Threat Designer · Envisioned by **Maître D** ·  
Designed & architected with Lead Architect **Maestro Data** (Cursor) ·  
Local inference — weapon of choice: **Gemma 4 12B** (coding & modeling)

See [NOTICE](NOTICE) for formal attribution.

## Status

**Planning** — zie [specsrebuild.md](specsrebuild.md) en [agents.md](agents.md).

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
