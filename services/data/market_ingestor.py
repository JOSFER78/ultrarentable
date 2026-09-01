"""services/data/market_ingestor.py
Ingestor multi-venue de datos reales (BingX USD-M Perpetuals y CME Futures) con auditoría estricta de calidad.
Detección de gaps, duplicados, velas fuera de orden y generación de manifests con firmas SHA-256.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from contracts.backtest import BarData, DatasetSnapshot
from services.data import session_calendar


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
    session_closure_bars: int = 0
    coverage_pct: float = 100.0
    checksum_sha256: str
    start_time_utc_ms: int
    end_time_utc_ms: int
    is_valid: bool = True
    audit_message: str = "Dataset verificado y conforme a la directiva REAL-ONLY."


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
        """Audita, desduplica, ordena y calcula métricas de integridad sobre una serie de velas."""
        if not bars:
            raise ValueError("No se pueden auditar series vacías de datos.")

        interval_ms = cls.INTERVAL_MS_MAP.get(interval, 3_600_000)

        # 1. Detección de fuera de orden y ordenación
        is_sorted = all(bars[i].timestamp_utc_ms <= bars[i + 1].timestamp_utc_ms for i in range(len(bars) - 1))
        out_of_order_count = 0 if is_sorted else sum(1 for i in range(len(bars) - 1) if bars[i].timestamp_utc_ms > bars[i + 1].timestamp_utc_ms)
        sorted_bars = sorted(bars, key=lambda b: b.timestamp_utc_ms)

        # 2. Detección de duplicados
        unique_bars: List[BarData] = []
        seen_timestamps = set()
        duplicate_count = 0
        for b in sorted_bars:
            if b.timestamp_utc_ms in seen_timestamps:
                duplicate_count += 1
            else:
                seen_timestamps.add(b.timestamp_utc_ms)
                unique_bars.append(b)

        # 3. Conteo de huecos contra el CALENDARIO DE SESION del venue (no 24/7). Cripto
        # (session_calendar.is_24_7_venue) trata cualquier hueco como anomalia real, igual que
        # antes. CME/forex/Dukascopy descuentan pausa diaria, fin de semana y festivo (deducidos
        # por forma del hueco, no por fecha fija) -- ver services/data/session_calendar.py y
        # orchestration/results/desbloqueo_tradfi_calidad_datos.md: medir cobertura contra un
        # calendario 24/7 hacia que un dataset TradFi perfecto (~68.5% techo estructural en CME)
        # se marcara siempre como incompleto.
        gap_count = 0
        session_closure_bars = 0
        for i in range(len(unique_bars) - 1):
            diff = unique_bars[i + 1].timestamp_utc_ms - unique_bars[i].timestamp_utc_ms
            if diff > interval_ms:
                missing_bars = max(0, (diff // interval_ms) - 1)
                gap_type, _hours = session_calendar.classify_gap(
                    venue, unique_bars[i].timestamp_utc_ms, unique_bars[i + 1].timestamp_utc_ms
                )
                if gap_type == "anomalo":
                    gap_count += missing_bars
                else:
                    session_closure_bars += missing_bars

        start_ts = unique_bars[0].timestamp_utc_ms
        end_ts = unique_bars[-1].timestamp_utc_ms
        expected_records = len(unique_bars) + gap_count
        coverage_pct = round((len(unique_bars) / max(1, expected_records)) * 100.0, 2)

        # 4. Checksum SHA-256 determinista
        payload = f"{venue}:{symbol}:{interval}:{len(unique_bars)}:{start_ts}:{end_ts}"
        sha_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

        dataset_id = f"ds_{venue.lower()}_{symbol.lower().replace('-', '_')}_{interval}_{start_ts}_{end_ts}_{sha_hash[:10]}"

        report = IngestionAuditReport(
            dataset_id=dataset_id,
            venue=venue.upper(),
            symbol=symbol,
            interval=interval,
            record_count=len(unique_bars),
            gap_count=gap_count,
            duplicate_count=duplicate_count,
            out_of_order_count=out_of_order_count,
            session_closure_bars=session_closure_bars,
            coverage_pct=min(100.0, coverage_pct),
            checksum_sha256=sha_hash,
            start_time_utc_ms=start_ts,
            end_time_utc_ms=end_ts,
            is_valid=(gap_count == 0 and duplicate_count == 0),
        )

        return unique_bars, report


class MarketDataIngestor:
    """Servicio de persistencia y normalización de datos de mercado."""

    def __init__(self, data_root: Optional[Path] = None) -> None:
        self.data_root = data_root or Path(__file__).resolve().parent.parent.parent / "data"
        self.normalized_dir = self.data_root / "normalized"
        self.normalized_dir.mkdir(parents=True, exist_ok=True)

    def persist_normalized_dataset(
        self,
        bars: List[BarData],
        venue: str,
        symbol: str,
        interval: str,
    ) -> IngestionAuditReport:
        """Audita y guarda el archivo JSON de velas y su manifest criptográfico correspondiente."""
        clean_bars, report = MarketDataAuditor.audit(bars, venue, symbol, interval)

        # Serialización de velas
        raw_list = [
            {
                "timestamp": b.timestamp_utc_ms,
                "open": b.open,
                "high": b.high,
                "low": b.low,
                "close": b.close,
                "volume": b.volume,
            }
            for b in clean_bars
        ]

        data_filename = f"{report.dataset_id}.json"
        manifest_filename = f"{report.dataset_id}_manifest.json"

        data_path = self.normalized_dir / data_filename
        manifest_path = self.normalized_dir / manifest_filename

        with open(data_path, "w", encoding="utf-8") as f:
            json.dump(raw_list, f, separators=(",", ":"))

        manifest_data = {
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
            "sessionClosureBars": report.session_closure_bars,
            "coveragePct": report.coverage_pct,
            "checksumSha256": report.checksum_sha256,
            "normalizedPath": f"normalized/{data_filename}",
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)

        return report
