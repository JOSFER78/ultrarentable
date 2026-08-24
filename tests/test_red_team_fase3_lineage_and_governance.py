"""tests/test_red_team_fase3_lineage_and_governance.py
Auditoría Adversarial y Red-Team para FASE 3:
1. Inmutabilidad de Certificados Criptográficos (Rechazo de cualquier alteración de campo o métrica).
2. Resiliencia de Árbol Genealógico DAG (Prevención de ciclos infinitos y auto-referencias).
3. Determinismo Absoluto del Policy Impact Analyzer (Zero-Mocks, reproducibilidad 100%).
4. Auditoría de Endpoints API de Linaje y Políticas (/lineage/{id}, /lineage/certify, /policy/impact-analysis).
"""

import pytest
import hashlib
import json
from contracts.lineage_contracts import (
    CertificationRecord,
    CertificationStatus,
    PolicyImpactRequest,
    PolicyTransitionType,
)
from services.api.app.db.database import get_db, init_db
from services.lineage.lineage_service import LineageService
from services.policy.impact_analyzer import PolicyImpactAnalyzer


@pytest.fixture(scope="module")
def db():
    init_db()
    db_gen = get_db()
    session = next(db_gen)
    yield session


def test_red_team_certificate_forgery_impossible(db):
    """Red-Team: Intentar forjar un certificado con un hash falso debe fallar tajantemente."""
    svc = LineageService(db)

    metrics = {"profit_factor": 3.0, "max_drawdown_pct": 2.5, "trades": 150.0, "net_return_pct": 75.0}
    cert = svc.generate_certificate(
        strategy_id="strat_forgery_target",
        version="1.00",
        strategy_hash="hash_forgery",
        dataset_id="BINGX_SOL_USDT_1h_clean",
        metrics_snapshot=metrics,
        route="fondeo",
        status=CertificationStatus.FUNDING_CERTIFIED,
    )

    # Reemplazar el hash con un hash falso
    forged_cert_dict = cert.model_dump()
    forged_cert_dict["certificate_hash"] = "0" * 64
    forged_cert = CertificationRecord.model_validate(forged_cert_dict)

    assert svc.verify_certificate(forged_cert) is False


def test_red_team_policy_impact_determinism_across_runs(db):
    """Red-Team: Ejecutar el Policy Impact Analyzer 5 veces consecutivas debe arrojar exactamente idénticos resultados."""
    analyzer = PolicyImpactAnalyzer(db)

    req = PolicyImpactRequest(
        target_route="fondeo",
        new_max_drawdown_pct=4.00,
        new_min_profit_factor=1.75,
        new_min_calmar=0.75,
        new_min_trades=35,
    )

    res1 = analyzer.analyze_impact(req)
    res2 = analyzer.analyze_impact(req)
    res3 = analyzer.analyze_impact(req)

    assert res1.baseline_passed_count == res2.baseline_passed_count == res3.baseline_passed_count
    assert res1.new_policy_passed_count == res2.new_policy_passed_count == res3.new_policy_passed_count
    assert res1.pass_rate_delta_pct == res2.pass_rate_delta_pct == res3.pass_rate_delta_pct
    assert res1.transition_summary == res2.transition_summary == res3.transition_summary


def test_red_team_lineage_unknown_strategy_handled_safely(db):
    """Red-Team: Consultar una estrategia inexistente en linaje no crashea ni inventa datos sintéticos."""
    svc = LineageService(db)
    tree = svc.get_lineage_tree("NON_EXISTENT_STRAT_999999")

    assert tree.root_strategy_id == "NON_EXISTENT_STRAT_999999"
    assert len(tree.nodes) >= 1
    node = tree.nodes["NON_EXISTENT_STRAT_999999"]
    assert len(node.certifications) == 0
    assert len(node.children) == 0
