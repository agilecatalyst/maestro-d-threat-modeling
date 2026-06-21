import json
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

API_DIR = Path(__file__).resolve().parent.parent / "backend" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from database import Base, SessionLocal, engine, get_db
from main import app
from models import AuditLog, JobStatus, ThreatModel


@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        model_ids = [
            row[0] for row in session.query(ThreatModel.id).filter(ThreatModel.owner == "local-user").all()
        ]
        if model_ids:
            session.query(AuditLog).filter(AuditLog.threat_model_id.in_(model_ids)).delete(
                synchronize_session=False
            )
            session.query(JobStatus).filter(JobStatus.id.in_(model_ids)).delete(synchronize_session=False)
        session.query(ThreatModel).filter(ThreatModel.owner == "local-user").delete(synchronize_session=False)
        session.commit()
        session.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _seed_catalog(session):
    model_id = uuid4()
    tm = ThreatModel(id=model_id, owner="local-user", title="Backup test", diagram_path="diagrams/x.png")
    job = JobStatus(
        id=model_id,
        state="COMPLETE",
        detail=json.dumps({"summary": "stored", "threats": [{"name": "T1"}]}),
    )
    audit = AuditLog(
        threat_model_id=model_id,
        action="threat_add",
        detail={"op": "add", "threat_names": ["T1"]},
        source_ip="127.0.0.1",
    )
    session.add(tm)
    session.flush()
    session.add(job)
    session.add(audit)
    session.commit()
    return model_id


def test_backup_returns_catalog_rows(client, db_session):
    model_id = _seed_catalog(db_session)
    response = client.get("/admin/backup")
    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "1.0"
    assert payload["counts"]["threat_models"] == 1
    assert payload["threat_models"][0]["id"] == str(model_id)
    assert payload["job_status"][0]["state"] == "COMPLETE"
    assert payload["audit_log"][0]["action"] == "threat_add"


def _wipe_owner_catalog(session, owner: str = "local-user") -> None:
    model_ids = [
        row[0] for row in session.query(ThreatModel.id).filter(ThreatModel.owner == owner).all()
    ]
    if model_ids:
        session.query(AuditLog).filter(AuditLog.threat_model_id.in_(model_ids)).delete(
            synchronize_session=False
        )
        session.query(JobStatus).filter(JobStatus.id.in_(model_ids)).delete(synchronize_session=False)
    session.query(ThreatModel).filter(ThreatModel.owner == owner).delete(synchronize_session=False)
    session.commit()


def test_restore_replace_recreates_empty_db(client, db_session):
    model_id = _seed_catalog(db_session)
    backup = client.get("/admin/backup").json()

    _wipe_owner_catalog(db_session)
    assert db_session.query(ThreatModel).count() == 0

    restore = client.post("/admin/restore", json={"mode": "replace", "backup": backup})
    assert restore.status_code == 200
    assert restore.json()["restored"]["threat_models"] == 1

    tm = db_session.query(ThreatModel).filter(ThreatModel.id == model_id).first()
    job = db_session.query(JobStatus).filter(JobStatus.id == model_id).first()
    assert tm is not None
    assert tm.title == "Backup test"
    assert job is not None
    assert job.state == "COMPLETE"
    assert db_session.query(AuditLog).filter(AuditLog.threat_model_id == model_id).count() == 1


def test_restore_merge_upserts_after_wipe(client, db_session):
    model_id = _seed_catalog(db_session)
    backup = client.get("/admin/backup").json()

    _wipe_owner_catalog(db_session)
    assert db_session.query(ThreatModel).count() == 0

    restore = client.post("/admin/restore", json={"mode": "merge", "backup": backup})
    assert restore.status_code == 200
    assert db_session.query(ThreatModel).filter(ThreatModel.id == model_id).count() == 1
