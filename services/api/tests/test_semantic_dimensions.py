from __future__ import annotations

import random

from services.api.app.dsl.engine import StrategyDSL, validate_semantics
from services.api.app.factory.genetic import GeneticOperators
from services.api.app.factory.seed_factory import SeedFactory


def test_rejects_price_vs_rsi() -> None:
    strategy = SeedFactory(seed=1).create_template_strategy(0, timeframe="15m")
    strategy["signals"]["longEntry"]["left"] = {
        "type": "SERIES", "series": "CLOSE", "offset": 0
    }
    strategy["signals"]["longEntry"]["right"] = {
        "type": "INDICATOR",
        "indicator": "RSI",
        "source": {"type": "SERIES", "series": "CLOSE", "offset": 0},
        "params": {"period": 14},
        "offset": 0,
    }
    errors = validate_semantics(StrategyDSL.model_validate(strategy))
    assert any(item.code == "INCOMPATIBLE_VALUE_DIMENSIONS" for item in errors)


def test_rejects_price_vs_volume() -> None:
    strategy = SeedFactory(seed=2).create_template_strategy(0, timeframe="15m")
    strategy["signals"]["shortEntry"]["right"] = {
        "type": "SERIES", "series": "VOLUME", "offset": 0
    }
    errors = validate_semantics(StrategyDSL.model_validate(strategy))
    assert any(item.code == "INCOMPATIBLE_VALUE_DIMENSIONS" for item in errors)


def test_rejects_price_level_vs_price_variation() -> None:
    strategy = SeedFactory(seed=2).create_template_strategy(0, timeframe="15m")
    strategy["signals"]["shortEntry"]["right"] = {
        "type": "INDICATOR",
        "indicator": "ATR",
        "source": {"type": "SERIES", "series": "CLOSE", "offset": 0},
        "params": {"period": 14},
        "offset": 0,
    }
    errors = validate_semantics(StrategyDSL.model_validate(strategy))
    assert any(item.code == "INCOMPATIBLE_VALUE_DIMENSIONS" for item in errors)


def test_rejects_self_comparison() -> None:
    strategy = SeedFactory(seed=3).create_template_strategy(0, timeframe="15m")
    value = {"type": "SERIES", "series": "CLOSE", "offset": 0}
    strategy["signals"]["longEntry"]["left"] = value
    strategy["signals"]["longEntry"]["right"] = dict(value)
    errors = validate_semantics(StrategyDSL.model_validate(strategy))
    assert any(item.code == "DEGENERATE_COMPARISON" for item in errors)


def test_generated_population_is_dimensionally_valid() -> None:
    population = SeedFactory(seed=4).generate_population(100, timeframe="15m")
    assert all(
        not validate_semantics(StrategyDSL.model_validate(strategy))
        for strategy in population
    )


def test_mutations_remain_dimensionally_valid() -> None:
    parent = SeedFactory(seed=5).create_template_strategy(0, timeframe="15m")
    genetic = GeneticOperators(random.Random(5))
    for _ in range(200):
        parent = genetic.mutate(parent)
        assert not validate_semantics(StrategyDSL.model_validate(parent))


def test_all_declared_templates_are_real_and_semantically_valid() -> None:
    factory = SeedFactory(seed=6)
    ema = factory.create_template_strategy(0, timeframe="5m")
    rsi = factory.create_template_strategy(1, timeframe="5m")
    donchian = factory.create_template_strategy(2, timeframe="5m")
    assert ema["signals"]["longEntry"]["left"]["indicator"] == "EMA"
    assert rsi["signals"]["longEntry"]["left"]["indicator"] == "RSI"
    assert donchian["signals"]["longEntry"]["right"]["indicator"] == "HIGHEST"
    assert donchian["signals"]["longEntry"]["right"]["offset"] == 1
    for strategy in (ema, rsi, donchian):
        assert not validate_semantics(StrategyDSL.model_validate(strategy))


def test_automatic_grammar_does_not_generate_continuous_equality() -> None:
    population = SeedFactory(seed=7).generate_population(100, timeframe="5m")
    for strategy in population:
        stack = list(strategy["signals"].values())
        while stack:
            node = stack.pop()
            if node.get("nodeType") == "COMPARISON":
                assert node["op"] != "EQ"
            stack.extend(node.get("children", []))


def test_automatic_strategies_use_only_executable_market_orders() -> None:
    population = SeedFactory(seed=8).generate_population(100, timeframe="5m")
    assert all(
        strategy["execution"]["entryOrderType"] == "MARKET"
        and strategy["execution"]["exitOrderType"] == "MARKET"
        for strategy in population
    )


def test_unpriced_limit_order_is_semantically_rejected() -> None:
    strategy = SeedFactory(seed=9).create_template_strategy(0, timeframe="5m")
    strategy["execution"]["entryOrderType"] = "LIMIT"
    errors = validate_semantics(StrategyDSL.model_validate(strategy))
    assert any(item.code == "UNPRICED_LIMIT_ORDER_UNSUPPORTED" for item in errors)
