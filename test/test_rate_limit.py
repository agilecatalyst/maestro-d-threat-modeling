import json
import os
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
from middleware.rate_limit import reset_buckets_for_tests
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


@pytest.fixture(autouse=True)
def enable_rate_limits(monkeypatch):
    monkeypatch.setenv("API_RATE_LIMIT_ENABLED", "true")
    reset_buckets_for_tests()
    yield
    reset_buckets_for_tests()


def _seed_model(session):
    model_id = uuid4()
    tm = ThreatModel(id=model_id, diagram_path="diagrams/sample.png", owner="local-user")
    job = JobStatus(id=model_id, state="PENDING", detail=json.dumps({}))
    session.add(tm)
    session.flush()
    session.add(job)
    session.commit()
    return model_id


def test_start_job_rate_limit_returns_429(client, db_session):
    model_ids = [_seed_model(db_session) for _ in range(6)]
    with patch("routes.threat_models.invoke_agent"):
        for model_id in model_ids[:5]:
            response = client.post(
                "/threat-designer",
                json={
                    "id": str(model_id),
                    "description": "Three-tier web app",
                    "application_type": "hybrid",
                },
            )
            assert response.status_code == 200

        blocked = client.post(
            "/threat-designer",
            json={
                "id": str(model_ids[5]),
                "description": "Three-tier web app",
                "application_type": "hybrid",
            },
        )
    assert blocked.status_code == 429
    assert blocked.headers.get("retry-after")
