import json
import sys
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

API_DIR = Path(__file__).resolve().parent.parent / "backend" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from database import Base, SessionLocal, engine, get_db
from main import app
from models import JobStatus, ThreatModel


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


def _seed_model(session):
    model_id = uuid4()
    tm = ThreatModel(id=model_id, diagram_path="diagrams/sample.png", owner="local-user")
    job = JobStatus(id=model_id, state="PENDING", detail=json.dumps({"summary": "cached"}))
    session.add(tm)
    session.flush()
    session.add(job)
    session.commit()
    return model_id


def test_start_job_returns_id(client, db_session):
    model_id = _seed_model(db_session)
    with patch("routes.threat_models.invoke_agent") as invoke:
        response = client.post(
            "/threat-designer",
            json={
                "id": str(model_id),
                "description": "Three-tier web app",
                "application_type": "hybrid",
            },
        )
    assert response.status_code == 200
    assert response.json()["id"] == str(model_id)
    invoke.assert_called_once()

    job = db_session.query(JobStatus).filter(JobStatus.id == model_id).first()
    assert job.state == "PROCESSING"


def test_status_endpoint_parses_detail(client, db_session):
    model_id = _seed_model(db_session)
    job = db_session.query(JobStatus).filter(JobStatus.id == model_id).first()
    job.state = "COMPLETE"
    job.detail = json.dumps({"summary": "Done", "threats": [{"name": "X"}]})
    db_session.commit()

    response = client.get(f"/threat-designer/status/{model_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["state"] == "COMPLETE"
    assert body["detail"]["summary"] == "Done"


def test_get_threat_model_merges_metadata(client, db_session):
    model_id = _seed_model(db_session)
    job = db_session.query(JobStatus).filter(JobStatus.id == model_id).first()
    job.state = "COMPLETE"
    job.detail = json.dumps(
        {
            "summary": "Summary text",
            "assets": [{"name": "API"}],
            "flows": {"data_flows": []},
            "threats": [{"name": "Threat A"}],
            "meta": {"threat_count": 1},
        }
    )
    db_session.commit()

    response = client.get(f"/threat-designer/{model_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["summary"] == "Summary text"
    assert body["threats"][0]["name"] == "Threat A"
    assert body["meta"]["threat_count"] == 1


def test_list_all_returns_items(client, db_session):
    model_id = _seed_model(db_session)
    response = client.get("/threat-designer/all?limit=10")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["items"][0]["id"] == str(model_id)
