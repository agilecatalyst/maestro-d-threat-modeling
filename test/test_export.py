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


def _seed_complete(session):
    model_id = uuid4()
    detail = {
        "summary": "Three-tier web application with API and database.",
        "assets": [{"type": "Asset", "name": "API", "description": "REST API", "criticality": "High"}],
        "flows": {
            "data_flows": [
                {
                    "source_entity": "Browser",
                    "target_entity": "API",
                    "flow_description": "HTTPS requests",
                }
            ],
            "threat_sources": [],
        },
        "threats": [
            {
                "name": "SQL Injection",
                "stride_category": "Tampering",
                "description": "Attacker can inject SQL.",
                "target": "API",
                "source": "External Threat Actors",
                "likelihood": "Medium",
                "impact": "Data breach",
                "mitigations": ["Parameterized queries"],
                "prerequisites": ["Input access"],
                "vector": "HTTP",
            }
        ],
        "meta": {"threat_count": 1},
    }
    tm = ThreatModel(id=model_id, diagram_path="diagrams/x.png", owner="local-user", title="Test Model")
    job = JobStatus(id=model_id, state="COMPLETE", detail=json.dumps(detail))
    session.add(tm)
    session.flush()
    session.add(job)
    session.commit()
    return model_id


def test_export_json_schema(client, db_session):
    model_id = _seed_complete(db_session)
    response = client.get(f"/threat-designer/{model_id}/export/json")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    payload = response.json()
    assert payload["schema_version"] == "1.0"
    assert payload["id"] == str(model_id)
    assert payload["exported_at"]
    assert len(payload["threats"]) == 1


def test_export_pdf_complete(client, db_session):
    model_id = _seed_complete(db_session)
    response = client.get(f"/threat-designer/{model_id}/export/pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:4] == b"%PDF"


def test_export_pdf_rejects_incomplete(client, db_session):
    model_id = uuid4()
    tm = ThreatModel(id=model_id, owner="local-user")
    job = JobStatus(id=model_id, state="PROCESSING", detail=json.dumps({"summary": "x"}))
    db_session.add(tm)
    db_session.flush()
    db_session.add(job)
    db_session.commit()

    response = client.get(f"/threat-designer/{model_id}/export/pdf")
    assert response.status_code == 400
