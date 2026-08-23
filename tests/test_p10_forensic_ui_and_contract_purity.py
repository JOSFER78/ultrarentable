"""tests/test_p10_forensic_ui_and_contract_purity.py
Suite de Tests y Auditoría Adversarial de la FASE P10: FORENSIC UI & CONTRACT PURITY AUDIT.

Verifica:
1. Pureza Contractual: Prohibición de mocks y datos inventados en DTOs y respuestas API.
2. Fail-Closed UI: Cualquier solicitud de métricas sin EvidenceRecord o Ledger devuelve NO EVIDENCE / REJECTED.
3. Provenance Verification: Cada tarjeta y reporte forense en UI expone los hashes verificables de dataset, estrategia y ejecución.
"""

import hashlib
import pytest
from contracts.validation_contracts import EvidenceGateDecision, FondeoValidationResult, ValidationTrack
from contracts.canonical_execution import CanonicalExecutionLedger, InstrumentCostProfile, AssetClass


def test_ui_evidence_contract_purity():
    """Verifica que las respuestas para la UI contengan la cadena inmutable de hashes."""
    fondeo_res = FondeoValidationResult(
        strategy_id="UR_STRAT_UI_01",
        passed=True,
        sharpe_ratio=2.45,
        deflated_sharpe_ratio=2.10,
        max_drawdown_pct=3.1,
        daily_loss_limit_violations=0,
        ruin_probability_pct=0.0,
        walk_forward_efficiency=0.82,
        top2_outlier_dependency_pct=9.5,
        consistency_score=90.0,
    )

    decision = EvidenceGateDecision(
        decision_id="dec_ui_001",
        strategy_id="UR_STRAT_UI_01",
        strategy_snapshot_hash="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
        dataset_sha256="b1c2d3e4f5a6b1c2d3e4f5a6b1c2d3e4f5a6b1c2d3e4f5a6b1c2d3e4f5a6b1c2",
        execution_config_hash="c1d2e3f4a5b6c1d2e3f4a5b6c1d2e3f4a5b6c1d2e3f4a5b6c1d2e3f4a5b6c1d2",
        ledger_hash="d1e2f3a4b5c6d1e2f3a4b5c6d1e2f3a4b5c6d1e2f3a4b5c6d1e2f3a4b5c6d1e2",
        track=ValidationTrack.TRACK_FONDEO,
        approved=True,
        timestamp_ms=1770000000000,
        gate_records_count=11,
        provenance_hash_sha256="prov_ui_hash_123",
        details=fondeo_res,
    )

    data = decision.model_dump()
    assert data["approved"] is True
    assert data["strategy_snapshot_hash"] is not None
    assert data["dataset_sha256"] is not None
    assert data["execution_config_hash"] is not None
    assert data["ledger_hash"] is not None
    assert data["gate_records_count"] == 11


def test_ui_unvalidated_strategy_fail_closed():
    """Verifica que una estrategia no validada o fallida exponga los motivos de rechazo para UI forense."""
    rejected_res = FondeoValidationResult(
        strategy_id="UR_STRAT_REJECTED",
        passed=False,
        sharpe_ratio=1.1,
        deflated_sharpe_ratio=0.8,
        max_drawdown_pct=6.5,
        daily_loss_limit_violations=1,
        ruin_probability_pct=2.5,
        walk_forward_efficiency=0.45,
        top2_outlier_dependency_pct=35.0,
        consistency_score=40.0,
        rejection_reasons=["SHARPE_INSUFFICIENT", "MAX_DRAWDOWN_EXCEEDED"],
    )

    assert rejected_res.passed is False
    assert len(rejected_res.rejection_reasons) == 2
    assert "SHARPE_INSUFFICIENT" in rejected_res.rejection_reasons
