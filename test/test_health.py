import requests

def test_api_health():
    response = requests.get("http://localhost:8000/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "maestro-d-api",
        "database": "connected",
    }

def test_agent_ping():
    response = requests.get("http://localhost:8080/ping")
    assert response.status_code == 200
    assert response.json() == {"status": "Healthy", "service": "maestro-d-agent"}