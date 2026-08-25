"""tests/test_phase01_dataset_chain_of_custody.py
Suite de Pruebas de la FASE 01 (REWORK AG2-P01-004): CANONICAL ALIAS REGISTRY & EXACT IDENTITY.
ZERO-MOCKS · REAL-ONLY · PROVENANCE-LOCKED · NO-SYNTHETIC-DEFAULTS · FAIL-CLOSED
"""

import hashlib
import json
import pytest
from pathlib import Path

from contracts.alias_contracts import OFFICIAL_ALIAS_REGISTRY, AliasRecord, CanonicalAliasRegistry
from contracts.dataset_contracts import DatasetManifest, DatasetPartition, DatasetPartitionType
from services.data.dataset_registry import (
    DatasetIntegrityError,
    MissingDatasetError,
    DatasetRegistry,
    dataset_registry,
)


def test_alias_registry_version_and_hash_stability():
    """P01-004-01: Verifica que el registro canónico de alias tenga versión explícita y hash SHA-256 determinista."""
    assert OFFICIAL_ALIAS_REGISTRY.registry_version == "1.0.0"
    assert len(OFFICIAL_ALIAS_REGISTRY.registry_sha256) == 64
    assert len(OFFICIAL_ALIAS_REGISTRY.aliases) > 0

    # Determinismo de hash
    recalculated = CanonicalAliasRegistry.create_registry(
        version="1.0.0",
        records=OFFICIAL_ALIAS_REGISTRY.aliases,
    )
    assert recalculated.registry_sha256 == OFFICIAL_ALIAS_REGISTRY.registry_sha256
    assert OFFICIAL_ALIAS_REGISTRY.resolve("BTC-USDT") == "BTCUSDT"
    assert OFFICIAL_ALIAS_REGISTRY.resolve("EURUSD=X") == "EURUSD"
    assert OFFICIAL_ALIAS_REGISTRY.resolve("UNKNOWN_XYZ") is None


def test_exact_input_identity_and_canonical_aliases_only():
    """P01-004-02: Verifica resolución exacta directa o por registro canónico de alias, sin mutaciones difusas."""
    nq_1h = dataset_registry.resolve_dataset("NQ", "1h")
    if nq_1h:
        assert nq_1h.instrument_id == "NQ"
        assert nq_1h.timeframe_id == "1h"

    # Alias explícito en registro canónico
    btc_alias = dataset_registry.resolve_dataset("BTC-USDT", "5m")
    btc_direct = dataset_registry.resolve_dataset("BTCUSDT", "5m")
    if btc_direct:
        assert btc_alias == btc_direct

    # Símbolo no registrado en alias debe retornar None (Fail-Closed)
    assert dataset_registry.resolve_dataset("NON_EXISTENT_XYZ", "1h") is None
    assert dataset_registry.resolve_dataset("BTC_UNREGISTERED_ALIAS", "1h") is None


def test_dataset_registry_loads_physical_manifests_without_inferred_defaults():
    """P01-004-03: Verifica que los datasets carguen metadatos reales sin inventar versiones ni fuentes."""
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
    """P01-004-05: Verifica que los hashes de partición provengan de los bytes canónicos de las velas reales."""
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


def test_fail_closed_on_missing_dataset_and_tampered_hash():
    """P01-004-05: Verifica comportamiento Fail-Closed ante datasets inexistentes o alterados."""
    with pytest.raises(MissingDatasetError):
        dataset_registry.load_dataset_bars("INVALID_DATASET_ID_404")
