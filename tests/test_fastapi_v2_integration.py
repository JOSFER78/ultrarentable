"""Integration tests for FastAPI V2 Routers."""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from services.api.app.main import app


@pytest.fixture
def client():
    # Evitar loops infinitos de red externa en tests unitarios
    with patch("services.api.app.main._periodic_sqx_sync", new_callable=AsyncMock):
        client_inst = TestClient(app, raise_server_exceptions=True)
        yield client_inst


def test_root_endpoint_reports_v2(client):
    """Verify GET / returns v2 capabilities and endpoints."""
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["version"] == "2.2.0"
    assert "TRACK_FONDEO" in data["tracks"]
    assert "TRACK_ULTRA" in data["tracks"]
    assert len(data["v2_endpoints"]) >= 8


def test_v2_telemetry_health_endpoint(client):
    """Verify GET /api/v2/telemetry/health returns 8 workers."""
    res = client.get("/api/v2/telemetry/health")
    assert res.status_code == 200
    data = res.json()
    assert data["total_workers"] == 8
    assert "DataWorker" in data["workers"]
    assert "PaperTradingWorker" in data["workers"]


def test_v2_semantic_failures_stats_endpoint(client):
    """Verify GET /api/v2/semantic/failures/stats returns statistics."""
    res = client.get("/api/v2/semantic/failures/stats")
    assert res.status_code == 200
    data = res.json()
    assert "total_failures_recorded" in data
    assert "category_distribution" in data


def test_v2_ultra_vault_config_endpoint(client):
    """Verify GET /api/v2/ultra/vault/config returns Obsidian Milestones."""
    res = client.get("/api/v2/ultra/vault/config")
    assert res.status_code == 200
    data = res.json()
    assert data["milestone_2x_lock_pct"] == 0.50
    assert data["milestone_3x_lock_pct"] == 0.65
    assert data["milestone_5x_lock_pct"] == 0.75
    assert data["milestone_10x_lock_pct"] == 0.85
