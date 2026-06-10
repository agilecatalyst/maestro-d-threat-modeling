"""Extract threat payloads from plain-text / tool-call LLM output."""

from __future__ import annotations

import json
import re
from typing import Any, List, Optional

from structured_tool_json import try_parse_json_object


def strip_thinking_markers(text: str) -> str:
    text = re.sub(
        r"<think>.*?</think>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    return text


def _extract_tool_call_parameter(text: str, function_name: str, param_name: str) -> Optional[str]:
    fn_pattern = re.compile(
        rf"<function\s*=\s*{re.escape(function_name)}\s*>(.*?)</function>",
        re.IGNORECASE | re.DOTALL,
    )
    match = fn_pattern.search(text)
    if not match:
        return None
    inner = match.group(1)
    param_pattern = re.compile(
        rf"<parameter\s*=\s*{re.escape(param_name)}\s*>(.*?)</parameter>",
        re.IGNORECASE | re.DOTALL,
    )
    param_match = param_pattern.search(inner)
    if not param_match:
        return None
    return param_match.group(1).strip()


def _parse_json_array(raw: str) -> Optional[List[Any]]:
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        pass
    try:
        parsed = json.loads(raw.strip())
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        pass
    bracket_start = raw.find("[")
    if bracket_start >= 0:
        depth = 0
        in_str = False
        esc = False
        for index in range(bracket_start, len(raw)):
            char = raw[index]
            if in_str:
                if esc:
                    esc = False
                elif char == "\\":
                    esc = True
                elif char == '"':
                    in_str = False
                continue
            if char == '"':
                in_str = True
                continue
            if char == "[":
                depth += 1
            elif char == "]":
                depth -= 1
                if depth == 0:
                    try:
                        parsed = json.loads(raw[bracket_start : index + 1])
                        if isinstance(parsed, list):
                            return parsed
                    except json.JSONDecodeError:
                        return None
    return None


def extract_threat_dicts_from_text(text: str) -> Optional[List[dict]]:
    if not text or not text.strip():
        return None

    cleaned = strip_thinking_markers(text)
    param_raw = _extract_tool_call_parameter(cleaned, "add_threats", "threats")
    if param_raw:
        rows = _parse_json_array(param_raw)
        if rows and all(isinstance(row, dict) for row in rows):
            return rows

    parsed = try_parse_json_object(cleaned)
    if parsed and isinstance(parsed.get("threats"), list):
        return [row for row in parsed["threats"] if isinstance(row, dict)]

    rows = _parse_json_array(cleaned)
    if rows and all(isinstance(row, dict) for row in rows):
        if "name" in rows[0] and "stride_category" in rows[0]:
            return rows

    return None
