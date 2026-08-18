"""Unit and Integration Tests for PortfolioEngine and UltraExploitationEngine (Fase 6)."""

import pytest
import numpy as np

from contracts.portfolio import (
    AllocationMethod,
    BulletTradeDirection,
    PortfolioRequest,
    VaultRatchetConfig,
)
from contracts.validation_contracts import BalaState
from services.exploitation_engines import UltraExploitationEngine
from services.portfolio import PortfolioEngine


# ============================================================================
# TESTS: PORTFOLIO ENGINE (MULTI-ASSET & RISK PARITY / HRP)
# ============================================================================

def test_portfolio_engine_temporal_alignment_and_cov():
    """Verify temporal alignment of asset series and covariance matrix computation."""
    engine = PortfolioEngine()

    asset_returns = {
        "NQ": {1000: 0.01, 2000: -0.005, 3000: 0.015, 4000: 0.002},
        "ES": {1000: 0.008, 2000: -0.004, 3000: 0.012, 4000: 0.001},
        "BTC": {1000: 0.025, 2000: -0.015, 3000: 0.035, 4000: -0.005},
        "ETH": {1000: 0.030, 2000: -0.020, 3000: 0.040, 4000: -0.008},
    }

    symbols, ret_matrix = engine.align_return_series(asset_returns)
    assert symbols == ["BTC", "ES", "ETH", "NQ"]
    assert ret_matrix.shape == (4, 4)

    cov = engine.compute_covariance_matrix(ret_matrix)
    assert cov.shape == (4, 4)
    assert np.all(np.diag(cov) > 0)


def test_portfolio_engine_allocations_all_methods():
    """Verify optimization under Equal Weight, Inverse Volatility, ERC, and HRP."""
    engine = PortfolioEngine()

    asset_returns = {
        "NQ": {t: float(np.sin(t / 10.0) * 0.01 + 0.001) for t in range(50)},
        "ES": {t: float(np.sin(t / 10.0) * 0.008 + 0.0008) for t in range(50)},
        "BTC": {t: float(np.sin(t / 5.0) * 0.03 + 0.002) for t in range(50)},
        "ETH": {t: float(np.sin(t / 5.0) * 0.035 + 0.002) for t in range(50)},
    }

    methods = [
        AllocationMethod.EQUAL_WEIGHT,
        AllocationMethod.INVERSE_VOLATILITY,
        AllocationMethod.RISK_PARITY_ERC,
        AllocationMethod.HIERARCHICAL_RISK_PARITY,
    ]

    for m in methods:
        req = PortfolioRequest(
            portfolio_id=f"port_{m.value.lower()}",
            total_capital_usd=100000.0,
            method=m,
            candidate_strategy_ids=["BTC", "ES", "ETH", "NQ"],
        )
        allocation = engine.optimize_portfolio(req, asset_returns=asset_returns)

        # Check budget sum
        total_weight = sum(w.weight for w in allocation.weights)
        assert pytest.approx(total_weight, rel=1e-2) == 1.0

        total_cap = sum(w.target_capital_usd for w in allocation.weights)
        assert pytest.approx(total_cap, rel=1e-2) == 100000.0

        assert allocation.diversification_ratio >= 1.0
        assert len(allocation.provenance_hash_sha256) == 64


# ============================================================================
# TESTS: ULTRA EXPLOITATION ENGINE (BALAS FSM & BÓVEDA RATCHET)
# ============================================================================

def test_ultra_exploitation_engine_bullet_lifecycle_and_ratchet_harvest():
    """Verify full Bala lifecycle: INICIO -> CONFIRMACION -> PIRAMIDACION (40% House Money) -> COSECHA VAULT -> CIERRE."""
    vault_cfg = VaultRatchetConfig(
        milestone_2x_lock_pct=0.50,
        milestone_3x_lock_pct=0.65,
        milestone_5x_lock_pct=0.75,
        milestone_10x_lock_pct=0.85,
    )
    engine = UltraExploitationEngine(vault_config=vault_cfg, house_money_reinvest_ratio=0.40)

    # 1. Sembrar bala con $100 de margen inicial en LONG a precio 100.0 (leverage 20x -> $2000 notional)
    bullet = engine.launch_bullet(
        bullet_id="bala_sol_01",
        symbol="SOL-USDT",
        direction=BulletTradeDirection.LONG,
        initial_margin_usd=100.0,
        entry_price=100.0,
        leverage=20.0,
        stop_loss_ticks_or_pct=0.01,  # Initial SL at 99.0 (-1R)
    )
    assert bullet.current_sl_price == 99.0

    # 2. Precio sube a 106.0 (+1.2R -> +$120 pnl) -> CONFIRMACION (SL a Breakeven+)
    st, harvest = engine.on_price_update("bala_sol_01", current_price=106.0, timestamp_ms=1000)
    assert st == BalaState.CONFIRMACION
    assert harvest is None
    assert engine._active_bullets["bala_sol_01"].current_sl_price >= 100.0

    # 3. Precio sube a 112.0 (+2.4R) -> PIRAMIDACIÓN (Capa House Money 40%) & COSECHA BÓVEDA (Milestone 2x: 50%)
    st, harvest = engine.on_price_update("bala_sol_01", current_price=112.0, timestamp_ms=2000)
    assert st in (BalaState.CRECIMIENTO_RECYCLING, BalaState.COSECHA_VAULT)
    assert engine.get_vault_balance() > 0.0
    if harvest:
        assert harvest.harvested_amount_usd > 0.0
        assert harvest.vault_cumulative_usd == engine.get_vault_balance()

    # 4. Precio sube a 125.0 (+5.0R) -> PROTECCION & Trailing SL activo
    st, _ = engine.on_price_update("bala_sol_01", current_price=125.0, timestamp_ms=3000)
    assert st in (BalaState.COSECHA_VAULT, BalaState.PROTECCION)

    # 5. Precio cae a 115.0 y golpea Trailing SL -> CIERRE con ganancia neta asegurada
    trail_sl = engine._active_bullets["bala_sol_01"].current_sl_price
    st_close, _ = engine.on_price_update("bala_sol_01", current_price=trail_sl - 1.0, timestamp_ms=4000)
    assert st_close == BalaState.CIERRE

    # Verificar registro final inmutable de la bala
    rec = engine.get_bullet_record("bala_sol_01")
    assert rec is not None
    assert rec.net_pnl_usd > 0.0
    assert rec.return_r > 0.0
    assert engine.get_vault_balance() > 0.0
