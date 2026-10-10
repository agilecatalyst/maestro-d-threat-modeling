"""Admin LLM provider endpoints (requires the local Postgres used by the suite)."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

API_DIR = Path(__file__).resolve().parent.parent / "backend" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from database import Base, SessionLocal, engine, get_db
from main import app
from models import LlmProviderProfile, LlmRoleBinding

BASE = "/admin/llm-providers"


@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.query(LlmRoleBinding).delete(synchronize_session=False)
        session.query(LlmProviderProfile).delete(synchronize_session=False)
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


def _payload(**overrides):
    body = {
        "name": "local-lmstudio",
        "kind": "openai_compatible",
        "base_url": "http://host.docker.internal:1234/v1",
        "model": "qwen3-8b",
        "api_key_env": "INFERENCE_API_KEY",
        "timeout_sec": 180,
    }
    body.update(overrides)
    return body


def test_crud_round_trip(client):
    created = client.post(BASE, json=_payload())
    assert created.status_code == 201, created.text
    profile = created.json()
    assert profile["name"] == "local-lmstudio"
    assert profile["kind"] == "openai_compatible"

    listed = client.get(BASE)
    assert listed.status_code == 200
    assert any(item["id"] == profile["id"] for item in listed.json())

    updated = client.put(f"{BASE}/{profile['id']}", json=_payload(model="qwen3-14b"))
    assert updated.status_code == 200
    assert updated.json()["model"] == "qwen3-14b"

    removed = client.delete(f"{BASE}/{profile['id']}")
    assert removed.status_code == 204
    assert client.get(BASE).json() == []


def test_secret_value_is_never_returned(client, monkeypatch):
    monkeypatch.setenv("LLM_OPENAI_API_KEY", "sk-super-secret")
    created = client.post(
        BASE, json=_payload(name="cloud", kind="openai", base_url=None, api_key_env="LLM_OPENAI_API_KEY")
    )
    assert created.status_code == 201
    body = created.json()
    assert body["api_key_env"] == "LLM_OPENAI_API_KEY"
    assert body["key_present"] is True
    assert "sk-super-secret" not in created.text


def test_api_key_env_outside_allowlist_is_rejected(client):
    response = client.post(BASE, json=_payload(api_key_env="POSTGRES_PASSWORD"))
    assert response.status_code == 422


def test_openai_compatible_requires_base_url(client):
    response = client.post(BASE, json=_payload(base_url=None))
    assert response.status_code == 422


def test_unknown_kind_is_rejected(client):
    response = client.post(BASE, json=_payload(kind="bedrock"))
    assert response.status_code == 422


def test_role_binding_and_bound_delete_conflict(client):
    profile = client.post(BASE, json=_payload()).json()

    bound = client.put(f"{BASE}/roles/threats", json={"profile_id": profile["id"]})
    assert bound.status_code == 200

    roles = client.get(f"{BASE}/roles").json()
    assert roles["threats"]["id"] == profile["id"]
    assert roles["sentry"] is None

    resolved = client.get(f"{BASE}/resolved/threats").json()
    assert resolved["source"] == "db"
    assert resolved["model"] == profile["model"]
    assert "api_key" not in resolved

    conflict = client.delete(f"{BASE}/{profile['id']}")
    assert conflict.status_code == 409


def test_resolved_falls_back_to_env_when_unbound(client, monkeypatch):
    monkeypatch.setenv("INFERENCE_BASE_URL", "http://localhost:1234/v1")
    monkeypatch.setenv("LOCAL_MODEL", "legacy-model")
    resolved = client.get(f"{BASE}/resolved/sentry").json()
    assert resolved["source"] == "env"
    assert resolved["model"] == "legacy-model"
    assert resolved["kind"] == "openai_compatible"


def test_unknown_role_is_rejected(client):
    assert client.get(f"{BASE}/resolved/nope").status_code == 422
