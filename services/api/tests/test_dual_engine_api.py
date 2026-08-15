"""Canonical Unit & Integration Tests for Dual-Engine API (ULTRA / FONDEO)."""

from fastapi.testclient import TestClient
from services.api.app.main import app

client = TestClient(app)


def test_providers_endpoint():
    """Verify that prop firm providers return versioned verified and unverified rules."""
    resp = client.get("/api/v1/providers")
    assert resp.status_code == 200
    providers = resp.json()
    assert len(providers) >= 6
    
    topstep = next((p for p in providers if p["provider_id"] == "topstep_combine_50k"), None)
    assert topstep is not None
    assert topstep["target_pct"] == 6.0
    assert topstep["max_trailing_dd_pct"] == 4.0
    assert topstep["verification_status"] == "VERIFIED"
    assert "MES" in topstep["allowed_instruments"]
    
    bulenox = next((p for p in providers if p["provider_id"] == "bulenox_50k"), None)
    assert bulenox is not None
    assert bulenox["verification_status"] == "UNVERIFIED"


def test_candidates_endpoint_honest_reclassification():
    """Verify Strategy 1.0.54 is RECHAZADA_FONDEO_DD and Strategy 1.0.32 is INVESTIGACION_BTC."""
    resp = client.get("/api/v1/candidates")
    assert resp.status_code == 200
    candidates = resp.json()
    assert len(candidates) >= 2
    
    strat_54 = next((c for c in candidates if c["candidate_id"] == "strat_1_0_54"), None)
    assert strat_54 is not None
    assert strat_54["status"] == "RECHAZADA_FONDEO_DD"
    assert strat_54["metrics"]["out_of_sample"]["max_drawdown_pct"] == 10.18
    assert "excede el límite canónico de fondeo" in strat_54["status_reason"]
    
    strat_32 = next((c for c in candidates if c["candidate_id"] == "strat_1_0_32"), None)
    assert strat_32 is not None
    assert strat_32["status"] == "INVESTIGACION_BTC"
    assert "No validada en instrumento CME" in strat_32["status_reason"]


def test_execution_session_kill_switch_lifecycle():
    """Verify triggering and resetting emergency Kill-Switch."""
    resp = client.get("/api/v1/execution/sessions")
    assert resp.status_code == 200
    sessions = resp.json()
    assert len(sessions) >= 1
    session_id = sessions[0]["session_id"]
    
    # Trigger kill switch
    kill_resp = client.post(
        f"/api/v1/execution/sessions/{session_id}/kill-switch",
        json={"reason": "Test emergency drawdown limit breach"}
    )
    assert kill_resp.status_code == 200
    assert kill_resp.json()["kill_switch_active"] is True
    
    # Check session state
    detail_resp = client.get(f"/api/v1/execution/sessions/{session_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["status"] == "KILL_SWITCH_TRIGGERED"
    assert detail_resp.json()["kill_switch_active"] is True
    assert len(detail_resp.json()["open_positions"]) == 0
    
    # Resume session
    resume_resp = client.post(f"/api/v1/execution/sessions/{session_id}/resume")
    assert resume_resp.status_code == 200
    assert resume_resp.json()["status"] == "RUNNING"


def test_audit_events_timeline():
    """Verify audit events recording and retrieval."""
    # Log test event
    create_resp = client.post(
        "/api/v1/audit/events",
        json={
            "category": "CAMPAIGN",
            "route": "FONDEO",
            "title": "Test Audit Event",
            "description": "Integration test event description",
            "severity": "INFO"
        }
    )
    assert create_resp.status_code == 200
    
    list_resp = client.get("/api/v1/audit/events?route=FONDEO")
    assert list_resp.status_code == 200
    events = list_resp.json()
    assert len(events) >= 1
    assert any(e["title"] == "Test Audit Event" for e in events)


def test_system_health_endpoint():
    """Verify non-mocked deep health diagnostics."""
    resp = client.get("/api/v1/system/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "services" in data
    assert "database" in data
    assert "market_data" in data
    assert data["services"]["api_backend"]["status"] == "ONLINE"
    assert data["database"]["wal_active"] is True
    assert "port_conflicts" in data
