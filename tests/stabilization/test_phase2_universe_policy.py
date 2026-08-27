"""Regression tests for the real Phase-2 universe contract."""

import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[2]
RESOLVER = ROOT / "scripts" / "resolve_phase2_universe.ts"


def test_universe_resolver_is_live_contract_driven():
    text = RESOLVER.read_text(encoding="utf-8")
    assert 'source: "BINGX_CONTRACTS"' in text
    assert "getContracts()" in text
    assert "PHASE2_REQUESTED_SYMBOLS_UNAVAILABLE" in text
    assert "PHASE2_UNIVERSE_EMPTY_AFTER_CONTRACT_FILTER" in text


def test_universe_resolver_has_no_random_or_time_based_selection():
    text = RESOLVER.read_text(encoding="utf-8")
    assert "Math.random(" not in text
    assert "Date.now(" not in text
    assert "Math.random()" not in text


def test_universe_resolver_exports_selected_symbols_to_workflow():
    text = RESOLVER.read_text(encoding="utf-8")
    assert "GITHUB_OUTPUT" in text
    assert "selected.join(\",\")" in text
    assert "universe_json" in text
