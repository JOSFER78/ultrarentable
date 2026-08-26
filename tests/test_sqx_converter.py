"""Tests for the retired SQX statistics-to-strategy conversion boundary."""

import pytest

from services.sqx_bridge.converter import StrategyConversionError, normalize_drawdown_pct, sqx_candidate_to_canonical, sqx_candidate_to_spec


def test_statistics_only_payload_is_rejected_for_spec_conversion():
    with pytest.raises(StrategyConversionError, match="LEGACY_SQX_CONVERTER_DISABLED"):
        sqx_candidate_to_spec(
            project_name="NQ BREAKOUT FUTURES H1",
            databank_name="MainDatabank",
            strategy_name="Strat_Breakout_NQ_001",
            sqx_stats={"TradesCount": 110, "ProfitFactor": 1.75},
            symbol="NQ",
        )


def test_statistics_only_payload_is_rejected_for_canonical_conversion():
    with pytest.raises(StrategyConversionError, match="LEGACY_SQX_CONVERTER_DISABLED"):
        sqx_candidate_to_canonical(
            project_name="Ultra_Auto_Pilot",
            databank_name="Results",
            strategy_name="Strategy 1.4.140",
            sqx_stats={"TradesCount": 140, "ProfitFactor": 1.88},
            symbol="NQ",
            route="FONDEO",
        )


def test_drawdown_normalization_is_pure_math():
    assert normalize_drawdown_pct(5.5, 2000.0) == 5.5
    assert normalize_drawdown_pct(1500.0, 5000.0, initial_capital=10000.0) == 10.0


def test_drawdown_requires_valid_reference():
    with pytest.raises(StrategyConversionError):
        normalize_drawdown_pct(1500.0, 5000.0, initial_capital=0.0)
