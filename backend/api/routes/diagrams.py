from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import get_db, LOCAL_USER
from models import ThreatModel, JobStatus
from middleware.rate_limit import rate_limit_dependency
from storage import resolve_diagram_path, save_diagram
from upload_validation import detect_image_extension
import uuid

router = APIRouter(prefix="/threat-designer/diagrams", tags=["diagrams"])


@router.post("/", dependencies=[Depends(rate_limit_dependency("upload"))])
async def upload_diagram(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.content_type not in ["image/png", "image/jpeg"]:
        raise HTTPException(status_code=400, detail="Invalid file type")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large")

    extension = detect_image_extension(content)
    if not extension:
        raise HTTPException(status_code=400, detail="Invalid image content (PNG or JPEG required)")

    if file.content_type not in ["image/png", "image/jpeg"]:
        raise HTTPException(status_code=400, detail="Invalid file type")

    relative_path = save_diagram(content, extension)

    new_id = uuid.uuid4()
    tm = ThreatModel(
        id=new_id,
        diagram_path=relative_path,
        owner=LOCAL_USER,
    )
    db.add(tm)
    db.flush()

    job = JobStatus(id=new_id, state="PENDING")
    db.add(job)
    db.commit()

    return {
        "id": str(new_id),
        "diagram_path": relative_path,
        "owner": LOCAL_USER,
        "state": "PENDING",
    }


@router.get("/{diagram_id}/file")
def get_diagram_file(diagram_id: uuid.UUID, db: Session = Depends(get_db)):
    tm = db.query(ThreatModel).filter(ThreatModel.id == diagram_id, ThreatModel.owner == LOCAL_USER).first()
    if not tm or not tm.diagram_path:
        raise HTTPException(status_code=404, detail="Diagram not found")

    try:
        file_path = resolve_diagram_path(tm.diagram_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid diagram path") from exc

    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Diagram file missing on disk")

    suffix = file_path.suffix.lower()
    media_type = "image/png" if suffix == ".png" else "image/jpeg"
    return FileResponse(file_path, media_type=media_type)


@router.get("/{diagram_id}")
def get_diagram(diagram_id: uuid.UUID, db: Session = Depends(get_db)):
    tm = db.query(ThreatModel).filter(ThreatModel.id == diagram_id).first()
    if not tm:
        raise HTTPException(status_code=404, detail="Diagram not found")

    job = db.query(JobStatus).filter(JobStatus.id == diagram_id).first()
    return {
        "id": str(tm.id),
        "owner": tm.owner,
        "diagram_path": tm.diagram_path,
        "state": job.state if job else "PENDING",
        "title": tm.title,
    }
