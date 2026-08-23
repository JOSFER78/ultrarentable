"""tests/test_ultra_and_fondeo_doctrine.py
Suite Maestra Automatizada de Validación Cuantitativa Formal para Ultrarentable V2.
Cubre:
  1) Aprobación Ultra con DD Flotante 80% y DD Realizado 75% con ROI masivo y convexidad.
  2) Aprobación Fondeo con DD Realizado <= 4.5% en cuentas de 25k a 300k USD.
  3) Rechazo sistemático de violaciones de reglas en ambas rutas.
"""

from __future__ import annotations

import math
from typing import List
import numpy as np
import pytest

from contracts.canonical_strategy import (
    CanonicalStrategy,
    ExecutionTrack,
    StrategyLifecycleStatus,
)
from contracts.validation_contracts import (
    ValidationTrack,
    ValidationTier,
    FondeoValidationCriteria,
    FondeoValidationResult,
    UltraValidationCriteria,
    UltraValidationResult,
    BalaExecutionRecord,
    BalaState,
    BalaHarvestEvent,
    EvidenceGateDecision,
)
from services.validation.quant_validation_fabric import (
    QuantValidationFabric,
    FondeoEvidenceGate,
    UltraEvidenceGate,
)
from services.exploitation_engines.prop_firm_engine import (
    PropFirmEvaluationEngine,
    PropFirmRules,
    PROP_FIRM_CATALOG,
)
from services.api.app.factory.quality_gates import (
    rentable,
    is_ruinous,
    drawdown_sustainable,
    drawdown_penalty_factor,
    MAX_ACCEPTABLE_DRAWDOWN_PCT,
    RIVETING_DRAWDOWN_PCT,
)


# ============================================================================
# BLOQUE 1: APROBACIÓN TRACK ULTRA (CONVEXIDAD ASIMÉTRICA & ALTO DRAWDOWN)
# ============================================================================

def test_ultra_strategy_approval_with_high_drawdown_massive_roi_and_vault():
    """Valida formalmente una estrategia ULTRA con:
      - Drawdown Flotante del 80.0%
      - Drawdown Realizado del 75.0%
      - Asimetría Hiperconvexa (Payoff Ratio > 2.5, Skewness > 0.5)
      - Tail Gain Ratio >= 40% (ganancias en trades >= 3R)
      - Cosecha activa a Bóveda Ratchet
    """
    criteria = UltraValidationCriteria(
        min_payoff_ratio=2.5,
        min_expected_r_per_bala=0.20,
        min_tail_gain_ratio=0.40,
        min_positive_skewness=0.50,
        min_vault_harvest_rate_pct=10.0,
        min_walk_forward_vault_efficiency=0.50,
        max_burst_ruin_probability_pct=25.0,
        max_realized_drawdown_pct=75.0,
        max_floating_drawdown_pct=80.0,
        burst_size_balas=10,
        taker_fee_pct=0.050,
        slippage_bps_per_pyramid=3.0,
    )
    ultra_gate = UltraEvidenceGate(criteria=criteria)

    # Generación de 60 balas de prueba:
    # 50 balas con pérdida acotada de -1.0R ($100 margen aislado)
    # 10 balas en mega-tendencia con piramidación (+18.5R promedio)
    oos_balas: List[BalaExecutionRecord] = []
    is_balas: List[BalaExecutionRecord] = []

    for i in range(60):
        if i % 6 == 0:
            record = BalaExecutionRecord(
                bala_id=f"bala_ultra_win_{i}",
                entry_time_ms=1771437600000 + i * 3600000,
                exit_time_ms=1771437600000 + (i + 1) * 3600000,
                margin_cost_usd=100.0,
                gross_pnl_usd=1850.0,
                net_pnl_usd=1840.0,
                return_r=18.4,
                reached_state=BalaState.COSECHA_VAULT,
                pyramid_levels_executed=3,
                friction_cost_usd=10.0,
                max_floating_drawdown_pct=80.0,
                margin_call=False,
                harvest_events=[
                    BalaHarvestEvent(
                        bala_id=f"bala_ultra_win_{i}",
                        timestamp_ms=1771437600000 + i * 3600000 + 1800000,
                        harvested_amount_usd=920.0,
                        vault_cumulative_usd=920.0 * (i // 6 + 1),
                        peak_unrealized_r=19.0,
                    )
                ],
            )
        else:
            record = BalaExecutionRecord(
                bala_id=f"bala_ultra_loss_{i}",
                entry_time_ms=1771437600000 + i * 3600000,
                exit_time_ms=1771437600000 + (i + 1) * 3600000,
                margin_cost_usd=100.0,
                gross_pnl_usd=-100.0,
                net_pnl_usd=-102.0,
                return_r=-1.02,
                reached_state=BalaState.CIERRE,
                pyramid_levels_executed=0,
                friction_cost_usd=2.0,
                max_floating_drawdown_pct=75.0,
                margin_call=False,
            )
        oos_balas.append(record)
        is_balas.append(record)

    result = ultra_gate.evaluate(
        strategy_id="UR-ULTRA-HYPERCONVEX-01",
        is_balas=is_balas,
        oos_balas=oos_balas,
        floating_drawdowns=[80.0],
        margin_call_occurred=False,
    )

    assert result.passed is True, f"Ultra Gate no debió rechazar: {result.rejection_reasons}"
    assert result.tier == ValidationTier.TIER_1_CERTIFIED
    assert result.payoff_ratio >= 2.5
    assert result.tail_gain_ratio >= 0.40
    assert result.skewness >= 0.50
    assert result.vault_harvest_rate_pct >= 10.0
    assert result.total_harvested_to_vault_usd > 0.0
    assert result.friction_stress_passed is True
    assert result.margin_call_occurred is False
    assert len(result.rejection_reasons) == 0

    net_return_pct = ((10 * 1840.0 - 50 * 102.0) / 1000.0) * 100.0
    assert rentable(net_return_pct=net_return_pct, profit_factor=3.6, drawdown_pct=75.0, mode="ultra") is True
    assert is_ruinous(75.0) is False
    assert drawdown_sustainable(75.0, mode="ultra") is True


# ============================================================================
# BLOQUE 2: APROBACIÓN TRACK FONDEO MULTI-ESCALA (CUENTAS 25K A 300K)
# ============================================================================

@pytest.mark.parametrize(
    "account_size,target_profit,max_dd_usd,dll_usd,max_single_trade_pct",
    [
        (25000.0, 1500.0, 1125.0, 500.0, 30.0),   # 25K: 4.5% DD = $1,125
        (50000.0, 3000.0, 2000.0, 1000.0, 35.0),  # 50K: 4.0% DD = $2,000
        (100000.0, 6000.0, 4500.0, 2000.0, 30.0), # 100K: 4.5% DD = $4,500
        (150000.0, 9000.0, 5000.0, 2500.0, 30.0), # 150K: 3.33% DD = $5,000
        (300000.0, 18000.0, 7500.0, 4000.0, 30.0),# 300K: 2.5% DD = $7,500
    ],
)
def test_fondeo_multi_tier_account_sizes_pass_evidence_gate(
    account_size: float,
    target_profit: float,
    max_dd_usd: float,
    dll_usd: float,
    max_single_trade_pct: float,
):
    """Valida formalmente la aprobación de estrategias de Fondeo en todas las escalas
    de cuentas (25k a 300k) garantizando que el Max Drawdown Realizado <= 4.5%.
    """
    allowed_dd_pct = (max_dd_usd / account_size) * 100.0
    assert allowed_dd_pct <= 4.50

    criteria = FondeoValidationCriteria(
        min_sharpe=2.0,
        min_deflated_sharpe=2.0,
        max_realized_drawdown_pct=4.50,
        max_floating_drawdown_pct=80.0,
        max_daily_loss_limit_usd=dll_usd,
        max_ruin_probability_pct=0.00,
        min_profit_factor_is=1.30,
        min_profit_factor_oos=1.15,
        min_walk_forward_efficiency=0.60,
        max_top2_outlier_dependency_pct=15.0,
    )
    gate = FondeoEvidenceGate(criteria=criteria)

    step_win = target_profit / 40.0
    step_loss = step_win * 0.50
    oos_trades = [step_win if i % 2 == 0 else -step_loss for i in range(80)]
    is_trades = [step_win * 1.1 if i % 2 == 0 else -step_loss for i in range(80)]

    daily_pnls = [dll_usd * 0.4, dll_usd * 0.2, -dll_usd * 0.3, dll_usd * 0.5, dll_usd * 0.3]

    result = gate.evaluate(
        strategy_id=f"UR-FONDEO-{int(account_size/1000)}K",
        is_trades=is_trades,
        oos_trades=oos_trades,
        daily_pnls=daily_pnls,
        dsr_score=2.65,
        mc_ruin_pct=0.0,
        floating_drawdowns=[allowed_dd_pct * 0.8],
        margin_call_occurred=False,
    )

    assert result.passed is True
    assert result.tier == ValidationTier.TIER_1_CERTIFIED
    assert result.max_realized_drawdown_pct <= 4.50
    assert result.deflated_sharpe_ratio >= 2.0
    assert result.daily_loss_limit_violations == 0
    assert result.ruin_probability_pct == 0.00
    assert result.margin_call_occurred is False
    assert len(result.rejection_reasons) == 0

    prop_rules = PropFirmRules(
        firm_name=f"PropFirm_{int(account_size/1000)}K",
        account_size_usd=account_size,
        profit_target_usd=target_profit,
        max_total_drawdown_usd=max_dd_usd,
        daily_loss_limit_usd=dll_usd,
        consistency_pct=max_single_trade_pct,
        allow_automated_bots=True,
    )
    prop_engine = PropFirmEvaluationEngine()
    prop_eval = prop_engine.evaluate_strategy(
        rules=prop_rules,
        max_drawdown_usd=max_dd_usd * 0.60,
        max_daily_loss_usd=dll_usd * 0.40,
        total_profit_usd=target_profit * 1.2,
        max_single_day_profit_usd=target_profit * 0.20,
        is_automated_bot=True,
    )
    assert prop_eval.eligible is True
    assert prop_eval.drawdown_passed is True
    assert prop_eval.daily_limit_passed is True
    assert prop_eval.consistency_passed is True


# ============================================================================
# BLOQUE 3: RECHAZO DETERMINISTA DE VIOLACIONES
# ============================================================================

def test_fondeo_rejection_on_excessive_realized_drawdown():
    """Violación Fondeo: Drawdown Realizado > 4.5%."""
    gate = FondeoEvidenceGate()
    oos_trades = [-2600.0] + [100.0 if i % 2 == 0 else -50.0 for i in range(40)]
    is_trades = [100.0, -50.0] * 20

    result = gate.evaluate(
        strategy_id="UR-FAIL-DD",
        is_trades=is_trades,
        oos_trades=oos_trades,
        dsr_score=2.1,
    )
    assert result.passed is False
    assert result.tier == ValidationTier.TIER_4_REJECTED
    assert any("Max Realized DD excesivo" in r for r in result.rejection_reasons)


def test_fondeo_rejection_on_daily_loss_limit_violation():
    """Violación Fondeo: Pérdida diaria excede el límite."""
    gate = FondeoEvidenceGate()
    oos_trades = [100.0, -50.0] * 30
    is_trades = [100.0, -50.0] * 30
    daily_pnls = [200.0, -1250.0, 300.0]

    result = gate.evaluate(
        strategy_id="UR-FAIL-DLL",
        is_trades=is_trades,
        oos_trades=oos_trades,
        daily_pnls=daily_pnls,
        dsr_score=2.2,
    )
    assert result.passed is False
    assert result.daily_loss_limit_violations >= 1
    assert any("Daily Loss Limit" in r for r in result.rejection_reasons)


def test_ultra_rejection_on_real_ruin():
    """Violación Ultra: Ruina Real (Drawdown >= 100%)."""
    assert is_ruinous(100.0) is True
    assert is_ruinous(105.0) is True
    assert rentable(net_return_pct=500.0, profit_factor=3.0, drawdown_pct=100.0, mode="ultra") is False
    assert drawdown_sustainable(100.0, mode="ultra") is False
