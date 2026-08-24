"""tests/test_fase6_frontend_synchronization.py
Pruebas de Integración para FASE 6: Sincronización de las 6 Vistas de Producto y Clientes de Frontend.
Especificación oficial según Sección 7 y 8 del Informe Maestro v5.3.0.
"""

import pytest
from fastapi.testclient import TestClient
from services.api.app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_product_view_1_dashboard_and_telemetry(client):
    """Vista 1: Dashboard y Telemetría del Sistema."""
    resp = client.get("/api/v1/system/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "overall_status" in data or "services" in data or "database" in data

    resp_alias = client.get("/api/v1/system/status")
    assert resp_alias.status_code == 200


def test_product_view_2_opportunity_matrix(client):
    """Vista 2: Matriz de Oportunidades BingX Real Data."""
    resp = client.get("/api/v2/opportunity-matrix")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_product_view_3_discovery_autopilot(client):
    """Vista 3: Motor de Búsqueda Autopilot y Discovery."""
    resp = client.get("/api/v1/discovery/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data


def test_product_view_4_research_lab_and_eight_roles(client):
    """Vista 4: Laboratorio Cuantitativo de Investigación (8 Roles) y Síntesis AST."""
    debate_resp = client.post("/api/v1/research-lab/debate/strat_f6_view4")
    assert debate_resp.status_code == 200
    deb = debate_resp.json()
    assert len(deb["hypotheses"]) == 8

    synth_resp = client.post(
        "/api/v1/research-lab/synthesize",
        json={"strategy_id": "strat_f6_view4", "debate_id": deb["debate_id"]},
    )
    assert synth_resp.status_code == 200
    assert synth_resp.json()["validation_status"] == "VALID"


def test_product_view_5_lineage_and_cryptographic_certification(client):
    """Vista 5: Árbol DAG de Linaje Genealógico y Certificación Criptográfica."""
    cert_payload = {
        "strategy_id": "strat_f6_view5",
        "version": "1.00",
        "strategy_hash": "hash_f6_view5",
        "dataset_id": "BINGX_BTC_USDT_1h_clean",
        "metrics_snapshot": {"profit_factor": 2.1, "max_drawdown_pct": 3.8, "trades": 50.0},
        "route": "fondeo",
        "status": "FUNDING_CERTIFIED",
        "scorecard": {"score": 90},
    }
    cert_resp = client.post("/api/v1/lineage/certify", json=cert_payload)
    assert cert_resp.status_code == 200
    cert = cert_resp.json()

    verify_resp = client.post("/api/v1/lineage/verify-certificate", json=cert)
    assert verify_resp.status_code == 200
    assert verify_resp.json()["is_valid"] is True

    tree_resp = client.get("/api/v1/lineage/strat_f6_view5")
    assert tree_resp.status_code == 200
    assert tree_resp.json()["root_strategy_id"] == "strat_f6_view5"


def test_product_view_6_portfolio_and_queue_monitor(client):
    """Vista 6: Portfolio Studio, Paper Trading y Monitor de Cola 24/7."""
    jobs_resp = client.get("/api/v1/jobs")
    assert jobs_resp.status_code == 200
    assert isinstance(jobs_resp.json(), list)

    fwd_payload = {
        "strategy_id": "strat_f6_view6",
        "route": "fondeo",
        "forward_days": 21,
        "forward_trades": 32,
        "forward_net_profit_pct": 7.5,
        "forward_max_dd_pct": 2.2,
        "is_expected_return_pct": 10.0,
        "is_max_dd_pct": 3.5,
    }
    fwd_resp = client.post("/api/v1/forward/evaluate", json=fwd_payload)
    assert fwd_resp.status_code == 200
    assert fwd_resp.json()["verdict"] == "FORWARD_CERTIFIED"
