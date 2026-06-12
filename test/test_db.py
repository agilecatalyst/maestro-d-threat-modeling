import os
import uuid
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

from database import LOCAL_USER, SessionLocal, engine, run_migrations
from models import JobStatus, ThreatModel


def _alembic_config() -> Config:
    api_dir = Path(__file__).resolve().parent.parent / "backend" / "api"
    if not (api_dir / "alembic.ini").exists():
        api_dir = Path("/app")
    config = Config(str(api_dir / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", os.environ.get("DATABASE_URL", engine.url.render_as_string(hide_password=False)))
    return config


def _ensure_migrated() -> None:
    """Re-apply Alembic when other tests' drop_all removed tables but left the stamp."""
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if "threat_models" in tables:
        run_migrations()
        return
    config = _alembic_config()
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.execute(text("GRANT ALL ON SCHEMA public TO PUBLIC"))
    command.upgrade(config, "head")


@pytest.fixture(scope="module", autouse=True)
def apply_migrations():
    _ensure_migrated()
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
