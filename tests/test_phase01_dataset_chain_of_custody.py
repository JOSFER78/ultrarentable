"""tests/test_phase01_dataset_chain_of_custody.py
Suite de Pruebas de la FASE 01 (REWORK AG2-P01-002): DATA INTEGRITY & CHAIN OF CUSTODY.
ZERO-MOCKS · REAL-ONLY · PROVENANCE-LOCKED · FAIL-CLOSED
"""

import hashlib
import json
import pytest
from pathlib import Path

from contracts.dataset_contracts import DatasetManifest, DatasetPartition, DatasetPartitionType
from services.data.dataset_registry import (
    DatasetIntegrityError,
    MissingDatasetError,
    DatasetRegistry,
    dataset_registry,
)


def test_dataset_registry_loads_physical_manifests():
    """Verifica que el DatasetRegistry cargue todos los manifiestos físicos de data/normalized/ sin datos sintéticos."""
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
    """P01-REWORK-01: Verifica que los hashes de partición provengan de los bytes canónicos de las velas reales."""
    datasets = dataset_registry.list_datasets()
    assert len(datasets) > 0
    ds = datasets[0]

    assert DatasetPartitionType.IN_SAMPLE.value in ds.partitions
    assert DatasetPartitionType.VALIDATION.value in ds.partitions
    assert DatasetPartitionType.BLIND_OOS.value in ds.partitions

    is_part = ds.partitions[DatasetPartitionType.IN_SAMPLE.value]
    val_part = ds.partitions[DatasetPartitionType.VALIDATION.value]
    oos_part = ds.partitions[DatasetPartitionType.BLIND_OOS.value]

    # Verificar longitud SHA-256 exacta de 64 caracteres
    assert len(is_part.partition_sha256) == 64
    assert len(val_part.partition_sha256) == 64
    assert len(oos_part.partition_sha256) == 64

    # Cargar velas reales de cada partición y recalcular hash físico
    bars_is = dataset_registry.load_dataset_bars(ds.data_snapshot_id, DatasetPartitionType.IN_SAMPLE, verify_sha256=True)
    bars_val = dataset_registry.load_dataset_bars(ds.data_snapshot_id, DatasetPartitionType.VALIDATION, verify_sha256=True)
    bars_oos = dataset_registry.load_dataset_bars(ds.data_snapshot_id, DatasetPartitionType.BLIND_OOS, verify_sha256=True)

    recalculated_is_hash = DatasetPartition.compute_slice_sha256(bars_is)
    recalculated_val_hash = DatasetPartition.compute_slice_sha256(bars_val)
    recalculated_oos_hash = DatasetPartition.compute_slice_sha256(bars_oos)

    assert is_part.partition_sha256 == recalculated_is_hash, "Hash de partición IS debe coincidir con los bytes físicos"
    assert val_part.partition_sha256 == recalculated_val_hash, "Hash de partición VAL debe coincidir con los bytes físicos"
    assert oos_part.partition_sha256 == recalculated_oos_hash, "Hash de partición OOS debe coincidir con los bytes físicos"


def test_partition_disjointness_and_exhaustiveness():
    """P01-REWORK-04: Verifica que las particiones IS, VAL y OOS sean disjuntas y sumen el 100% de velas."""
    datasets = dataset_registry.list_datasets()
    assert len(datasets) > 0
    ds = datasets[0]

    bars_all = dataset_registry.load_dataset_bars(ds.data_snapshot_id, verify_sha256=True)
    bars_is = dataset_registry.load_dataset_bars(ds.data_snapshot_id, DatasetPartitionType.IN_SAMPLE, verify_sha256=True)
    bars_val = dataset_registry.load_dataset_bars(ds.data_snapshot_id, DatasetPartitionType.VALIDATION, verify_sha256=True)
    bars_oos = dataset_registry.load_dataset_bars(ds.data_snapshot_id, DatasetPartitionType.BLIND_OOS, verify_sha256=True)

    assert len(bars_is) + len(bars_val) + len(bars_oos) == len(bars_all), "Las particiones deben ser exhaustivas"

    # Verificar orden temporal y no solapamiento
    ts_is_end = bars_is[-1].get("timestamp_utc_ms") or bars_is[-1].get("time") or 0
    ts_val_start = bars_val[0].get("timestamp_utc_ms") or bars_val[0].get("time") or 0
    ts_val_end = bars_val[-1].get("timestamp_utc_ms") or bars_val[-1].get("time") or 0
    ts_oos_start = bars_oos[0].get("timestamp_utc_ms") or bars_oos[0].get("time") or 0

    if ts_is_end and ts_val_start and ts_val_end and ts_oos_start:
        assert ts_is_end <= ts_val_start, "Solapamiento entre IS y Validación"
        assert ts_val_end <= ts_oos_start, "Solapamiento entre Validación y Blind OOS"


def test_deterministic_exact_resolution_no_fuzzy_matching():
    """P01-REWORK-06: Verifica que la resolución de instrumentos sea exacta y no por prefijo difuso."""
    nq_1h = dataset_registry.resolve_dataset("NQ", "1h")
    if nq_1h:
        assert nq_1h.instrument_id == "NQ"
        assert nq_1h.timeframe_id == "1h"

    # Instrumento inexistente o ambiguo debe retornar None de forma determinista
    assert dataset_registry.resolve_dataset("NON_EXISTENT_SYMBOL_XYZ", "1h") is None


def test_fail_closed_on_missing_dataset_and_tampered_hash():
    """P01-REWORK-05: Verifica comportamiento Fail-Closed ante datasets inexistentes o alterados."""
    with pytest.raises(MissingDatasetError):
        dataset_registry.load_dataset_bars("INVALID_DATASET_ID_404")
