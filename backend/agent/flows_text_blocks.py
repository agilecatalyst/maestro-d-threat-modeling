"""Extract FlowsList-shaped dicts from plain-text LLM output."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

_DATA_FLOW_IGNORE = frozenset({"assets"})
_TRUST_IGNORE = frozenset({"boundary_type", "security_controls"})


def strip_thinking_markers(text: str) -> str:
    return re.sub(
        r"<think>.*?</think>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )


def _parse_tagged_blocks(tag: str, text: str) -> List[str]:
    pattern = re.compile(
        rf"<{re.escape(tag)}\s*>\s*(.*?)\s*</{re.escape(tag)}\s*>",
        re.IGNORECASE | re.DOTALL,
    )
    return [match.group(1).strip() for match in pattern.finditer(text)]


def _parse_kv_block(block: str, *, ignore: frozenset) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for line in block.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, val = line.split(":", 1)
        key = key.strip().lower()
        val = val.strip()
        if key in ignore:
            continue
        out[key] = val
    return out


def _parse_threat_actor_table(text: str) -> List[Dict[str, str]]:
    lines = text.splitlines()
    start: Optional[int] = None
    for index, line in enumerate(lines):
        low = line.lower()
        if "|" in line and "category" in low and "description" in low and "example" in low:
            start = index + 1
            break
    if start is None:
        return []
    while start < len(lines) and not lines[start].strip():
        start += 1
    if start < len(lines):
        sep = lines[start].strip()
        if sep and set(sep.replace("|", "").replace(" ", "")) <= {"-", ":"}:
            start += 1
    rows: List[Dict[str, str]] = []
    for line in lines[start:]:
        line = line.strip()
        if not line:
            continue
        if not line.startswith("|"):
            break
        if set(line.replace("|", "").replace(" ", "")) <= {"-", ":"}:
            continue
        inner = [part.strip() for part in line.split("|") if part.strip()]
        if len(inner) < 3:
            continue
        rows.append(
            {"category": inner[0], "description": inner[1], "example": inner[2]}
        )
    return rows


def extract_flows_dict_from_text(text: str) -> Optional[Dict[str, Any]]:
    if not text or not text.strip():
        return None

    cleaned = strip_thinking_markers(text)
    data_flows: List[Dict[str, str]] = []
    for inner in _parse_tagged_blocks("data_flow", cleaned):
        kv = _parse_kv_block(inner, ignore=_DATA_FLOW_IGNORE)
        required = ("flow_description", "source_entity", "target_entity")
        if all(key in kv for key in required):
            data_flows.append({key: kv[key] for key in required})

    trust_boundaries: List[Dict[str, str]] = []
    for inner in _parse_tagged_blocks("trust_boundary", cleaned):
        kv = _parse_kv_block(inner, ignore=_TRUST_IGNORE)
        required = ("purpose", "source_entity", "target_entity")
        if all(key in kv for key in required):
            trust_boundaries.append({key: kv[key] for key in required})

    threat_sources = _parse_threat_actor_table(cleaned)
    if not data_flows and not trust_boundaries and not threat_sources:
        return None

    return {
        "data_flows": data_flows,
        "trust_boundaries": trust_boundaries,
        "threat_sources": threat_sources,
    }
