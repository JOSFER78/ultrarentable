"""services/api/tests/test_legacy_revalidation_api.py
Tests for POST /api/v1/candidates/revalidate-legacy and POST /api/v1/candidates/{id}/revalidate.
"""

from fastapi.testclient import TestClient
from services.api.app.main import app
from services.engine_version import CURRENT_ENGINE_VERSION

client = TestClient(app)


def test_revalidate_legacy_batch_endpoint():
    res = client.post(
        "/api/v1/candidates/revalidate-legacy",
        json={
            "target_version": "1.02",
            "only_approved": True,
            "route": "ALL",
            "max_candidates": 2,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "COMPLETED"
    assert data["target_engine_version"] == CURRENT_ENGINE_VERSION
    assert "total_evaluated" in data
    assert "promoted_count" in data
    assert "rejected_count" in data


def test_revalidate_single_candidate_endpoint():
    res = client.post("/api/v1/candidates/UR_ULTRA_SOL_USDT_1H/revalidate")
    assert res.status_code == 200
    data = res.json()
    assert data["candidate_id"] == "UR_ULTRA_SOL_USDT_1H"
    assert "passed" in data
    assert "new_status" in data
