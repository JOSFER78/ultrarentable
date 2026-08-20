"""tests/test_data_integrity_and_isolation.py
Pruebas de Integridad de Datos Físicos y Aislamiento de Holdout (Fase 4).
"""

import json
import pytest
from services.data.dataset_integrity_validator import DatasetIntegrityValidator
from services.data.holdout_partitioner import HoldoutPartitioner, BlindHoldoutAccessViolation


@pytest.fixture
def real_sui_candles():
    sample_file = "/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/normalized/ds_binance_suiusdt_1h_1695290400000_1787086800000.json"
    with open(sample_file, "r") as f:
        return json.load(f)


def test_real_dataset_passes_physical_integrity(real_sui_candles):
    """Verify that real normalized dataset satisfies all OHLC and ordering invariants."""
    validator = DatasetIntegrityValidator()
    report = validator.validate_candles(real_sui_candles, filename="ds_sui_1h")
    assert report.passed is True
    assert report.total_bars == len(real_sui_candles)
    assert report.has_duplicates is False
    assert report.has_ohlc_inconsistencies is False
    assert report.is_ordered is True


def test_corrupt_ohlc_is_strictly_rejected():
    """Verify that inverted High < Low or invalid prices fail integrity checks."""
    corrupt_candles = [
        {"time": 1000, "open": 10.0, "high": 9.0, "low": 11.0, "close": 10.0},  # High < Low
    ] * 60
    validator = DatasetIntegrityValidator()
    report = validator.validate_candles(corrupt_candles, filename="ds_corrupt")
    assert report.passed is False
    assert report.has_ohlc_inconsistencies is True


def test_holdout_partition_60_20_20(real_sui_candles):
    """Verify 60% IS, 20% WFO and 20% Blind Holdout split."""
    partitioner = HoldoutPartitioner()
    part = partitioner.partition(real_sui_candles, "ds_sui_1h", "SUIUSDT", "1h")
    
    total = len(real_sui_candles)
    assert part.is_bars_count == int(total * 0.60)
    assert part.wfo_bars_count == int(total * 0.20)
    assert part.blind_oos_bars_count == total - (part.is_bars_count + part.wfo_bars_count)
    assert len(part.is_data) + len(part.wfo_data) + len(part.blind_oos_data) == total


def test_discovery_blocked_from_blind_oos():
    """Verify that any discovery module attempting to read blind holdout is blocked with exception."""
    with pytest.raises(BlindHoldoutAccessViolation) as exc:
        HoldoutPartitioner.assert_discovery_cannot_read_holdout(
            caller_module="services.discovery.ultra_discovery",
            requested_partition="blind_oos",
        )
    assert "CONTAMINACION_BLIND_HOLDOUT_DETECTADA" in str(exc.value)
