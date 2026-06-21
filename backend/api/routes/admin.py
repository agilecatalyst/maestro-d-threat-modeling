from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database import LOCAL_USER, get_db
from schemas import RestoreRequest
from services.backup_service import build_backup, restore_backup

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/backup")
def export_backup(db: Session = Depends(get_db)):
    payload = build_backup(db, owner=LOCAL_USER)
    return JSONResponse(
        content=payload,
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="maestro-d-backup.json"'},
    )


@router.post("/restore")
def import_backup(body: RestoreRequest, db: Session = Depends(get_db)):
    result = restore_backup(db, body.backup, body.mode, owner=LOCAL_USER)
    return result
