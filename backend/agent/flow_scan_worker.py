"""Single LLM call to discover threats for a specific data flow."""

from __future__ import annotations

import logging
from typing import List, Optional

from langchain_core.messages import HumanMessage

from llm import get_chat_model
from threats_schema import STRIDE_VALUES
from threats_text_parser import parse_threats_list_from_text

logger = logging.getLogger(__name__)


def _response_text(content) -> str:
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            else:
                parts.append(str(block))
        return "\n".join(parts)
    return str(content)


def scan_flow_threats(
    summary: str,
    assets: list,
    flow: dict,
    threat_sources: Optional[list] = None,
) -> List[dict]:
    asset_lines = "\n".join(
        f"- {item.get('name', '?')} ({item.get('criticality', 'Medium')})"
        for item in assets
    )
    source_lines = "\n".join(
        f"- {row.get('category', '?')}"
        for row in (threat_sources or [])[:6]
    )
    stride_line = ", ".join(STRIDE_VALUES)
    source = flow.get("source_entity", "?")
    target = flow.get("target_entity", "?")
    description = flow.get("flow_description", "?")

    prompt = (
        "You are a security architect. Identify 3-5 STRIDE threats specific to this data flow.\n\n"
        f"Architecture summary:\n{summary}\n\n"
        f"Assets:\n{asset_lines or '- unknown'}\n\n"
        f"Data flow:\n- {source} → {target}: {description}\n\n"
        f"Threat actor categories:\n{source_lines or '- External threat actor'}\n\n"
        "Return a JSON array of threats. Each threat needs: name, stride_category, "
        "description, target, source, likelihood, impact, mitigations (list), "
        "prerequisites (list), vector.\n"
        f"stride_category must be one of: {stride_line}.\n"
        "Description grammar: [source] [prerequisites] can [action] which leads to "
        "[impact], negatively impacting [target].\n"
        "Focus only on threats relevant to this specific flow.\n"
    )

    try:
        response = get_chat_model().invoke([HumanMessage(content=prompt)])
        parsed = parse_threats_list_from_text(_response_text(response.content))
        if parsed:
            return [threat.model_dump() for threat in parsed.threats]
    except Exception as exc:
        logger.warning("Flow scan LLM failed: %s", exc)

    return []
