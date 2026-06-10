"""Parse tool-style JSON from plain LLM text (Gemma / local models)."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional


def repair_json_llm_typos(s: str) -> str:
    return s.replace('"、name"', '"name"')


def extract_first_balanced_json_object(text: str) -> Optional[str]:
    if not text:
        return None
    i = text.find("{")
    if i < 0:
        return None
    depth = 0
    in_str = False
    esc = False
    for j in range(i, len(text)):
        c = text[j]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[i : j + 1]
    return None


def _strip_markdown_fence(text: str) -> str:
    t = text.strip()
    if not t.startswith("```"):
        return t
    lines = t.split("\n")
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def try_parse_json_object(text: str) -> Optional[Dict[str, Any]]:
    if not text or not str(text).strip():
        return None
    t = repair_json_llm_typos(_strip_markdown_fence(str(text).strip()))
    try:
        out = json.loads(t)
        if isinstance(out, dict):
            return out
    except json.JSONDecodeError:
        pass
    inner = extract_first_balanced_json_object(t)
    if inner is None:
        return None
    inner = repair_json_llm_typos(inner)
    try:
        out = json.loads(inner)
        if isinstance(out, dict):
            return out
    except json.JSONDecodeError:
        pass
    return None


def tool_arguments_if_name(
    data: Dict[str, Any], expected_name: str
) -> Optional[Dict[str, Any]]:
    if data.get("name") != expected_name:
        return None
    args = data.get("arguments")
    return args if isinstance(args, dict) else None
