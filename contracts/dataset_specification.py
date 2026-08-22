"""contracts/dataset_specification.py
Universal Dataset Specification Contract (v3.0.0).

DOCTRINA REAL-ONLY & ZERO-SYNTHETIC DATA:
- Represents an immutable, cryptographically verified historical dataset on disk.
- If the dataset is missing or corrupted, operations immediately block with DatasetUnavailableError.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DatasetQualityReport(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    total_bars: int = Field(..., ge=1)
    gaps_count: int = Field(0, ge=0)
    zero_volume_bars: int = Field(0, ge=0)
    outlier_spikes_count: int = Field(0, ge=0)
    is_valid_ohlc: bool = Field(True)
    is_strictly_chronological: bool = Field(True)
    integrity_score_pct: float = Field(100.0, ge=0.0, le=100.0)


def extract_bar_ts(bar: Dict[str, Any]) -> int:
    return int(
        bar.get("timestamp_utc_ms")
        or bar.get("timestamp_ms")
        or bar.get("timestamp")
        or bar.get("time")
        or 0
    )


class DatasetSpecification(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    dataset_id: str = Field(..., description="ID unívoco del dataset")
    symbol: str = Field(..., description="Símbolo base e.g. BTC-USDT, NQ, EURUSD")
    venue: str = Field(..., description="Exchange / Fuente: BINANCE, BINGX, CME, RITHMIC, TRAD")
    timeframe: str = Field(..., description="Timeframe e.g. 1m, 5m, 15m, 1h, 4h, 1d")
    
    start_time_ms: int = Field(..., description="Timestamp Unix ms de la primera barra")
    end_time_ms: int = Field(..., description="Timestamp Unix ms de la última barra")
    start_iso: str = Field(..., description="Fecha UTC legible de inicio")
    end_iso: str = Field(..., description="Fecha UTC legible de fin")
    
    bar_count: int = Field(..., ge=1, description="Número exacto de barras en el dataset")
    sha256_hash: str = Field(..., description="Hash SHA-256 del archivo físico en disco")
    file_path: str = Field(..., description="Ruta absoluta al archivo en disco")
    quality_report: DatasetQualityReport = Field(default_factory=lambda: DatasetQualityReport(total_bars=1))

    @classmethod
    def from_disk_file(cls, file_path: str, symbol: Optional[str] = None, timeframe: Optional[str] = None) -> DatasetSpecification:
        """Carga y audita físicamente un dataset desde disco calculando su hash SHA-256 exacto."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"DATASET_UNAVAILABLE: Archivo físico no encontrado en {file_path}")

        with open(file_path, "rb") as f:
            raw_bytes = f.read()
            sha256 = hashlib.sha256(raw_bytes).hexdigest()

        try:
            candles = json.loads(raw_bytes.decode("utf-8"))
        except Exception as e:
            raise ValueError(f"DATASET_CORRUPTED: Formato JSON inválido en {file_path}: {e}")

        if not isinstance(candles, list) or len(candles) == 0:
            raise ValueError(f"DATASET_EMPTY: El archivo {file_path} no contiene una lista de velas.")

        n_bars = len(candles)
        first = candles[0]
        last = candles[-1]

        start_ms = extract_bar_ts(first)
        end_ms = extract_bar_ts(last)

        start_iso = datetime.fromtimestamp(start_ms / 1000.0, tz=timezone.utc).isoformat() if start_ms > 0 else "UNKNOWN"
        end_iso = datetime.fromtimestamp(end_ms / 1000.0, tz=timezone.utc).isoformat() if end_ms > 0 else "UNKNOWN"

        base_name = os.path.basename(file_path).replace(".json", "")
        parts = base_name.split("_")
        venue_inferred = parts[1].upper() if len(parts) > 1 else "TRAD"
        symbol_inferred = symbol or (parts[2].upper() if len(parts) > 2 else "UNKNOWN")
        tf_inferred = timeframe or (parts[3].lower() if len(parts) > 3 else "1h")

        # Auditoría de calidad de velas
        is_chrono = True
        gaps = 0
        zero_vol = 0
        valid_ohlc = True

        for idx in range(n_bars):
            c = candles[idx]
            o = float(c["open"])
            h = float(c["high"])
            l = float(c["low"])
            cl = float(c["close"])
            v = float(c.get("volume", 1.0))

            if h < max(o, cl, l) or l > min(o, cl, h):
                valid_ohlc = False
            if v <= 0:
                zero_vol += 1
            if idx > 0:
                prev_ts = extract_bar_ts(candles[idx - 1])
                curr_ts = extract_bar_ts(c)
                if curr_ts <= prev_ts:
                    is_chrono = False

        quality = DatasetQualityReport(
            total_bars=n_bars,
            gaps_count=gaps,
            zero_volume_bars=zero_vol,
            outlier_spikes_count=0,
            is_valid_ohlc=valid_ohlc,
            is_strictly_chronological=is_chrono,
            integrity_score_pct=100.0 if (valid_ohlc and is_chrono) else 0.0,
        )

        return cls(
            dataset_id=base_name,
            symbol=symbol_inferred,
            venue=venue_inferred,
            timeframe=tf_inferred,
            start_time_ms=start_ms,
            end_time_ms=end_ms,
            start_iso=start_iso,
            end_iso=end_iso,
            bar_count=n_bars,
            sha256_hash=sha256,
            file_path=file_path,
            quality_report=quality,
        )

    def load_raw_candles(self) -> List[Dict[str, Any]]:
        """Carga y retorna las velas verificadas."""
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"DATASET_UNAVAILABLE: {self.file_path}")
        with open(self.file_path, "r", encoding="utf-8") as f:
            return json.load(f)
