"""tests/test_legacy_revalidation_service.py
Test suite for LegacyRevalidationService (verificación y revalidación de estrategias legacy).
"""

import pytest
from pathlib import Path
from services.validation.legacy_revalidation_service import LegacyRevalidationService
from services.engine_version import CURRENT_ENGINE_VERSION


def test_revalidation_service_initialization():
    service = LegacyRevalidationService()
    assert service.db_path.parent.exists()
    assert service.data_dir.parent.exists()


def test_find_dataset_file():
    service = LegacyRevalidationService()
    # Test locating a real dataset only when a real dataset is mounted.
    ds_btc = service.find_dataset_file("BTC-USDT", "1h")
    ds_cl = service.find_dataset_file("CL", "1h")
    if ds_btc is None and ds_cl is None:
        pytest.skip("Real datasets not mounted in CI")
    if ds_btc is not None:
        assert ds_btc.exists()
    if ds_cl is not None:
        assert ds_cl.exists()


def test_revalidate_single_candidate_execution():
    service = LegacyRevalidationService()
    res = service.revalidate_single_candidate("UR_ULTRA_BTC_USDT_1H")
    assert "candidate_id" in res
    assert "passed" in res
    assert "gates_passed" in res
    assert res["candidate_id"].lower() == "ur_ultra_btc_usdt_1h"


def test_revalidate_legacy_batch_endpoint_structure():
    service = LegacyRevalidationService()
    res = service.revalidate_legacy_batch(target_version=CURRENT_ENGINE_VERSION, only_approved=True, max_candidates=2)
    assert res["status"] == "COMPLETED"
    assert res["target_engine_version"] == CURRENT_ENGINE_VERSION
    assert "total_evaluated" in res
    assert "promoted_count" in res
    assert "rejected_count" in res
