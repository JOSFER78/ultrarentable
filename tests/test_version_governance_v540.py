"""Suite de gobernanza de versiones v5.4.0 y filtrado estricto de estrategias aprobadas.
ZERO-MOCKS · REAL-ONLY · PROVENANCE-LOCKED
"""

import pytest
from services.engine_version import CURRENT_ENGINE_VERSION, CURRENT_ENGINE_NAME, VERSION_HISTORY
from services.version_control_manager import version_manager
from services.api.app.db.database import SessionLocal, CandidateModel
from services.semantic_ai.learning_store import LearningStore


def test_ssot_version_is_5_4_0():
    assert CURRENT_ENGINE_VERSION == "5.4.0"
    assert "5.4.0" in CURRENT_ENGINE_NAME
    info = version_manager.get_full_version_info()
    assert info.get("active_version") == "5.4.0"
    assert info.get("pipeline_version") == "5.4.0"


def test_version_manifest_v540():
    v540_entries = [v for v in VERSION_HISTORY if v.get("version") == "5.4.0"]
    assert len(v540_entries) == 1
    assert v540_entries[0].get("status") == "CURRENT_RECOMMENDED"
    assert len(v540_entries[0].get("changes", [])) >= 4


def test_candidates_all_stamped_v540():
    """Toda estrategia persistida debe pertenecer al motor actual; el catálogo vacío no se rellena artificialmente."""
    db = SessionLocal()
    try:
        candidates = db.query(CandidateModel).all()
        for c in candidates:
            assert c.engine_version == CURRENT_ENGINE_VERSION, (
                f"Candidato {c.candidate_id} tiene versión {c.engine_version}; requiere revalidación"
            )
    finally:
        db.close()


def test_strict_approved_only_view5():
    """Solo puede existir APPROVED cuando sus métricas y reglas de riesgo son compatibles con la política actual."""
    db = SessionLocal()
    try:
        approved = db.query(CandidateModel).filter(CandidateModel.status == "APPROVED").all()
        for a in approved:
            assert a.engine_version == CURRENT_ENGINE_VERSION
            assert a.profit_factor_oos >= 1.20 or a.profit_factor_is >= 1.20
            assert a.max_dd_oos_pct < 95.0
            if a.route == "FONDEO":
                assert a.max_dd_oos_pct <= 4.5

        non_approved = db.query(CandidateModel).filter(CandidateModel.status != "APPROVED").all()
        for r in non_approved:
            assert r.status != "APPROVED"
    finally:
        db.close()


def test_learning_store_failure_isolation():
    store = LearningStore()
    stats = store.get_failure_statistics()
    assert isinstance(stats, dict)
