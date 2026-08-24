"""tests/test_fase3_api_endpoints.py
Pruebas de Integración de Endpoints FastAPI para FASE 3: Linaje, Certificados y Policy Impact Analyzer.
"""

import pytest
from fastapi.testclient import TestClient
from services.api.app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_api_versions_endpoint(client):
    """Verifica los endpoints de gobernanza de versiones /api/v1/versions y /api/v2/versions."""
    resp = client.get("/api/v1/versions")
    assert resp.status_code == 200
    data = resp.json()
    assert "current_version" in data
    assert "codebase_fingerprint" in data
    assert "git_commit" in data

    resp_v2 = client.get("/api/v2/versions")
    assert resp_v2.status_code == 200
    assert resp_v2.json()["engine_version"] == data["current_version"]


def test_api_lineage_and_certification_endpoints(client):
    """Verifica emisión, consulta de linaje y verificación de certificados vía API."""
    # 1. Emisión de certificado
    cert_payload = {
        "strategy_id": "strat_api_test_100",
        "version": "1.00",
        "strategy_hash": "sha256_strat_api_100",
        "dataset_id": "BINGX_BTC_USDT_1h_clean",
        "metrics_snapshot": {
            "profit_factor": 2.25,
            "max_drawdown_pct": 3.90,
            "trades": 80.0,
            "net_return_pct": 40.0,
        },
        "route": "fondeo",
        "status": "FUNDING_CERTIFIED",
        "scorecard": {"pass_score": 95},
    }

    cert_resp = client.post("/api/v1/lineage/certify", json=cert_payload)
    assert cert_resp.status_code == 200
    cert_data = cert_resp.json()
    assert cert_data["strategy_id"] == "strat_api_test_100"
    assert len(cert_data["certificate_hash"]) == 64

    # 2. Verificación criptográfica
    verify_resp = client.post("/api/v1/lineage/verify-certificate", json=cert_data)
    assert verify_resp.status_code == 200
    assert verify_resp.json()["is_valid"] is True
    assert verify_resp.json()["tampering_detected"] is False

    # 3. Consulta de árbol de linaje
    tree_resp = client.get("/api/v1/lineage/strat_api_test_100")
    assert tree_resp.status_code == 200
    tree_data = tree_resp.json()
    assert tree_data["root_strategy_id"] == "strat_api_test_100"
    assert "strat_api_test_100" in tree_data["nodes"]


def test_api_policy_impact_analysis_endpoint(client):
    """Verifica la simulación de impacto de políticas vía endpoint POST."""
    req_payload = {
        "target_route": "fondeo",
        "new_max_drawdown_pct": 3.80,
        "new_min_profit_factor": 1.70,
        "new_min_calmar": 0.6,
        "new_min_trades": 35,
    }

    resp = client.post("/api/v1/policy/impact-analysis", json=req_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["target_route"] == "fondeo"
    assert "baseline_policy" in data
    assert "new_policy" in data
    assert "transition_summary" in data
    assert "recommendation" in data
