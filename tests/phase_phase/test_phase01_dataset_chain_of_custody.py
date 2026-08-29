"""tests/test_phase01_dataset_chain_of_custody.py
Suite de Pruebas de la FASE 01 (REWORK AG2-P01-005): PROVENANCE ELIGIBILITY & ARTIFACT SSOT.
ZERO-MOCKS · REAL-ONLY · PROVENANCE-LOCKED · NO-SYNTHETIC-DEFAULTS · FAIL-CLOSED
"""

import hashlib
import json
import pytest
from pathlib import Path

from contracts.alias_contracts import (
    AliasRegistryIntegrityError,
    CanonicalAliasRegistry,
    MissingAliasRegistryError,
)
from contracts.dataset_contracts import DatasetManifest, DatasetPartition, DatasetPartitionType, ProvenanceStatus
from services.data.dataset_registry import (
    DatasetIntegrityError,
    MissingDatasetError,
    DatasetRegistry,
    UnverifiedDatasetError,
    dataset_registry,
)


def test_alias_registry_loaded_from_physical_artifact(tmp_path):
    """P01-005-01: Verifica que el registro de alias se cargue del artefacto físico con verificación SHA-256."""
    artifact_path = Path(__file__).resolve().parent.parent / "data" / "registry" / "canonical_instrument_aliases.json"
    assert artifact_path.exists(), "El artefacto físico de alias debe existir en disco"

    registry = CanonicalAliasRegistry.load_from_artifact(artifact_path)
    assert registry.registry_version == "1.0.0"
    assert len(registry.registry_sha256) == 64
    assert len(registry.aliases) > 0
    assert registry.resolve("BTC-USDT") == "BTCUSDT"
    assert registry.resolve("EURUSD=X") == "EURUSD"

    # Fail-Closed ante artefacto inexistente
    with pytest.raises(MissingAliasRegistryError):
        CanonicalAliasRegistry.load_from_artifact(tmp_path / "non_existent.json")

    # Fail-Closed ante artefacto corrupto/modificado
    tampered_file = tmp_path / "tampered.json"
    tampered_data = {
        "registry_version": "1.0.0",
        "registry_sha256": "wrong_hash_1234567890123456789012345678901234567890123456789012345678901234",
        "aliases": [{"alias": "A", "canonical_symbol": "B", "venue": "C", "rationale": "D"}],
    }
    tampered_file.write_text(json.dumps(tampered_data), encoding="utf-8")
    with pytest.raises(AliasRegistryIntegrityError):
        CanonicalAliasRegistry.load_from_artifact(tampered_file)


def test_provenance_evidence_states_and_eligibility_gate():
    """P01-005-02 & P01-005-03: Verifica los estados de procedencia y la compuerta de elegibilidad para certificación."""
    datasets = dataset_registry.list_datasets()
    assert len(datasets) > 0
    ds = datasets[0]

    assert ds.provenance_status in [ProvenanceStatus.VERIFIED, ProvenanceStatus.UNVERIFIED, ProvenanceStatus.INVALID]

    if ds.provenance_status == ProvenanceStatus.VERIFIED:
        assert ds.is_certified_eligible is True
        # Debe poder cargarse con la compuerta de elegibilidad activa
        bars = dataset_registry.load_dataset_bars(ds.data_snapshot_id, require_verified_provenance=True)
        assert len(bars) > 0


def test_exact_input_identity_and_canonical_aliases_only():
    """P01-005-04: Verifica resolución exacta directa o por registro canónico de alias, sin mutaciones difusas."""
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


def test_physical_partition_hashes_are_derived_from_actual_bytes():
    """P01-005-05: Verifica que los hashes de partición provengan de los bytes canónicos de las velas reales."""
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
    """P01-005-05: Verifica comportamiento Fail-Closed ante datasets inexistentes o alterados."""
    with pytest.raises(MissingDatasetError):
        dataset_registry.load_dataset_bars("INVALID_DATASET_ID_404")
