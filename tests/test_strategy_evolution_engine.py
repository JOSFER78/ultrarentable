from services.discovery.strategy_evolution_engine import StrategyEvolutionEngine


def test_strategy_evolution_is_deterministic_and_structural() -> None:
    engine = StrategyEvolutionEngine()
    params = {
        "ema_fast": 12,
        "ema_slow": 50,
        "rsi_period": 14,
        "rsi_threshold_long": 55.0,
        "rsi_threshold_short": 45.0,
        "sl_atr_mult": 2.0,
        "tp_atr_mult": 6.0,
        "archetype": "MOMENTUM_BREAKOUT",
    }

    first = engine.propose("parent-1", params, archetype="MOMENTUM_BREAKOUT", limit=16)
    second = engine.propose("parent-1", params, archetype="MOMENTUM_BREAKOUT", limit=16)

    assert first == second
    assert len(first) == 16
    assert any(p.mutation_type == "SWAP_SIGNAL_FAMILY" for p in first)
    assert any(p.mutation_type == "CHANGE_EXIT_FAMILY" for p in first)
    assert any(p.mutation_type == "ADD_VOLATILITY_FILTER" for p in first)
    assert any(p.parameters["sl_atr_mult"] != params["sl_atr_mult"] for p in first)
    assert all(p.parent_strategy_id == "parent-1" for p in first)
    assert all(p.expected_effect for p in first)
