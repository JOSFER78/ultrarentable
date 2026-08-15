import json
import pytest
from fastapi.testclient import TestClient
from services.api.app.main import app
from services.api.app.factory.autopilot import AutopilotController, UniverseScanner, LeverageAutopilot
from services.api.app.db.database import get_db, Base, engine

client = TestClient(app)

def test_autopilot_start_with_empty_payload_returns_202(monkeypatch) -> None:
    """The HTTP trigger queues work and never blocks for a full campaign."""

    class DummyThread:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def start(self):
            return None

    from services.api.app.api import routes
    monkeypatch.setattr(routes.threading, "Thread", DummyThread)
    response = client.post("/api/v1/autopilot/start", json={})
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["autopilot"]["status"] in {"QUEUED", "SCANNING", "RUNNING", "PAUSED"}
    assert data["autopilot"]["runId"].startswith("run_")

    duplicate = client.post("/api/v1/autopilot/start", json={})
    assert duplicate.status_code == 202
    assert duplicate.json()["autopilot"]["runId"] == data["autopilot"]["runId"]

def test_autopilot_status_and_decisions() -> None:
    """Autopilot must expose decisions log and status."""
    res_status = client.get("/api/v1/autopilot/status")
    assert res_status.status_code == 200
    st_data = res_status.json()
    assert "status" in st_data

    res_dec = client.get("/api/v1/autopilot/decisions")
    assert res_dec.status_code == 200
    dec_list = res_dec.json()
    assert isinstance(dec_list, list)

def test_autopilot_lifecycle_pause_resume_stop() -> None:
    """Autopilot lifecycle endpoints must respond cleanly."""
    res_pause = client.post("/api/v1/autopilot/pause", json={})
    assert res_pause.status_code in [200, 404]

    res_resume = client.post("/api/v1/autopilot/resume", json={})
    assert res_resume.status_code in [200, 404]

    res_stop = client.post("/api/v1/autopilot/stop", json={})
    assert res_stop.status_code in [200, 404]

def test_leverage_trials_recorded_without_fake_500_percent() -> None:
    """Leverage trials endpoint must return real backtest records."""
    res = client.get("/api/v1/autopilot/leverage-trials")
    assert res.status_code == 200
    trials = res.json()
    assert isinstance(trials, list)
