"""Phase-2 regression tests for real parameter activation and fail-closed data custody."""

from datetime import datetime, timezone

from services.discovery.funding_discovery import FundingDiscoveryEngine
from services.discovery.research_objective import robust_research_score
from services.discovery.ultra_discovery import UltraDiscoveryEngine
from services.discovery.discovery_validation_pipeline import validate_real_dataset


def _dataset_ref() -> tuple[str, str]:
    return "ds_test", "a" * 64


def test_ultra_parameters_change_canonical_strategy():
    engine = UltraDiscoveryEngine()
    dataset_id, dataset_hash = _dataset_ref()
    base = engine.generate_candidate_blueprint(
        "u1", "BTC-USDT", "1h", dataset_id, dataset_hash,
        ema_fast=8, ema_slow=30, rsi_period=10,
        rsi_threshold_long=52, rsi_threshold_short=48,
        sl_atr_mult=1.5, tp_atr_mult=4.0,
        archetype="MOMENTUM_BREAKOUT", pyramiding_tiers_count=3,
    )
    changed = engine.generate_candidate_blueprint(
        "u2", "BTC-USDT", "1h", dataset_id, dataset_hash,
        ema_fast=20, ema_slow=80, rsi_period=21,
        rsi_threshold_long=60, rsi_threshold_short=40,
        sl_atr_mult=3.0, tp_atr_mult=8.0,
        archetype="MEAN_REVERSION", pyramiding_tiers_count=0,
    )
    assert base.canonical_hash != changed.canonical_hash
    assert base.exit_rules.sl_value != changed.exit_rules.sl_value
    assert base.entry_rules.model_dump_json() != changed.entry_rules.model_dump_json()


def test_fondeo_parameters_change_canonical_strategy():
    engine = FundingDiscoveryEngine()
    dataset_id, dataset_hash = _dataset_ref()
    base = engine.generate_candidate_blueprint(
        "f1", "NQ", "15m", dataset_id, dataset_hash,
        ema_fast=5, ema_slow=21, rsi_period=10,
        rsi_threshold_long=50, rsi_threshold_short=50,
        stop_loss_ticks=10, target_profit_ticks=20,
    )
    changed = engine.generate_candidate_blueprint(
        "f2", "NQ", "15m", dataset_id, dataset_hash,
        ema_fast=13, ema_slow=55, rsi_period=21,
        rsi_threshold_long=55, rsi_threshold_short=45,
        stop_loss_ticks=20, target_profit_ticks=60,
    )
    assert base.canonical_hash != changed.canonical_hash
    assert base.exit_rules.sl_value != changed.exit_rules.sl_value
    assert base.exit_rules.tp_value != changed.exit_rules.tp_value


def test_objective_penalizes_large_drawdown_and_zero_trade_trials():
    good = robust_research_score(
        profit_factor=2.0, max_drawdown_pct=3.0, trades=80,
        initial_capital_usd=10000, net_profit_usd=2500, drawdown_ceiling_pct=25,
    )
    bad = robust_research_score(
        profit_factor=2.0, max_drawdown_pct=20.0, trades=80,
        initial_capital_usd=10000, net_profit_usd=2500, drawdown_ceiling_pct=25,
    )
    blocked = robust_research_score(
        profit_factor=5.0, max_drawdown_pct=1.0, trades=0,
        initial_capital_usd=10000, net_profit_usd=5000, drawdown_ceiling_pct=25,
    )
    assert good > bad
    assert blocked == float("-inf")


def test_future_dataset_is_fail_closed():
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    candles = [
        {"time": now_ms - (300 - i) * 60_000, "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1}
        for i in range(200)
    ]
    candles[-1]["time"] = now_ms + 60_000
    valid, reason = validate_real_dataset(candles, "future.json")
    assert not valid
    assert reason.startswith("future_data_end=")
