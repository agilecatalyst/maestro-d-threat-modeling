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
from schemas import DESCRIPTION_MAX_LENGTH


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
    job = JobStatus(id=model_id, state="PENDING", detail=json.dumps({}))
    session.add(tm)
    session.flush()
    session.add(job)
    session.commit()
    return model_id


def test_description_rejects_over_max_length(client, db_session):
    model_id = _seed_model(db_session)
    too_long = "x" * (DESCRIPTION_MAX_LENGTH + 1)
    response = client.post(
        "/threat-designer",
        json={"id": str(model_id), "description": too_long, "application_type": "hybrid"},
    )
    assert response.status_code == 422


def test_description_accepts_at_max_length(client, db_session):
    model_id = _seed_model(db_session)
    at_limit = "x" * DESCRIPTION_MAX_LENGTH
    with patch("routes.threat_models.invoke_agent"):
        response = client.post(
            "/threat-designer",
            json={"id": str(model_id), "description": at_limit, "application_type": "hybrid"},
        )
    assert response.status_code == 200
