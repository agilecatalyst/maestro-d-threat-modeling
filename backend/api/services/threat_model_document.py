"""Build canonical threat model document for export."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional

from models import JobStatus, ThreatModel

SCHEMA_VERSION = "1.0"


def parse_detail(raw: Optional[str]) -> dict:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {"raw": raw}
    except json.JSONDecodeError:
        return {"raw": raw}


def build_threat_model_document(tm: ThreatModel, job: JobStatus) -> dict:
    detail = parse_detail(job.detail)
    return {
        "schema_version": SCHEMA_VERSION,
        "id": str(tm.id),
        "owner": tm.owner,
        "title": tm.title,
        "diagram_path": tm.diagram_path,
        "application_type": tm.application_type,
        "state": job.state,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
        "created_at": tm.created_at.isoformat() if tm.created_at else None,
        "summary": detail.get("summary"),
        "assets": detail.get("assets", []),
        "flows": detail.get("flows", {}),
        "threats": detail.get("threats", []),
        "meta": detail.get("meta", {}),
        "error": detail.get("error"),
    }
