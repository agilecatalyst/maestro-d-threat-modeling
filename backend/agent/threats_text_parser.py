"""Build ThreatsList from JSON or plain-text LLM output."""

from __future__ import annotations

from typing import Any, List, Optional

from pydantic import ValidationError

from structured_tool_json import tool_arguments_if_name, try_parse_json_object
from threats_schema import Threat, ThreatsList
from threats_text_blocks import extract_threat_dicts_from_text
from tool_request_markers import normalize_text_for_structured_fallback


def _coerce_prerequisites(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _coerce_mitigations(value: Any) -> List[str]:
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
        return items or ["Apply defense in depth controls"]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return ["Apply defense in depth controls"]


def _normalize_threat_row(row: dict) -> dict:
    normalized = dict(row)
    normalized["prerequisites"] = _coerce_prerequisites(row.get("prerequisites"))
    normalized["mitigations"] = _coerce_mitigations(row.get("mitigations"))
    normalized.pop("starred", None)
    normalized.pop("notes", None)
    return normalized


def _threats_from_rows(rows: List[dict]) -> Optional[ThreatsList]:
    threats: List[Threat] = []
    for row in rows:
        try:
            threats.append(Threat(**_normalize_threat_row(row)))
        except ValidationError:
            continue
    if not threats:
        return None
    return ThreatsList(threats=threats)


def _unwrap_threats_payload(data: dict) -> Optional[List[dict]]:
    threats = data.get("threats")
    if isinstance(threats, list):
        return [row for row in threats if isinstance(row, dict)]
    if isinstance(threats, dict):
        inner = threats.get("threats")
        if isinstance(inner, list):
            return [row for row in inner if isinstance(row, dict)]
    return None


def parse_threats_list_from_text(text: str) -> Optional[ThreatsList]:
    if not text or not str(text).strip():
        return None

    normalized = normalize_text_for_structured_fallback(str(text))
    parsed = try_parse_json_object(normalized)
    if parsed:
        for tool_name in ("ThreatsList", "add_threats"):
            args = tool_arguments_if_name(parsed, tool_name)
            if args is not None:
                rows = _unwrap_threats_payload(args)
                if rows:
                    result = _threats_from_rows(rows)
                    if result:
                        return result
        rows = _unwrap_threats_payload(parsed)
        if rows:
            result = _threats_from_rows(rows)
            if result:
                return result

    raw_rows = extract_threat_dicts_from_text(normalized)
    if raw_rows:
        return _threats_from_rows(raw_rows)

    return None
