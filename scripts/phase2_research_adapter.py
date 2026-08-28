"""Compatibility adapter for canonical Phase-2 research.

Adds BingX array-form candle normalization, deterministic family-stratified
trial planning, and stability-first Validation without changing the canonical
backtest engine or consuming Blind OOS.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import phase2_research_run as runner  # noqa: E402
from scripts import phase2_trial_planner as trial_planner  # noqa: E402
from scripts.phase2_validation import evaluate_validation  # noqa: E402

_original_loader = runner.load_custodied_dataset
_OriginalEngine = runner.EventBacktestEngine


@dataclass
class _RobustValidationProxy:
    profit_factor: float
    total_trades: int
    max_drawdown_pct: float
    net_profit_usd: float
    win_rate_pct: float


class _RobustSelectionEngine(_OriginalEngine):
    """Use contiguous-block Validation only during discovery selection."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._reference_is_len: int | None = None
        self._robust_validation_calls = 0

    def run_backtest(self, strategy, candles, initial_capital_usd=1000.0):
        result = super().run_backtest(
            strategy,
            candles,
            initial_capital_usd=initial_capital_usd,
        )
        current_len = len(candles)
        if self._reference_is_len is None:
            self._reference_is_len = current_len
            return result

        # Phase-2 research is 60/20/20. Validation is therefore ~1/3 of IS.
        is_reference = self._reference_is_len
        is_validation_window = current_len > 0 and abs((is_reference / current_len) - 3.0) < 0.05
        if not is_validation_window or self._robust_validation_calls >= runner.TOP_VALIDATION:
            return result

        self._robust_validation_calls += 1
        robust = evaluate_validation(
            _OriginalEngine(),
            strategy,
            candles,
            initial_capital_usd,
        )
        return _RobustValidationProxy(
            profit_factor=robust.score,
            total_trades=int(round(robust.median_trades)),
            max_drawdown_pct=robust.worst_drawdown_pct,
            net_profit_usd=0.0,
            win_rate_pct=robust.profitable_block_fraction * 100.0,
        )


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
runner.EventBacktestEngine = _RobustSelectionEngine
runner.budget_space = trial_planner.budget_space
runner.TRIAL_PLANNER_VERSION = trial_planner.PLANNER_VERSION
runner.VALIDATION_SCORING_VERSION = "phase2-validation-v1"


if __name__ == "__main__":
    raise SystemExit(runner.main())
