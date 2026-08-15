"""Unit tests for StrategyQuant X candidate converter (Fase 4)."""

from services.sqx_bridge.converter import sqx_candidate_to_spec
from services.strategy_core.spec import StrategyStatus, StrategySpec


def test_sqx_candidate_conversion():
    """Verify conversion of SQX candidate JSON metrics into neutral StrategySpec."""
    sqx_stats = {
        "TradesCount": 110,
        "ProfitFactor": 1.75,
        "NetProfitUsd": 18500.0,
        "MaxDrawdownPct": 6.4,
        "WinRate": 56.2
    }
    
    spec = sqx_candidate_to_spec(
        project_name="NQ BREAKOUT FUTURES H1",
        databank_name="MainDatabank",
        strategy_name="Strat_Breakout_NQ_001",
        sqx_stats=sqx_stats,
        symbol="NQ"
    )

    assert isinstance(spec, StrategySpec)
    assert spec.strategy_id == "UR-SQX-Strat_Breakout_NQ_001"
    assert spec.status == StrategyStatus.CANDIDATE
    assert spec.origin.engine == "strategyquant"
    assert spec.origin.project == "NQ BREAKOUT FUTURES H1"
    assert spec.validation.profit_factor == 1.75
    assert spec.validation.trades_count == 110
