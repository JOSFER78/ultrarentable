"""Compatibility adapter for the canonical Phase-2 runner and BingX array-form candles."""
from __future__ import annotations

from scripts import phase2_research_run as runner


_original_loader = runner.load_custodied_dataset


def load_custodied_dataset(path):
    manifest, candles = _original_loader(path)
    normalized = []
    for row in candles:
        if isinstance(row, dict):
            normalized.append(row)
            continue
        if not isinstance(row, list) or len(row) < 6:
            raise RuntimeError(f"INVALID_CANDLE_FORMAT: {path.name}")
        normalized.append({
            "timestamp": int(row[0]),
            "open": float(row[1]),
            "high": float(row[2]),
            "low": float(row[3]),
            "close": float(row[4]),
            "volume": float(row[5]),
        })
    return manifest, normalized


runner.load_custodied_dataset = load_custodied_dataset

if __name__ == "__main__":
    raise SystemExit(runner.main())
