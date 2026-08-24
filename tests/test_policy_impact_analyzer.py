"""tests/test_policy_impact_analyzer.py
Pruebas Unitarias y de Integración para el Policy Impact Analyzer.
Especificación oficial según Sección 7 y 8 del Informe Maestro v5.3.0.
"""

import pytest
from contracts.lineage_contracts import (
    PolicyImpactRequest,
    PolicyImpactResult,
    PolicyTransitionType,
)
from services.api.app.db.database import get_db, init_db, CandidateModel
from services.policy.impact_analyzer import PolicyImpactAnalyzer, evaluate_policy_verdict


@pytest.fixture(scope="module")
def db():
    init_db()
    db_gen = get_db()
    session = next(db_gen)
    yield session


def test_evaluate_policy_verdict_deterministic_rules():
    """Prueba la función pura de evaluación de veredictos según umbrales de política."""
    valid_metrics = {
        "trades": 60,
        "profitFactor": 2.1,
        "maxDrawdownPct": 3.5,
        "netReturnPct": 45.0,
        "calmar": 12.8,
    }

    # 1. Pasa Fondeo baseline
    passed, status, reason = evaluate_policy_verdict(
        valid_metrics, "fondeo", max_dd_pct=4.50, min_pf=1.60, min_calmar=0.5, min_trades=30, min_net_return=5.0
    )
    assert passed is True
    assert status == "APPROVED"
    assert reason is None

    # 2. Cae ante política más estricta (DD <= 3.0%)
    passed_strict, status_strict, reason_strict = evaluate_policy_verdict(
        valid_metrics, "fondeo", max_dd_pct=3.00, min_pf=1.60, min_calmar=0.5, min_trades=30, min_net_return=5.0
    )
    assert passed_strict is False
    assert status_strict == "REJECTED_ALTO_DRAWDOWN"
    assert "3.50% > 3.00%" in reason_strict

    # 3. Cae ante trades insuficientes (< 80)
    passed_trades, status_trades, reason_trades = evaluate_policy_verdict(
        valid_metrics, "fondeo", max_dd_pct=4.50, min_pf=1.60, min_calmar=0.5, min_trades=80, min_net_return=5.0
    )
    assert passed_trades is False
    assert status_trades == "REJECTED_LOW_TRADES"


def test_policy_impact_analyzer_simulation(db):
    """Simula el impacto de un cambio de política sobre las cohortes reales de la base de datos."""
    analyzer = PolicyImpactAnalyzer(db)

    # 1. Petición con ajuste más exigente en Fondeo (Drawdown 4.5% -> 3.5%, PF 1.6 -> 1.8)
    req = PolicyImpactRequest(
        target_route="fondeo",
        new_max_drawdown_pct=3.50,
        new_min_profit_factor=1.80,
        new_min_calmar=0.8,
        new_min_trades=40,
    )

    result = analyzer.analyze_impact(req)

    assert isinstance(result, PolicyImpactResult)
    assert result.target_route == "fondeo"
    assert result.total_cohort_size >= 0
    assert result.pass_rate_new_pct <= result.pass_rate_baseline_pct + 0.01  # Al endurecer, la tasa de pase no puede aumentar significativamente
    assert "CONSISTENT_PASS" in result.transition_summary
    assert "REVOKED" in result.transition_summary
    assert result.revoked_count == result.transition_summary["REVOKED"]


def test_policy_impact_analyzer_relaxing_policy(db):
    """Simula el impacto al relajar una política (Drawdown 4.5% -> 10.0%, PF 1.6 -> 1.2)."""
    analyzer = PolicyImpactAnalyzer(db)

    req = PolicyImpactRequest(
        target_route="fondeo",
        new_max_drawdown_pct=10.0,
        new_min_profit_factor=1.20,
        new_min_calmar=0.1,
        new_min_trades=10,
    )

    result = analyzer.analyze_impact(req)

    assert isinstance(result, PolicyImpactResult)
    assert result.pass_rate_new_pct >= result.pass_rate_baseline_pct - 0.01
    assert result.newly_qualified_count == result.transition_summary["NEWLY_QUALIFIED"]
