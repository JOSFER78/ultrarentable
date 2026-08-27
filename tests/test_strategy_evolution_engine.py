from services.discovery.strategy_evolution_engine import StrategyEvolutionEngine


def _params() -> dict:
    return {
        "ema_fast": 12,
        "ema_slow": 50,
        "rsi_period": 14,
        "rsi_threshold_long": 55.0,
        "rsi_threshold_short": 45.0,
        "sl_atr_mult": 2.0,
        "tp_atr_mult": 6.0,
        "archetype": "MOMENTUM_BREAKOUT",
    }


def test_strategy_evolution_is_deterministic_and_structural() -> None:
    engine = StrategyEvolutionEngine()
    first = engine.propose("parent-1", _params(), archetype="MOMENTUM_BREAKOUT", limit=16)
    second = engine.propose("parent-1", _params(), archetype="MOMENTUM_BREAKOUT", limit=16)

    assert first == second
    assert len(first) == 16
    assert any(p.mutation_type == "SWAP_SIGNAL_FAMILY" for p in first)
    assert any(p.mutation_type == "CHANGE_EXIT_FAMILY" for p in first)
    assert any(p.mutation_type == "ADD_VOLATILITY_FILTER" for p in first)
    assert any(p.parameters["sl_atr_mult"] != _params()["sl_atr_mult"] for p in first)
    assert all(p.parent_strategy_id == "parent-1" for p in first)
    assert all(p.expected_effect for p in first)


def test_small_evolution_budget_preserves_semantic_diversity() -> None:
    engine = StrategyEvolutionEngine()
    proposals = engine.propose("parent-small", _params(), archetype="MOMENTUM_BREAKOUT", limit=4)
    mutation_types = {p.mutation_type for p in proposals}

    assert len(proposals) == 4
    assert any(t in mutation_types for t in {
        "SWAP_SIGNAL_FAMILY",
        "ADD_VOLATILITY_FILTER",
        "REMOVE_VOLATILITY_FILTER",
        "ADD_VOLUME_CONFIRMATION",
        "ADD_BREAKOUT_CONFIRMATION",
    })
    assert any(t in mutation_types for t in {
        "CHANGE_EXIT_FAMILY",
        "WIDEN_STOP",
        "TIGHTEN_STOP",
        "WIDEN_TARGET",
        "TIGHTEN_TARGET",
    })
    assert any(t in mutation_types for t in {
        "CHANGE_SESSION",
        "REDUCE_COMPLEXITY",
        "INCREASE_COMPLEXITY",
    })


def test_noop_mutations_do_not_consume_research_budget() -> None:
    engine = StrategyEvolutionEngine()
    proposals = engine.propose(
        "parent-noop",
        {
            **_params(),
            "volatility_filter": None,
            "complexity": 1,
            "ema_fast": 2,
            "rsi_threshold_long": 50.0,
            "rsi_threshold_short": 50.0,
        },
        limit=16,
    )
    mutation_types = {p.mutation_type for p in proposals}

    assert "REMOVE_VOLATILITY_FILTER" not in mutation_types
    assert "RELAX_CONFIRMATION" not in mutation_types
    assert "SHIFT_FAST_REACTION" not in mutation_types
