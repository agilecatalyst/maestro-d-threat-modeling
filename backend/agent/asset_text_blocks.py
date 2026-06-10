"""Extract asset rows from plain-text LLM output (Type/Name/Description/Criticality)."""

# Portions adapted from awslabs/threat-designer (Apache-2.0)
# https://github.com/awslabs/threat-designer

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


_ASSET_BLOCK_RE = re.compile(
    r"Type:\s*(Asset|Entity)\s*\n"
    r"\s*Name:\s*([^\n]+?)\s*\n"
    r"\s*Description:\s*((?:.|\n)+?)(?=\n\s*Criticality:\s*(?:Low|Medium|High)\b)"
    r"\s*\n\s*Criticality:\s*(Low|Medium|High)\b",
    re.IGNORECASE | re.MULTILINE,
)


def strip_thinking_markers(text: str) -> str:
    return re.sub(
        r"<think>.*?</think>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )


def extract_asset_dicts_from_text(text: str) -> Optional[List[Dict[str, Any]]]:
    if not text or not text.strip():
        return None

    cleaned = strip_thinking_markers(text)
    rows: List[Dict[str, Any]] = []

    for match in _ASSET_BLOCK_RE.finditer(cleaned):
        raw_type = match.group(1).strip().title()
        if raw_type not in ("Asset", "Entity"):
            continue
        crit = match.group(4).strip().title()
        if crit not in ("Low", "Medium", "High"):
            continue
        rows.append(
            {
                "type": raw_type,
                "name": match.group(2).strip(),
                "description": match.group(3).strip(),
                "criticality": crit,
            }
        )

    return rows if rows else None
