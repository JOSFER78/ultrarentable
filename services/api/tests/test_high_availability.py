"""services/api/tests/test_high_availability.py
Pruebas de Alta Disponibilidad 24/7, Watchdog y Auto-Recuperación.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from services.api.app.main import app
from services.monitoring.high_availability_watchdog import ha_watchdog


def test_ha_watchdog_health_cycle():
    """Verifica que el ciclo de supervisión del watchdog 24/7 opere de forma determinista."""
    res = ha_watchdog.perform_health_and_recovery_cycle()
    assert res["status"] == "WATCHDOG_ACTIVE"
    assert "engine_mode" in res
    assert isinstance(res["actions_taken"], list)


def test_ha_watchdog_manual_reset():
    """Verifica que el reseteo manual y self-healing de infraestructura restaure los servicios."""
    res = ha_watchdog.manual_system_reset()
    assert res["overall_status"] == "ALL_SYSTEMS_RESTORED_AND_RUNNING"
    assert "continuous_search_daemon" in res
    assert "supervisor_workers" in res


def test_system_auto_recover_endpoint():
    """Verifica el endpoint POST /api/v1/system/auto-recover."""
    client = TestClient(app)
    response = client.post("/api/v1/system/auto-recover")
    assert response.status_code == 200
    data = response.json()
    assert "Auto-recuperación" in data["message"]
    assert data["details"]["overall_status"] == "ALL_SYSTEMS_RESTORED_AND_RUNNING"


def test_system_watchdog_status_endpoint():
    """Verifica el endpoint GET /api/v1/system/watchdog-status."""
    client = TestClient(app)
    response = client.get("/api/v1/system/watchdog-status")
    assert response.status_code == 200
    data = response.json()
    assert "engine_mode" in data
    assert "recent_recoveries" in data
