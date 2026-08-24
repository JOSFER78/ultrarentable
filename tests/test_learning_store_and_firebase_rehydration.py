"""tests/test_learning_store_and_firebase_rehydration.py
Suite de verificación rigurosa para el LearningStore canónico y la rehidratación forense de Firebase.
Zero-Mocks, persistencia SQLite WAL y trazabilidad relacional completa.
"""

import os
import json
import sqlite3
import tempfile
import pytest

from contracts.learning_contracts import (
    FailureCategory,
    FailureRecordEntity,
    StrategyVersionRecord,
    ValidationSnapshotRecord,
    ResearchProposalRecord,
    AgentDebateRecord,
    MutationHistoryRecord,
    SQXFeedbackRecord,
    RevalidationQueueItem,
    StrategyVersionStatus,
)
from services.semantic_ai.learning_store import LearningStore
from services.semantic_ai.failure_knowledge import FailureKnowledgeDB, FailureRecord


def test_learning_store_schema_initialization():
    """Verifica que las 11 tablas maestras se crean correctamente en SQLite WAL."""
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as tmp:
        db_path = tmp.name

    try:
        store = LearningStore(db_path=db_path)
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = set(row[0] for row in cur.fetchall())
        conn.close()

        expected_tables = {
            "strategy_versions",
            "validation_snapshots",
            "failure_records",
            "research_proposals",
            "research_experiments",
            "agent_debates",
            "mutation_history",
            "sqx_feedback",
            "revalidation_queue",
            "learning_patterns",
            "knowledge_links",
        }
        assert expected_tables.issubset(tables), f"Faltan tablas: {expected_tables - tables}"
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_learning_store_crud_and_persistence_across_instances():
    """Verifica que los datos persisten físicamente en disco y se recuperan entre instancias."""
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as tmp:
        db_path = tmp.name

    try:
        # Instancia 1: Escritura
        store1 = LearningStore(db_path=db_path)
        
        # 1. Version
        v_rec = StrategyVersionRecord(
            strategy_id="UR_FONDEO_NQ_15M",
            version="1.02",
            parent_hash="parent_root",
            strategy_hash="hash_nq_v102",
            mutation_reason="Initial SQX compilation",
            creator="SQX_FACTORY",
            engine_version="1.02",
            policy_version="1.02",
            created_at_utc="2026-08-24T12:00:00Z",
            status=StrategyVersionStatus.CERTIFIED_CURRENT,
            metadata_json={"symbol": "NQ", "timeframe": "15m"},
        )
        store1.record_strategy_version(v_rec)

        # 2. Failure
        f_rec = FailureRecordEntity(
            failure_id="fail_nq_001",
            strategy_hash="hash_nq_v102",
            strategy_id="UR_FONDEO_NQ_15M",
            track="FONDEO",
            gate_name="DAILY_LOSS_LIMIT",
            category=FailureCategory.DAILY_LOSS_VIOLATION,
            market_regime="HIGH_VOLATILITY",
            metrics_snapshot={"max_daily_loss": -2500.0, "threshold": -2000.0},
            rejection_reasons=["Daily loss limit breached on FOMC day"],
            failing_indicators=["EMA_50", "RSI_14"],
            rule_signature_hash="sig_nq_ema_rsi_cross",
            root_cause_summary="Violation of daily hard stop",
            created_at_utc="2026-08-24T12:05:00Z",
            is_verified=True,
        )
        store1.record_failure(f_rec)

        # Instancia 2: Lectura en frío desde el mismo archivo SQLite
        store2 = LearningStore(db_path=db_path)
        stats = store2.get_failure_statistics()
        assert stats["total_failures_recorded"] == 1
        assert stats["total_strategy_versions"] == 1
        assert stats["total_learning_patterns"] == 1
        assert stats["category_distribution"].get("DAILY_LOSS_VIOLATION") == 1
        assert store2.is_rule_tree_blacklisted("sig_nq_ema_rsi_cross") is True
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_rehydrate_from_real_firebase_recovery_snapshot():
    """Verifica la rehidratación completa y real del snapshot forense de Firebase."""
    snapshot_path = os.path.join(
        os.path.dirname(__file__), "..", "backups", "firebase_ultrarentable_recovery_snapshot.json"
    )
    if not os.path.exists(snapshot_path):
        pytest.skip(f"Snapshot file not found at {snapshot_path}")

    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as tmp:
        db_path = tmp.name

    try:
        store = LearningStore(db_path=db_path)
        result = store.rehydrate_from_firebase_snapshot(snapshot_path)

        assert result["status"] == "SUCCESS"
        assert result["rehydrated_strategies"] == 258
        assert result["rehydrated_validation_snapshots"] == 258
        assert result["rehydrated_failure_records"] > 0

        # Verificar estadísticas persistidas
        stats = store.get_failure_statistics()
        assert stats["total_strategy_versions"] == 258
        assert stats["total_validation_snapshots"] == 258
        assert stats["total_failures_recorded"] > 0
        assert stats["total_learning_patterns"] > 0
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_failure_knowledge_db_backward_compatibility():
    """Verifica que FailureKnowledgeDB funciona transparentemente delegando en LearningStore."""
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as tmp:
        db_path = tmp.name

    try:
        custom_store = LearningStore(db_path=db_path)
        fk_db = FailureKnowledgeDB(store=custom_store)

        stats = fk_db.get_failure_statistics()
        assert stats["total_failures_recorded"] == 0
        assert stats["blacklisted_patterns_count"] == 0
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)
