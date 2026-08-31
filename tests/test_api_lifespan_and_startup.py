"""tests/test_api_lifespan_and_startup.py
Verificación del ciclo de vida y arranque limpio de FastAPI sin excepciones silenciosas.
"""
import pytest
from fastapi.testclient import TestClient
from services.api.app.main import app
from services.engine_version import CURRENT_ENGINE_VERSION

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_api_startup_and_version_endpoints(client):
    response = client.get("/api/v1/versions")
    assert response.status_code == 200
    data = response.json()
    assert CURRENT_ENGINE_VERSION in (data.get("current_version"), data.get("active_version"))
    assert "codebase_fingerprint" in data
    assert len(data["codebase_fingerprint"]) == 64

def test_root_endpoint_real_only(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "RUNNING"
    assert data["mode"] == "REAL_ONLY"
    assert data["version"] in [CURRENT_ENGINE_VERSION, "2.0.0", "2.2.0"]
