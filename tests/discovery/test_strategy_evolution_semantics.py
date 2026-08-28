from services.discovery.strategy_evolution_engine import StrategyEvolutionEngine


def test_evolution_includes_semantic_non_indicator_mutations():
    engine = StrategyEvolutionEngine()
    proposals = engine.propose(
        parent_strategy_id="parent",
        parameters={
            "ema_fast": 12,
            "ema_slow": 50,
            "rsi_period": 14,
            "rsi_threshold_long": 55.0,
            "rsi_threshold_short": 45.0,
            "sl_atr_mult": 2.0,
            "tp_atr_mult": 6.0,
            "signal_family": "TREND",
            "exit_family": "ATR_DYNAMIC",
        },
        limit=16,
    )
    types = {p.mutation_type for p in proposals}
    assert "SWAP_SIGNAL_FAMILY" in types
    assert "ADD_VOLATILITY_FILTER" in types
    assert "ADD_VOLUME_CONFIRMATION" in types
    assert "CHANGE_EXIT_FAMILY" in types
    assert "REDUCE_COMPLEXITY" in types
