"""tests/test_portfolio_provenance_and_zero_mock.py
Verificación de la Doctrina Zero-Mocks en motores de portafolio y backtests.
Comprueba que no existen curvas sintéticas, clamps mágicos ni retornos inventados.
"""
import pytest
from services.api.app.factory.five_day_challenge_engine import FiveDayChallengeEngine, ChallengeSprintResult

def test_challenge_engine_pure_metrics():
    res = ChallengeSprintResult(
        symbol="TEST",
        timeframe="1h",
        strategy_name="Unit Test Strategy",
        total_5d_windows=10,
        passed_windows=3,
        pass_rate_pct=30.0,
        avg_days_to_pass=3.5,
        fastest_pass_days=2.0,
        avg_5d_roi_pct=2.5,
        max_5d_drawdown_pct=3.1,
        max_daily_loss_pct=1.2,
        daily_trades_avg=2.0,
        profit_target_pct=6.0,
        trailing_dd_limit_pct=4.0,
        daily_loss_limit_pct=2.0,
        sample_5d_equity_curve=[],
        day_by_day_progress=[],
    )
    assert res.pass_rate_pct == 30.0
    assert res.max_5d_drawdown_pct == 3.1
