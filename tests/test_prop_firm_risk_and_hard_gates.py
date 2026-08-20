"""tests/test_prop_firm_risk_and_hard_gates.py
Pruebas de PropFirmRiskEngine y Ley de Hard Gates (Fase 5).
"""

import pytest
from services.validation.prop_firm_risk_engine import PropFirmRiskEngine


def test_prop_firm_risk_engine_rejects_high_dd_strategy():
    """Verify that a strategy with severe drawdown clusters is rejected for prop firms."""
    # 30 trades with heavy losses
    trades = [100.0, -800.0, -1200.0, 200.0, -1500.0, -900.0, 50.0] * 5
    engine = PropFirmRiskEngine(max_bust_probability_allowed=0.05, min_pass_probability_required=0.50)
    
    res = engine.evaluate_prop_survival(
        trade_pnls_usd=trades,
        account_size_usd=50000.0,
        profit_target_pct=6.0,
        daily_loss_limit_pct=2.0,  # $1000 limit
        max_trailing_dd_pct=4.0,   # $2000 limit
    )
    assert res.passed is False
    assert res.p_account_bust_before_target > 0.05
    assert len(res.diagnostics) > 0


def test_prop_firm_risk_engine_accepts_consistent_edge():
    """Verify that a consistent strategy with tight stops passes prop evaluation."""
    # Consistent small losses and 3R wins
    trades = [300.0, 450.0, -100.0, 350.0, -100.0, 500.0, -80.0, 400.0] * 10
    engine = PropFirmRiskEngine(max_bust_probability_allowed=0.05, min_pass_probability_required=0.50)
    
    res = engine.evaluate_prop_survival(
        trade_pnls_usd=trades,
        account_size_usd=50000.0,
        profit_target_pct=6.0,
        daily_loss_limit_pct=2.0,
        max_trailing_dd_pct=4.0,
    )
    assert res.passed is True
    assert res.p_account_bust_before_target <= 0.05
    assert res.p_pass_challenge_probability >= 0.50


def test_hard_gate_failure_is_fatal():
    """Verify that failing any hard threshold immediately results in passed=False."""
    engine = PropFirmRiskEngine(max_bust_probability_allowed=0.01)
    # Marginal strategy
    trades = [150.0, -120.0, 180.0, -150.0, -200.0, 100.0] * 10
    res = engine.evaluate_prop_survival(trades, account_size_usd=50000.0)
    if res.p_account_bust_before_target > 0.01:
        assert res.passed is False
