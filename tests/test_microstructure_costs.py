"""tests/test_microstructure_costs.py
Pruebas del Registro de Microestructura y Doctrina Zero-Default (Fase 3).
"""

import pytest
from contracts.canonical_execution import AssetClass
from services.data.instrument_cost_registry import (
    CANONICAL_COST_REGISTRY,
    MissingCostModelError,
    get_instrument_cost_profile,
    normalize_instrument_symbol,
)


def test_registered_instruments_have_non_zero_costs():
    """Verify that all registered canonical instruments have realistic non-zero cost parameters."""
    assert len(CANONICAL_COST_REGISTRY) >= 20
    for sym, profile in CANONICAL_COST_REGISTRY.items():
        assert profile.point_value > 0.0
        assert profile.tick_size > 0.0
        assert profile.contract_multiplier > 0.0
        assert profile.taker_fee_pct > 0.0
        assert profile.typical_spread_ticks >= 0.0
        assert profile.slippage_ticks_baseline > 0.0


def test_forex_multiplier_is_100k():
    """Verify Forex instruments use the standard 100,000 contract multiplier and point value."""
    eurusd = get_instrument_cost_profile("EURUSD")
    assert eurusd.asset_class == AssetClass.FOREX_SPOT
    assert eurusd.contract_multiplier == 100_000.0
    assert eurusd.point_value == 10.0


def test_unknown_symbol_raises_missing_cost_model_error():
    """Verify that querying an unverified instrument raises MissingCostModelError (BLOCKED)."""
    with pytest.raises(MissingCostModelError) as exc_info:
        get_instrument_cost_profile("SYNTHETIC_SHITCOIN_999")
    assert "BLOCKED_NO_COST_MODEL" in str(exc_info.value)


def test_symbol_normalization_handles_variations():
    """Verify normalization of symbols with hyphens, underscores and lowercase."""
    p1 = get_instrument_cost_profile("btc_usdt")
    p2 = get_instrument_cost_profile("BTC-USDT")
    p3 = get_instrument_cost_profile("BTC/USDT")
    assert p1.symbol == "BTCUSDT"
    assert p1 == p2 == p3
