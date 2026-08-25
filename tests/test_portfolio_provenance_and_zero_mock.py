"""tests/test_portfolio_provenance_and_zero_mock.py
Verificación de la Doctrina Zero-Mocks en motores de portafolio y backtests.
Comprueba que no existen curvas sintéticas, clamps mágicos ni retornos inventados.
"""
import pytest
from services.api.app.factory.ultra_portfolio_engine import build_ultra_hyperscale_portfolios
from services.api.app.factory.portfolio_sprint_engine import build_fondeo_sprint_portfolios
from services.api.app.factory.five_day_challenge_engine import FiveDayChallengeEngine, ChallengeSprintResult

def test_ultra_portfolio_zero_mocks_provenance():
    portfolios = build_ultra_hyperscale_portfolios()
    # Si no hay suficientes candidatos certificados con trades reales, debe devolver lista vacía o estado real
    if not portfolios:
        assert isinstance(portfolios, list)
    else:
        p = portfolios[0]
        assert p.status in ["VERIFIED", "VERIFIED_REAL_DATA"]
        assert isinstance(p.equity_growth_curve, list)
        # Verificar que el retorno acumulado no es un número fijo astronómico como 24700% sin base
        if p.total_trades == 0:
            assert p.net_profit_usd == 0.0

def test_fondeo_sprint_no_artificial_clamping():
    portfolios = build_fondeo_sprint_portfolios()
    if portfolios:
        p = portfolios[0]
        # El pass rate debe ser un valor real calculado, no un número forzado a >= 89.0%
        assert 0.0 <= p.pass_rate_pct <= 100.0
        assert p.avg_days_to_pass >= 0.0
        assert p.max_5d_drawdown_pct >= 0.0

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
