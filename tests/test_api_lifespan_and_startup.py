"""tests/test_api_lifespan_and_startup.py
Verificación del ciclo de vida y arranque limpio de FastAPI sin excepciones silenciosas.
"""
import pytest
from fastapi.testclient import TestClient
from services.api.app.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_api_startup_and_version_endpoints(client):
    response = client.get("/api/v1/versions")
    assert response.status_code == 200
    data = response.json()
    assert data["current_version"] in ["5.3.0", "5.4.0"]
    assert data["engine_version"] in ["5.3.0", "5.4.0"]
    assert "codebase_fingerprint" in data
    assert len(data["codebase_fingerprint"]) == 64

def test_root_endpoint_real_only(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "RUNNING"
    assert data["mode"] == "REAL_ONLY"
    assert data["version"] in ["5.3.0", "5.4.0", "2.0.0"]
