"""Extract payload between [TOOL_REQUEST] and [END_TOOL_REQUEST]."""

from __future__ import annotations

from typing import Optional

MARKER_START = "[TOOL_REQUEST]"
MARKER_END = "[END_TOOL_REQUEST]"


def extract_inner_payload(text: str) -> Optional[str]:
    if not text or not isinstance(text, str):
        return None
    start = text.find(MARKER_START)
    if start < 0:
        return None
    after_start = text[start + len(MARKER_START) :]
    end = after_start.find(MARKER_END)
    if end < 0:
        return None
    return after_start[:end].strip()


def normalize_text_for_structured_fallback(text: str) -> str:
    inner = extract_inner_payload(text)
    if inner is not None:
        return inner
    return text
