# Cursor + lokaal model — beperkingen & alternatieven

> **Update 2026-06-08:** `http://127.0.0.1:8002/v1` in Cursor werkt voor de meeste gebruikers **niet** zoals verwacht.  
> Dit is (vooralsnog) een **Cursor-platformlimiet**, geen oMLX-configfout.

---

## Waarom jouw setup faalt

Uit [Cursor forum](https://forum.cursor.com/) (o.a. staff antwoord mei 2026):

| Feit | Impact |
|------|--------|
| Requests gaan via **Cursor backend**, niet rechtstreeks vanuit de IDE | `localhost` / `127.0.0.1` is vanaf hun servers **onbereikbaar** |
| **Agent-modus** + lokaal custom model | **Niet ondersteund** |
| Custom modelnamen (`gemma-4-12B-it-8bit`) | Vaak **validatie-fout** (streepjes, hoofdletters) |
| Override OpenAI URL | Soms alleen Chat/Cmd+K; bugs (`model is required`) in Agent |

Je screenshot (Override URL + custom model aan) is **logisch**, maar past niet bij hoe Cursor vandaag werkt.

---

## Opties (gerangschikt voor Maestro'D)

### ⭐ Plan A — Aanbevolen: Builder-script (100% lokaal)

| | |
|--|--|
| **Wie specificeert** | Maestro Data (Cursor, cloud) |
| **Wie codeert** | Gemma @ oMLX via **lokaal Python-script** op je Mac |
| **Privacy** | Code gaat **niet** via Cursor naar oMLX — alleen jij start het script |

Flow:

1. Maestro schrijft `docs/specs/slice-NNN.md` + `slicedworkload.md`
2. Jij draait: `python scripts/local_builder.py` (slice 000)
3. Script leest spec, roept `http://127.0.0.1:8002/v1` aan, schrijft files
4. Switch terug naar Maestro → review → `VERIFIED`

*Slice 000 kan ook handmatig: oMLX Admin Chat + copy-paste tot script klaar is.*

---

### Plan B — oMLX Admin (`/admin`)

| Feature | URL |
|---------|-----|
| Dashboard | `http://127.0.0.1:8002/admin` |
| **Chat** | `http://127.0.0.1:8002/admin/chat` |
| Tool-integraties | oMLX admin → one-click config o.a. OpenClaw, Copilot |

- **Chat:** geen automatische file-writes in je repo — copy-paste of Plan A script
- **Model directory:** oMLX ontdekt modellen in `--model-dir` / HF cache — geen “Cursor directory point”

---

### Plan C — Claude Code + oMLX (echte agent-loop, lokaal)

oMLX ondersteunt **Anthropic Messages API** — bedoeld voor coding agents met tools.

```bash
export ANTHROPIC_BASE_URL=http://127.0.0.1:8002
export ANTHROPIC_API_KEY=local
# oMLX admin genereert exacte env voor jouw setup
```

- Volledige tool-loop (read/write/run) **lokaal**
- Andere CLI dan Cursor; wel in `maestro-d-threat-modeling/` werken
- oMLX dashboard: integratie-presets

---

### Plan D — VS Code Insiders + Copilot + OpenAI-compatible

- OpenAI-compatible → `http://127.0.0.1:8002/v1`
- Experimenteler; werkt voor sommigen met Insiders
- Zie [blogpost oMLX + Copilot](https://www.hristoforgeorgiev.com/posts/local-llm-macbook-pro-m5pro-claude/)

---

### Plan E — Cursor + ngrok (⚠️ niet voor jullie privacy-verhaal)

- Tunnel: `ngrok http 8002` → HTTPS URL in Override Base URL
- Requests gaan nog steeds **eerst door Cursor cloud**, daarna naar jouw tunnel
- **Niet** passend bij “code blijft lokaal” voor OWASP/Maître D

---

## oMLX model directory — wat wél kan

Geen Cursor-koppeling, wel oMLX:

| Instelling | Waar |
|------------|------|
| Model-dir | oMLX admin of `omlx serve --model-dir ~/path` |
| Settings | `~/.omlx/settings.json` |
| Download | HF → map die oMLX scant (`mlx-community/gemma-4-12B-it-8bit`) |

Verify:

```bash
curl -s http://127.0.0.1:8002/v1/models
```

---

## Aanbevolen werkwijze Maestro'D (herzien)

```
Spec/review  →  Maestro Data (Cursor, Composer — cloud)
Build        →  Plan A script OF oMLX chat OF Claude Code + oMLX
Product LLM  →  LM Studio :1234 → Docker tm-agent (later)
```

Zie [builder-session.md](../builder-session.md) (wordt bijgewerkt).
