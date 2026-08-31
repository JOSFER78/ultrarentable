"""Suite de gobernanza de versiones del motor (SSOT 5.6.0) y filtrado estricto de aprobadas.
ZERO-MOCKS · REAL-ONLY · PROVENANCE-LOCKED

Regla #26 de la doctrina: al subir CURRENT_ENGINE_VERSION, toda certificación con versión
anterior deja de contar como aprobada (pasa a LEGACY_MOTOR_* / reclasificación); las filas
históricas se conservan. Por tanto la invariante NO es "todos los candidatos llevan la versión
vigente", sino "ningún candidato en estado aprobado lleva una versión que no sea la vigente".
"""

import pytest
from services.engine_version import CURRENT_ENGINE_VERSION, CURRENT_ENGINE_NAME, VERSION_HISTORY
from services.version_control_manager import version_manager
from services.api.app.db.database import SessionLocal, CandidateModel
from services.semantic_ai.learning_store import LearningStore

APPROVED_STATUSES = ("APPROVED", "APPROVED_CURRENT_ENGINE")


def test_ssot_version_is_current():
    assert CURRENT_ENGINE_VERSION == "5.13.0"
    assert "5.13.0" in CURRENT_ENGINE_NAME
    info = version_manager.get_full_version_info()
    assert info.get("active_version") == "5.13.0"


def test_version_history_current_entry():
    current_entries = [v for v in VERSION_HISTORY if v.get("version") == CURRENT_ENGINE_VERSION]
    assert len(current_entries) == 1
    assert current_entries[0].get("status") == "CURRENT_RECOMMENDED"
    assert len(current_entries[0].get("changes", [])) >= 1
    # Solo una entrada puede ser la recomendada.
    recommended = [v for v in VERSION_HISTORY if v.get("status") == "CURRENT_RECOMMENDED"]
    assert len(recommended) == 1


def test_no_approved_with_stale_engine():
    """Regla #26: un estado aprobado con motor no vigente es una certificación fantasma."""
    db = SessionLocal()
    try:
        approved = (
            db.query(CandidateModel)
            .filter(CandidateModel.status.in_(APPROVED_STATUSES))
            .all()
        )
        stale = [c for c in approved if c.engine_version != CURRENT_ENGINE_VERSION]
        assert not stale, (
            f"{len(stale)} candidatos en estado aprobado con motor no vigente "
            f"(p.ej. {stale[0].candidate_id} @ {stale[0].engine_version}); "
            "requieren reclasificación LEGACY_MOTOR_* (regla #26)"
        )
    finally:
        db.close()


def test_approved_requires_gate_evidence():
    """Un estado aprobado con gates_passed=0 es una aprobación sin evidencia: prohibido.

    La columna física gates_passed no está mapeada en CandidateModel; se consulta por SQL.
    """
    from sqlalchemy import text

    db = SessionLocal()
    try:
        rows = db.execute(
            text(
                "SELECT candidate_id, gates_passed FROM candidates "
                "WHERE status IN ('APPROVED', 'APPROVED_CURRENT_ENGINE') "
                "AND (gates_passed IS NULL OR gates_passed = 0)"
            )
        ).fetchall()
        assert not rows, (
            f"{len(rows)} candidatos aprobados con gates_passed=0 (p.ej. {rows[0][0]})"
        )
    finally:
        db.close()


def test_strict_approved_metrics():
    """Solo puede existir un aprobado cuando sus métricas son compatibles con la política actual."""
    db = SessionLocal()
    try:
        approved = (
            db.query(CandidateModel)
            .filter(CandidateModel.status.in_(APPROVED_STATUSES))
            .all()
        )
        for a in approved:
            assert a.profit_factor_oos >= 1.20 or a.profit_factor_is >= 1.20
            assert a.max_dd_oos_pct < 95.0
            if a.route == "FONDEO":
                assert a.max_dd_oos_pct <= 4.5
    finally:
        db.close()


def test_learning_store_failure_isolation():
    store = LearningStore()
    stats = store.get_failure_statistics()
    assert isinstance(stats, dict)
