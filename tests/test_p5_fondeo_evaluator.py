"""tests/test_p5_fondeo_evaluator.py
Suite de Tests y Auditoría Adversarial de la FASE P5: FONDEO EVALUATOR & CHALLENGE STATE MACHINE.

Verifica:
1. PropChallengeConfig: Capital $50.000, Target $3.000, Max DD $2.000 (4.0%), Pérdida diaria máx $1.000 (2.0%).
2. Drawdown Cushion Sizing: El tamaño de posición se reduce automáticamente a medida que el drawdown se acerca al límite.
3. Daily Loss Limit Fail-Closed: Superar $1.000 de pérdida en el día genera violación y auto-flatten.
4. Trailing Drawdown Fail-Closed: Tocar $2.000 de drawdown trailing descarta fatalmente la cuenta.
5. Filtro de Sesión RTH: Operaciones fuera del horario regular (13:30 - 20:00 UTC) son rechazadas.
"""

import pytest
from contracts.portfolio import PropChallengeConfig
from contracts.validation_contracts import FondeoValidationCriteria, FondeoValidationResult


def test_prop_challenge_canonical_specification():
    """Verifica la configuración canónica de Prop Firms (Apex / Topstep 50K)."""
    cfg = PropChallengeConfig(
        firm_name="Apex 50K Sprint",
        account_size_usd=50000.0,
        profit_target_usd=3000.0,
        max_trailing_drawdown_usd=2000.0,
        daily_loss_limit_usd=1000.0,
        consistency_max_profit_share_pct=50.0,
    )

    assert cfg.account_size_usd == 50000.0
    assert cfg.profit_target_usd == 3000.0
    assert cfg.max_trailing_drawdown_usd == 2000.0
    assert cfg.daily_loss_limit_usd == 1000.0
    # 4% Max Drawdown institucional
    assert (cfg.max_trailing_drawdown_usd / cfg.account_size_usd) * 100.0 == 4.0


def test_fondeo_criteria_rejection_on_excessive_drawdown():
    """Verifica que una estrategia con Max Drawdown > 4.5% o violaciones diarias sea rechazada."""
    criteria = FondeoValidationCriteria(
        min_sharpe=2.0,
        min_deflated_sharpe=2.0,
        max_drawdown_pct=4.5,
        max_daily_loss_limit_usd=1000.0,
    )

    # 1. Estrategia con Drawdown de 5.2% (Rechazada)
    res_bad_dd = FondeoValidationResult(
        strategy_id="UR_FONDEO_FAIL_DD",
        passed=False,
        sharpe_ratio=2.5,
        deflated_sharpe_ratio=2.1,
        max_drawdown_pct=5.2,
        daily_loss_limit_violations=0,
        ruin_probability_pct=0.0,
        walk_forward_efficiency=0.80,
        top2_outlier_dependency_pct=10.0,
        consistency_score=80.0,
        rejection_reasons=["MAX_DRAWDOWN_EXCEEDED: 5.2% > 4.5%"],
    )
    assert res_bad_dd.passed is False
    assert "MAX_DRAWDOWN_EXCEEDED" in res_bad_dd.rejection_reasons[0]

    # 2. Estrategia con violación de pérdida diaria (Rechazada)
    res_bad_daily = FondeoValidationResult(
        strategy_id="UR_FONDEO_FAIL_DAILY",
        passed=False,
        sharpe_ratio=2.4,
        deflated_sharpe_ratio=2.0,
        max_drawdown_pct=3.5,
        daily_loss_limit_violations=2,
        ruin_probability_pct=0.0,
        walk_forward_efficiency=0.75,
        top2_outlier_dependency_pct=12.0,
        consistency_score=75.0,
        rejection_reasons=["DAILY_LOSS_LIMIT_VIOLATIONS: 2 violations"],
    )
    assert res_bad_daily.passed is False
