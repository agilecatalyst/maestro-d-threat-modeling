import logging
import os
from typing import List, Optional

from langchain_core.messages import HumanMessage

from llm import get_chat_model
from threat_catalog import ThreatCatalog
from threat_tools import add_threats, gap_analysis
from threats_schema import STRIDE_VALUES, Threat, ThreatsList
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


def _build_context_prompt(
    summary: str,
    assets: list,
    flows: dict,
    *,
    existing_count: int,
    gap_findings: Optional[List[str]] = None,
) -> str:
    asset_lines = "\n".join(
        f"- {item.get('name', '?')} ({item.get('criticality', 'Medium')})"
        for item in assets
    )
    flow_lines = "\n".join(
        f"- {row.get('flow_description', '?')}"
        for row in flows.get("data_flows", [])[:5]
    )
    source_lines = "\n".join(
        f"- {row.get('category', '?')}"
        for row in flows.get("threat_sources", [])[:6]
    )
    stride_line = ", ".join(STRIDE_VALUES)

    prompt = (
        "You are a security architect. Produce STRIDE threats for threat modeling.\n\n"
        f"Summary:\n{summary}\n\n"
        f"Assets:\n{asset_lines or '- unknown'}\n\n"
        f"Data flows:\n{flow_lines or '- unknown'}\n\n"
        f"Threat actor categories:\n{source_lines or '- External threat actor'}\n\n"
        f"Catalog size so far: {existing_count}\n"
        "Return 5-10 new threats as JSON array or tool call add_threats.\n"
        "Each threat needs: name, stride_category, description, target, source, "
        "likelihood, impact, mitigations (list), prerequisites (list), vector.\n"
        f"stride_category must be one of: {stride_line}.\n"
        "Description grammar: [source] [prerequisites] can [action] which leads to "
        "[impact], negatively impacting [target].\n"
    )
    if gap_findings:
        prompt += "\nFix these catalog gaps:\n"
        for finding in gap_findings:
            prompt += f"- {finding}\n"
    return prompt


def run_threats_agent(
    summary: str,
    assets: list,
    flows: dict,
) -> ThreatCatalog:
    catalog = ThreatCatalog()
    asset_names = [item.get("name", "") for item in assets if item.get("name")]
    max_iterations = int(os.getenv("THREAT_AGENT_MAX_ITERATIONS", "3"))
    gap_findings: Optional[List[str]] = None

    for iteration in range(max_iterations):
        try:
            prompt = _build_context_prompt(
                summary,
                assets,
                flows,
                existing_count=catalog.count(),
                gap_findings=gap_findings,
            )
            response = get_chat_model().invoke([HumanMessage(content=prompt)])
            parsed = parse_threats_list_from_text(_response_text(response.content))
            if parsed:
                add_threats(catalog, parsed)
        except Exception as exc:
            logger.warning("Threats LLM iteration %s failed: %s", iteration + 1, exc)

        gap = gap_analysis(catalog, asset_names=asset_names)
        if gap.stop:
            break
        gap_findings = gap.findings

    return catalog
