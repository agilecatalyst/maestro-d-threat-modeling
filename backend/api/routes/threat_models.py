import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from pydantic import ValidationError
from sqlalchemy.orm import Session

from database import LOCAL_USER, get_db
from middleware.rate_limit import client_ip, rate_limit_dependency
from models import JobStatus, ThreatModel
from schemas import ScanFlowRequest, StartThreatModelRequest, ThreatItem, ThreatModelListItem, ThreatModelStatusResponse, ThreatMutationRequest
from services.agent_client import invoke_agent, scan_flow_agent
from services.audit_log import audit_mutation, record_audit
from services.export_service import render_json_export, render_pdf_export
from services.threat_model_document import build_threat_model_document, parse_detail
from services.threat_mutations import apply_mutation, rebuild_meta
from security import require_internal_key
from storage import delete_diagram

router = APIRouter(prefix="/threat-designer", tags=["threat-models"])

MUTABLE_STATES = {"COMPLETE", "THREATS_DONE"}
RESTARTABLE_STATES = {"PENDING", "FAILED", "COMPLETE", "THREATS_DONE"}
PIPELINE_BUSY_STATES = {"PROCESSING", "SUMMARIZED", "ASSETS_DONE", "FLOWS_DONE"}


def _threat_count_from_job(job: JobStatus | None) -> int | None:
    if not job or not job.detail:
        return None
    detail = parse_detail(job.detail)
    meta = detail.get("meta") or {}
    if isinstance(meta.get("threat_count"), int):
        return meta["threat_count"]
    threats = detail.get("threats")
    if isinstance(threats, list):
        return len(threats)
    return None


def _job_or_404(db: Session, job_id: UUID) -> JobStatus:
    job = db.query(JobStatus).filter(JobStatus.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Threat model not found")
    return job


def _tm_or_404(db: Session, job_id: UUID) -> ThreatModel:
    tm = (
        db.query(ThreatModel)
        .filter(ThreatModel.id == job_id, ThreatModel.owner == LOCAL_USER)
        .first()
    )
    if not tm:
        raise HTTPException(status_code=404, detail="Threat model not found")
    return tm


def _document_for(db: Session, job_id: UUID) -> dict:
    tm = _tm_or_404(db, job_id)
    job = _job_or_404(db, job_id)
    return build_threat_model_document(tm, job)


def _save_detail(db: Session, job: JobStatus, detail: dict, state: str = None) -> None:
    if state:
        job.state = state
    job.detail = json.dumps(detail)
    db.commit()


def _mutate_threats(db: Session, job_id: UUID, body: ThreatMutationRequest) -> dict:
    _tm_or_404(db, job_id)
    job = _job_or_404(db, job_id)
    if job.state not in MUTABLE_STATES:
        raise HTTPException(
            status_code=400,
            detail=f"Threat mutations require state COMPLETE or THREATS_DONE (got {job.state})",
        )

    detail = parse_detail(job.detail)
    existing = detail.get("threats", [])
    payload = [row.model_dump() for row in body.threats]
    updated = apply_mutation(existing, body.op, payload)
    detail["threats"] = updated
    detail["meta"] = rebuild_meta(updated)
    _save_detail(db, job, detail)
    return build_threat_model_document(_tm_or_404(db, job_id), job)


@router.post("", dependencies=[Depends(rate_limit_dependency("start_job"))])
def start_threat_model(body: StartThreatModelRequest, db: Session = Depends(get_db)):
    tm = _tm_or_404(db, body.id)
    job = _job_or_404(db, body.id)

    if job.state in PIPELINE_BUSY_STATES:
        raise HTTPException(status_code=409, detail=f"Pipeline already running (state {job.state})")
    if job.state not in RESTARTABLE_STATES:
        raise HTTPException(status_code=400, detail=f"Cannot restart pipeline from state {job.state}")

    if body.title:
        tm.title = body.title
    if body.application_type:
        tm.application_type = body.application_type

    detail = parse_detail(job.detail)
    if body.description:
        detail["input_description"] = body.description
    detail.pop("error", None)
    job.detail = json.dumps(detail)
    job.state = "PROCESSING"
    job.retry_count = (job.retry_count or 0) + 1
    db.commit()

    try:
        invoke_agent(
            str(tm.id),
            tm.diagram_path,
            body.description,
            body.application_type,
        )
    except RuntimeError as exc:
        job.state = "FAILED"
        fail_detail = parse_detail(job.detail)
        fail_detail["error"] = str(exc)
        job.detail = json.dumps(fail_detail)
        db.commit()
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return {"id": str(tm.id)}


@router.get("/status/{job_id}", response_model=ThreatModelStatusResponse)
def get_status(job_id: UUID, db: Session = Depends(get_db)):
    _tm_or_404(db, job_id)
    job = _job_or_404(db, job_id)
    return ThreatModelStatusResponse(
        id=str(job.id),
        state=job.state,
        detail=parse_detail(job.detail),
        updated_at=job.updated_at.isoformat() if job.updated_at else None,
        retry=job.retry_count or 0,
    )


@router.get("/all")
def list_threat_models(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(ThreatModel, JobStatus)
        .outerjoin(JobStatus, JobStatus.id == ThreatModel.id)
        .filter(ThreatModel.owner == LOCAL_USER)
        .order_by(ThreatModel.updated_at.desc())
        .limit(limit)
        .all()
    )
    items = []
    for tm, job in rows:
        detail = parse_detail(job.detail if job else None)
        items.append(
            ThreatModelListItem(
                id=str(tm.id),
                title=tm.title,
                state=job.state if job else "PENDING",
                diagram_path=tm.diagram_path,
                application_type=tm.application_type,
                updated_at=tm.updated_at.isoformat() if tm.updated_at else None,
                threat_count=_threat_count_from_job(job),
            ).model_dump()
        )
    return {"items": items, "count": len(items)}


@router.get("/{job_id}/export/json")
def export_threat_model_json(job_id: UUID, db: Session = Depends(get_db)):
    document = _document_for(db, job_id)
    body = render_json_export(document)
    filename = f"threat-model-{job_id}.json"
    return Response(
        content=body,
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{job_id}/export/pdf")
def export_threat_model_pdf(job_id: UUID, db: Session = Depends(get_db)):
    document = _document_for(db, job_id)
    if document.get("state") != "COMPLETE":
        raise HTTPException(
            status_code=400,
            detail="Threat model must be COMPLETE before PDF export",
        )
    try:
        pdf_bytes = render_pdf_export(document)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {exc}") from exc
    filename = f"threat-model-{job_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.patch("/{job_id}/threats", dependencies=[Depends(require_internal_key)])
def mutate_threats(
    job_id: UUID,
    body: ThreatMutationRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    document = _mutate_threats(db, job_id, body)
    audit_mutation(
        db,
        threat_model_id=job_id,
        op=body.op,
        threats=[row.model_dump() for row in body.threats],
        source_ip=client_ip(request),
    )
    return {
        "id": document["id"],
        "state": document["state"],
        "threats": document.get("threats", []),
        "meta": document.get("meta", {}),
    }


@router.post(
    "/{job_id}/threats/scan-flow",
    dependencies=[Depends(require_internal_key), Depends(rate_limit_dependency("scan_flow"))],
)
def scan_flow_threats(
    job_id: UUID,
    body: ScanFlowRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    _tm_or_404(db, job_id)
    job = _job_or_404(db, job_id)
    if job.state not in MUTABLE_STATES:
        raise HTTPException(
            status_code=400,
            detail=f"Flow scan requires state COMPLETE or THREATS_DONE (got {job.state})",
        )

    detail = parse_detail(job.detail)
    try:
        agent_result = scan_flow_agent(
            summary=detail.get("summary", ""),
            assets=detail.get("assets", []),
            flow={
                "source_entity": body.source_entity,
                "target_entity": body.target_entity,
                "flow_description": body.flow_description,
            },
            threat_sources=(detail.get("flows") or {}).get("threat_sources", []),
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    discovered = agent_result.get("threats") or []
    valid_rows = []
    for row in discovered:
        try:
            valid_rows.append(ThreatItem(**row).model_dump())
        except ValidationError:
            continue

    if not valid_rows:
        record_audit(
            db,
            threat_model_id=job_id,
            action="scan_flow",
            detail={
                "source_entity": body.source_entity,
                "target_entity": body.target_entity,
                "added": 0,
            },
            source_ip=client_ip(request),
        )
        return {
            "id": str(job_id),
            "added": 0,
            "threats": detail.get("threats", []),
            "meta": detail.get("meta", {}),
        }

    mutation = ThreatMutationRequest(op="add", threats=valid_rows)
    document = _mutate_threats(db, job_id, mutation)
    record_audit(
        db,
        threat_model_id=job_id,
        action="scan_flow",
        detail={
            "source_entity": body.source_entity,
            "target_entity": body.target_entity,
            "added": len(valid_rows),
        },
        source_ip=client_ip(request),
    )
    return {
        "id": document["id"],
        "added": len(valid_rows),
        "threats": document.get("threats", []),
        "meta": document.get("meta", {}),
    }


@router.delete("/{job_id}")
def delete_threat_model(job_id: UUID, db: Session = Depends(get_db)):
    tm = _tm_or_404(db, job_id)
    diagram_path = tm.diagram_path
    db.delete(tm)
    db.commit()
    delete_diagram(diagram_path)
    return {"id": str(job_id), "deleted": True}


@router.get("/{job_id}")
def get_threat_model(job_id: UUID, db: Session = Depends(get_db)):
    document = _document_for(db, job_id)
    detail = parse_detail(_job_or_404(db, job_id).detail)
    return {
        "id": document["id"],
        "owner": document["owner"],
        "title": document["title"],
        "diagram_path": document["diagram_path"],
        "application_type": document["application_type"],
        "state": document["state"],
        "updated_at": document["updated_at"],
        "input_description": detail.get("input_description"),
        "summary": document.get("summary"),
        "assets": document.get("assets", []),
        "flows": document.get("flows", {}),
        "threats": document.get("threats", []),
        "meta": document.get("meta", {}),
        "error": document.get("error"),
    }
