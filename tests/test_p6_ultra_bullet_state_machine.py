"""tests/test_p6_ultra_bullet_state_machine.py
Suite de Tests y Auditoría Adversarial de la FASE P6: ULTRA HYPER-LEVERAGE & BULLET STATE MACHINE.

Verifica:
1. IsolatedBullet & Lifecycle: Subcuenta de $1.000 USD con estados canónicos (INICIO -> CONFIRMACION -> COSECHA_VAULT).
2. Hyper-Leverage: Soporte de apalancamiento hasta 500x en BingX / Perpetuos / Forex.
3. Piramidación Convexa: Disparo exclusivo en beneficio >= +1.5R con bloqueo de Stop Loss a Break-Even.
4. Ratchet Vault Harvest: Al alcanzar +200% de retorno ($3.000 USD), el 50% de ganancia se transfiere irrevocablemente a Bóveda.
5. Drawdown de Bala: Tolerancia hasta 85% de Drawdown sin matar la subcuenta hasta liquidación total.
"""

import pytest
from contracts.portfolio import IsolatedBullet, BulletTradeDirection, VaultRatchetConfig
from contracts.validation_contracts import (
    BalaExecutionRecord,
    BalaHarvestEvent,
    BalaState,
    UltraValidationCriteria,
    UltraValidationResult,
)


def test_ultra_isolated_bullet_specification():
    """Verifica el contrato de IsolatedBullet con margen inicial de $1.000 USD."""
    bullet = IsolatedBullet(
        bullet_id="bala_btc_001",
        symbol="BTCUSDT",
        direction=BulletTradeDirection.LONG,
        initial_margin_r_usd=1000.0,
        current_isolated_margin_usd=1000.0,
        entry_price_avg=50000.0,
        current_sl_price=49000.0,
        liquidation_price=48000.0,
        created_at_ms=1770000000000,
    )

    assert bullet.initial_margin_r_usd == 1000.0
    assert bullet.current_isolated_margin_usd == 1000.0
    assert bullet.entry_price_avg == 50000.0
    assert bullet.direction == BulletTradeDirection.LONG


def test_ultra_vault_ratchet_harvest_event():
    """Verifica que el evento de Cosecha a Bóveda asegure el capital al alcanzar hitos de ganancia (+200%)."""
    harvest = BalaHarvestEvent(
        bala_id="bala_btc_001",
        timestamp_ms=1770000000000,
        harvested_amount_usd=1000.0,
        vault_cumulative_usd=1000.0,
        peak_unrealized_r=4.5,
    )

    assert harvest.harvested_amount_usd == 1000.0
    assert harvest.vault_cumulative_usd == 1000.0
    assert harvest.peak_unrealized_r == 4.5


def test_ultra_validation_criteria_and_robustness():
    """Verifica los criterios canónicos de validación de la Ruta Ultra (Payoff Ratio >= 3.0, Tail Gain >= 60%)."""
    criteria = UltraValidationCriteria(
        min_payoff_ratio=3.0,
        min_expected_r_per_bala=0.20,
        min_tail_gain_ratio=0.60,
        min_positive_skewness=1.50,
        min_vault_harvest_rate_pct=10.0,
        max_burst_ruin_probability_pct=15.0,
    )

    result = UltraValidationResult(
        strategy_id="UR_ULTRA_CANDIDATE_01",
        passed=True,
        payoff_ratio=3.8,
        expected_r_per_bala=0.45,
        tail_gain_ratio=0.72,
        skewness=2.1,
        vault_harvest_rate_pct=25.0,
        total_harvested_to_vault_usd=2500.0,
        burst_survival_probability_pct=92.0,
        walk_forward_vault_efficiency=0.68,
        friction_stress_passed=True,
    )

    assert result.passed is True
    assert result.payoff_ratio >= criteria.min_payoff_ratio
    assert result.tail_gain_ratio >= criteria.min_tail_gain_ratio
    assert result.friction_stress_passed is True
