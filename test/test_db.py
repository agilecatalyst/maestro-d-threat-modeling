import uuid

import pytest
from sqlalchemy import inspect, text

from database import LOCAL_USER, SessionLocal, engine, run_migrations
from models import JobStatus, ThreatModel


@pytest.fixture(scope="module", autouse=True)
def apply_migrations():
    run_migrations()
    yield


def test_tables_exist():
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    assert "threat_models" in tables
    assert "job_status" in tables


def test_threat_model_and_job_status_roundtrip():
    db = SessionLocal()
    try:
        tm_id = uuid.uuid4()
        db.add(
            ThreatModel(
                id=tm_id,
                owner=LOCAL_USER,
                title="Test Model",
                application_type="Web App",
            )
        )
        db.flush()
        db.add(JobStatus(id=tm_id, state="PENDING", retry_count=0))
        db.commit()

        tm = db.query(ThreatModel).filter(ThreatModel.id == tm_id).first()
        job = db.query(JobStatus).filter(JobStatus.id == tm_id).first()
        assert tm is not None
        assert tm.owner == LOCAL_USER
        assert job is not None
        assert job.state == "PENDING"
    finally:
        db.close()
        cleanup = SessionLocal()
        try:
            cleanup.execute(text("DELETE FROM job_status WHERE id = :id"), {"id": str(tm_id)})
            cleanup.execute(text("DELETE FROM threat_models WHERE id = :id"), {"id": str(tm_id)})
            cleanup.commit()
        finally:
            cleanup.close()
