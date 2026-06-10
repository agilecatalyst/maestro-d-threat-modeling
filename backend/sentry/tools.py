import logging
import os
from typing import List

import httpx
from langchain_core.tools import tool

from models import ThreatRecord

logger = logging.getLogger(__name__)

THREAT_API_URL = os.getenv("THREAT_API_URL", "http://api:8000")


def _patch_threats(threat_model_id: str, op: str, threats: List[dict]) -> str:
    url = f"{THREAT_API_URL}/threat-designer/{threat_model_id}/threats"
    payload = {"op": op, "threats": threats}
    try:
        response = httpx.patch(url, json=payload, timeout=30.0)
        response.raise_for_status()
        data = response.json()
        count = len(data.get("threats") or [])
        return f"{op} succeeded; catalog now has {count} threats."
    except httpx.HTTPError as exc:
        logger.warning("Threat API %s failed: %s", op, exc)
        return f"Failed to {op} threats: {exc}"


def build_tools(threat_model_id: str):
    @tool
    def add_threats(threats: List[ThreatRecord]) -> str:
        """Add new threats to the threat catalog."""
        rows = [row.model_dump() for row in threats]
        return _patch_threats(threat_model_id, "add", rows)

    @tool
    def edit_threats(threats: List[ThreatRecord]) -> str:
        """Update existing threats matched by name."""
        rows = [row.model_dump() for row in threats]
        return _patch_threats(threat_model_id, "update", rows)

    @tool
    def delete_threats(threats: List[ThreatRecord]) -> str:
        """Delete threats from the catalog by name."""
        rows = [row.model_dump() for row in threats]
        return _patch_threats(threat_model_id, "delete", rows)

    return [add_threats, edit_threats, delete_threats]
