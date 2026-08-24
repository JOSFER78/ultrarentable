"""tests/test_fase4_api_endpoints.py
Pruebas de Integración de Endpoints FastAPI para FASE 4: Research Lab, Debate y Síntesis.
"""

import pytest
from fastapi.testclient import TestClient
from services.api.app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_api_research_lab_debate_and_synthesis_flow(client):
    """Verifica el flujo completo de debate de 8 roles y síntesis de mutación vía API."""
    # 1. Iniciar debate
    debate_resp = client.post("/api/v1/research-lab/debate/strat_api_flow_001")
    assert debate_resp.status_code == 200
    debate_data = debate_resp.json()
    assert debate_data["strategy_id"] == "strat_api_flow_001"
    assert len(debate_data["hypotheses"]) == 8
    debate_id = debate_data["debate_id"]

    # 2. Sintetizar reprogramación
    synth_payload = {
        "strategy_id": "strat_api_flow_001",
        "debate_id": debate_id,
    }
    synth_resp = client.post("/api/v1/research-lab/synthesize", json=synth_payload)
    assert synth_resp.status_code == 200
    synth_data = synth_resp.json()
    assert synth_data["strategy_id"] == "strat_api_flow_001"
    assert synth_data["validation_status"] == "VALID"
    assert "mutated_dsl" in synth_data

    # 3. Listar propuestas y experimentos
    prop_resp = client.get("/api/v1/research-lab/proposals")
    assert prop_resp.status_code == 200
    assert isinstance(prop_resp.json(), list)

    exp_resp = client.get("/api/v1/research-lab/experiments")
    assert exp_resp.status_code == 200
    assert isinstance(exp_resp.json(), list)
