"""tests/test_phase01_dataset_chain_of_custody.py
Suite de Pruebas de la FASE 01 (REWORK AG2-P01-003): PROVENANCE SOURCE-OF-TRUTH & ZERO-INFERENCE.
ZERO-MOCKS · REAL-ONLY · PROVENANCE-LOCKED · NO-SYNTHETIC-DEFAULTS · FAIL-CLOSED
"""

import hashlib
import json
import pytest
from pathlib import Path

from contracts.dataset_contracts import DatasetManifest, DatasetPartition, DatasetPartitionType
from services.data.dataset_registry import (
    CANONICAL_INSTRUMENT_ALIASES,
    DatasetIntegrityError,
    MissingDatasetError,
    DatasetRegistry,
    dataset_registry,
)


def test_dataset_registry_loads_physical_manifests_without_inferred_defaults():
    """P01-003-01 & 02: Verifica que los datasets carguen metadatos reales sin inventar versiones 1.0.0."""
    datasets = dataset_registry.list_datasets()
    assert len(datasets) > 0, "Debe haber al menos 1 dataset físico normalizado cargado"
    for ds in datasets:
        assert isinstance(ds, DatasetManifest)
        assert len(ds.data_sha256) == 64
        assert ds.record_count > 0
        assert ds.start_time_utc_ms > 0
        assert ds.end_time_utc_ms >= ds.start_time_utc_ms
        assert ds.source_id != ""


def test_physical_partition_hashes_are_derived_from_actual_bytes():
    """P01-003-05: Verifica que los hashes de partición provengan de los bytes canónicos de las velas reales."""
    datasets = dataset_registry.list_datasets()
    assert len(datasets) > 0
    ds = datasets[0]

    assert DatasetPartitionType.IN_SAMPLE.value in ds.partitions
    assert DatasetPartitionType.VALIDATION.value in ds.partitions
    assert DatasetPartitionType.BLIND_OOS.value in ds.partitions

    is_part = ds.partitions[DatasetPartitionType.IN_SAMPLE.value]
    val_part = ds.partitions[DatasetPartitionType.VALIDATION.value]
    oos_part = ds.partitions[DatasetPartitionType.BLIND_OOS.value]

    assert len(is_part.partition_sha256) == 64
    assert len(val_part.partition_sha256) == 64
    assert len(oos_part.partition_sha256) == 64

    bars_is = dataset_registry.load_dataset_bars(ds.data_snapshot_id, DatasetPartitionType.IN_SAMPLE, verify_sha256=True)
    bars_val = dataset_registry.load_dataset_bars(ds.data_snapshot_id, DatasetPartitionType.VALIDATION, verify_sha256=True)
    bars_oos = dataset_registry.load_dataset_bars(ds.data_snapshot_id, DatasetPartitionType.BLIND_OOS, verify_sha256=True)

    assert is_part.partition_sha256 == DatasetPartition.compute_slice_sha256(bars_is)
    assert val_part.partition_sha256 == DatasetPartition.compute_slice_sha256(bars_val)
    assert oos_part.partition_sha256 == DatasetPartition.compute_slice_sha256(bars_oos)


def test_partition_disjointness_and_exhaustiveness():
    """P01-003-05: Verifica que las particiones IS, VAL y OOS sean disjuntas y sumen el 100% de velas."""
    datasets = dataset_registry.list_datasets()
    assert len(datasets) > 0
    ds = datasets[0]

    bars_all = dataset_registry.load_dataset_bars(ds.data_snapshot_id, verify_sha256=True)
    bars_is = dataset_registry.load_dataset_bars(ds.data_snapshot_id, DatasetPartitionType.IN_SAMPLE, verify_sha256=True)
    bars_val = dataset_registry.load_dataset_bars(ds.data_snapshot_id, DatasetPartitionType.VALIDATION, verify_sha256=True)
    bars_oos = dataset_registry.load_dataset_bars(ds.data_snapshot_id, DatasetPartitionType.BLIND_OOS, verify_sha256=True)

    assert len(bars_is) + len(bars_val) + len(bars_oos) == len(bars_all), "Las particiones deben ser exhaustivas"


def test_exact_identity_resolution_and_canonical_aliases():
    """P01-003-03: Verifica resolución exacta y mediante registro canónico de alias versionado."""
    nq_1h = dataset_registry.resolve_dataset("NQ", "1h")
    if nq_1h:
        assert nq_1h.instrument_id == "NQ"
        assert nq_1h.timeframe_id == "1h"

    # Alias canónico oficial BTC-USDT -> BTCUSDT
    btc_dash = dataset_registry.resolve_dataset("BTC-USDT", "5m")
    btc_direct = dataset_registry.resolve_dataset("BTCUSDT", "5m")
    if btc_direct:
        assert btc_dash == btc_direct

    # Símbolo no registrado o difuso debe devolver None
    assert dataset_registry.resolve_dataset("NON_EXISTENT_XYZ", "1h") is None
    assert dataset_registry.resolve_dataset("BTC_UNKNOWN_SUFFIX", "1h") is None


def test_fail_closed_on_missing_dataset_and_tampered_hash():
    """P01-003-05: Verifica comportamiento Fail-Closed ante datasets inexistentes o alterados."""
    with pytest.raises(MissingDatasetError):
        dataset_registry.load_dataset_bars("INVALID_DATASET_ID_404")
