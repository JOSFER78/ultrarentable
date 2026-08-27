from services.discovery.strategy_research_loop import StrategyResearchLoop


def _candidate(score: float, strategy_id: str, archetype: str):
    return (score, strategy_id, {"archetype": archetype}, archetype, None, None, None)


def test_survivor_selection_keeps_family_diversity_before_score_fill() -> None:
    evaluated = [
        _candidate(100.0, "m1", "MOMENTUM_BREAKOUT"),
        _candidate(99.0, "m2", "MOMENTUM_BREAKOUT"),
        _candidate(98.0, "m3", "MOMENTUM_BREAKOUT"),
        _candidate(90.0, "t1", "TREND_FOLLOWING"),
        _candidate(89.0, "r1", "RSI_MOMENTUM"),
        _candidate(88.0, "mr1", "MEAN_REVERSION"),
    ]

    survivors = StrategyResearchLoop._select_survivors(evaluated, limit=4)

    assert [item[3] for item in survivors] == [
        "MOMENTUM_BREAKOUT",
        "TREND_FOLLOWING",
        "RSI_MOMENTUM",
        "MEAN_REVERSION",
    ]


def test_survivor_selection_is_deterministic() -> None:
    evaluated = [
        _candidate(100.0, "m1", "MOMENTUM_BREAKOUT"),
        _candidate(99.0, "t1", "TREND_FOLLOWING"),
        _candidate(98.0, "r1", "RSI_MOMENTUM"),
        _candidate(97.0, "mr1", "MEAN_REVERSION"),
        _candidate(96.0, "m2", "MOMENTUM_BREAKOUT"),
    ]

    first = StrategyResearchLoop._select_survivors(evaluated, limit=4)
    second = StrategyResearchLoop._select_survivors(evaluated, limit=4)

    assert first == second
