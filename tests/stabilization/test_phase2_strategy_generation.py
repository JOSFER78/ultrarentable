from scripts import phase2_research_adapter as adapter
from services.discovery.ultra_discovery import UltraDiscoveryEngine


def _strategy(params):
    engine = UltraDiscoveryEngine()
    manifest = {
        "symbol": "BTCUSDT",
        "interval": "1h",
        "datasetId": "dataset-test",
        "physicalFileSha256": "a" * 64,
    }
    return adapter._strategy_from_params("ULTRA", manifest, "candidate", params, engine, object())


def test_search_dimensions_change_executable_strategy_hash():
    base = adapter._ultra_search_space()[0]
    alt = dict(base)
    alt["archetype"] = "TREND_FOLLOWING"
    alt["volatility_filter"] = "ATR_REGIME"
    alt["volume_confirmation"] = "RELATIVE_VOLUME"
    alt["exit_family"] = "TRAILING_PROFIT"
    first = _strategy(base)
    second = _strategy(alt)
    assert first.canonical_hash != second.canonical_hash
    assert first.entry_rules.model_dump_json() != second.entry_rules.model_dump_json()
    assert first.exit_rules.model_dump_json() != second.exit_rules.model_dump_json()


def test_breakout_family_can_enable_shifted_donchian_confirmation():
    params = next(
        p
        for p in adapter._ultra_search_space()
        if p["archetype"] == "MOMENTUM_BREAKOUT" and p["breakout_confirmation"]
    )
    strategy = _strategy(params)
    rules = strategy.entry_rules.model_dump_json()
    assert "DONCHIAN_HIGH" in rules
    assert "DONCHIAN_LOW" in rules
