"""Canonical repository for real, normalized market datasets.

The repository never fabricates bars. A missing, malformed or unverifiable dataset
is a hard failure so downstream research cannot accidentally consume synthetic data.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from contracts.backtest import BarData, DatasetSnapshot
from services.api.app.config import DATA_DIR as BASE_DATA_DIR


class DatasetRepository:
    """Acceso y gestión de datasets canónicos verificados en disco."""

    def __init__(self, data_root: Optional[Path] = None) -> None:
        self.data_root = data_root or BASE_DATA_DIR
        self.normalized_dir = self.data_root / "normalized"

    @staticmethod
    def _sha256_file(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)
        return digest.hexdigest()

    def list_available_datasets(self) -> List[Dict[str, Any]]:
        """Lista manifests legibles; un manifest corrupto no se convierte en datos válidos."""
        manifests: List[Dict[str, Any]] = []
        if not self.normalized_dir.exists():
            return manifests

        for manifest_file in sorted(self.normalized_dir.glob("*_manifest.json")):
            with manifest_file.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, dict):
                manifests.append(data)
        return manifests

    def _find_dataset_file(self, symbol: str, timeframe: str) -> Path:
        formatted_sym = symbol.replace("-", "_").replace("/", "_")
        pattern = f"ds_*_{formatted_sym}_{timeframe}_*.json"
        matching_files = sorted(
            path
            for path in self.normalized_dir.glob(pattern)
            if not path.name.endswith("_manifest.json") and path.is_file()
        )
        if not matching_files:
            raise FileNotFoundError(
                f"No canonical normalized dataset for {symbol}/{timeframe} under {self.normalized_dir}"
            )
        return max(matching_files, key=lambda path: path.stat().st_size)

    @staticmethod
    def _parse_bar(item: Any, index: int) -> BarData:
        if isinstance(item, dict):
            required = ("timestamp", "time", "open", "high", "low", "close", "volume")
            timestamp_value = item.get("timestamp", item.get("time"))
            if timestamp_value is None:
                raise ValueError(f"bar {index}: missing timestamp/time")
            values = {
                "timestamp_utc_ms": int(timestamp_value),
                "open": float(item["open"]),
                "high": float(item["high"]),
                "low": float(item["low"]),
                "close": float(item["close"]),
                "volume": float(item["volume"]),
            }
            return BarData(**values)

        if isinstance(item, list) and len(item) >= 6:
            return BarData(
                timestamp_utc_ms=int(item[0]),
                open=float(item[1]),
                high=float(item[2]),
                low=float(item[3]),
                close=float(item[4]),
                volume=float(item[5]),
            )

        raise ValueError(f"bar {index}: unsupported normalized format")

    def load_bars(self, symbol: str = "ETH-USDT", timeframe: str = "1h") -> List[BarData]:
        """Carga velas físicas normalizadas y exige orden temporal y precios válidos."""
        target_file = self._find_dataset_file(symbol, timeframe)
        try:
            with target_file.open("r", encoding="utf-8") as handle:
                raw_data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"Cannot read canonical dataset {target_file}: {exc}") from exc

        if not isinstance(raw_data, list) or not raw_data:
            raise ValueError(f"Canonical dataset is empty or not a list: {target_file}")

        bars = [self._parse_bar(item, index) for index, item in enumerate(raw_data)]
        bars.sort(key=lambda bar: bar.timestamp_utc_ms)

        for index, bar in enumerate(bars):
            if bar.timestamp_utc_ms <= 0:
                raise ValueError(f"bar {index}: invalid timestamp")
            if min(bar.open, bar.high, bar.low, bar.close) <= 0:
                raise ValueError(f"bar {index}: non-positive price")
            if bar.high < max(bar.open, bar.close) or bar.low > min(bar.open, bar.close):
                raise ValueError(f"bar {index}: invalid OHLC envelope")
            if index and bar.timestamp_utc_ms <= bars[index - 1].timestamp_utc_ms:
                raise ValueError(f"bars are not strictly increasing at index {index}")

        return bars

    def get_snapshot(
        self,
        symbol: str = "ETH-USDT",
        timeframe: str = "1h",
        is_in_sample: bool = False,
        split_ratio: float = 0.70,
    ) -> DatasetSnapshot:
        """Devuelve un snapshot respaldado por el hash SHA-256 físico del dataset."""
        if not 0.0 < split_ratio < 1.0:
            raise ValueError("split_ratio must be between 0 and 1")

        bars = self.load_bars(symbol, timeframe)
        target_file = self._find_dataset_file(symbol, timeframe)
        split_idx = int(len(bars) * split_ratio)
        if split_idx <= 0 or split_idx >= len(bars):
            raise ValueError("Dataset is too small for the requested split")

        selected_bars = bars[:split_idx] if is_in_sample else bars[split_idx:]
        start_ts = selected_bars[0].timestamp_utc_ms
        end_ts = selected_bars[-1].timestamp_utc_ms

        return DatasetSnapshot(
            dataset_id=f"ds_{symbol.lower().replace('-', '_')}_{timeframe}_{'is' if is_in_sample else 'oos'}",
            symbol=symbol,
            timeframe=timeframe,
            start_timestamp_utc_ms=start_ts,
            end_timestamp_utc_ms=end_ts,
            total_bars=len(selected_bars),
            sha256_hash=self._sha256_file(target_file),
            is_in_sample=is_in_sample,
        )
