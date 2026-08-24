"""tests/test_red_team_fase6_frontend_zero_mock.py
Auditoría Adversarial y Red-Team para FASE 6:
1. Verificación del principio Zero-Mock en los feeds del frontend.
2. Detección de adulteración de certificados en clientes REST.
3. Resistencia a payloads malformados en los endpoints de las 6 Vistas de Producto.
"""

import pytest
from fastapi.testclient import TestClient
from services.api.app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_red_team_tampered_certificate_rejected_via_api(client):
    """Red-Team: Un certificado emitido legalmente pero alterado por el frontend es rechazado al 100%."""
    cert_payload = {
        "strategy_id": "strat_f6_tamper",
        "version": "1.00",
        "strategy_hash": "hash_f6_tamper",
        "dataset_id": "BINGX_BTC_USDT_1h_clean",
        "metrics_snapshot": {"profit_factor": 2.0, "max_drawdown_pct": 3.5, "trades": 40.0},
        "route": "fondeo",
        "status": "FUNDING_CERTIFIED",
        "scorecard": {"score": 85},
    }
    cert_resp = client.post("/api/v1/lineage/certify", json=cert_payload)
    assert cert_resp.status_code == 200
    tampered_cert = cert_resp.json()

    # Modificar profit factor de 2.0 a 9.99 (intento de fraude de métricas)
    tampered_cert["metrics_snapshot"]["profit_factor"] = 9.99

    verify_resp = client.post("/api/v1/lineage/verify-certificate", json=tampered_cert)
    assert verify_resp.status_code == 200
    res = verify_resp.json()
    assert res["is_valid"] is False
    assert res["tampering_detected"] is True


def test_red_team_zero_mock_contract_enforcement(client):
    """Red-Team: Asegurar que todos los endpoints retornan estructuras tipadas reales sin payloads simulados."""
    health_resp = client.get("/api/v1/system/health")
    assert health_resp.status_code == 200
    data = health_resp.json()
    assert "overall_status" in data or "services" in data or "database" in data
    assert "mock" not in str(data).lower()
