"""services/semantic_ai/learning_store.py
LearningStore Canónico y Persistente de ULTRARENTABLE v5.3.0.
Sustituye la memoria en proceso volátil por almacenamiento SQLite WAL durable,
soportando el ciclo relacional completo:
Failure -> Hypothesis -> Mutation -> Evaluation -> Learning Pattern -> Future Priors.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from services.api.app.config import LEARNING_DB_PATH
from contracts.learning_contracts import (
    AgentDebateRecord,
    FailureCategory,
    FailureRecordEntity,
    KnowledgeLinkRecord,
    LearningPatternRecord,
    MutationHistoryRecord,
    ResearchExperimentRecord,
    ResearchProposalRecord,
    SQXFeedbackRecord,
    StrategyVersionRecord,
    StrategyVersionStatus,
    ValidationSnapshotRecord,
)

logger = logging.getLogger("LearningStore")


class LearningStore:
    """Motor de almacenamiento relacional e inmutable del aprendizaje cuantitativo."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            self.db_path = str(LEARNING_DB_PATH)
        else:
            self.db_path = str(db_path)

        self._lock = threading.Lock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _init_db(self) -> None:
        """Inicializa el esquema relacional con las 11 tablas maestras."""
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()

            # 1. strategy_versions
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS strategy_versions (
                    strategy_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    parent_hash TEXT,
                    strategy_hash TEXT NOT NULL,
                    mutation_reason TEXT NOT NULL,
                    creator TEXT NOT NULL,
                    engine_version TEXT NOT NULL,
                    policy_version TEXT NOT NULL,
                    created_at_utc TEXT NOT NULL,
                    status TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    PRIMARY KEY (strategy_id, version),
                    UNIQUE (strategy_hash)
                );
                """
            )
            cur.execute("CREATE INDEX IF NOT EXISTS idx_strat_hash ON strategy_versions(strategy_hash);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_strat_parent ON strategy_versions(parent_hash);")

            # 2. validation_snapshots
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS validation_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    strategy_hash TEXT NOT NULL,
                    dataset_hash TEXT NOT NULL,
                    engine_version TEXT NOT NULL,
                    gate_policy_version TEXT NOT NULL,
                    verdict TEXT NOT NULL,
                    evidence_hash TEXT NOT NULL,
                    metrics_snapshot TEXT NOT NULL,
                    scorecard_json TEXT NOT NULL,
                    created_at_utc TEXT NOT NULL
                );
                """
            )
            cur.execute("CREATE INDEX IF NOT EXISTS idx_val_strat_hash ON validation_snapshots(strategy_hash);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_val_verdict ON validation_snapshots(verdict);")

            # 3. failure_records
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS failure_records (
                    failure_id TEXT PRIMARY KEY,
                    strategy_hash TEXT NOT NULL,
                    strategy_id TEXT NOT NULL,
                    track TEXT NOT NULL,
                    gate_name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    market_regime TEXT NOT NULL,
                    metrics_snapshot TEXT NOT NULL,
                    rejection_reasons TEXT NOT NULL,
                    failing_indicators TEXT NOT NULL,
                    rule_signature_hash TEXT NOT NULL,
                    root_cause_summary TEXT NOT NULL,
                    created_at_utc TEXT NOT NULL,
                    is_verified INTEGER NOT NULL DEFAULT 1
                );
                """
            )
            cur.execute("CREATE INDEX IF NOT EXISTS idx_fail_sig ON failure_records(rule_signature_hash);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_fail_gate ON failure_records(gate_name);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_fail_cat ON failure_records(category);")

            # 4. research_proposals
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS research_proposals (
                    proposal_id TEXT PRIMARY KEY,
                    parent_hash TEXT NOT NULL,
                    hypotheses TEXT NOT NULL,
                    tools_required TEXT NOT NULL,
                    blind_scope TEXT NOT NULL,
                    status TEXT NOT NULL,
                    creator_agent TEXT NOT NULL,
                    created_at_utc TEXT NOT NULL
                );
                """
            )
            cur.execute("CREATE INDEX IF NOT EXISTS idx_prop_parent ON research_proposals(parent_hash);")

            # 5. research_experiments
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS research_experiments (
                    experiment_id TEXT PRIMARY KEY,
                    proposal_id TEXT NOT NULL,
                    inputs_hash TEXT NOT NULL,
                    tool_calls TEXT NOT NULL,
                    results_hash TEXT NOT NULL,
                    outcome_summary TEXT NOT NULL,
                    created_at_utc TEXT NOT NULL
                );
                """
            )
            cur.execute("CREATE INDEX IF NOT EXISTS idx_exp_prop ON research_experiments(proposal_id);")

            # 6. agent_debates
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_debates (
                    debate_id TEXT PRIMARY KEY,
                    strategy_hash TEXT NOT NULL,
                    participants TEXT NOT NULL,
                    positions TEXT NOT NULL,
                    disagreement_level REAL NOT NULL,
                    final_consensus_hypothesis TEXT NOT NULL,
                    created_at_utc TEXT NOT NULL
                );
                """
            )
            cur.execute("CREATE INDEX IF NOT EXISTS idx_deb_strat ON agent_debates(strategy_hash);")

            # 7. mutation_history
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS mutation_history (
                    mutation_id TEXT PRIMARY KEY,
                    parent_hash TEXT NOT NULL,
                    child_hash TEXT NOT NULL,
                    changed_fields TEXT NOT NULL,
                    complexity_delta INTEGER NOT NULL,
                    outcome_verdict TEXT NOT NULL,
                    created_at_utc TEXT NOT NULL
                );
                """
            )
            cur.execute("CREATE INDEX IF NOT EXISTS idx_mut_parent ON mutation_history(parent_hash);")

            # 8. sqx_feedback
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS sqx_feedback (
                    feedback_id TEXT PRIMARY KEY,
                    cohort_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    route TEXT NOT NULL,
                    fertility_score REAL NOT NULL,
                    evidence_summary TEXT NOT NULL,
                    recommendation TEXT NOT NULL,
                    created_at_utc TEXT NOT NULL
                );
                """
            )
            cur.execute("CREATE INDEX IF NOT EXISTS idx_sqx_cohort ON sqx_feedback(cohort_id);")

            # 9. revalidation_queue
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS revalidation_queue (
                    queue_id TEXT PRIMARY KEY,
                    strategy_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    strategy_hash TEXT NOT NULL,
                    invalidation_reason TEXT NOT NULL,
                    required_policies TEXT NOT NULL,
                    status TEXT NOT NULL,
                    scheduled_at_utc TEXT NOT NULL,
                    processed_at_utc TEXT
                );
                """
            )
            cur.execute("CREATE INDEX IF NOT EXISTS idx_rev_status ON revalidation_queue(status);")

            # 10. learning_patterns
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS learning_patterns (
                    pattern_signature TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    failure_count INTEGER NOT NULL,
                    successful_repairs INTEGER NOT NULL,
                    confidence_score REAL NOT NULL,
                    evidence_refs TEXT NOT NULL,
                    suggested_mutation_priors TEXT NOT NULL,
                    last_updated_utc TEXT NOT NULL
                );
                """
            )
            cur.execute("CREATE INDEX IF NOT EXISTS idx_pat_cat ON learning_patterns(category);")

            # 11. knowledge_links
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS knowledge_links (
                    link_id TEXT PRIMARY KEY,
                    failure_id TEXT,
                    proposal_id TEXT,
                    experiment_id TEXT,
                    mutation_id TEXT,
                    strategy_version_id TEXT,
                    validation_snapshot_id TEXT,
                    created_at_utc TEXT NOT NULL
                );
                """
            )
            cur.execute("CREATE INDEX IF NOT EXISTS idx_link_fail ON knowledge_links(failure_id);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_link_ver ON knowledge_links(strategy_version_id);")

            conn.commit()
            conn.close()

    # --- Operaciones CRUD Tipadas y Transaccionales ---

    def record_strategy_version(self, record: StrategyVersionRecord) -> None:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT OR REPLACE INTO strategy_versions (
                    strategy_id, version, parent_hash, strategy_hash, mutation_reason,
                    creator, engine_version, policy_version, created_at_utc, status, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    record.strategy_id,
                    record.version,
                    record.parent_hash,
                    record.strategy_hash,
                    record.mutation_reason,
                    record.creator,
                    record.engine_version,
                    record.policy_version,
                    record.created_at_utc,
                    record.status.value,
                    json.dumps(record.metadata_json),
                ),
            )
            conn.commit()
            conn.close()

    def record_validation_snapshot(self, record: ValidationSnapshotRecord) -> None:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT OR REPLACE INTO validation_snapshots (
                    snapshot_id, strategy_hash, dataset_hash, engine_version,
                    gate_policy_version, verdict, evidence_hash, metrics_snapshot,
                    scorecard_json, created_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    record.snapshot_id,
                    record.strategy_hash,
                    record.dataset_hash,
                    record.engine_version,
                    record.gate_policy_version,
                    record.verdict,
                    record.evidence_hash,
                    json.dumps(record.metrics_snapshot),
                    json.dumps(record.scorecard_json),
                    record.created_at_utc,
                ),
            )
            conn.commit()
            conn.close()

    def record_failure(self, record: FailureRecordEntity) -> None:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT OR REPLACE INTO failure_records (
                    failure_id, strategy_hash, strategy_id, track, gate_name,
                    category, market_regime, metrics_snapshot, rejection_reasons,
                    failing_indicators, rule_signature_hash, root_cause_summary,
                    created_at_utc, is_verified
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    record.failure_id,
                    record.strategy_hash,
                    record.strategy_id,
                    record.track,
                    record.gate_name,
                    record.category.value,
                    record.market_regime,
                    json.dumps(record.metrics_snapshot),
                    json.dumps(record.rejection_reasons),
                    json.dumps(record.failing_indicators),
                    record.rule_signature_hash,
                    record.root_cause_summary,
                    record.created_at_utc,
                    1 if record.is_verified else 0,
                ),
            )

            # Actualizar o insertar patrón de aprendizaje asociado
            cur.execute(
                "SELECT failure_count, successful_repairs, evidence_refs FROM learning_patterns WHERE pattern_signature = ?",
                (record.rule_signature_hash,),
            )
            row = cur.fetchone()
            now_utc = datetime.now(timezone.utc).isoformat()
            if row:
                f_count = row[0] + 1
                s_rep = row[1]
                refs = json.loads(row[2])
                if record.failure_id not in refs:
                    refs.append(record.failure_id)
                confidence = max(0.1, min(1.0, f_count / (f_count + s_rep + 1.0)))
                cur.execute(
                    """
                    UPDATE learning_patterns
                    SET failure_count = ?, confidence_score = ?, evidence_refs = ?, last_updated_utc = ?
                    WHERE pattern_signature = ?
                    """,
                    (f_count, confidence, json.dumps(refs), now_utc, record.rule_signature_hash),
                )
            else:
                confidence = 0.5
                cur.execute(
                    """
                    INSERT INTO learning_patterns (
                        pattern_signature, category, failure_count, successful_repairs,
                        confidence_score, evidence_refs, suggested_mutation_priors, last_updated_utc
                    ) VALUES (?, ?, 1, 0, ?, ?, '{}', ?);
                    """,
                    (
                        record.rule_signature_hash,
                        record.category.value,
                        confidence,
                        json.dumps([record.failure_id]),
                        now_utc,
                    ),
                )

            conn.commit()
            conn.close()

    def record_research_proposal(self, record: ResearchProposalRecord) -> None:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT OR REPLACE INTO research_proposals (
                    proposal_id, parent_hash, hypotheses, tools_required,
                    blind_scope, status, creator_agent, created_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    record.proposal_id,
                    record.parent_hash,
                    json.dumps(record.hypotheses),
                    json.dumps(record.tools_required),
                    record.blind_scope,
                    record.status,
                    record.creator_agent,
                    record.created_at_utc,
                ),
            )
            conn.commit()
            conn.close()

    def record_research_experiment(self, record: ResearchExperimentRecord) -> None:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT OR REPLACE INTO research_experiments (
                    experiment_id, proposal_id, inputs_hash, tool_calls,
                    results_hash, outcome_summary, created_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    record.experiment_id,
                    record.proposal_id,
                    record.inputs_hash,
                    json.dumps(record.tool_calls),
                    record.results_hash,
                    record.outcome_summary,
                    record.created_at_utc,
                ),
            )
            conn.commit()
            conn.close()

    def record_agent_debate(self, record: AgentDebateRecord) -> None:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT OR REPLACE INTO agent_debates (
                    debate_id, strategy_hash, participants, positions,
                    disagreement_level, final_consensus_hypothesis, created_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    record.debate_id,
                    record.strategy_hash,
                    json.dumps(record.participants),
                    json.dumps(record.positions),
                    record.disagreement_level,
                    record.final_consensus_hypothesis,
                    record.created_at_utc,
                ),
            )
            conn.commit()
            conn.close()

    def record_mutation(self, record: MutationHistoryRecord) -> None:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT OR REPLACE INTO mutation_history (
                    mutation_id, parent_hash, child_hash, changed_fields,
                    complexity_delta, outcome_verdict, created_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    record.mutation_id,
                    record.parent_hash,
                    record.child_hash,
                    json.dumps(record.changed_fields),
                    record.complexity_delta,
                    record.outcome_verdict,
                    record.created_at_utc,
                ),
            )
            conn.commit()
            conn.close()

    def record_sqx_feedback(self, record: SQXFeedbackRecord) -> None:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT OR REPLACE INTO sqx_feedback (
                    feedback_id, cohort_id, symbol, timeframe, route,
                    fertility_score, evidence_summary, recommendation, created_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    record.feedback_id,
                    record.cohort_id,
                    record.symbol,
                    record.timeframe,
                    record.route,
                    record.fertility_score,
                    json.dumps(record.evidence_summary),
                    record.recommendation,
                    record.created_at_utc,
                ),
            )
            conn.commit()
            conn.close()

    def enqueue_revalidation(self, item: RevalidationQueueItem) -> None:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT OR REPLACE INTO revalidation_queue (
                    queue_id, strategy_id, version, strategy_hash, invalidation_reason,
                    required_policies, status, scheduled_at_utc, processed_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    item.queue_id,
                    item.strategy_id,
                    item.version,
                    item.strategy_hash,
                    item.invalidation_reason,
                    json.dumps(item.required_policies),
                    item.status,
                    item.scheduled_at_utc,
                    item.processed_at_utc,
                ),
            )
            conn.commit()
            conn.close()

    def get_pending_revalidations(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT queue_id, strategy_id, version, strategy_hash, invalidation_reason,
                       required_policies, status, scheduled_at_utc
                FROM revalidation_queue
                WHERE status = 'PENDING'
                ORDER BY scheduled_at_utc ASC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cur.fetchall()
            conn.close()

            items = []
            for r in rows:
                items.append(
                    {
                        "queue_id": r[0],
                        "strategy_id": r[1],
                        "version": r[2],
                        "strategy_hash": r[3],
                        "invalidation_reason": r[4],
                        "required_policies": json.loads(r[5]),
                        "status": r[6],
                        "scheduled_at_utc": r[7],
                    }
                )
            return items

    def link_knowledge(self, link: KnowledgeLinkRecord) -> None:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT OR REPLACE INTO knowledge_links (
                    link_id, failure_id, proposal_id, experiment_id,
                    mutation_id, strategy_version_id, validation_snapshot_id, created_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    link.link_id,
                    link.failure_id,
                    link.proposal_id,
                    link.experiment_id,
                    link.mutation_id,
                    link.strategy_version_id,
                    link.validation_snapshot_id,
                    link.created_at_utc,
                ),
            )
            conn.commit()
            conn.close()

    # --- Consultas de Aprendizaje y Estadísticas ---

    def get_failure_records_by_strategy(self, strategy_id: str, limit: int = 50) -> List[FailureRecordEntity]:
        """Obtiene el historial de fallos de una estrategia específica."""
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT failure_id, strategy_hash, strategy_id, track, gate_name,
                       category, market_regime, metrics_snapshot, rejection_reasons,
                       failing_indicators, rule_signature_hash, root_cause_summary,
                       created_at_utc, is_verified
                FROM failure_records
                WHERE strategy_id = ?
                ORDER BY created_at_utc DESC LIMIT ?;
                """,
                (strategy_id, limit),
            )
            rows = cur.fetchall()
            conn.close()
            records = []
            for r in rows:
                records.append(
                    FailureRecordEntity(
                        failure_id=r[0],
                        strategy_hash=r[1],
                        strategy_id=r[2],
                        track=r[3],
                        gate_name=r[4],
                        category=FailureCategory(r[5]),
                        market_regime=r[6],
                        metrics_snapshot=json.loads(r[7]),
                        rejection_reasons=json.loads(r[8]),
                        failing_indicators=json.loads(r[9]),
                        rule_signature_hash=r[10],
                        root_cause_summary=r[11],
                        created_at_utc=r[12],
                        is_verified=bool(r[13]),
                    )
                )
            return records

    def get_learning_patterns_by_category(self, category: FailureCategory, limit: int = 20) -> List[LearningPatternRecord]:
        """Obtiene patrones de aprendizaje indexados por categoría de fallo."""
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT pattern_signature, category, failure_count, successful_repairs,
                       confidence_score, evidence_refs, suggested_mutation_priors, last_updated_utc
                FROM learning_patterns
                WHERE category = ?
                ORDER BY confidence_score DESC, failure_count DESC LIMIT ?;
                """,
                (category.value if hasattr(category, "value") else str(category), limit),
            )
            rows = cur.fetchall()
            conn.close()
            patterns = []
            for r in rows:
                patterns.append(
                    LearningPatternRecord(
                        pattern_signature=r[0],
                        category=FailureCategory(r[1]),
                        failure_count=r[2],
                        successful_repairs=r[3],
                        confidence_score=float(r[4]),
                        evidence_refs=json.loads(r[5]),
                        suggested_mutation_priors=json.loads(r[6]),
                        last_updated_utc=r[7],
                    )
                )
            return patterns

    def is_rule_tree_blacklisted(self, rule_signature_hash: str) -> bool:
        """Determina si un patrón de reglas ha fallado repetidamente sin reparaciones exitosas."""
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT failure_count, successful_repairs, confidence_score FROM learning_patterns WHERE pattern_signature = ?",
                (rule_signature_hash,),
            )
            row = cur.fetchone()
            conn.close()
            if not row:
                return False
            f_count, s_rep, conf = row
            return f_count > 0 and s_rep == 0 and conf >= 0.5

    def get_failure_statistics(self) -> Dict[str, Any]:
        """Calcula estadísticas consolidadas de la memoria de fallos."""
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT count(*) FROM failure_records;")
            total_failures = cur.fetchone()[0]

            cur.execute("SELECT category, count(*) FROM failure_records GROUP BY category;")
            cat_dist = {r[0]: r[1] for r in cur.fetchall()}

            cur.execute("SELECT gate_name, count(*) FROM failure_records GROUP BY gate_name ORDER BY count(*) DESC LIMIT 5;")
            top_gates = [{"gate": r[0], "failures": r[1]} for r in cur.fetchall()]

            cur.execute("SELECT count(*) FROM learning_patterns;")
            total_patterns = cur.fetchone()[0]

            cur.execute("SELECT count(*) FROM strategy_versions;")
            total_versions = cur.fetchone()[0]

            cur.execute("SELECT count(*) FROM validation_snapshots;")
            total_snapshots = cur.fetchone()[0]

            conn.close()

            return {
                "total_failures_recorded": total_failures,
                "total_learning_patterns": total_patterns,
                "total_strategy_versions": total_versions,
                "total_validation_snapshots": total_snapshots,
                "category_distribution": cat_dist,
                "top_failing_gates": top_gates,
            }

    def get_proposals(self, limit: int = 50) -> List[ResearchProposalRecord]:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT proposal_id, parent_hash, hypotheses, tools_required,
                       blind_scope, status, creator_agent, created_at_utc
                FROM research_proposals
                ORDER BY created_at_utc DESC LIMIT ?;
                """,
                (limit,),
            )
            rows = cur.fetchall()
            conn.close()
            records = []
            for r in rows:
                records.append(
                    ResearchProposalRecord(
                        proposal_id=r[0],
                        parent_hash=r[1],
                        hypotheses=json.loads(r[2]),
                        tools_required=json.loads(r[3]),
                        blind_scope=r[4],
                        status=r[5],
                        creator_agent=r[6],
                        created_at_utc=r[7],
                    )
                )
            return records

    def get_experiments(self, limit: int = 50) -> List[ResearchExperimentRecord]:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT experiment_id, proposal_id, inputs_hash, tool_calls,
                       results_hash, outcome_summary, created_at_utc
                FROM research_experiments
                ORDER BY created_at_utc DESC LIMIT ?;
                """,
                (limit,),
            )
            rows = cur.fetchall()
            conn.close()
            records = []
            for r in rows:
                records.append(
                    ResearchExperimentRecord(
                        experiment_id=r[0],
                        proposal_id=r[1],
                        inputs_hash=r[2],
                        tool_calls=json.loads(r[3]),
                        results_hash=r[4],
                        outcome_summary=r[5],
                        created_at_utc=r[6],
                    )
                )
            return records

    def get_debates(self, limit: int = 50) -> List[AgentDebateRecord]:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT debate_id, strategy_hash, participants, positions,
                       disagreement_level, final_consensus_hypothesis, created_at_utc
                FROM agent_debates
                ORDER BY created_at_utc DESC LIMIT ?;
                """,
                (limit,),
            )
            rows = cur.fetchall()
            conn.close()
            records = []
            for r in rows:
                records.append(
                    AgentDebateRecord(
                        debate_id=r[0],
                        strategy_hash=r[1],
                        participants=json.loads(r[2]),
                        positions=json.loads(r[3]),
                        disagreement_level=float(r[4]),
                        final_consensus_hypothesis=r[5],
                        created_at_utc=r[6],
                    )
                )
            return records

    # --- Rehidratación Forense de Firebase de Alta Velocidad (Batch) ---

    def rehydrate_from_firebase_snapshot(self, snapshot_data_or_path: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Rehidrata los registros históricos desde el snapshot forense de Firebase RTDB (/ultrarentable).
        Ejecuta en una única transacción atómica de alto rendimiento.
        """
        if isinstance(snapshot_data_or_path, str):
            with open(snapshot_data_or_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = snapshot_data_or_path

        candidates = data.get("candidates", [])
        if isinstance(candidates, dict):
            candidates = list(candidates.values())

        rehydrated_strategies = 0
        rehydrated_failures = 0
        rehydrated_snapshots = 0

        now_utc = datetime.now(timezone.utc).isoformat()

        strat_rows = []
        snap_rows = []
        fail_rows = []
        pattern_map: Dict[str, Dict[str, Any]] = {}

        for cand in candidates:
            if not isinstance(cand, dict):
                continue

            cid = cand.get("candidate_id") or f"cand_{time.time()}"
            name = cand.get("name", cid)
            route = cand.get("route", "UNKNOWN")
            status = cand.get("status", "DRAFT")
            status_reason = cand.get("status_reason", "")
            engine_v = cand.get("engine_version", "1.00")
            pipeline_v = cand.get("validation_pipeline_version", "1.00")
            metrics = cand.get("metrics", {})
            dna_scorecard = cand.get("dna_scorecard", {})

            strat_hash = f"hash_{cid}_{engine_v}"

            strat_status = "CANDIDATE"
            if status == "APPROVED":
                strat_status = "CERTIFIED_LEGACY" if engine_v != "1.02" else "CERTIFIED_CURRENT"
            elif status == "REJECTED":
                strat_status = "REJECTED"

            meta_json = json.dumps({
                "name": name,
                "route": route,
                "symbol": cand.get("symbol", ""),
                "timeframe": cand.get("timeframe", ""),
                "historical_tier": cand.get("tier", "TIER_4_REJECTED"),
                "gates_passed_count": cand.get("gates_passed_count", 0),
                "is_historical_rehydrated": True,
            })

            strat_rows.append((
                cid,
                engine_v,
                None,
                strat_hash,
                f"Historical rehydration from Firebase ({status_reason[:100]})",
                "SQX_OR_HISTORICAL",
                engine_v,
                pipeline_v,
                cand.get("last_synced_utc", now_utc),
                strat_status,
                meta_json,
            ))
            rehydrated_strategies += 1

            snap_id = f"snap_hist_{cid}_{int(time.time()*1000)}"
            snap_metrics = {k: float(v) for k, v in metrics.items() if isinstance(v, (int, float))}
            snap_rows.append((
                snap_id,
                strat_hash,
                f"ds_hist_{cand.get('symbol', 'UNKNOWN')}_{cand.get('timeframe', 'UNKNOWN')}",
                engine_v,
                pipeline_v,
                status,
                f"ev_hist_{cid}",
                json.dumps(snap_metrics),
                json.dumps(dna_scorecard if isinstance(dna_scorecard, dict) else {}),
                cand.get("last_synced_utc", now_utc),
            ))
            rehydrated_snapshots += 1

            iter_history = dna_scorecard.get("iteration_history", []) if isinstance(dna_scorecard, dict) else []
            for idx, it in enumerate(iter_history):
                if not isinstance(it, dict):
                    continue
                failed_gates = it.get("failed_gate_names", [])
                it_params = it.get("parameters", {})
                it_metrics = {
                    "max_dd_oos_pct": float(it.get("max_dd_oos_pct", 0.0)),
                    "net_profit_oos": float(it.get("net_profit_oos", 0.0)),
                    "profit_factor_oos": float(it.get("profit_factor_oos", 0.0)),
                    "trades_count": float(it.get("trades_count", 0)),
                }

                rule_sig = f"sig_{cid}_gen_{it.get('generation', 0)}_it_{idx}"

                for fg in failed_gates:
                    cat = "GATES_REJECTION"
                    if "DRAWDOWN" in fg or it_metrics["max_dd_oos_pct"] > 35.0:
                        cat = "MAX_DRAWDOWN_EXCEEDED"
                    elif "COSTES" in fg or "SLIPPAGE" in fg:
                        cat = "FRICTION_SENSITIVE"
                    elif "OVERFITTING" in fg or "NOVELTY" in fg:
                        cat = "OVERFITTING_IS_OOS"

                    fail_id = f"fail_{cid}_it_{idx}_{fg}"
                    fail_rows.append((
                        fail_id,
                        strat_hash,
                        cid,
                        route,
                        fg,
                        cat,
                        "HISTORICAL_OOS",
                        json.dumps(it_metrics),
                        json.dumps([f"Failed {fg} with params {json.dumps(it_params)}"]),
                        json.dumps(list(it_params.keys())),
                        rule_sig,
                        f"Historical failure at Gate {fg}: DD {it_metrics['max_dd_oos_pct']}%, PF {it_metrics['profit_factor_oos']}",
                        cand.get("last_synced_utc", now_utc),
                        1,
                    ))
                    rehydrated_failures += 1

                    if rule_sig not in pattern_map:
                        pattern_map[rule_sig] = {
                            "cat": cat,
                            "f_count": 0,
                            "refs": [],
                        }
                    pattern_map[rule_sig]["f_count"] += 1
                    if fail_id not in pattern_map[rule_sig]["refs"]:
                        pattern_map[rule_sig]["refs"].append(fail_id)

        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("BEGIN TRANSACTION;")

            cur.executemany(
                """
                INSERT OR REPLACE INTO strategy_versions (
                    strategy_id, version, parent_hash, strategy_hash, mutation_reason,
                    creator, engine_version, policy_version, created_at_utc, status, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                strat_rows,
            )

            cur.executemany(
                """
                INSERT OR REPLACE INTO validation_snapshots (
                    snapshot_id, strategy_hash, dataset_hash, engine_version,
                    gate_policy_version, verdict, evidence_hash, metrics_snapshot,
                    scorecard_json, created_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                snap_rows,
            )

            cur.executemany(
                """
                INSERT OR REPLACE INTO failure_records (
                    failure_id, strategy_hash, strategy_id, track, gate_name,
                    category, market_regime, metrics_snapshot, rejection_reasons,
                    failing_indicators, rule_signature_hash, root_cause_summary,
                    created_at_utc, is_verified
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                fail_rows,
            )

            pat_rows = []
            for sig, pdata in pattern_map.items():
                confidence = max(0.1, min(1.0, pdata["f_count"] / (pdata["f_count"] + 1.0)))
                pat_rows.append((
                    sig,
                    pdata["cat"],
                    pdata["f_count"],
                    0,
                    confidence,
                    json.dumps(pdata["refs"][:20]),
                    "{}",
                    now_utc,
                ))

            cur.executemany(
                """
                INSERT OR REPLACE INTO learning_patterns (
                    pattern_signature, category, failure_count, successful_repairs,
                    confidence_score, evidence_refs, suggested_mutation_priors, last_updated_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                pat_rows,
            )

            conn.commit()
            conn.close()

        summary = {
            "status": "SUCCESS",
            "rehydrated_strategies": rehydrated_strategies,
            "rehydrated_validation_snapshots": rehydrated_snapshots,
            "rehydrated_failure_records": rehydrated_failures,
            "db_path": self.db_path,
        }
        logger.info(f"Rehidratación completada exitosamente: {summary}")
        return summary


# Instancia singleton para el runtime del sistema
learning_store = LearningStore()
