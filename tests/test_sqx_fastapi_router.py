"""Integration test for FastAPI SQX router endpoint with 100% real backend."""

from fastapi.testclient import TestClient
from services.api.app.main import app

client = TestClient(app)


def test_fastapi_sqx_status():
    """Verify GET /api/v1/sqx/status returns real SQX MCP status."""
    response = client.get("/api/v1/sqx/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ONLINE"
    assert "server_info" in data


def test_fastapi_sqx_projects():
    """Verify GET /api/v1/sqx/projects returns live projects from StrategyQuant X."""
    response = client.get("/api/v1/sqx/projects")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert "projects" in data
    assert data["count"] > 0
