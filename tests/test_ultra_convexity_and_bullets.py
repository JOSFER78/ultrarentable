"""tests/test_ultra_convexity_and_bullets.py
Pruebas de la Estructura de Balas ULTRA y Gestión Asimétrica de Beneficios (Fase 6).
"""

import pytest
from services.ultra.bala_convex_engine import BalaUltra, BalaPhase


def test_bala_ultra_initialization():
    """Verify BalaUltra starts with fixed bounded cash risk."""
    bala = BalaUltra(
        bala_id="bala_001",
        symbol="BTCUSDT",
        side="LONG",
        entry_price=60000.0,
        stop_loss_price=59000.0,
        take_profit_price=66000.0,
        initial_risk_cash_usd=100.0,
        max_allowed_loss_usd=100.0,
        initial_quantity=0.1,
        current_quantity=0.1,
    )
    assert bala.current_phase == BalaPhase.ARMED
    assert bala.pyramid_tiers_executed == 0


def test_bala_ultra_blocks_martingale_when_losing():
    """Verify that when price is below entry, pyramiding is strictly refused."""
    bala = BalaUltra(
        bala_id="bala_002",
        symbol="BTCUSDT",
        side="LONG",
        entry_price=60000.0,
        stop_loss_price=59000.0,
        take_profit_price=66000.0,
        initial_risk_cash_usd=100.0,
        max_allowed_loss_usd=100.0,
        initial_quantity=0.1,
        current_quantity=0.1,
    )
    # Price drops to 59500 (in loss)
    pyramid_ok = bala.evaluate_pyramiding_step(current_price=59500.0, current_atr=500.0)
    assert pyramid_ok is False
    assert bala.current_quantity == 0.1
    assert bala.stop_loss_price == 59000.0


def test_bala_ultra_pyramids_and_locks_profit_when_winning():
    """Verify that at +2R, stop loss is moved into profit and tier is added using profit reinvestment."""
    bala = BalaUltra(
        bala_id="bala_003",
        symbol="BTCUSDT",
        side="LONG",
        entry_price=60000.0,
        stop_loss_price=59000.0,
        take_profit_price=66000.0,
        initial_risk_cash_usd=100.0,
        max_allowed_loss_usd=100.0,
        initial_quantity=0.1,
        current_quantity=0.1,
    )
    # Price rises to 62000 (+2R)
    pyramid_ok = bala.evaluate_pyramiding_step(current_price=62000.0, current_atr=500.0)
    assert pyramid_ok is True
    assert bala.pyramid_tiers_executed == 1
    # Stop loss must be locked above entry (in profit)
    assert bala.stop_loss_price > 60000.0
    assert bala.current_quantity > 0.1
    assert bala.current_phase == BalaPhase.PYRAMIDING_REINVEST


def test_bala_ultra_harvests_to_vault():
    """Verify extraordinary gains (>= 4R) trigger harvest to secure vault."""
    bala = BalaUltra(
        bala_id="bala_004",
        symbol="BTCUSDT",
        side="LONG",
        entry_price=60000.0,
        stop_loss_price=59000.0,
        take_profit_price=68000.0,
        initial_risk_cash_usd=100.0,
        max_allowed_loss_usd=100.0,
        initial_quantity=0.1,
        current_quantity=0.1,
    )
    # Price rises to 65000 (+$500 profit = 5R on $100 risk)
    harvested = bala.harvest_to_vault(current_price=65000.0, timestamp_ms=1700000000)
    assert harvested > 0.0
    assert bala.vault_harvested_usd == harvested
    assert len(bala.harvest_events) == 1
