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
        "summary": "Web app",
        "assets": [],
        "flows": {"data_flows": [], "threat_sources": []},
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
    tm = ThreatModel(id=model_id, owner="local-user", title="Mutations")
    job = JobStatus(id=model_id, state="COMPLETE", detail=json.dumps(detail))
    session.add(tm)
    session.flush()
    session.add(job)
    session.commit()
    return model_id


def _threat(name: str) -> dict:
    return {
        "name": name,
        "stride_category": "Spoofing",
        "description": f"[Actor] can spoof {name}.",
        "target": "API",
        "source": "External Threat Actors",
        "likelihood": "Low",
        "impact": "Integrity loss",
        "mitigations": ["MFA"],
        "prerequisites": ["Network access"],
        "vector": "HTTP",
    }


def test_patch_add_update_delete(client, db_session):
    model_id = _seed_complete(db_session)

    add_resp = client.patch(
        f"/threat-designer/{model_id}/threats",
        json={"op": "add", "threats": [_threat("Session Hijack")]},
    )
    assert add_resp.status_code == 200
    assert len(add_resp.json()["threats"]) == 2

    update_resp = client.patch(
        f"/threat-designer/{model_id}/threats",
        json={
            "op": "update",
            "threats": [{**_threat("SQL Injection"), "likelihood": "High"}],
        },
    )
    assert update_resp.status_code == 200
    updated = next(t for t in update_resp.json()["threats"] if t["name"] == "SQL Injection")
    assert updated["likelihood"] == "High"

    delete_resp = client.patch(
        f"/threat-designer/{model_id}/threats",
        json={"op": "delete", "threats": [_threat("Session Hijack")]},
    )
    assert delete_resp.status_code == 200
    assert len(delete_resp.json()["threats"]) == 1


def test_patch_rejects_processing(client, db_session):
    model_id = uuid4()
    tm = ThreatModel(id=model_id, owner="local-user")
    job = JobStatus(id=model_id, state="PROCESSING", detail=json.dumps({"summary": "x"}))
    db_session.add(tm)
    db_session.flush()
    db_session.add(job)
    db_session.commit()

    response = client.patch(
        f"/threat-designer/{model_id}/threats",
        json={"op": "add", "threats": [_threat("X")]},
    )
    assert response.status_code == 400


def test_scan_flow_adds_threats(client, db_session):
    model_id = _seed_complete(db_session)
    mock_threats = {
        "threats": [_threat("Flow sniffing")],
        "count": 1,
    }
    with patch("routes.threat_models.scan_flow_agent", return_value=mock_threats):
        response = client.post(
            f"/threat-designer/{model_id}/threats/scan-flow",
            json={
                "source_entity": "Browser",
                "target_entity": "API",
                "flow_description": "HTTPS",
            },
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["added"] == 1
    assert any(t["name"] == "Flow sniffing" for t in payload["threats"])
