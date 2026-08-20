"""services/api/tests/test_legacy_revalidation_api.py
Tests for POST /api/v1/candidates/revalidate-legacy, GET /status, POST /cancel and POST /{id}/revalidate.
"""

import time
from fastapi.testclient import TestClient
from services.api.app.main import app
from services.engine_version import CURRENT_ENGINE_VERSION

client = TestClient(app)


def test_revalidate_legacy_sync_batch_endpoint():
    res = client.post(
        "/api/v1/candidates/revalidate-legacy",
        json={
            "target_version": "1.02",
            "only_approved": True,
            "route": "ALL",
            "max_candidates": 2,
            "background": False,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "COMPLETED"
    assert data["target_engine_version"] == CURRENT_ENGINE_VERSION
    assert "total_evaluated" in data
    assert "promoted_count" in data
    assert "rejected_count" in data


def test_revalidate_legacy_background_and_status_endpoint():
    # Start background job
    res = client.post(
        "/api/v1/candidates/revalidate-legacy",
        json={
            "target_version": "ALL",
            "only_approved": True,
            "route": "ALL",
            "max_candidates": 2,
            "background": True,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["STARTED", "ALREADY_RUNNING"]
    assert "total_candidates" in data

    # Poll status
    time.sleep(0.5)
    st_res = client.get("/api/v1/candidates/revalidate-legacy/status")
    assert st_res.status_code == 200
    st_data = st_res.json()
    assert "status" in st_data
    assert "processed_count" in st_data


def test_revalidate_single_candidate_endpoint():
    res = client.post("/api/v1/candidates/UR_ULTRA_SOL_USDT_1H/revalidate")
    assert res.status_code == 200
    data = res.json()
    assert data["candidate_id"] == "UR_ULTRA_SOL_USDT_1H"
    assert "passed" in data
    assert "new_status" in data
