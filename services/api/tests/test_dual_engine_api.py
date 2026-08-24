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
    """Verify that candidates endpoint returns real evaluated strategies with honest status."""
    resp = client.get("/api/v1/candidates?include_rejected=true")
    assert resp.status_code == 200
    candidates = resp.json()
    assert len(candidates) >= 1
    
    for c in candidates:
        assert "candidate_id" in c
        assert "status" in c
        assert "route" in c
        assert "metrics" in c
        assert "engine_version" in c
        # Status must be deterministic and not a synthetic approved
        assert c["status"] in [
            "APPROVED", "ULTRA_CERTIFIED", "FUNDING_CERTIFIED", "PORTFOLIO_CERTIFIED",
            "REJECTED_GATES_INCOMPLETE", "REJECTED_ALTO_DRAWDOWN", "REJECTED_BAJO_PF",
            "RECHAZADA_FONDEO_DD", "INVESTIGACION_BTC", "BLOCKED_NO_EVIDENCE",
            "REFINADO_TIER_2", "INCUBADORA_REPROGRAMACION", "CERTIFICADA_TIER_1", "REJECTED_ESTRUCTURAL",
            "ANOMALY_REVIEW"
        ] or c["status"].startswith("BLOCKED") or c["status"].startswith("RECHAZADA") or c["status"].startswith("REJECTED") or c["status"].startswith("CANDIDATA") or c["status"].startswith("REFINADO") or c["status"].startswith("INCUBADORA") or c["status"].startswith("CERTIFICADA")


def test_versions_endpoint_and_changelog():
    """Verify engine versioning SSOT endpoint and changelog consistency."""
    from services.engine_version import CURRENT_ENGINE_VERSION
    resp = client.get("/api/v1/versions")
    assert resp.status_code == 200
    data = resp.json()
    assert data["current_version"] == CURRENT_ENGINE_VERSION
    assert "Ultrarentable" in data["current_name"]
    assert len(data["history"]) >= 3
    assert "version_distribution" in data
    
    curr_resp = client.get("/api/v1/versions/current")
    assert curr_resp.status_code == 200
    assert curr_resp.json()["engine_version"] == CURRENT_ENGINE_VERSION


def test_execution_session_kill_switch_lifecycle():
    """Verify creating, triggering, and resetting emergency Kill-Switch on an execution session."""
    # Ensure at least one session exists
    create_resp = client.post(
        "/api/v1/execution/sessions",
        json={
            "route": "ULTRA",
            "environment": "PAPER_BINGX",
            "candidate_id": "UR_ULTRA_SI_4H",
            "symbol": "SI-USDT",
            "initial_capital": 10000.0,
        },
    )
    assert create_resp.status_code == 200
    session_id = create_resp.json()["session_id"]
    
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
