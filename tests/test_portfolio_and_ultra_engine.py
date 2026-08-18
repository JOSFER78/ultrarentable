"""Unit tests for PortfolioEngine and UltraExploitationEngine (Fase 6)."""

import pytest

from contracts import (
    AllocationMethod,
    BulletTradeDirection,
    CanonicalStrategy,
    ExecutionTrack,
    IsolatedBullet,
    PortfolioAllocation,
    PortfolioRequest,
    TradeLog,
    VaultRatchetConfig,
)
from services.exploitation_engines import UltraExploitationEngine
from services.portfolio import PortfolioEngine
from services.semantic_ai import SemanticQuantEngine
from contracts.validation_contracts import BalaState


def create_sample_trades(symbol: str, count: int = 50, win_pct: float = 0.55) -> list[TradeLog]:
    trades = []
    for i in range(count):
        is_win = (i % 100) < (win_pct * 100)
        ret = 2.5 if is_win else -1.0
        pnl = 250.0 if is_win else -100.0
        trades.append(
            TradeLog(
                trade_id=f"trade_{symbol}_{i}",
                direction="LONG",
                entry_time_utc_ms=1770000000000 + i * 3600000,
                exit_time_utc_ms=1770000000000 + (i + 1) * 3600000,
                entry_price=20000.0,
                exit_price=20100.0 if is_win else 19950.0,
                quantity=1.0,
                leverage=1.0,
                gross_pnl_usd=pnl,
                net_pnl_usd=pnl - 2.5,
                return_pct=ret,
                return_r=ret,
                exit_reason="TAKE_PROFIT" if is_win else "STOP_LOSS",
            )
        )
    return trades


# ============================================================================
# TESTS: PORTFOLIO ENGINE
# ============================================================================

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

def test_ultra_bullet_lifecycle_and_pyramiding():
    """Verify complete bullet lifecycle: INICIO -> CONFIRMACION -> RECYCLING -> VAULT -> CIERRE."""
    ultra_engine = UltraExploitationEngine()
    semantic_ai = SemanticQuantEngine()

    strat = semantic_ai.generate_candidate(symbol="ETH-USDT", track=ExecutionTrack.TRACK_ULTRA)
    
    # 1. Crear bala en INICIO (ETH a $2,000, 1R = $100 margen, 20x apalancamiento -> 1.0 ETH)
    bullet = ultra_engine.create_bullet(
        strategy=strat,
        bullet_id="bala_eth_01",
        direction=BulletTradeDirection.LONG,
        entry_price=2000.0,
        margin_r_usd=100.0,
        leverage=20.0,
    )

    assert bullet.entry_price_avg == 2000.0
    assert bullet.current_sl_price == 1900.0  # -1R ($100 / 1.0 ETH)
    assert bullet.pyramid_count == 0

    # 2. Precio sube a $2,120 (+1.2R) -> CONFIRMACION (Stop a Break-Even $2,000)
    bullet, state, _ = ultra_engine.process_price_tick(bullet, current_price=2120.0, timestamp_ms=1000)
    assert state == BalaState.CONFIRMACION
    assert bullet.current_sl_price == 2000.0  # Break-Even

    # 3. Precio sube a $2,250 (+2.5R = +$250) -> CRECIMIENTO_RECYCLING (Piramidación con House Money)
    bullet, state, _ = ultra_engine.process_price_tick(bullet, current_price=2250.0, timestamp_ms=2000)
    assert state == BalaState.CRECIMIENTO_RECYCLING
    assert bullet.pyramid_count == 1
    assert len(bullet.layers) == 2
    # El SL Free-Risk debe estar estrictamente por encima del precio medio de entrada
    assert bullet.current_sl_price > bullet.entry_price_avg

    # 4. Precio sube a $2,400 (+4.0R) -> COSECHA_VAULT (Ratchet Trigger)
    bullet, state, harvest = ultra_engine.process_price_tick(bullet, current_price=2400.0, timestamp_ms=3000)
    assert state == BalaState.COSECHA_VAULT
    assert harvest is not None
    assert harvest.harvested_amount_usd > 0.0
    assert harvest.peak_unrealized_r >= 3.0

    # 5. Reversión de precio a Stop Loss -> CIERRE con beneficio garantizado
    closed_bullet, final_state, _ = ultra_engine.process_price_tick(bullet, current_price=bullet.current_sl_price - 1.0, timestamp_ms=4000)
    assert final_state == BalaState.CIERRE
    assert closed_bullet.closed_at_ms is not None
    assert closed_bullet.realized_net_pnl_usd > 0.0
