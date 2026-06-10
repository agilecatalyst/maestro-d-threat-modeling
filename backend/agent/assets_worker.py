import json
import logging
from typing import Optional

from langchain_core.messages import HumanMessage
from sqlalchemy import text

from asset_text_parser import parse_assets_list_from_text
from assets_schema import Assets, AssetsList
from db import SessionLocal, merge_job_detail
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


def run_assets(
    job_id: str,
    description: Optional[str] = None,
    application_type: Optional[str] = None,
):
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

    assets_list = None
    try:
        prompt = (
            f"List system assets and entities for threat modeling.\n\n"
            f"Summary:\n{summary_text}\n\n"
            f"Application type: {application_type or 'Web App'}\n\n"
            "Format each item as:\n"
            "Type: Asset\nName: ...\nDescription: ...\nCriticality: High\n"
        )
        response = get_chat_model().invoke([HumanMessage(content=prompt)])
        assets_list = parse_assets_list_from_text(_response_text(response.content))
    except Exception as exc:
        logger.warning("Assets LLM failed for %s, using fallback: %s", job_id, exc)

    if not assets_list:
        assets_list = AssetsList(
            assets=[
                Assets(
                    type="Asset",
                    name="System Overview",
                    description=(summary_text or description or "Unknown")[:300],
                    criticality="Medium",
                )
            ]
        )

    merge_job_detail(
        job_id,
        "ASSETS_DONE",
        assets=[asset.model_dump() for asset in assets_list.assets],
    )
