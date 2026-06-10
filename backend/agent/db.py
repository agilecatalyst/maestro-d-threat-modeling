import json
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://maestro:maestro@postgres:5432/maestro_d")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _load_detail(raw) -> dict:
    if not raw:
        return {}
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}
    return dict(raw)


def update_job_summary(job_id, summary, state="SUMMARIZED"):
    db = SessionLocal()
    try:
        detail = (
            json.dumps({"error": summary})
            if state == "FAILED"
            else json.dumps({"summary": summary})
        )
        db.execute(
            text(
                "UPDATE job_status SET state = :state, detail = :detail, "
                "updated_at = NOW() WHERE id = :id"
            ),
            {"state": state, "detail": detail, "id": str(job_id)},
        )
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def merge_job_detail(job_id, state, **fields):
    db = SessionLocal()
    try:
        row = db.execute(
            text("SELECT detail FROM job_status WHERE id = :id"),
            {"id": str(job_id)},
        ).fetchone()
        detail = _load_detail(row[0] if row else None)
        detail.update(fields)
        db.execute(
            text(
                "UPDATE job_status SET state = :state, detail = :detail, "
                "updated_at = NOW() WHERE id = :id"
            ),
            {"state": state, "detail": json.dumps(detail), "id": str(job_id)},
        )
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()
