"""tests/test_floating_vs_realized_gates.py
Suite de tests para validación de compuertas: Drawdown Flotante vs Drawdown Realizado.
"""

from __future__ import annotations

import math
import numpy as np
import pytest

from contracts.canonical_strategy import (
    CanonicalStrategy,
    ExecutionTrack,
    StrategyLifecycleStatus,
    TargetInstrument,
    RuleTree,
    ExitModel,
    SizingAndRisk,
    ProvenanceMetadata,
)
from contracts.validation_contracts import (
    ValidationTrack,
    FondeoValidationCriteria,
    FondeoValidationResult,
    UltraValidationCriteria,
    UltraValidationResult,
    BalaExecutionRecord,
    BalaState,
    BalaHarvestEvent,
)
from services.validation.quant_validation_fabric import (
    QuantValidationFabric,
    FondeoEvidenceGate,
    UltraEvidenceGate,
)
from services.validation.candidate_registry import CandidateRegistry
from services.exploitation_engines.prop_firm_engine import (
    PropFirmEvaluationEngine,
    PROP_FIRM_CATALOG,
)
from services.api.app.factory.quality_gates import (
    rentable,
    is_ruinous,
    drawdown_sustainable,
    drawdown_acceptable,
    drawdown_penalty_factor,
    calmar_ratio,
    MAX_ACCEPTABLE_DRAWDOWN_PCT,
)
from services.api.app.factory.strategy_evidence import (
    StrategyEvidenceJudge,
    EvidenceStatus,
)


def classify_strategy_tier(
    realized_dd_pct: float,
    fondeo_passed: bool,
    dsr_score: float = 2.5,
    profit_factor: float = 1.8,
) -> str:
    if realized_dd_pct >= MAX_ACCEPTABLE_DRAWDOWN_PCT or realized_dd_pct >= 90.0:
        return "TIER_4_REJECTED_CRITICAL_DD"
    if fondeo_passed and realized_dd_pct <= 4.5 and dsr_score >= 2.0:
        return "TIER_1_FONDEO_APPROVED"
    if realized_dd_pct <= 15.0 and profit_factor >= 1.30:
        return "TIER_2_CANDIDATE_MONITORING"
    return "TIER_3_RESEARCH_INVESTIGATION"


def test_floating_75_realized_3_5_passes_fondeo_evidence_gate():
    gate = FondeoEvidenceGate(
        criteria=FondeoValidationCriteria(
            max_realized_drawdown_pct=4.5,
            max_floating_drawdown_pct=80.0,
            min_deflated_sharpe=2.0,
            min_profit_factor_is=1.30,
            min_profit_factor_oos=1.15,
            min_walk_forward_efficiency=0.60,
        )
    )

    initial_cap = 50000.0
    # IS: Profit factor = 170 / 100 = 1.70
    is_trades = [170.0, -100.0] * 50

    # OOS: Profit factor = (50 * 170) / (49 * 100 + 1750) = 8500 / 6650 = 1.28 >= 1.15
    oos_trades = []
    for i in range(100):
        if i == 20:
            pnl = -1750.0  # Max dip realizado de $1,750 (3.5% sobre $50,000)
        elif i % 2 == 0:
            pnl = 170.0
        else:
            pnl = -100.0
        oos_trades.append(pnl)

    daily_pnls = [250.0, 180.0, -150.0, 320.0, 110.0, -200.0, 400.0]

    result = gate.evaluate(
        strategy_id="UR-STRAT-FLOAT75-REAL35",
        is_trades=is_trades,
        oos_trades=oos_trades,
        daily_pnls=daily_pnls,
        dsr_score=2.45,
        mc_ruin_pct=0.0,
        floating_drawdowns=[75.0],
        margin_call_occurred=False,
    )

    assert result.passed is True, f"Fondeo Gate debió aprobar la estrategia: {result.rejection_reasons}"
    assert result.max_realized_drawdown_pct <= 4.5
    assert result.max_floating_drawdown_pct <= 80.0
    assert result.deflated_sharpe_ratio >= 2.0
    assert result.daily_loss_limit_violations == 0
    assert result.walk_forward_efficiency >= 0.60
    assert len(result.rejection_reasons) == 0

    tier = classify_strategy_tier(
        realized_dd_pct=result.max_realized_drawdown_pct,
        fondeo_passed=result.passed,
        dsr_score=result.deflated_sharpe_ratio,
    )
    assert tier == "TIER_1_FONDEO_APPROVED"


def test_realized_91_3_rejected_by_fondeo_evidence_gate():
    gate = FondeoEvidenceGate()

    initial_cap = 50000.0
    oos_trades = [-45650.0] + [50.0 if i % 2 == 0 else -50.0 for i in range(50)]
    is_trades = [100.0, -50.0] * 30

    result = gate.evaluate(
        strategy_id="UR-STRAT-REAL913-REJECT",
        is_trades=is_trades,
        oos_trades=oos_trades,
        dsr_score=1.1,
    )

    assert result.passed is False
    assert result.max_realized_drawdown_pct >= 91.0
    assert any("Max Realized DD excesivo" in r for r in result.rejection_reasons)

    tier = classify_strategy_tier(
        realized_dd_pct=result.max_realized_drawdown_pct,
        fondeo_passed=result.passed,
        dsr_score=result.deflated_sharpe_ratio,
    )
    assert tier == "TIER_4_REJECTED_CRITICAL_DD"
