# Dependencies — Maestro'D (canonical pins)

> **Eigenaar:** Maestro Data — bijgewerkt na Context7 + `pip-audit` (Python **3.12**).  
> **Dev (Gemma):** kopieer exact deze versies; geen `>=` of `~=` tenzij hier expliciet.

Laatste audit: **2026-06-08** — `pip-audit` → **0 known vulnerabilities** (in `python:3.12-slim`).

---

## Backend core (`api` + `tm-agent`)

| Package | Pin | Opmerking |
|---------|-----|-----------|
| `fastapi` | `==0.136.3` | Context7 `/fastapi/fastapi` — current stable |
| `uvicorn[standard]` | `==0.34.0` | ASGI server |
| `pydantic` | `==2.11.5` | `>=2.7,<3` band (FastAPI docs) |
| `httpx` | `==0.28.1` | alleen `tm-agent` (later slices) |
| `python-dotenv` | `>=1.2.2` | transitief via uvicorn; expliciet voor CVE fix |

### `backend/api/requirements.txt`

```
fastapi==0.136.3
uvicorn[standard]==0.34.0
pydantic==2.11.5
python-dotenv>=1.2.2
```

### `backend/agent/requirements.txt`

```
fastapi==0.136.3
uvicorn[standard]==0.34.0
pydantic==2.11.5
httpx==0.28.1
python-dotenv>=1.2.2
```

---

## Review gate (Maestro, elke slice)

```bash
docker run --rm -v "$PWD:/app" -w /app python:3.12-slim sh -c '
  pip install -q pip-audit &&
  pip-audit -r backend/api/requirements.txt -r backend/agent/requirements.txt
'
```

Verwacht: `No known vulnerabilities found`.

---

## Dev (Local Builder) — harde regels

| Regel | Reden |
|-------|--------|
| **Geen nieuwe packages** zonder `ALLOW` in slice-spec | Scope + supply chain |
| **Pins uit dit document** — geen eigen versies kiezen | Reproduceerbaar + audit |
| **Tests = unit tests alleen** in `test/` | Geen e2e, geen integration zonder slice |
| **Max tests per slice** zoals in slice-spec (meestal 1–3 files) | KISS |
| **Geen `requirements*.txt` wijzigen** tenzij slice expliciet `MODIFY` + verwijst hierheen | Maestro checkt audit |

Maestro past pins aan **vóór** of **tijdens** review — niet de Dev.

---

## Builder script (`scripts/requirements.txt`)

| Package | Pin |
|---------|-----|
| `openai` | `>=1.40.0` | host-only, niet in containers |

---

## Slice 001 — database (`api` only)

| Package | Pin | Opmerking |
|---------|-----|-----------|
| `sqlalchemy` | `==2.0.40` | ORM + Core |
| `alembic` | `==1.15.2` | migrations |
| `psycopg2-binary` | `==2.9.10` | Postgres driver (sync) |

### `backend/api/requirements.txt` (na slice 001)

```
fastapi==0.136.3
uvicorn[standard]==0.34.0
pydantic==2.11.5
python-dotenv>=1.2.2
sqlalchemy==2.0.40
alembic==1.15.2
psycopg2-binary==2.9.10
```

`backend/agent/requirements.txt` — **ongewijzigd** in slice 001.

---

## Slice 002 — diagram upload (`api` only)

| Package | Pin | Opmerking |
|---------|-----|-----------|
| `python-multipart` | `==0.0.20` | FastAPI `UploadFile` |

Toevoegen aan `backend/api/requirements.txt` (rest ongewijzigd t.o.v. slice 001).

---

## Slice 004b1 — agent LLM + diagram loader

| Package | Pin | Opmerking |
|---------|-----|-----------|
| `langchain-openai` | `==1.1.7` | ChatOpenAI → oMLX |
| `langchain-core` | `==1.2.6` | messages (langchain-openai 1.1.7) |
| `sqlalchemy` | `==2.0.40` | job_status update (004b2) |
| `psycopg2-binary` | `==2.9.10` | Postgres |

### `backend/agent/requirements.txt` (na slice 004b1)

```
fastapi==0.136.3
uvicorn[standard]==0.34.0
pydantic==2.11.5
httpx==0.28.1
python-dotenv>=1.2.2
langchain-openai==1.1.7
langchain-core==1.2.6
sqlalchemy==2.0.40
psycopg2-binary==2.9.10
```

## Slice 008 — API job flow + LangGraph

| Package | Pin | Opmerking |
|---------|-----|-----------|
| `httpx` | `==0.28.1` | api → tm-agent invoke |
| `langgraph` | `==1.0.10` | tm-agent pipeline |
| `langgraph-prebuilt` | `==1.0.8` | ToolNode-ready (threats later) |

### `backend/api/requirements.txt` (na slice 008)

```
fastapi==0.136.3
uvicorn[standard]==0.34.0
pydantic==2.11.5
python-dotenv>=1.2.2
sqlalchemy==2.0.40
alembic==1.15.2
psycopg2-binary==2.9.10
python-multipart==0.0.20
httpx==0.28.1
```

### `backend/agent/requirements.txt` (na slice 008)

```
fastapi==0.136.3
uvicorn[standard]==0.34.0
pydantic==2.11.5
httpx==0.28.1
python-dotenv>=1.2.2
langchain-openai==1.1.7
langchain-core==1.2.6
langgraph==1.0.10
langgraph-prebuilt==1.0.8
sqlalchemy==2.0.40
psycopg2-binary==2.9.10
```

---

## Toekomstige slices

Nieuwe deps (LangGraph, WeasyPrint, …) komen **eerst** in dit document met audit, dan pas in slice-spec `ALLOW`.
