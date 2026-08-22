"""tests/test_challenge_evaluator.py
Unit tests for PropChallengeEvaluator (Sim101 / Prop Firm rules).
"""

from __future__ import annotations

from contracts.portfolio import PropChallengeConfig
from services.fondeo.challenge_evaluator import PropChallengeEvaluator


def test_prop_challenge_evaluator_health_pass():
    evaluator = PropChallengeEvaluator()
    config = PropChallengeConfig(
        firm_name="Apex 50K Combine",
        account_size_usd=50000.0,
        profit_target_usd=3000.0,
        max_trailing_drawdown_usd=2000.0,
        daily_loss_limit_usd=1000.0,
        min_trading_days=5,
        consistency_max_profit_share_pct=40.0,
    )

    # 1. Healthy account, mid-challenge
    res = evaluator.evaluate_account_health(
        config=config,
        current_equity=51500.0,
        peak_equity=52000.0,
        daily_loss=200.0,
        daily_profits_history=[500.0, 400.0, 600.0],
        days_traded=3,
    )
    assert not res["passed"]
    assert not res["failed"]
    assert res["profit_secured_usd"] == 1500.0
    assert res["trailing_drawdown_usd"] == 500.0
    assert res["trailing_drawdown_cushion_usd"] == 1500.0
    assert res["daily_loss_cushion_usd"] == 800.0
    assert res["progress_pct"] == 50.0

    # 2. Challenge Completed (Passed)
    res_passed = evaluator.evaluate_account_health(
        config=config,
        current_equity=53200.0,
        peak_equity=53200.0,
        daily_loss=0.0,
        daily_profits_history=[700.0, 600.0, 650.0, 550.0, 700.0],
        days_traded=5,
    )
    assert res_passed["passed"]
    assert not res_passed["failed"]
    assert res_passed["progress_pct"] == 100.0
    assert res_passed["min_days_reached"]


def test_prop_challenge_evaluator_violations():
    evaluator = PropChallengeEvaluator()
    config = PropChallengeConfig(
        firm_name="Topstep 50K",
        account_size_usd=50000.0,
        profit_target_usd=3000.0,
        max_trailing_drawdown_usd=2000.0,
        daily_loss_limit_usd=1000.0,
    )

    # Daily Loss Limit breach
    res_dll = evaluator.evaluate_account_health(
        config=config,
        current_equity=49000.0,
        peak_equity=50000.0,
        daily_loss=1050.0,
    )
    assert res_dll["failed"]
    assert res_dll["daily_violation"]

    # Trailing DD breach
    res_tdd = evaluator.evaluate_account_health(
        config=config,
        current_equity=49500.0,
        peak_equity=52000.0,
        daily_loss=100.0,
    )
    assert res_tdd["failed"]
    assert res_tdd["trailing_violation"]
    assert res_tdd["trailing_drawdown_usd"] == 2500.0


def test_prop_challenge_evaluator_live_fill():
    evaluator = PropChallengeEvaluator()
    config = PropChallengeConfig(
        firm_name="NinjaTrader Sim101",
        account_size_usd=50000.0,
        profit_target_usd=3000.0,
        max_trailing_drawdown_usd=2000.0,
        daily_loss_limit_usd=1000.0,
    )

    res = evaluator.evaluate_live_fill(
        config=config,
        current_equity=50000.0,
        peak_equity=50000.0,
        fill_pnl=250.0,
        session_daily_pnl=250.0,
    )
    assert res["current_equity_usd"] == 50250.0
    assert res["peak_equity_usd"] == 50250.0
    assert not res["failed"]
    assert res["profit_secured_usd"] == 250.0
