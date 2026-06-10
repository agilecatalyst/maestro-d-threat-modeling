import json
import logging
from typing import Optional

from langchain_core.messages import HumanMessage
from sqlalchemy import text

from db import SessionLocal, merge_job_detail
from flows_schema import DataFlow, FlowsList, ThreatSource, TrustBoundary
from flows_text_parser import parse_flows_list_from_text
from llm import get_chat_model

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


def _fallback_flows(summary: str, assets: list) -> FlowsList:
    names = [item.get("name", "Component") for item in assets[:2]] or ["Client", "API"]
    source, target = names[0], names[-1] if len(names) > 1 else "Backend"
    return FlowsList(
        data_flows=[
            DataFlow(
                flow_description=f"Data exchange: {summary[:120]}",
                source_entity=source,
                target_entity=target,
            )
        ],
        trust_boundaries=[
            TrustBoundary(
                purpose="Network trust boundary between user zone and application",
                source_entity=source,
                target_entity=target,
            )
        ],
        threat_sources=[
            ThreatSource(
                category="External threat actor",
                description="Internet-facing entry points",
                example="Opportunistic attacker",
            )
        ],
    )


def run_flows(job_id: str, description: Optional[str] = None):
    db = SessionLocal()
    try:
        row = db.execute(
            text("SELECT detail FROM job_status WHERE id = :id"),
            {"id": str(job_id)},
        ).fetchone()
        detail = json.loads(row[0]) if row and row[0] else {}
    finally:
        db.close()

    summary_text = detail.get("summary", description or "")
    assets = detail.get("assets", [])
    asset_names = ", ".join(item.get("name", "?") for item in assets) or "unknown"

    flows_list = None
    try:
        prompt = (
            "Identify data flows, trust boundaries, and threat actors.\n\n"
            f"Summary:\n{summary_text}\n\n"
            f"Known assets: {asset_names}\n\n"
            "Use blocks like:\n"
            "<data_flow>\nflow_description: ...\nsource_entity: ...\n"
            "target_entity: ...\n</data_flow>\n"
            "<trust_boundary>\npurpose: ...\nsource_entity: ...\n"
            "target_entity: ...\n</trust_boundary>\n"
            "## Threat Actors\n| Category | Description | Examples |\n"
        )
        response = get_chat_model().invoke([HumanMessage(content=prompt)])
        flows_list = parse_flows_list_from_text(_response_text(response.content))
    except Exception as exc:
        logger.warning("Flows LLM failed for %s: %s", job_id, exc)

    if not flows_list:
        flows_list = _fallback_flows(summary_text, assets)

    merge_job_detail(
        job_id,
        "FLOWS_DONE",
        flows={
            "data_flows": [f.model_dump() for f in flows_list.data_flows],
            "trust_boundaries": [b.model_dump() for b in flows_list.trust_boundaries],
            "threat_sources": [t.model_dump() for t in flows_list.threat_sources],
        },
    )
