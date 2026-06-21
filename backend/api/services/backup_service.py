"""Bulk JSON backup and restore for local threat model catalog."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from database import LOCAL_USER
from models import AuditLog, JobStatus, ThreatModel
from services.threat_model_document import SCHEMA_VERSION

BACKUP_FORMAT_VERSION = "1"


def _serialize_value(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _row_dict(row) -> dict[str, Any]:
    return {col.name: _serialize_value(getattr(row, col.name)) for col in row.__table__.columns}


def _parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    return datetime.fromisoformat(text)


def _parse_uuid(value: Any) -> UUID:
    return value if isinstance(value, UUID) else UUID(str(value))


def build_backup(db: Session, owner: str = LOCAL_USER) -> dict[str, Any]:
    threat_models = db.query(ThreatModel).filter(ThreatModel.owner == owner).order_by(ThreatModel.created_at).all()
    model_ids = [tm.id for tm in threat_models]
    jobs = (
        db.query(JobStatus).filter(JobStatus.id.in_(model_ids)).order_by(JobStatus.updated_at).all()
        if model_ids
        else []
    )
    audits = (
        db.query(AuditLog).filter(AuditLog.threat_model_id.in_(model_ids)).order_by(AuditLog.created_at).all()
        if model_ids
        else []
    )
    return {
        "backup_format_version": BACKUP_FORMAT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "owner": owner,
        "counts": {
            "threat_models": len(threat_models),
            "job_status": len(jobs),
            "audit_log": len(audits),
        },
        "threat_models": [_row_dict(row) for row in threat_models],
        "job_status": [_row_dict(row) for row in jobs],
        "audit_log": [_row_dict(row) for row in audits],
    }


def _validate_backup(backup: dict[str, Any]) -> None:
    if not isinstance(backup, dict):
        raise HTTPException(status_code=400, detail="Backup must be a JSON object")
    if backup.get("backup_format_version") != BACKUP_FORMAT_VERSION:
        raise HTTPException(status_code=400, detail="Unsupported backup_format_version")
    if backup.get("schema_version") != SCHEMA_VERSION:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported schema_version (expected {SCHEMA_VERSION})",
        )
    for key in ("threat_models", "job_status", "audit_log"):
        if key not in backup or not isinstance(backup[key], list):
            raise HTTPException(status_code=400, detail=f"Backup missing list field: {key}")


def _clear_owner_catalog(db: Session, owner: str) -> None:
    model_ids = [
        row[0]
        for row in db.query(ThreatModel.id).filter(ThreatModel.owner == owner).all()
    ]
    if model_ids:
        db.query(AuditLog).filter(AuditLog.threat_model_id.in_(model_ids)).delete(
            synchronize_session=False
        )
        db.query(JobStatus).filter(JobStatus.id.in_(model_ids)).delete(synchronize_session=False)
    db.query(ThreatModel).filter(ThreatModel.owner == owner).delete(synchronize_session=False)
    db.flush()


def _insert_threat_model(db: Session, row: dict[str, Any]) -> None:
    db.add(
        ThreatModel(
            id=_parse_uuid(row["id"]),
            owner=row["owner"],
            title=row.get("title"),
            diagram_path=row.get("diagram_path"),
            application_type=row.get("application_type"),
            created_at=_parse_datetime(row.get("created_at")),
            updated_at=_parse_datetime(row.get("updated_at")),
        )
    )


def _insert_job_status(db: Session, row: dict[str, Any]) -> None:
    db.add(
        JobStatus(
            id=_parse_uuid(row["id"]),
            state=row["state"],
            detail=row.get("detail"),
            retry_count=row.get("retry_count", 0),
            updated_at=_parse_datetime(row.get("updated_at")),
        )
    )


def _insert_audit_log(db: Session, row: dict[str, Any]) -> None:
    db.add(
        AuditLog(
            id=_parse_uuid(row["id"]),
            threat_model_id=_parse_uuid(row["threat_model_id"]),
            action=row["action"],
            detail=row.get("detail"),
            source_ip=row.get("source_ip"),
            created_at=_parse_datetime(row.get("created_at")),
        )
    )


def _upsert_threat_model(db: Session, row: dict[str, Any]) -> None:
    model_id = _parse_uuid(row["id"])
    existing = db.query(ThreatModel).filter(ThreatModel.id == model_id).first()
    if existing:
        existing.owner = row["owner"]
        existing.title = row.get("title")
        existing.diagram_path = row.get("diagram_path")
        existing.application_type = row.get("application_type")
        existing.created_at = _parse_datetime(row.get("created_at"))
        existing.updated_at = _parse_datetime(row.get("updated_at"))
    else:
        _insert_threat_model(db, row)


def _upsert_job_status(db: Session, row: dict[str, Any]) -> None:
    job_id = _parse_uuid(row["id"])
    existing = db.query(JobStatus).filter(JobStatus.id == job_id).first()
    if existing:
        existing.state = row["state"]
        existing.detail = row.get("detail")
        existing.retry_count = row.get("retry_count", 0)
        existing.updated_at = _parse_datetime(row.get("updated_at"))
    else:
        _insert_job_status(db, row)


def _upsert_audit_log(db: Session, row: dict[str, Any]) -> None:
    audit_id = _parse_uuid(row["id"])
    existing = db.query(AuditLog).filter(AuditLog.id == audit_id).first()
    if existing:
        existing.threat_model_id = _parse_uuid(row["threat_model_id"])
        existing.action = row["action"]
        existing.detail = row.get("detail")
        existing.source_ip = row.get("source_ip")
        existing.created_at = _parse_datetime(row.get("created_at"))
    else:
        _insert_audit_log(db, row)


def restore_backup(
    db: Session,
    backup: dict[str, Any],
    mode: Literal["replace", "merge"],
    owner: str = LOCAL_USER,
) -> dict[str, Any]:
    _validate_backup(backup)
    backup_owner = backup.get("owner", owner)
    if backup_owner != owner:
        raise HTTPException(status_code=400, detail="Backup owner does not match local catalog owner")

    for row in backup["threat_models"]:
        if row.get("owner") != owner:
            raise HTTPException(status_code=400, detail="Backup contains foreign owner rows")

    if mode == "replace":
        _clear_owner_catalog(db, owner)
        for row in backup["threat_models"]:
            _insert_threat_model(db, row)
        db.flush()
        for row in backup["job_status"]:
            _insert_job_status(db, row)
        db.flush()
        for row in backup["audit_log"]:
            _insert_audit_log(db, row)
    else:
        for row in backup["threat_models"]:
            _upsert_threat_model(db, row)
        db.flush()
        for row in backup["job_status"]:
            _upsert_job_status(db, row)
        db.flush()
        for row in backup["audit_log"]:
            _upsert_audit_log(db, row)

    db.commit()
    counts = build_backup(db, owner=owner)["counts"]
    return {"mode": mode, "restored": counts}
