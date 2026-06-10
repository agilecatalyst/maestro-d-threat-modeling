"""LangGraph subgraph: generate → gap → loop for threats phase."""

from __future__ import annotations

import logging
import os
from typing import List, Literal, Optional, TypedDict

from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph

from llm import get_chat_model
from threat_catalog import ThreatCatalog
from threat_tools import add_threats, gap_analysis
from threats_schema import STRIDE_VALUES, Threat, ThreatsList
from threats_text_parser import parse_threats_list_from_text

logger = logging.getLogger(__name__)

MAX_ITERATIONS = int(os.getenv("THREAT_AGENT_MAX_ITERATIONS", "3"))


class ThreatsGraphState(TypedDict, total=False):
    summary: str
    assets: list
    flows: dict
    threats: List[dict]
    iteration: int
    should_stop: bool
    gap_findings: List[str]


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


def _catalog_from_state(state: ThreatsGraphState) -> ThreatCatalog:
    catalog = ThreatCatalog()
    rows = state.get("threats") or []
    if rows:
        try:
            catalog.add(ThreatsList(threats=[Threat(**row) for row in rows]))
        except Exception:
            pass
    return catalog


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


def generate_node(state: ThreatsGraphState) -> dict:
    catalog = _catalog_from_state(state)
    gap_findings = state.get("gap_findings") or None
    try:
        prompt = _build_context_prompt(
            state.get("summary", ""),
            state.get("assets", []),
            state.get("flows", {}),
            existing_count=catalog.count(),
            gap_findings=gap_findings,
        )
        response = get_chat_model().invoke([HumanMessage(content=prompt)])
        parsed = parse_threats_list_from_text(_response_text(response.content))
        if parsed:
            add_threats(catalog, parsed)
    except Exception as exc:
        logger.warning("Threats generate node failed: %s", exc)
    return {"threats": catalog.to_dicts()}


def gap_node(state: ThreatsGraphState) -> dict:
    catalog = _catalog_from_state(state)
    asset_names = [
        item.get("name", "") for item in state.get("assets", []) if item.get("name")
    ]
    gap = gap_analysis(catalog, asset_names=asset_names)
    iteration = int(state.get("iteration") or 0) + 1
    return {
        "should_stop": gap.stop,
        "gap_findings": gap.findings,
        "iteration": iteration,
        "threats": catalog.to_dicts(),
    }


def route_after_gap(state: ThreatsGraphState) -> Literal["generate", "__end__"]:
    if state.get("should_stop"):
        return "__end__"
    if int(state.get("iteration") or 0) >= MAX_ITERATIONS:
        return "__end__"
    return "generate"


_builder = StateGraph(ThreatsGraphState)
_builder.add_node("generate", generate_node)
_builder.add_node("gap", gap_node)
_builder.set_entry_point("generate")
_builder.add_edge("generate", "gap")
_builder.add_conditional_edges(
    "gap",
    route_after_gap,
    {"generate": "generate", "__end__": END},
)
threats_subgraph = _builder.compile()


def run_threats_subgraph(summary: str, assets: list, flows: dict) -> ThreatCatalog:
    result = threats_subgraph.invoke(
        {
            "summary": summary,
            "assets": assets,
            "flows": flows,
            "threats": [],
            "iteration": 0,
            "should_stop": False,
            "gap_findings": [],
        }
    )
    catalog = ThreatCatalog()
    rows = result.get("threats") or []
    if rows:
        try:
            catalog.add(ThreatsList(threats=[Threat(**row) for row in rows]))
        except Exception:
            pass
    return catalog
