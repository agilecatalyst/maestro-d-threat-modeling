# Third-party notices

Maestro'D ThreatModeling is licensed under [Apache License 2.0](LICENSE).

## AWS Threat Designer (upstream)

| Field | Value |
|-------|--------|
| Project | [awslabs/threat-designer](https://github.com/awslabs/threat-designer) |
| Copyright | Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. |
| License | Apache License 2.0 |
| Relationship | Inspired by; portions adapted/reimplemented |

### Modules with adapted logic

The following files implement concepts and parsing patterns derived from the
upstream Threat Designer codebase (via the threat-designer-owasped reference fork).
They have been substantially rewritten for the local Postgres/FastAPI stack but
retain upstream lineage:

| File | Description |
|------|-------------|
| `backend/agent/structured_tool_json.py` | Balanced JSON extraction from LLM text |
| `backend/agent/tool_request_markers.py` | Tool-call marker normalization |
| `backend/agent/asset_text_parser.py` | Assets list parser |
| `backend/agent/asset_text_blocks.py` | Assets text block extraction |
| `backend/agent/flows_text_parser.py` | Flows list parser |
| `backend/agent/flows_text_blocks.py` | Flows text block extraction |
| `backend/agent/threats_text_parser.py` | Threats list parser |
| `backend/agent/threats_text_blocks.py` | Threats text block extraction |
| `backend/agent/threats_schema.py` | STRIDE threat Pydantic models |
| `backend/agent/assets_schema.py` | Asset Pydantic models |
| `backend/agent/flows_schema.py` | Data flow Pydantic models |

Greenfield components (no upstream code copy): FastAPI API layer, PostgreSQL
persistence, LangGraph orchestration, React frontend, Sentry chat service,
PDF export, Docker Compose stack.

## Reference fork (development only)

| Field | Value |
|-------|--------|
| Project | threat-designer-owasped (local reference) |
| License | Apache License 2.0 |
| Use | QA captures, pipeline documentation, design reference — not shipped as dependency |

## Open-source dependencies

Runtime dependencies are listed in:

- `backend/api/requirements.txt`
- `backend/agent/requirements.txt`
- `backend/sentry/requirements.txt`
- `frontend/package.json`

Most Python and JavaScript dependencies use permissive licenses (MIT, Apache-2.0,
BSD). Run `pip-audit` and `npm audit` periodically (see [SECURITY.md](SECURITY.md)).
