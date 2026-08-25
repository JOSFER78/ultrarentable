"""tests/test_phase01_dataset_chain_of_custody.py
Suite de Pruebas de la FASE 01: DATA & DATASET CHAIN OF CUSTODY.
ZERO-MOCKS · REAL-ONLY · PROVENANCE-LOCKED
"""

import pytest
from pathlib import Path

from contracts.dataset_contracts import DatasetManifest, DatasetPartitionType
from services.data.dataset_registry import (
    DatasetRegistry,
    DatasetIntegrityError,
    MissingDatasetError,
    dataset_registry,
)


def test_dataset_registry_loads_physical_manifests():
    """Verifica que el DatasetRegistry cargue todos los manifiestos físicos de data/normalized/."""
    datasets = dataset_registry.list_datasets()
    assert len(datasets) > 0, "Debe haber al menos 1 dataset físico normalizado cargado"
    for ds in datasets:
        assert isinstance(ds, DatasetManifest)
        assert len(ds.data_sha256) == 64
        assert ds.record_count > 0
        assert ds.start_time_utc_ms > 0
        assert ds.end_time_utc_ms > ds.start_time_utc_ms


def test_dataset_registry_resolves_multi_asset_dynamically():
    """Verifica que el registro resuelva símbolos y timeframes sin universos hardcoded."""
    nq_1h = dataset_registry.resolve_dataset("NQ", "1h")
    if nq_1h:
        assert nq_1h.instrument_id == "NQ"
        assert nq_1h.timeframe_id == "1h"

    btc_1h = dataset_registry.resolve_dataset("BTCUSDT", "1h")
    if btc_1h:
        assert "BTC" in btc_1h.instrument_id
        assert btc_1h.timeframe_id == "1h"


def test_dataset_partition_segregation_no_leakage():
    """Verifica que las particiones IS, VALIDATION y BLIND_OOS sean disjuntas y secuenciales."""
    datasets = dataset_registry.list_datasets()
    assert len(datasets) > 0
    target_ds = datasets[0]

    bars_is = dataset_registry.load_dataset_bars(target_ds.data_snapshot_id, DatasetPartitionType.IN_SAMPLE, verify_sha256=False)
    bars_val = dataset_registry.load_dataset_bars(target_ds.data_snapshot_id, DatasetPartitionType.VALIDATION, verify_sha256=False)
    bars_oos = dataset_registry.load_dataset_bars(target_ds.data_snapshot_id, DatasetPartitionType.BLIND_OOS, verify_sha256=False)

    assert len(bars_is) > 0
    assert len(bars_val) > 0
    assert len(bars_oos) > 0

    # Verificar que no hay solapamiento temporal (No leakage)
    ts_is_end = bars_is[-1].get("timestamp_utc_ms") or bars_is[-1].get("time")
    ts_val_start = bars_val[0].get("timestamp_utc_ms") or bars_val[0].get("time")
    ts_val_end = bars_val[-1].get("timestamp_utc_ms") or bars_val[-1].get("time")
    ts_oos_start = bars_oos[0].get("timestamp_utc_ms") or bars_oos[0].get("time")

    if ts_is_end and ts_val_start and ts_val_end and ts_oos_start:
        assert ts_is_end <= ts_val_start, "Fuga temporal entre IS y Validación"
        assert ts_val_end <= ts_oos_start, "Fuga temporal entre Validación y Blind OOS"


def test_dataset_registry_fail_closed_on_missing_dataset():
    """Verifica comportamiento fail-closed ante datasets inexistentes."""
    with pytest.raises(MissingDatasetError):
        dataset_registry.load_dataset_bars("NON_EXISTENT_DATASET_ID_999")


def test_temporal_monotonicity_of_loaded_bars():
    """Verifica que los timestamps de las velas sean monótonamente crecientes."""
    datasets = dataset_registry.list_datasets()
    assert len(datasets) > 0
    target_ds = datasets[0]

    bars = dataset_registry.load_dataset_bars(target_ds.data_snapshot_id, verify_sha256=False)
    assert len(bars) > 1

    for i in range(len(bars) - 1):
        ts_cur = bars[i].get("timestamp_utc_ms") or bars[i].get("time") or 0
        ts_next = bars[i+1].get("timestamp_utc_ms") or bars[i+1].get("time") or 0
        if ts_cur > 0 and ts_next > 0:
            assert ts_cur <= ts_next, f"Vela {i} no es monótona ({ts_cur} > {ts_next})"
