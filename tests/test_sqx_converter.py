"""Unit tests for StrategyQuant X candidate converter (Fase 3 & Fase 4)."""

from contracts import CanonicalStrategy, ExecutionTrack, StrategyLifecycleStatus
from services.sqx_bridge.converter import (
    sqx_candidate_to_spec,
    sqx_candidate_to_canonical,
    normalize_drawdown_pct,
)
from services.strategy_core.spec import StrategyStatus, StrategySpec


def test_sqx_candidate_conversion_legacy():
    """Verify conversion of SQX candidate JSON metrics into neutral StrategySpec."""
    sqx_stats = {
        "TradesCount": 110,
        "ProfitFactor": 1.75,
        "NetProfitUsd": 18500.0,
        "MaxDrawdownPct": 6.4,
        "WinRate": 56.2,
    }

    spec = sqx_candidate_to_spec(
        project_name="NQ BREAKOUT FUTURES H1",
        databank_name="MainDatabank",
        strategy_name="Strat_Breakout_NQ_001",
        sqx_stats=sqx_stats,
        symbol="NQ",
    )

    assert isinstance(spec, StrategySpec)
    assert spec.strategy_id == "UR-SQX-Strat_Breakout_NQ_001"
    assert spec.status == StrategyStatus.CANDIDATE
    assert spec.origin.engine == "strategyquant"
    assert spec.origin.project == "NQ BREAKOUT FUTURES H1"
    assert spec.validation.profit_factor == 1.75
    assert spec.validation.trades_count == 110


def test_sqx_candidate_conversion_canonical():
    """Verify conversion of SQX candidate into CanonicalStrategy v2.0.0."""
    sqx_stats = {
        "TradesCount": 140,
        "ProfitFactor": 1.88,
        "NetProfitUsd": 24000.0,
        "MaxDrawdownPct": 1200.0,  # Absolute USD DD
        "WinRate": 58.5,
    }

    canon = sqx_candidate_to_canonical(
        project_name="Ultra_Auto_Pilot",
        databank_name="Results",
        strategy_name="Strategy 1.4.140",
        sqx_stats=sqx_stats,
        symbol="NQ",
        target_track=ExecutionTrack.TRACK_FONDEO,
    )

    assert isinstance(canon, CanonicalStrategy)
    assert canon.strategy_id == "UR-SQX-Strategy_1.4.140"
    assert canon.status == StrategyLifecycleStatus.CANDIDATE
    assert canon.target_track == ExecutionTrack.TRACK_FONDEO
    assert canon.instrument.symbol == "NQ"
    assert canon.session.force_close_at_end is True
    # Verify absolute USD drawdown is normalized to percentage
    assert canon.metadata["max_drawdown_pct"] <= 100.0
    assert len(canon.compute_sha256()) == 64


def test_drawdown_normalization():
    """Verify absolute and relative drawdowns are normalized properly."""
    # Percentage input
    assert normalize_drawdown_pct(5.5, 2000.0) == 5.5
    # Absolute USD input on $10k initial + $5k profit = $15k peak -> $1500 DD is 10.0%
    assert normalize_drawdown_pct(1500.0, 5000.0, initial_capital=10000.0) == 10.0
