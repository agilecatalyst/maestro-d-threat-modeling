from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db, LOCAL_USER
from models import ThreatModel, JobStatus
from storage import save_diagram
import uuid

router = APIRouter(prefix="/threat-designer/diagrams", tags=["diagrams"])


@router.post("/")
async def upload_diagram(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.content_type not in ["image/png", "image/jpeg"]:
        raise HTTPException(status_code=400, detail="Invalid file type")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large")

    extension = file.filename.split(".")[-1]
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
