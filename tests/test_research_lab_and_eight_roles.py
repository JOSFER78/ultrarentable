"""tests/test_research_lab_and_eight_roles.py
Pruebas Unitarias y de Integración para el Laboratorio Cuantitativo de Investigación y los 8 Roles.
Especificación oficial según Sección 7 y 8 del Informe Maestro v5.3.0.
"""

import pytest
from contracts.research_contracts import (
    ResearchDebateResponse,
    ResearchRole,
    ResearchSynthesisResponse,
)
from services.api.app.db.database import get_db, init_db
from services.research.research_lab import QuantitativeResearchLab
from services.semantic_ai.learning_store import learning_store


@pytest.fixture(scope="module")
def db():
    init_db()
    db_gen = get_db()
    session = next(db_gen)
    yield session


def test_research_debate_all_eight_roles_participate(db):
    """Verifica que el debate multi-agente involucra a los 8 roles especializados y produce consenso."""
    lab = QuantitativeResearchLab(db)

    debate = lab.run_research_debate("strat_test_debate_001")

    assert isinstance(debate, ResearchDebateResponse)
    assert debate.strategy_id == "strat_test_debate_001"
    assert debate.blind_scope == "STRUCTURAL_ONLY"
    assert len(debate.hypotheses) == 8

    # Verificar que los 8 roles están presentes
    roles_in_debate = {h.role for h in debate.hypotheses}
    for expected_role in ResearchRole:
        assert expected_role in roles_in_debate, f"Falta el rol {expected_role} en el debate"

    assert len(debate.consensus_hypothesis) > 20
    assert len(debate.recommended_mutations) >= 8
    assert 0.0 <= debate.disagreement_level <= 1.0

    # Verificar persistencia en LearningStore
    debates = learning_store.get_debates(limit=5)
    assert any(d.debate_id == debate.debate_id for d in debates)


def test_research_synthesis_produces_valid_ast_and_persists_experiment(db):
    """Verifica que la síntesis de reprogramación produce StrategyDSL válido y persiste en LearningStore."""
    lab = QuantitativeResearchLab(db)

    debate = lab.run_research_debate("strat_test_synth_002")
    synthesis = lab.synthesize_reprogramming("strat_test_synth_002", debate.debate_id)

    assert isinstance(synthesis, ResearchSynthesisResponse)
    assert synthesis.strategy_id == "strat_test_synth_002"
    assert synthesis.validation_status == "VALID"
    assert "signals" in synthesis.mutated_dsl
    assert "position" in synthesis.mutated_dsl
    assert "execution" in synthesis.mutated_dsl

    # Verificar registros persistidos en LearningStore
    proposals = learning_store.get_proposals(limit=5)
    assert any(p.proposal_id == synthesis.proposal_id for p in proposals)

    experiments = learning_store.get_experiments(limit=5)
    assert any(e.experiment_id == synthesis.experiment_id for e in experiments)
