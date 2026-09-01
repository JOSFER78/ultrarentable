"""Parte CUARENTENADA (2026-09-01, W6.0/D8) del test tests/test_portfolio_and_ultra_engine.py: estas funciones probaban modulos que fabricaban datos (ver MOTIVO.md). Se conservan integras, sin ejecutarse."""
from services.portfolio import PortfolioEngine
def test_portfolio_engine_multi_asset_allocation():
    """Verify multi-asset allocation and diversification ratio calculation."""
    engine = PortfolioEngine()
    
    asset_trades = {
        "NQ": create_sample_trades("NQ", 60, 0.58),
        "ES": create_sample_trades("ES", 60, 0.54),
        "BTC-USDT": create_sample_trades("BTC-USDT", 60, 0.50),
    }

    request = PortfolioRequest(
        portfolio_id="port_ultra_001",
        total_capital_usd=100000.0,
        method=AllocationMethod.HIERARCHICAL_RISK_PARITY,
        candidate_strategy_ids=["UR-NQ-01", "UR-ES-01", "UR-BTC-01"],
        max_correlation_allowed=0.85,
    )

    allocation = engine.allocate_capital(
        request=request,
        asset_trades=asset_trades,
        asset_point_values={"NQ": 20.0, "ES": 50.0, "BTC-USDT": 1.0},
    )

    assert isinstance(allocation, PortfolioAllocation)
    assert allocation.portfolio_id == "port_ultra_001"
    assert len(allocation.weights) == 3
    assert abs(sum(w.weight for w in allocation.weights) - 1.0) < 1e-4
    assert allocation.expected_sharpe > 0.0
    assert len(allocation.provenance_hash_sha256) == 64


# ============================================================================
# TESTS: ULTRA EXPLOITATION ENGINE
# ============================================================================

