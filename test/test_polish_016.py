import json
import sys
from io import BytesIO
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
from storage import STORAGE_PATH, save_diagram


@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


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


def _seed_model(session, diagram_path: str | None = None):
    model_id = uuid4()
    tm = ThreatModel(id=model_id, diagram_path=diagram_path, owner="local-user", title="Delete me")
    job = JobStatus(id=model_id, state="COMPLETE", detail=json.dumps({"summary": "x", "threats": []}))
    session.add(tm)
    session.flush()
    session.add(job)
    session.commit()
    return model_id


def test_delete_threat_model_removes_rows(client, db_session):
    model_id = _seed_model(db_session)
    db_session.add(
        AuditLog(threat_model_id=model_id, action="threat_add", detail={"op": "add"}, source_ip="127.0.0.1")
    )
    db_session.commit()

    response = client.delete(f"/threat-designer/{model_id}")
    assert response.status_code == 200
    assert response.json()["deleted"] is True
    assert db_session.query(ThreatModel).filter(ThreatModel.id == model_id).first() is None
    assert db_session.query(JobStatus).filter(JobStatus.id == model_id).first() is None
    assert db_session.query(AuditLog).filter(AuditLog.threat_model_id == model_id).count() == 0


def test_diagram_file_endpoint_serves_image(client, db_session):
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
        b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
        b"\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    relative = save_diagram(png_bytes, "png")
    model_id = _seed_model(db_session, diagram_path=relative)

    response = client.get(f"/threat-designer/diagrams/{model_id}/file")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/png")
    assert response.content == png_bytes

    file_path = STORAGE_PATH / relative
    if file_path.is_file():
        file_path.unlink()
