# Maestro'D Frontend

Vite + React UI for local threat modeling.

## Dev

```bash
# from repo root — API stack must be running
docker compose up -d

cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Style

**Architect's Forge** — dark slate workspace, copper/amber accents, STRIDE color coding. Built for long threat-review sessions without AWS/Amplify chrome.

## Routes

| Path | Screen |
|------|--------|
| `/` | Catalog (`GET /threat-designer/all`) |
| `/new` | Wizard — upload + start job |
| `/models/:id` | Results — poll + tabs |

API proxy: `vite.config.ts` forwards `/threat-designer` → `localhost:8000`.
