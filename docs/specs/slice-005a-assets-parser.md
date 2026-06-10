# Slice 005a — AssetsList parsers (port)

**Status:** VERIFIED  
**Depends on:** slice 004c  
**Next:** [slice-005b-assets-worker.md](slice-005b-assets-worker.md)

Port from owasped — Maestro (reference), geen Bob (regex).

## Files

- `assets_schema.py` — Pydantic Assets, AssetsList
- `structured_tool_json.py`, `asset_text_blocks.py`, `asset_text_parser.py`
- `test/test_assets_parser.py`

## DoD

```bash
pytest test/test_assets_parser.py -q
```
