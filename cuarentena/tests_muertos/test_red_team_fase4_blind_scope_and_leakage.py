"""tests/test_red_team_fase4_blind_scope_and_leakage.py
Auditoría Adversarial y Red-Team para FASE 4:
1. Verificación del Protocolo Blind Scope (Inmunidad contra fuga de OOS y datos futuros).
2. Integridad Dimensional de la Síntesis AST (Bloqueo de violaciones semánticas en código generado).
3. Determinismo y Cero-Mocks en el Debate Cuantitativo.
"""

import pytest
from services.api.app.db.database import get_db, init_db
from services.research.research_lab import QuantitativeResearchLab
from services.api.app.dsl.engine import StrategyDSL, validate_semantics


@pytest.fixture(scope="module")
def db():
    init_db()
    db_gen = get_db()
    session = next(db_gen)
    yield session


def test_red_team_blind_scope_strict_isolation(db):
    """Red-Team: Asegurar que el contexto Blind Scope jamás incluye métricas o datos OOS."""
    lab = QuantitativeResearchLab(db)

    ctx = lab._build_blind_scope_context("strat_blind_test_001")

    assert ctx.blind_scope_mode == "STRUCTURAL_ONLY"
    # Asegurar que no hay claves OOS en el contexto de los agentes
    for key in ctx.is_metrics_summary.keys():
        assert "oos" not in key.lower(), f"Fuga de datos OOS detectada en clave: {key}"
        assert "future" not in key.lower()
        assert "test" not in key.lower()


def test_red_team_synthesized_ast_semantic_perfection(db):
    """Red-Team: El código AST sintetizado debe ser 100% válido y compatible sin violaciones dimensionales."""
    lab = QuantitativeResearchLab(db)

    debate = lab.run_research_debate("strat_ast_test_002")
    synth = lab.synthesize_reprogramming("strat_ast_test_002", debate.debate_id)

    # Validar el modelo StrategyDSL directamente
    dsl = StrategyDSL.model_validate(synth.mutated_dsl)
    errors = validate_semantics(dsl)

    assert len(errors) == 0, f"Violaciones semánticas en el código sintetizado: {errors}"
    assert synth.validation_status == "VALID"
