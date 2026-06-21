from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from database import LOCAL_USER, get_db
from schemas import RestoreRequest
from services.backup_service import build_backup, restore_backup

router = APIRouter(prefix="/admin", tags=["admin"])
MAX_RESTORE_BODY_BYTES = 32 * 1024 * 1024


@router.get("/backup")
def export_backup(db: Session = Depends(get_db)):
    payload = build_backup(db, owner=LOCAL_USER)
    return JSONResponse(
        content=payload,
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="maestro-d-backup.json"'},
    )


@router.post("/restore")
async def import_backup(request: Request, db: Session = Depends(get_db)):
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            if int(content_length) > MAX_RESTORE_BODY_BYTES:
                raise HTTPException(status_code=413, detail="Restore payload too large")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid Content-Length") from exc

    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON body") from exc

    try:
        body = RestoreRequest.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc

    result = restore_backup(db, body.backup, body.mode, owner=LOCAL_USER)
    return result
