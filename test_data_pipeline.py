"""tests/test_data_pipeline.py
Suite de pruebas para el Pipeline de Datos, DatasetRepository, MarketDataAuditor y MarketDataIngestor.
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import pytest

from contracts.backtest import BarData, DatasetSnapshot
from services.data.dataset_repository import DatasetRepository
from services.data.market_ingestor import IngestionAuditReport, MarketDataAuditor, MarketDataIngestor


def test_dataset_repository_load_and_partitioning():
    """Valida que DatasetRepository cargue series y aplique partición IS/OOS determinista."""
    repo = DatasetRepository()
    snapshot_is = repo.get_snapshot("ETH-USDT", "1h", is_in_sample=True, split_ratio=0.7)
    snapshot_oos = repo.get_snapshot("ETH-USDT", "1h", is_in_sample=False, split_ratio=0.7)

    assert isinstance(snapshot_is, DatasetSnapshot)
    assert isinstance(snapshot_oos, DatasetSnapshot)
    assert snapshot_is.is_in_sample is True
    assert snapshot_oos.is_in_sample is False
    assert snapshot_is.sha256_hash != snapshot_oos.sha256_hash
    assert len(snapshot_is.sha256_hash) == 64
    assert len(snapshot_oos.sha256_hash) == 64


def test_market_data_auditor_detects_duplicates_and_sorts():
    """Valida que el auditor elimine duplicados y ordene velas fuera de secuencia."""
    t0 = 1771718400000
    # Velas con desorden y un duplicado
    bars = [
        BarData(timestamp_utc_ms=t0 + 7200000, open=102, high=103, low=101, close=102, volume=10),
        BarData(timestamp_utc_ms=t0, open=100, high=101, low=99, close=100, volume=10),
        BarData(timestamp_utc_ms=t0 + 3600000, open=101, high=102, low=100, close=101, volume=10),
        BarData(timestamp_utc_ms=t0 + 3600000, open=101, high=102, low=100, close=101, volume=10), # DUPLICADO
    ]

    clean_bars, report = MarketDataAuditor.audit(bars, venue="BINGX", symbol="ETH-USDT", interval="1h")

    assert len(clean_bars) == 3
    assert report.duplicate_count == 1
    assert report.out_of_order_count >= 1
    assert report.gap_count == 0
    assert clean_bars[0].timestamp_utc_ms == t0
    assert clean_bars[1].timestamp_utc_ms == t0 + 3600000
    assert clean_bars[2].timestamp_utc_ms == t0 + 7200000


def test_market_data_auditor_detects_gaps():
    """Valida el cálculo de gaps temporales y porcentaje de cobertura."""
    t0 = 1771718400000
    # Falta la vela de t0 + 3600000
    bars = [
        BarData(timestamp_utc_ms=t0, open=100, high=101, low=99, close=100, volume=10),
        BarData(timestamp_utc_ms=t0 + 7200000, open=102, high=103, low=101, close=102, volume=10),
    ]

    clean_bars, report = MarketDataAuditor.audit(bars, venue="CME", symbol="NQ", interval="1h")

    assert report.gap_count == 1
    assert report.coverage_pct < 100.0
    assert report.is_valid is False


def test_market_data_ingestor_persists_json_and_manifest():
    """Valida que el ingestor guarde los archivos JSON y sus manifests criptográficos en disco."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_root = Path(tmp_dir)
        ingestor = MarketDataIngestor(data_root=tmp_root)

        t0 = 1771718400000
        bars = [
            BarData(timestamp_utc_ms=t0 + (i * 3600000), open=100 + i, high=105 + i, low=95 + i, close=102 + i, volume=50)
            for i in range(10)
        ]

        report = ingestor.persist_normalized_dataset(bars, venue="BINGX", symbol="SOL-USDT", interval="1h")

        assert report.record_count == 10
        assert report.gap_count == 0
        assert report.is_valid is True

        data_file = tmp_root / "normalized" / f"{report.dataset_id}.json"
        manifest_file = tmp_root / "normalized" / f"{report.dataset_id}_manifest.json"

        assert data_file.exists()
        assert manifest_file.exists()

        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)
            assert manifest["datasetId"] == report.dataset_id
            assert manifest["checksumSha256"] == report.checksum_sha256
            assert manifest["recordCount"] == 10
            assert manifest["coveragePct"] == 100.0
