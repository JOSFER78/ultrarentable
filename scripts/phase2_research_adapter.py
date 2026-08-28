"""Phase-2 adapter: real candle normalization + richer executable search.

The adapter keeps the canonical runner and backtest engine intact while adding
finite, deterministic search dimensions whose parameters change executable
rules: signal archetype, volatility/volume filters, breakout confirmation,
exit family and exit-specific parameters.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import phase2_research_run as runner  # noqa: E402
from scripts import phase2_trial_planner as trial_planner  # noqa: E402
from scripts.phase2_validation import evaluate_validation  # noqa: E402
from services.discovery.funding_discovery import FundingDiscoveryEngine  # noqa: E402
from services.discovery.ultra_discovery import UltraDiscoveryEngine  # noqa: E402

_original_loader = runner.load_custodied_dataset
_original_process_dataset = runner.process_dataset
_original_strategy_from_params = runner.strategy_from_params
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
        result = super().run_backtest(strategy, candles, initial_capital_usd=initial_capital_usd)
        current_len = len(candles)
        if self._reference_is_len is None:
            self._reference_is_len = current_len
            return result
        is_reference = self._reference_is_len
        is_validation_window = current_len > 0 and abs((is_reference / current_len) - 3.0) < 0.05
        if not is_validation_window or self._robust_validation_calls >= runner.TOP_VALIDATION:
            return result
        self._robust_validation_calls += 1
        robust = evaluate_validation(_OriginalEngine(), strategy, candles, initial_capital_usd)
        return _RobustValidationProxy(
            profit_factor=robust.score,
            total_trades=int(round(robust.median_trades)),
            max_drawdown_pct=robust.worst_drawdown_pct,
            net_profit_usd=0.0,
            win_rate_pct=robust.profitable_block_fraction * 100.0,
        )


def _ultra_search_space() -> list[dict]:
    archetypes = ["MOMENTUM_BREAKOUT", "TREND_FOLLOWING", "RSI_MOMENTUM", "MEAN_REVERSION"]
    fast = [8, 12, 20]
    slow = [30, 50, 80]
    rsi_periods = [10, 14, 21]
    thresholds = [(52.0, 48.0), (55.0, 45.0), (60.0, 40.0)]
    sl = [1.5, 2.0, 3.0]
    tp = [4.0, 6.0, 8.0]
    tiers = [0, 1, 2]
    volatility = [None, "ATR_REGIME"]
    volume = [None, "RELATIVE_VOLUME"]
    breakout = [False, True]
    lookbacks = [20, 40]
    exits = [None, "RR_DYNAMIC", "TIME_DECAY", "TRAILING_PROFIT"]
    space = []
    for values in product(archetypes, fast, slow, rsi_periods, thresholds, sl, tp, tiers, volatility, volume, breakout, lookbacks, exits):
        archetype, f, s, rp, threshold, sl_mult, tp_mult, tier_count, vol_filter, vol_confirm, breakout_on, lookback, exit_family = values
        if f >= s:
            continue
        if archetype != "MOMENTUM_BREAKOUT" and breakout_on:
            continue
        r_long, r_short = threshold
        space.append({
            "archetype": archetype,
            "ema_fast": f,
            "ema_slow": s,
            "rsi_period": rp,
            "rsi_threshold_long": r_long,
            "rsi_threshold_short": r_short,
            "sl_atr_mult": sl_mult,
            "tp_atr_mult": tp_mult,
            "pyramiding_tiers_count": tier_count,
            "volatility_filter": vol_filter,
            "volume_confirmation": vol_confirm,
            "breakout_confirmation": breakout_on,
            "breakout_lookback": lookback,
            "exit_family": exit_family,
        })
    return space


def _deterministic_space(route: str) -> list[dict]:
    if route == "ULTRA":
        return _ultra_search_space()
    return runner.deterministic_space(route)


def _strategy_from_params(route, manifest, strategy_id, params, ultra, funding):
    if route != "ULTRA":
        return _original_strategy_from_params(route, manifest, strategy_id, params, ultra, funding)
    return ultra.generate_candidate_blueprint(
        strategy_id=strategy_id,
        symbol=str(manifest["symbol"]),
        timeframe=str(manifest["interval"]),
        dataset_id=str(manifest["datasetId"]),
        dataset_sha256=str(manifest["physicalFileSha256"]),
        archetype=str(params["archetype"]),
        ema_fast=int(params["ema_fast"]),
        ema_slow=int(params["ema_slow"]),
        rsi_period=int(params["rsi_period"]),
        rsi_threshold_long=float(params["rsi_threshold_long"]),
        rsi_threshold_short=float(params["rsi_threshold_short"]),
        sl_atr_mult=float(params["sl_atr_mult"]),
        tp_atr_mult=float(params["tp_atr_mult"]),
        pyramiding_tiers_count=int(params["pyramiding_tiers_count"]),
        volatility_filter=params["volatility_filter"],
        volume_confirmation=params["volume_confirmation"],
        breakout_confirmation=bool(params["breakout_confirmation"]),
        breakout_lookback=int(params["breakout_lookback"]),
        exit_family=params["exit_family"],
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


def process_dataset(path, cycle=1):
    """Run canonical research, then enrich frozen champion with robust Validation."""
    result = _original_process_dataset(path, cycle=cycle)
    if result.get("status") != "FROZEN_VALIDATION_CHAMPION":
        return result
    freeze_path = runner.EVIDENCE_DIR / f"{result['run_id']}_frozen.json"
    if not freeze_path.is_file():
        raise RuntimeError(f"MISSING_FREEZE_ARTIFACT: {freeze_path.name}")
    manifest, candles = load_custodied_dataset(path)
    route = str(result["route"])
    ultra = UltraDiscoveryEngine()
    funding = FundingDiscoveryEngine()
    strategy = _strategy_from_params(route, manifest, str(result["candidate_id"]), dict(result["parameters"]), ultra, funding)
    strategy_hash = getattr(strategy, "canonical_hash", "")
    if strategy_hash != str(result["strategy_snapshot_hash"]):
        raise RuntimeError("FREEZE_STRATEGY_HASH_DRIFT")
    idx_val = int(result["partition"]["blind_oos_start_index"])
    idx_is = int(idx_val * 0.75)
    validation = candles[idx_is:idx_val]
    if not validation:
        raise RuntimeError("EMPTY_VALIDATION_WINDOW")
    initial_capital = 50_000.0 if route == "FONDEO" else 1_000.0
    robust = evaluate_validation(_OriginalEngine(), strategy, validation, initial_capital)
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    freeze["validation_scoring_version"] = "phase2-validation-v1"
    freeze["validation_robustness"] = robust.to_dict()
    freeze["validation_selection_score"] = float(robust.score)
    freeze_path.write_text(json.dumps(freeze, indent=2, ensure_ascii=False), encoding="utf-8")
    return freeze


runner.load_custodied_dataset = load_custodied_dataset
runner.process_dataset = process_dataset
runner.deterministic_space = _deterministic_space
runner.strategy_from_params = _strategy_from_params
runner.EventBacktestEngine = _RobustSelectionEngine
runner.budget_space = trial_planner.budget_space
runner.TRIAL_PLANNER_VERSION = trial_planner.PLANNER_VERSION
runner.VALIDATION_SCORING_VERSION = "phase2-validation-v1"


if __name__ == "__main__":
    raise SystemExit(runner.main())
