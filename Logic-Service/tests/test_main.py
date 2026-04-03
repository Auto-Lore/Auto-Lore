from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "logic-service"


def test_logic_ping():
    response = client.get("/logic/ping")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "logic service running"
