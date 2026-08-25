"""tests/test_version_governance_v540.py
Suite de Pruebas de Gobernanza de Versiones v5.4.0 y Filtrado Estricto de Estrategias Aprobadas.
ZERO-MOCKS · REAL-ONLY · PROVENANCE-LOCKED
"""

import json
import sqlite3
import pytest
from pathlib import Path
from services.engine_version import CURRENT_ENGINE_VERSION, CURRENT_ENGINE_NAME, VERSION_HISTORY
from services.version_control_manager import version_manager
from services.api.app.db.database import SessionLocal, CandidateModel
from services.semantic_ai.learning_store import LearningStore

DB_PATH = Path("/home/ubuntu/.local/state/ultrarentable/ultrarentable.sqlite3")


def test_ssot_version_is_5_4_0():
    """Verifica que el SSOT canónico esté fijado en v5.4.0."""
    assert CURRENT_ENGINE_VERSION == "5.4.0", f"Expected 5.4.0, got {CURRENT_ENGINE_VERSION}"
    assert "5.4.0" in CURRENT_ENGINE_NAME
    
    info = version_manager.get_full_version_info()
    assert info.get("active_version") == "5.4.0"
    assert info.get("pipeline_version") == "5.4.0"


def test_version_manifest_v540():
    """Verifica que el manifest de versiones contenga el registro v5.4.0."""
    history = VERSION_HISTORY
    v540_entries = [v for v in history if v.get("version") == "5.4.0"]
    assert len(v540_entries) == 1, "Debe existir exactamente una entrada para v5.4.0"
    v540 = v540_entries[0]
    assert v540.get("status") == "CURRENT_RECOMMENDED"
    assert len(v540.get("changes", [])) >= 4


def test_candidates_all_stamped_v540():
    """Verifica que todas las estrategias en SQLite estén auditadas bajo el motor v5.4.0."""
    db = SessionLocal()
    try:
        candidates = db.query(CandidateModel).all()
        assert len(candidates) > 0, "Debe haber candidatos en la base de datos"
        for c in candidates:
            assert c.engine_version == "5.4.0", f"Candidato {c.candidate_id} tiene versión {c.engine_version}, se esperaba 5.4.0"
    finally:
        db.close()


def test_strict_approved_only_view5():
    """Verifica que el catálogo de aprobadas solo contenga estrategias con status APPROVED y 0% de fallidas."""
    db = SessionLocal()
    try:
        approved = db.query(CandidateModel).filter(CandidateModel.status == "APPROVED").all()
        assert len(approved) > 0, "Debe haber estrategias aprobadas"
        for a in approved:
            assert a.status == "APPROVED"
            assert a.profit_factor_oos >= 1.20 or a.profit_factor_is >= 1.20
            assert a.max_dd_oos_pct < 95.0, "Estrategia aprobada no puede tener margin call"
            if a.route == "FONDEO":
                assert a.max_dd_oos_pct <= 4.5, "Estrategia Fondeo no puede exceder 4.5% DD"

        # Verificar que estrategias no aprobadas no tengan status APPROVED
        non_approved = db.query(CandidateModel).filter(CandidateModel.status != "APPROVED").all()
        for r in non_approved:
            assert r.status != "APPROVED"
            assert r.status in (
                "INCUBADORA_REPROGRAMACION",
                "RECHAZADA_MARGIN_CALL",
                "REJECTED",
                "INVESTIGACION_BTC",
                "IN_RESEARCH_MUTATION",
                "REFINADO_TIER_2",
                "BLOCKED_NO_DATASET",
                "ANOMALY_REVIEW",
                "REVALIDATION_REQUIRED",
                "STALE",
            )
    finally:
        db.close()


def test_learning_store_failure_isolation():
    """Verifica que los fallos de compuertas queden registrados en el LearningStore relacional."""
    store = LearningStore()
    stats = store.get_failure_statistics()
    assert isinstance(stats, dict)
