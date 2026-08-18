"""Unit tests for Semantic AI Engine and FailureKnowledgeDB (Fase 5)."""

import pytest

from contracts import (
    CanonicalStrategy,
    ExecutionTrack,
    StrategyLifecycleStatus,
    ValidationTrack,
)
from services.semantic_ai import (
    SemanticQuantEngine,
    FailureKnowledgeDB,
    FailureCategory,
    CriticAgent,
    InterpreterAgent,
    ImproverAgent,
)
from services.validation import FondeoEvidenceGate


def test_failure_knowledge_db_recording_and_blacklisting():
    """Verify recording failure properly blacklists rule signatures and updates statistics."""
    db = FailureKnowledgeDB()
    engine = SemanticQuantEngine(failure_db=db)

    strat = engine.generate_candidate(symbol="NQ", track=ExecutionTrack.TRACK_FONDEO)
    assert db.is_rule_tree_blacklisted(strat.rules) is False

    # Record rejection
    record = db.record_failure(
        strategy=strat,
        track=ValidationTrack.TRACK_FONDEO,
        category=FailureCategory.OUTLIER_DEPENDENCY,
        rejection_reasons=["Dependencia excesiva de Top 2 trades (68% > 15%)"],
        metrics_snapshot={"top2_outlier_pct": 68.0, "dsr": 1.2},
    )

    assert record.category == FailureCategory.OUTLIER_DEPENDENCY
    assert db.is_rule_tree_blacklisted(strat.rules) is True

    stats = db.get_failure_statistics()
    assert stats["total_failures_recorded"] == 1
    assert stats["blacklisted_patterns_count"] == 1
    assert "OUTLIER_DEPENDENCY" in stats["category_distribution"]


def test_critic_agent_structural_and_failure_checks():
    """Verify CriticAgent blocks blacklisted patterns and missing risk controls."""
    db = FailureKnowledgeDB()
    engine = SemanticQuantEngine(failure_db=db)
    critic = CriticAgent(failure_db=db)

    strat = engine.generate_candidate(symbol="ES", track=ExecutionTrack.TRACK_FONDEO)
    passed, warnings = critic.critique(strat)
    assert passed is True

    # Record failure of this strategy pattern
    db.record_failure(
        strategy=strat,
        track=ValidationTrack.TRACK_FONDEO,
        category=FailureCategory.MAX_DRAWDOWN_EXCEEDED,
        rejection_reasons=["Max DD 6.2% > 4.5%"],
    )

    # Now Critic should reject it immediately
    passed_after_blacklist, warnings_after = critic.critique(strat)
    assert passed_after_blacklist is False
    assert any("FailureKnowledgeDB" in w for w in warnings_after)


def test_improver_agent_mutation_avoids_blacklist():
    """Verify ImproverAgent mutates strategy and avoids known blacklisted patterns."""
    db = FailureKnowledgeDB()
    engine = SemanticQuantEngine(failure_db=db)
    improver = ImproverAgent(failure_db=db)

    base = engine.generate_candidate(symbol="NQ", track=ExecutionTrack.TRACK_FONDEO)
    # Blacklist base pattern
    db.record_failure(
        strategy=base,
        track=ValidationTrack.TRACK_FONDEO,
        category=FailureCategory.OVERFITTING_IS_OOS,
        rejection_reasons=["WFE 0.35 < 0.60"],
    )

    mutant = improver.mutate(base)
    assert mutant.strategy_id != base.strategy_id
    assert mutant.metadata.get("parent_strategy_id") == base.strategy_id
    assert db.is_rule_tree_blacklisted(mutant.rules) is False


def test_closed_loop_ai_proposes_gate_approves():
    """Verify end-to-end closed loop: AI proposes -> Gate rejects -> Failure recorded -> AI mutates -> Gate approves."""
    db = FailureKnowledgeDB()
    engine = SemanticQuantEngine(failure_db=db)
    gate = FondeoEvidenceGate()

    # Step 1: Generate initial candidate
    strat = engine.generate_candidate(symbol="NQ", track=ExecutionTrack.TRACK_FONDEO)

    # Step 2: Gate evaluates flawed run (simulate rejection)
    bad_oos_trades = [1000.0, 1000.0] + [5.0 if i % 2 == 0 else -10.0 for i in range(48)]
    bad_is_trades = [50.0] * 50
    result_flawed = gate.evaluate("UR-TEST-BAD", is_trades=bad_is_trades, oos_trades=bad_oos_trades)
    assert result_flawed.passed is False

    # Step 3: Record failure in DB
    db.record_failure(
        strategy=strat,
        track=ValidationTrack.TRACK_FONDEO,
        category=FailureCategory.OUTLIER_DEPENDENCY,
        rejection_reasons=result_flawed.rejection_reasons,
    )

    # Step 4: AI mutates candidate
    improved_strat = engine.improve_candidate(strat)
    assert improved_strat is not None
    assert db.is_rule_tree_blacklisted(improved_strat.rules) is False

    # Step 5: Gate evaluates healthy run for improved candidate
    good_is_trades = [100.0 if i % 2 == 0 else -50.0 for i in range(100)]
    good_oos_trades = [95.0 if i % 2 == 0 else -50.0 for i in range(100)]
    result_good = gate.evaluate(improved_strat.strategy_id, is_trades=good_is_trades, oos_trades=good_oos_trades)
    assert result_good.passed is True
