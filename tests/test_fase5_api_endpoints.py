"""tests/test_fase5_api_endpoints.py
Pruebas de Integración de Endpoints FastAPI para FASE 5: Cola de Trabajos, Watchdog y Suficiencia Forward.
"""

import pytest
from fastapi.testclient import TestClient
from services.api.app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_api_job_queue_enqueue_and_status(client):
    """Verifica encolar y consultar trabajos vía API REST."""
    payload = {
        "job_type": "REVALIDATE_CANDIDATE",
        "payload": {"candidate_id": "cand_api_test_01"},
        "priority": 7,
        "max_attempts": 3,
    }
    resp = client.post("/api/v1/jobs/enqueue", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_type"] == "REVALIDATE_CANDIDATE"
    assert data["priority"] == 7
    job_id = data["job_id"]

    # Consultar estado
    get_resp = client.get(f"/api/v1/jobs/{job_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["job_id"] == job_id


def test_api_watchdog_recovery_endpoint(client):
    """Verifica el endpoint de recuperación del Watchdog."""
    resp = client.post("/api/v1/jobs/watchdog/recover?max_in_progress_seconds=0")
    assert resp.status_code == 200
    data = resp.json()
    assert "recovered_jobs_count" in data
    assert "orphaned_jobs_reset" in data


def test_api_forward_sufficiency_endpoint(client):
    """Verifica la evaluación adaptativa de suficiencia forward vía API."""
    payload = {
        "strategy_id": "strat_api_fwd_01",
        "route": "fondeo",
        "forward_days": 25,
        "forward_trades": 38,
        "forward_net_profit_pct": 9.2,
        "forward_max_dd_pct": 2.1,
        "is_expected_return_pct": 12.0,
        "is_max_dd_pct": 3.8,
    }
    resp = client.post("/api/v1/forward/evaluate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["verdict"] == "FORWARD_CERTIFIED"
    assert data["is_certified_ready"] is True
    assert data["drawdown_consumption_pct"] < 50.0
