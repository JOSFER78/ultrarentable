"""Real market-data ingestion and forensic auditing.

This module only persists bars supplied by an external market-data source.
It does not synthesize or repair missing candles. Invalid coverage is quarantined
by the audit result instead of being silently filled.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel

from contracts.backtest import BarData
from services.api.app.config import DATA_DIR as BASE_DATA_DIR


class IngestionAuditReport(BaseModel):
    """Informe cuantitativo de calidad e integridad de datos."""

    dataset_id: str
    venue: str
    symbol: str
    interval: str
    record_count: int
    gap_count: int = 0
    duplicate_count: int = 0
    out_of_order_count: int = 0
    coverage_pct: float = 100.0
    checksum_sha256: str
    start_time_utc_ms: int
    end_time_utc_ms: int
    is_valid: bool = True
    audit_message: str = "Dataset verificado y conforme a REAL-ONLY."


class MarketDataAuditor:
    """Auditor determinista de series temporales de velas financieras."""

    INTERVAL_MS_MAP: Dict[str, int] = {
        "1m": 60_000,
        "5m": 300_000,
        "15m": 900_000,
        "1h": 3_600_000,
        "4h": 14_400_000,
        "1d": 86_400_000,
    }

    @classmethod
    def audit(
        cls,
        bars: List[BarData],
        venue: str,
        symbol: str,
        interval: str,
    ) -> Tuple[List[BarData], IngestionAuditReport]:
        if not bars:
            raise ValueError("No se pueden auditar series vacías de datos.")
        if interval not in cls.INTERVAL_MS_MAP:
            raise ValueError(f"Unsupported market-data interval: {interval}")

        interval_ms = cls.INTERVAL_MS_MAP[interval]
        sorted_bars = sorted(bars, key=lambda bar: bar.timestamp_utc_ms)
        out_of_order_count = sum(
            1
            for i in range(len(bars) - 1)
            if bars[i].timestamp_utc_ms > bars[i + 1].timestamp_utc_ms
        )

        unique_bars: List[BarData] = []
        seen_timestamps = set()
        duplicate_count = 0
        for bar in sorted_bars:
            if bar.timestamp_utc_ms in seen_timestamps:
                duplicate_count += 1
                continue
            seen_timestamps.add(bar.timestamp_utc_ms)
            unique_bars.append(bar)

        for index, bar in enumerate(unique_bars):
            if bar.timestamp_utc_ms <= 0:
                raise ValueError(f"Invalid non-positive timestamp at index {index}")
            if min(bar.open, bar.high, bar.low, bar.close) <= 0:
                raise ValueError(f"Invalid non-positive OHLC at index {index}")
            if bar.high < max(bar.open, bar.close) or bar.low > min(bar.open, bar.close):
                raise ValueError(f"Invalid OHLC envelope at index {index}")

        gap_count = 0
        for index in range(len(unique_bars) - 1):
            diff = unique_bars[index + 1].timestamp_utc_ms - unique_bars[index].timestamp_utc_ms
            if diff > interval_ms:
                gap_count += max(0, (diff // interval_ms) - 1)

        start_ts = unique_bars[0].timestamp_utc_ms
        end_ts = unique_bars[-1].timestamp_utc_ms
        expected_records = ((end_ts - start_ts) // interval_ms) + 1
        coverage_pct = min(100.0, round(len(unique_bars) / max(1, expected_records) * 100.0, 2))

        canonical_payload = [
            [
                bar.timestamp_utc_ms,
                bar.open,
                bar.high,
                bar.low,
                bar.close,
                bar.volume,
            ]
            for bar in unique_bars
        ]
        checksum = hashlib.sha256(
            json.dumps(canonical_payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        dataset_id = (
            f"ds_{venue.lower()}_{symbol.lower().replace('-', '_')}_{interval}_"
            f"{start_ts}_{end_ts}_{checksum[:12]}"
        )

        valid = gap_count == 0 and duplicate_count == 0 and out_of_order_count == 0
        message = (
            "Dataset verificado y conforme a REAL-ONLY."
            if valid
            else "Dataset rechazado para investigación: gaps/duplicados/orden temporal detectados."
        )
        report = IngestionAuditReport(
            dataset_id=dataset_id,
            venue=venue.upper(),
            symbol=symbol,
            interval=interval,
            record_count=len(unique_bars),
            gap_count=gap_count,
            duplicate_count=duplicate_count,
            out_of_order_count=out_of_order_count,
            coverage_pct=coverage_pct,
            checksum_sha256=checksum,
            start_time_utc_ms=start_ts,
            end_time_utc_ms=end_ts,
            is_valid=valid,
            audit_message=message,
        )
        return unique_bars, report


class MarketDataIngestor:
    """Persistencia de datasets reales ya obtenidos por una fuente externa."""

    def __init__(self, data_root: Optional[Path] = None) -> None:
        self.data_root = data_root or BASE_DATA_DIR
        self.normalized_dir = self.data_root / "normalized"
        self.normalized_dir.mkdir(parents=True, exist_ok=True)

    def persist_normalized_dataset(
        self,
        bars: List[BarData],
        venue: str,
        symbol: str,
        interval: str,
    ) -> IngestionAuditReport:
        clean_bars, report = MarketDataAuditor.audit(bars, venue, symbol, interval)
        if not report.is_valid:
            raise ValueError(report.audit_message)

        raw_list = [
            {
                "timestamp": bar.timestamp_utc_ms,
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume,
            }
            for bar in clean_bars
        ]

        data_path = self.normalized_dir / f"{report.dataset_id}.json"
        manifest_path = self.normalized_dir / f"{report.dataset_id}_manifest.json"
        with data_path.open("w", encoding="utf-8") as handle:
            json.dump(raw_list, handle, separators=(",", ":"), ensure_ascii=False)

        physical_sha256 = hashlib.sha256(data_path.read_bytes()).hexdigest()
        manifest_data: Dict[str, Any] = {
            "datasetId": report.dataset_id,
            "venue": report.venue,
            "symbol": report.symbol,
            "interval": report.interval,
            "startTime": report.start_time_utc_ms,
            "endTime": report.end_time_utc_ms,
            "recordCount": report.record_count,
            "gapCount": report.gap_count,
            "duplicateCount": report.duplicate_count,
            "outOfOrderCount": report.out_of_order_count,
            "coveragePct": report.coverage_pct,
            "contentChecksumSha256": report.checksum_sha256,
            "physicalFileSha256": physical_sha256,
            "normalizedPath": f"normalized/{data_path.name}",
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }
        with manifest_path.open("w", encoding="utf-8") as handle:
            json.dump(manifest_data, handle, indent=2, ensure_ascii=False)
        return report
