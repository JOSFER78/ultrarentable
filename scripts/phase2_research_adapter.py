"""Compatibility adapter for canonical Phase-2 research.

Adds BingX array-form candle normalization and the deterministic family-
stratified trial planner without modifying the canonical runner's contract.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import phase2_research_run as runner  # noqa: E402
from scripts import phase2_trial_planner as trial_planner  # noqa: E402

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
runner.budget_space = trial_planner.budget_space
runner.TRIAL_PLANNER_VERSION = trial_planner.PLANNER_VERSION


if __name__ == "__main__":
    raise SystemExit(runner.main())
