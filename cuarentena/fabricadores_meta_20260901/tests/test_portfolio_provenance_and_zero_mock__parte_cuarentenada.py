"""Parte CUARENTENADA (2026-09-01, W6.0/D8) del test tests/test_portfolio_provenance_and_zero_mock.py: estas funciones probaban modulos que fabricaban datos (ver MOTIVO.md). Se conservan integras, sin ejecutarse."""
from services.api.app.factory.ultra_portfolio_engine import build_ultra_hyperscale_portfolios
from services.api.app.factory.portfolio_sprint_engine import build_fondeo_sprint_portfolios
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

