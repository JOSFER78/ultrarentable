"""Universal Dataset Specification Contract (v3.0.0).

REAL-ONLY / ZERO-SYNTHETIC DATA:
A dataset is executable only when its physical file, timestamps and OHLC schema
are valid. Missing information is an error, never a value fabricated for convenience.
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
    """Return a real bar timestamp; never synthesize a zero timestamp."""
    for key in ("timestamp_utc_ms", "timestamp_ms", "timestamp", "time"):
        value = bar.get(key)
        if value is not None:
            try:
                timestamp = int(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"INVALID_TIMESTAMP: {key}={value!r}") from exc
            if timestamp <= 0:
                raise ValueError(f"INVALID_TIMESTAMP: non-positive timestamp {timestamp}")
            return timestamp
    raise ValueError("MISSING_TIMESTAMP: physical market data bar has no timestamp field")


class DatasetSpecification(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    dataset_id: str = Field(...)
    symbol: str = Field(...)
    venue: str = Field(...)
    timeframe: str = Field(...)
    start_time_ms: int = Field(..., gt=0)
    end_time_ms: int = Field(..., gt=0)
    start_iso: str = Field(...)
    end_iso: str = Field(...)
    bar_count: int = Field(..., ge=1)
    sha256_hash: str = Field(..., min_length=64, max_length=64)
    file_path: str = Field(...)
    quality_report: DatasetQualityReport

    @classmethod
    def from_disk_file(
        cls,
        file_path: str,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None,
    ) -> "DatasetSpecification":
        """Load and physically audit a dataset from disk."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"DATASET_UNAVAILABLE: Archivo físico no encontrado en {file_path}")

        with open(file_path, "rb") as f:
            raw_bytes = f.read()
            sha256 = hashlib.sha256(raw_bytes).hexdigest()

        try:
            candles = json.loads(raw_bytes.decode("utf-8"))
        except Exception as exc:
            raise ValueError(f"DATASET_CORRUPTED: Formato JSON inválido en {file_path}: {exc}") from exc

        if not isinstance(candles, list) or len(candles) == 0:
            raise ValueError(f"DATASET_EMPTY: El archivo {file_path} no contiene una lista de velas.")

        n_bars = len(candles)
        start_ms = extract_bar_ts(candles[0])
        end_ms = extract_bar_ts(candles[-1])
        if end_ms <= start_ms:
            raise ValueError(f"INVALID_TIME_RANGE: end={end_ms} <= start={start_ms}")

        start_iso = datetime.fromtimestamp(start_ms / 1000.0, tz=timezone.utc).isoformat()
        end_iso = datetime.fromtimestamp(end_ms / 1000.0, tz=timezone.utc).isoformat()

        base_name = os.path.basename(file_path).replace(".json", "")
        parts = base_name.split("_")
        venue_inferred = parts[1].upper() if len(parts) > 1 else "UNKNOWN"
        symbol_inferred = symbol or (parts[2].upper() if len(parts) > 2 else "UNKNOWN")
        tf_inferred = timeframe or (parts[3].lower() if len(parts) > 3 else "UNKNOWN")

        is_chrono = True
        zero_vol = 0
        valid_ohlc = True

        for idx, candle in enumerate(candles):
            try:
                o = float(candle["open"])
                h = float(candle["high"])
                l = float(candle["low"])
                cl = float(candle["close"])
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"INVALID_OHLC: bar_index={idx}") from exc

            if h < max(o, cl, l) or l > min(o, cl, h):
                valid_ohlc = False

            # Volume is optional market metadata; if supplied it must be valid.
            if "volume" in candle:
                try:
                    volume = float(candle["volume"])
                except (TypeError, ValueError) as exc:
                    raise ValueError(f"INVALID_VOLUME: bar_index={idx}") from exc
                if volume <= 0:
                    zero_vol += 1

            current_ts = extract_bar_ts(candle)
            if idx > 0:
                previous_ts = extract_bar_ts(candles[idx - 1])
                if current_ts <= previous_ts:
                    is_chrono = False
                    break

        quality = DatasetQualityReport(
            total_bars=n_bars,
            gaps_count=0,
            zero_volume_bars=zero_vol,
            outlier_spikes_count=0,
            is_valid_ohlc=valid_ohlc,
            is_strictly_chronological=is_chrono,
            integrity_score_pct=100.0 if (valid_ohlc and is_chrono) else 0.0,
        )

        if not valid_ohlc:
            raise ValueError("INVALID_OHLC: dataset contains physically inconsistent bars")
        if not is_chrono:
            raise ValueError("NON_MONOTONIC_TIMESTAMPS: dataset chronology is not strictly increasing")

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
        """Load only the physical candles represented by the verified file."""
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"DATASET_UNAVAILABLE: {self.file_path}")
        with open(self.file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list) or not data:
            raise ValueError("DATASET_EMPTY: no physical candles available")
        return data
