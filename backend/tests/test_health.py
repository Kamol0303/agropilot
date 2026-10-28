from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_liveness():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_root():
    assert client.get("/").json()["name"] == "AgroPilot"
