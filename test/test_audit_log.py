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
    tm = ThreatModel(id=model_id, owner="local-user", title="Audit test")
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


def test_patch_writes_audit_log(client, db_session):
    model_id = _seed_complete(db_session)
    response = client.patch(
        f"/threat-designer/{model_id}/threats",
        json={"op": "add", "threats": [_threat("Session Hijack")]},
    )
    assert response.status_code == 200

    rows = db_session.query(AuditLog).filter(AuditLog.threat_model_id == model_id).all()
    assert len(rows) == 1
    assert rows[0].action == "threat_add"
    assert rows[0].detail["op"] == "add"
    assert "Session Hijack" in rows[0].detail["threat_names"]


def test_scan_flow_writes_audit_log(client, db_session):
    from unittest.mock import patch

    model_id = _seed_complete(db_session)
    with patch(
        "routes.threat_models.scan_flow_agent",
        return_value={"threats": [_threat("Flow sniffing")], "count": 1},
    ):
        response = client.post(
            f"/threat-designer/{model_id}/threats/scan-flow",
            json={
                "source_entity": "Browser",
                "target_entity": "API",
                "flow_description": "HTTPS",
            },
        )
    assert response.status_code == 200

    rows = db_session.query(AuditLog).filter(AuditLog.threat_model_id == model_id).all()
    assert len(rows) == 1
    assert rows[0].action == "scan_flow"
    assert rows[0].detail["added"] == 1
