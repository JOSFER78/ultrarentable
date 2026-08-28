from services.discovery.adaptive_hypothesis_engine import AdaptiveHypothesisEngine


def test_director_maps_archetypes_to_semantic_signal_families():
    history = [
        {"archetype": "TREND_FOLLOWING", "validation_score": 4.0},
        {"archetype": "MOMENTUM_BREAKOUT", "validation_score": 2.0},
    ]
    summary = AdaptiveHypothesisEngine().summarize(history)
    assert summary["TREND"].trials == 1
    assert summary["BREAKOUT"].trials == 1


def test_director_ignores_blind_oos_evidence():
    history = [
        {
            "archetype": "TREND_FOLLOWING",
            "validation_score": 1.0,
            "profit_factor_oos": 100.0,
            "max_drawdown_oos_pct": 0.0,
            "blind_oos_access": "NOT_CONSUMED",
        },
        {
            "archetype": "TREND_FOLLOWING",
            "validation_score": 1.0,
            "profit_factor_oos": 100.0,
            "max_drawdown_oos_pct": 0.0,
            "blind_oos_access": "CONSUMED",
        },
    ]
    stats = AdaptiveHypothesisEngine().summarize(history)["TREND"]
    assert stats.trials == 1
    assert stats.mean_oos_score == 0.0


def test_director_is_deterministic_for_same_pre_oos_history():
    history = [
        {"archetype": "TREND_FOLLOWING", "validation_score": 2.0},
        {"archetype": "BREAKOUT", "validation_score": 3.0},
    ]
    engine = AdaptiveHypothesisEngine()
    first = [plan.plan_id for plan in engine.plan("dataset-hash", history, budget=8)]
    second = [plan.plan_id for plan in engine.plan("dataset-hash", history, budget=8)]
    assert first == second
