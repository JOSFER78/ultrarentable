from services.discovery.adaptive_hypothesis_engine import AdaptiveHypothesisEngine
from services.discovery.meta_strategy_engine import MetaStrategyEngine, StrategyEvidence


def test_adaptive_planner_is_deterministic_and_broad():
    engine = AdaptiveHypothesisEngine()
    first = engine.plan("a" * 64, [], budget=24)
    second = engine.plan("a" * 64, [], budget=24)
    assert first == second
    assert len(first) == 24
    assert len({p.signal_family for p in first}) >= 6
    assert len({p.exit_family for p in first}) >= 4


def test_adaptive_planner_learns_from_history():
    engine = AdaptiveHypothesisEngine()
    history = [
        {"archetype": "TREND", "validation_score": 2.0, "profit_factor_validation": 1.8, "max_drawdown_validation_pct": 10.0},
    ] * 12
    history += [
        {"archetype": "MEAN_REVERSION", "validation_score": 0.5, "profit_factor_validation": 1.1, "max_drawdown_validation_pct": 25.0},
    ] * 12
    plans = engine.plan("b" * 64, history, budget=18)
    assert plans
    assert plans[0].family == "TREND"


def test_meta_engine_rejects_unproven_members():
    engine = MetaStrategyEngine()
    candidate = StrategyEvidence(
        strategy_id="x",
        strategy_hash="h",
        route="ULTRA",
        symbol="BTCUSDT",
        timeframe="1h",
        oos_returns=(0.01, 0.02, -0.01),
        oos_profit_factor=1.2,
        oos_drawdown_pct=10.0,
        robustness_passed=False,
        evidence_hash="e",
    )
    result = engine.build([candidate])
    assert result["status"] == "NO_META_STRATEGY"
