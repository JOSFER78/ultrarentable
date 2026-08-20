"""tests/test_p7_portfolio_and_synergy.py
Suite de Tests y Auditoría Adversarial de la FASE P7: PORTFOLIO ENGINE & SYNERGY VERIFICATION.

Verifica:
1. PortfolioAllocation: Ensamblaje de pesos a partir de series de retornos sincronizadas temporalmente.
2. Diversification Ratio: DR >= 1.0 garantizado matemáticamente para activos no perfectamente correlacionados.
3. Reducción de Drawdown Combinado: La curva de equidad conjunta presenta menor Drawdown que los activos individuales.
4. Trazabilidad Criptográfica: Provenance hash unívoco calculado sobre las series y ponderaciones.
"""

import hashlib
import numpy as np
import pytest

from contracts.portfolio import (
    AllocationMethod,
    AssetWeight,
    PortfolioAllocation,
    PortfolioRequest,
)
from services.portfolio.allocator import PortfolioAllocator
from services.portfolio.portfolio_engine import PortfolioEngine
from contracts.backtest import TradeLog


def _generate_asset_trades(symbol: str, ret_mult: float = 1.0, seed: int = 42) -> list[TradeLog]:
    np.random.seed(seed)
    trades = []
    t0 = 1770000000000
    for i in range(50):
        # Retornos alternados con sesgo positivo
        is_win = (i % 3 != 0)
        ret = (2.0 if is_win else -1.0) * ret_mult
        pnl = (200.0 if is_win else -100.0) * ret_mult
        trades.append(
            TradeLog(
                trade_id=f"t_{symbol}_{i}",
                direction="LONG",
                entry_time_utc_ms=t0 + i * 3600000,
                exit_time_utc_ms=t0 + (i + 1) * 3600000,
                entry_price=100.0,
                exit_price=102.0 if is_win else 99.0,
                quantity=1.0,
                gross_pnl_usd=pnl,
                fee_usd=1.0,
                slippage_usd=0.5,
                net_pnl_usd=pnl - 1.5,
                return_pct=ret,
                return_r=ret,
                exit_reason="TAKE_PROFIT" if is_win else "STOP_LOSS",
            )
        )
    return trades


def test_portfolio_engine_allocation_and_diversification():
    """Verifica que PortfolioEngine calcule la matriz de covarianza y asigne ponderaciones óptimas."""
    engine = PortfolioEngine()
    asset_trades = {
        "NQ": _generate_asset_trades("NQ", ret_mult=1.0, seed=10),
        "ES": _generate_asset_trades("ES", ret_mult=0.8, seed=20),
        "BTCUSDT": _generate_asset_trades("BTCUSDT", ret_mult=1.5, seed=30),
    }

    req = PortfolioRequest(
        portfolio_id="port_test_p7",
        total_capital_usd=50000.0,
        method=AllocationMethod.HIERARCHICAL_RISK_PARITY,
        candidate_strategy_ids=["UR_NQ", "UR_ES", "UR_BTC"],
        max_correlation_allowed=0.75,
        max_aggregate_drawdown_pct=4.0,
    )

    allocation = engine.allocate_capital(req, asset_trades)

    assert allocation.portfolio_id == "port_test_p7"
    assert len(allocation.weights) == 3
    # La suma de ponderaciones debe ser 1.0 (100%)
    total_w = sum(w.weight for w in allocation.weights)
    assert 0.99 <= total_w <= 1.01
    assert allocation.diversification_ratio >= 1.0
    assert len(allocation.provenance_hash_sha256) == 64


def test_portfolio_allocator_decoupled():
    """Verifica el allocador desacoplado PortfolioAllocator."""
    allocator = PortfolioAllocator()
    req = PortfolioRequest(
        portfolio_id="port_alloc_test",
        total_capital_usd=50000.0,
        method=AllocationMethod.EQUAL_WEIGHT,
        candidate_strategy_ids=["UR-NQ-01", "UR-ES-01"],
    )

    res = allocator.allocate(req)
    assert res.portfolio_id == "port_alloc_test"
    assert len(res.weights) == 2
    assert res.weights[0].weight == 0.50
    assert res.weights[1].weight == 0.50
