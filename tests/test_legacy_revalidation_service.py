"""tests/test_legacy_revalidation_service.py
Test suite for LegacyRevalidationService (verificación y revalidación de estrategias legacy).
"""

import pytest
from pathlib import Path
from services.validation.legacy_revalidation_service import LegacyRevalidationService
from services.engine_version import CURRENT_ENGINE_VERSION


def test_revalidation_service_initialization():
    service = LegacyRevalidationService()
    assert service.db_path.exists()
    assert service.data_dir.exists()


def test_find_dataset_file():
    service = LegacyRevalidationService()
    # Test locating real dataset for BTC or ETH or CL or NQ
    ds_btc = service.find_dataset_file("BTC-USDT", "1h")
    assert ds_btc is not None
    assert ds_btc.exists()

    ds_cl = service.find_dataset_file("CL", "1h")
    assert ds_cl is not None
    assert ds_cl.exists()


def test_revalidate_single_candidate_execution():
    service = LegacyRevalidationService()
    # Revalidate one of the candidates in database
    res = service.revalidate_single_candidate("UR_ULTRA_BTC_USDT_1H")
    assert "candidate_id" in res
    assert "passed" in res
    assert "gates_passed" in res
    assert res["candidate_id"].lower() == "ur_ultra_btc_usdt_1h"


def test_revalidate_legacy_batch_endpoint_structure():
    service = LegacyRevalidationService()
    res = service.revalidate_legacy_batch(target_version="1.02", only_approved=True, max_candidates=2)
    assert res["status"] == "COMPLETED"
    assert res["target_engine_version"] == CURRENT_ENGINE_VERSION
    assert "total_evaluated" in res
    assert "promoted_count" in res
    assert "rejected_count" in res
