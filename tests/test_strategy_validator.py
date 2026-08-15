"""Unit tests for Strategy Core neutral spec & independent strategy validator."""

from services.strategy_core.spec import StrategySpec, AssetClass, StrategySource, RuleCondition
from services.strategy_core.validator import IndependentStrategyValidator


def test_strategy_spec_creation():
    """Verify neutral StrategySpec construction."""
    spec = StrategySpec(
        strategy_id="strat_nq_breakout_001",
        name="NQ Breakout H1",
        source=StrategySource.STRATEGYQUANT_MCP,
        asset_class=AssetClass.FUTURES,
        symbol="NQ",
        main_timeframe="1h",
        entry_long_rules=[
            RuleCondition(indicator="RSI", timeframe="1h", period=14, comparison="GREATER_THAN", threshold_value=50.0)
        ],
        stop_loss_ticks=20,
        take_profit_ticks=60,
        close_at_session_end=True,
        risk_per_trade_pct=1.0,
        max_contracts=5
    )
    assert spec.strategy_id == "strat_nq_breakout_001"
    assert spec.symbol == "NQ"
    assert spec.close_at_session_end is True


def test_independent_validator_approval():
    """Verify strategy validator approves robust candidate stats."""
    validator = IndependentStrategyValidator(min_trades=30, min_profit_factor=1.3, max_drawdown_pct=20.0)
    spec = StrategySpec(
        strategy_id="strat_nq_test",
        name="NQ Test Strategy",
        symbol="NQ",
        close_at_session_end=True
    )
    sqx_stats = {
        "TradesCount": 120,
        "ProfitFactor": 1.85,
        "MaxDrawdownPct": 8.5
    }
    report = validator.validate_sqx_stats(spec, sqx_stats)
    assert report.overall_passed is True
    assert report.robustness_score >= 80.0
    assert "APPROVED" in report.recommendation


def test_independent_validator_rejection():
    """Verify strategy validator rejects weak candidate stats."""
    validator = IndependentStrategyValidator(min_trades=50, min_profit_factor=1.5, max_drawdown_pct=15.0)
    spec = StrategySpec(
        strategy_id="strat_weak_test",
        name="Weak Strategy",
        symbol="NQ",
        close_at_session_end=False
    )
    sqx_stats = {
        "TradesCount": 12,  # Too few trades
        "ProfitFactor": 1.1, # Too low profit factor
        "MaxDrawdownPct": 25.0 # Drawdown too high
    }
    report = validator.validate_sqx_stats(spec, sqx_stats)
    assert report.overall_passed is False
    assert "REJECTED" in report.recommendation
