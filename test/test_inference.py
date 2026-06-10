import pytest
import requests


def test_agent_ping_unchanged():
    response = requests.get("http://localhost:8080/ping", timeout=10)
    assert response.status_code == 200
    assert response.json() == {"status": "Healthy", "service": "maestro-d-agent"}


def test_inference_health():
    response = requests.get("http://localhost:8080/inference/health", timeout=10)
    data = response.json()

    assert "status" in data
    assert "service" in data
    assert data["service"] == "maestro-d-agent"

    if response.status_code == 503:
        pytest.skip("INFERENCE_BASE_URL not reachable (LLM offline)")
        return

    assert response.status_code == 200
    assert data["status"] == "connected"
    assert isinstance(data.get("model_loaded"), bool)
    assert "models_count" in data
    assert "local_model" in data
