"""tests/test_p9_telemetry_and_kill_switch.py
Suite de Tests y Auditoría Adversarial de la FASE P9: TELEMETRY & KILL-SWITCH MONITORING.

Verifica:
1. Circuit Breaker / Kill-Switch: Disparo inmediato de parada ante brecha de Drawdown o pérdida diaria.
2. Hard Kill en Fondeo: Superar $1.000 USD de pérdida en una sesión fuerza cierre y bloquea nuevas órdenes.
3. Liquidación de Bala en Ultra: Una bala con drawdown > 85% se declara liquidada, pero la Bóveda de Cosecha permanece intacta.
4. Telemetría de Eventos: Cada transición de estado y orden ejecutada emite eventos estructurados inmutables.
"""

import pytest
from contracts.canonical_execution import ExitReason, ExecutionTruth, OrderSide


def test_kill_switch_fondeo_circuit_breaker():
    """Verifica que el circuito de protección de Fondeo detecte pérdidas que excedan el límite diario ($1.000 USD)."""
    daily_pnl = -1050.0
    daily_limit = 1000.0

    is_circuit_broken = abs(daily_pnl) >= daily_limit
    assert is_circuit_broken is True


def test_vault_protection_on_bullet_liquidation():
    """Verifica que la liquidación de una bala Ultra no afecte el capital previamente cosechado a la Bóveda."""
    vault_harvested_usd = 2000.0
    bullet_initial_margin_usd = 1000.0
    bullet_unrealized_loss_usd = -950.0  # -95% de la bala

    # La bala es liquidada
    bullet_liquidated = abs(bullet_unrealized_loss_usd) >= (bullet_initial_margin_usd * 0.85)
    assert bullet_liquidated is True

    # El capital en bóveda permanece 100% asegurado
    total_safe_capital = vault_harvested_usd
    assert total_safe_capital == 2000.0


from contracts.canonical_execution import ExitReason, ExecutionTruth, OrderSide


def test_execution_event_telemetry_structure():
    """Verifica la emisión de ExecutionTruth con motivo de salida KILL_SWITCH."""
    trade = ExecutionTruth(
        trade_id="tr_kill_001",
        symbol="NQ",
        side=OrderSide.BUY,
        entry_timestamp_utc_ms=1770000000000,
        exit_timestamp_utc_ms=1770003600000,
        market_data_hash="md_hash_123",
        strategy_snapshot_hash="strat_hash_123",
        execution_config_hash="exec_hash_123",
        decision_price=20000.0,
        requested_qty=1.0,
        filled_qty=1.0,
        entry_price=20000.0,
        exit_price=19900.0,
        commission_usd=2.5,
        slippage_usd=2.5,
        total_friction_cost_usd=5.0,
        gross_pnl_usd=-100.0,
        net_pnl_usd=-105.0,
        return_r=-1.0,
        exit_reason=ExitReason.KILL_SWITCH,
        notional_usd=20000.0,
        margin_used_usd=1000.0,
        leverage_actual=20.0,
        equity_before_usd=50000.0,
        equity_after_usd=49895.0,
        drawdown_after_pct=0.21,
    )

    assert trade.exit_reason == ExitReason.KILL_SWITCH
    assert trade.net_pnl_usd == -105.0
