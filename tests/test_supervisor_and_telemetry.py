"""Unit tests for SystemSupervisor, Worker Pool, and Telemetry (Fase 8)."""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from services.monitoring import (
    SystemSupervisor,
    WorkerType,
    WorkerState,
    ForbiddenSelfHealingActionError,
    telemetry_router,
)
from services.core.event_bus import SystemAlertEvent, event_bus


@pytest.fixture
def app():
    _app = FastAPI()
    _app.include_router(telemetry_router, prefix="/api/v2/telemetry")
    return _app


@pytest.mark.asyncio
async def test_system_supervisor_starts_8_workers():
    """Verify SystemSupervisor initializes and starts all 8 specialized workers."""
    supervisor = SystemSupervisor()
    assert len(supervisor.workers) == 8

    await supervisor.start_all()
    health = supervisor.get_system_health()

    assert health["supervisor_active"] is True
    assert health["overall_healthy"] is True
    assert len(health["workers"]) == 8
    assert health["workers"]["DataWorker"]["state"] == "RUNNING"
    assert health["workers"]["PaperTradingWorker"]["state"] == "RUNNING"

    await supervisor.stop_all()


@pytest.mark.asyncio
async def test_supervisor_self_healing_recovers_failed_worker():
    """Verify Self-Healing detects and restarts an errored or stalled worker."""
    supervisor = SystemSupervisor()
    await supervisor.start_all()

    # Simulate SQXWorker failure
    sqx_worker = supervisor.workers[WorkerType.SQX_WORKER]
    sqx_worker.record_failure("Connection to StrategyQuant X JSON-RPC lost")

    health_before = supervisor.get_system_health()
    assert health_before["overall_healthy"] is False
    assert health_before["workers"]["SQXWorker"]["state"] == "ERROR"

    # Run self-healing
    healed_workers = await supervisor.run_self_healing_check()
    assert "SQXWorker" in healed_workers

    health_after = supervisor.get_system_health()
    assert health_after["workers"]["SQXWorker"]["state"] == "RUNNING"
    assert health_after["workers"]["SQXWorker"]["restart_count"] == 1

    await supervisor.stop_all()


def test_supervisor_governance_boundaries():
    """Verify strict prohibition of relaxing gates or altering backtests in self-healing."""
    supervisor = SystemSupervisor()
    
    with pytest.raises(ForbiddenSelfHealingActionError):
        supervisor.execute_governance_action("RELAX_EVIDENCE_GATE")

    with pytest.raises(ForbiddenSelfHealingActionError):
        supervisor.execute_governance_action("ALTER_BACKTEST_METRICS")


def test_telemetry_api_endpoints(app):
    """Verify FastAPI telemetry endpoints for health and event history."""
    client = TestClient(app)

    # 1. Health check
    res_health = client.get("/api/v2/telemetry/health")
    assert res_health.status_code == 200
    data = res_health.json()
    assert "workers" in data
    assert len(data["workers"]) == 8

    # 2. History check
    res_history = client.get("/api/v2/telemetry/history")
    assert res_history.status_code == 200
    assert isinstance(res_history.json(), list)
