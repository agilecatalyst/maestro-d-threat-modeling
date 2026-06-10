"""Persist security-relevant threat catalog changes."""

from __future__ import annotations

import uuid
from typing import Any, Optional

from sqlalchemy.orm import Session

from models import AuditLog

ACTION_BY_OP = {
    "add": "threat_add",
    "update": "threat_update",
    "delete": "threat_delete",
    "replace": "threat_replace",
}


def record_audit(
    db: Session,
    *,
    threat_model_id: uuid.UUID,
    action: str,
    detail: Optional[dict[str, Any]] = None,
    source_ip: Optional[str] = None,
) -> None:
    row = AuditLog(
        threat_model_id=threat_model_id,
        action=action,
        detail=detail or {},
        source_ip=source_ip,
    )
    db.add(row)
    db.commit()


def audit_mutation(
    db: Session,
    *,
    threat_model_id: uuid.UUID,
    op: str,
    threats: list[dict],
    source_ip: Optional[str],
) -> None:
    action = ACTION_BY_OP.get(op, f"threat_{op}")
    names = [row.get("name") for row in threats if row.get("name")]
    record_audit(
        db,
        threat_model_id=threat_model_id,
        action=action,
        detail={"op": op, "threat_names": names, "count": len(threats)},
        source_ip=source_ip,
    )
