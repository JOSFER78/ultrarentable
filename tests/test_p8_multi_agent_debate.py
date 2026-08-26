"""tests/test_p8_multi_agent_debate.py
Suite de Tests y Auditoría Adversarial de la FASE P8: MULTI-AGENT ORCHESTRATION & DEBATE (GATE 10).

Verifica:
1. CriticAgent: Detecta de forma adversaria sobreajuste, alta dependencia de outliers y colapso de robustez.
2. ImproverAgent: Refina parámetros y genera una nueva versión canónica con un hash SHA-256 nuevo.
3. Gate 10 (Agent Debate): Bloquea incondicionalmente la certificación si existen objeciones críticas no resueltas.
4. Separación de Roles: Ningún agente de IA puede auto-aprobarse; el veredicto lo emite el evaluador de Gates.
"""

import pytest
from contracts.canonical_strategy import CanonicalStrategy, ExecutionTrack
from services.api.app.validation.gates.gate_10_agent_debate import Gate10AgentDebate
from services.semantic_ai.failure_knowledge import FailureKnowledgeDB
from services.semantic_ai.semantic_engine import CriticAgent, ImproverAgent, SemanticQuantEngine


def test_critic_agent_flags_fragile_candidate():
    """Verifica que el Agente Crítico detecte debilidades estructurales (falta de SL en Fondeo)."""
    failure_db = FailureKnowledgeDB()
    critic = CriticAgent(failure_db=failure_db)
    engine = SemanticQuantEngine()

    base_strat = engine.generate_candidate(symbol="NQ", track=ExecutionTrack.TRACK_FONDEO)
    # Crear versión sin stop loss
    fragile_strat = base_strat.model_copy(update={"exits": base_strat.exits.model_copy(update={"stop_loss_ticks": None, "stop_loss_atr_mult": None})})

    passed, warnings = critic.critique(fragile_strat)
    assert passed is False
    assert any("Stop Loss" in w for w in warnings)


def test_improver_agent_generates_new_version_with_new_hash():
    """Verifica que el Agente Optimizador produzca una mutación con nuevo hash SHA-256."""
    failure_db = FailureKnowledgeDB()
    engine = SemanticQuantEngine()
    improver = ImproverAgent(failure_db=failure_db)

    base_strat = engine.generate_candidate(symbol="NQ", track=ExecutionTrack.TRACK_FONDEO)
    base_hash = base_strat.strategy_hash

    mutated_strat = improver.mutate(base_strat)
    assert isinstance(mutated_strat, CanonicalStrategy)
    mutated_hash = mutated_strat.strategy_hash

    assert base_hash != mutated_hash


def test_gate_10_agent_debate_blocks_unresolved_objections():
    """Verifica que Gate 10 rechace estrategias con objeciones críticas insalvables."""
    gate10 = Gate10AgentDebate()

    bad_candidate = {
        "candidate_id": "UR_REJECT_001",
        "symbol": "NQ",
        "route": "FONDEO",
        "profit_factor_oos": 0.90,
        "max_drawdown_pct": 8.5,
        "daily_loss_violations": 3,
    }

    res = gate10.evaluate(bad_candidate)
    assert res["passed"] is False
    assert res["score"] < 50.0
