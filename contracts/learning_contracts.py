"""contracts/learning_contracts.py
Contratos canónicos e inmutables para el LearningStore y el Sistema de Aprendizaje Persistente.
Especificación oficial según Sección 7 y 8 del Informe Maestro v5.3.0.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class FailureCategory(str, Enum):
    OVERFITTING_IS_OOS = "OVERFITTING_IS_OOS"
    OUTLIER_DEPENDENCY = "OUTLIER_DEPENDENCY"
    MAX_DRAWDOWN_EXCEEDED = "MAX_DRAWDOWN_EXCEEDED"
    DAILY_LOSS_VIOLATION = "DAILY_LOSS_VIOLATION"
    LOW_PAYOFF_RATIO = "LOW_PAYOFF_RATIO"
    LOW_EXPECTED_R = "LOW_EXPECTED_R"
    SKEWNESS_INSUFFICIENT = "SKEWNESS_INSUFFICIENT"
    VAULT_HARVEST_FAIL = "VAULT_HARVEST_FAIL"
    FRICTION_SENSITIVE = "FRICTION_SENSITIVE"
    BURST_RUIN_EXCEEDED = "BURST_RUIN_EXCEEDED"
    REGIME_MISMATCH = "REGIME_MISMATCH"
    GATES_REJECTION = "GATES_REJECTION"
    UNVERIFIED_FAILURE = "UNVERIFIED_FAILURE"


class StrategyVersionStatus(str, Enum):
    DRAFT = "DRAFT"
    CANDIDATE = "CANDIDATE"
    EVALUATING = "EVALUATING"
    CERTIFIED_CURRENT = "CERTIFIED_CURRENT"
    CERTIFIED_LEGACY = "CERTIFIED_LEGACY"
    STALE = "STALE"
    REVALIDATION_REQUIRED = "REVALIDATION_REQUIRED"
    REJECTED = "REJECTED"


class StrategyVersionRecord(BaseModel):
    """Registro de versión inmutable de una estrategia en el LearningStore."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    strategy_id: str
    version: str
    parent_hash: Optional[str] = None
    strategy_hash: str
    mutation_reason: str
    creator: str
    engine_version: str
    policy_version: str
    created_at_utc: str
    status: StrategyVersionStatus = StrategyVersionStatus.DRAFT
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class ValidationSnapshotRecord(BaseModel):
    """Snapshot inmutable de examen y certificación de una estrategia."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    snapshot_id: str
    strategy_hash: str
    dataset_hash: str
    engine_version: str
    gate_policy_version: str
    verdict: str
    evidence_hash: str
    metrics_snapshot: Dict[str, float] = Field(default_factory=dict)
    scorecard_json: Dict[str, Any] = Field(default_factory=dict)
    created_at_utc: str


class FailureRecordEntity(BaseModel):
    """Registro relacional y persistente de fallo cuantitativo."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    failure_id: str
    strategy_hash: str
    strategy_id: str
    track: str
    gate_name: str
    category: FailureCategory
    market_regime: str = "UNKNOWN"
    metrics_snapshot: Dict[str, float] = Field(default_factory=dict)
    rejection_reasons: List[str] = Field(default_factory=list)
    failing_indicators: List[str] = Field(default_factory=list)
    rule_signature_hash: str
    root_cause_summary: str
    created_at_utc: str
    is_verified: bool = True


class ResearchProposalRecord(BaseModel):
    """Propuesta de investigación cuantitativa generada en Fase 4."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    proposal_id: str
    parent_hash: str
    hypotheses: List[str]
    tools_required: List[str]
    blind_scope: str = "STRUCTURAL_ONLY"
    status: str = "PROPOSED"
    creator_agent: str
    created_at_utc: str


class ResearchExperimentRecord(BaseModel):
    """Experimento cuantitativo ejecutado por los agentes de investigación."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    experiment_id: str
    proposal_id: str
    inputs_hash: str
    tool_calls: List[Dict[str, Any]]
    results_hash: str
    outcome_summary: str
    created_at_utc: str


class AgentDebateRecord(BaseModel):
    """Registro de debate multi-agente de la Fase 4 de Research."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    debate_id: str
    strategy_hash: str
    participants: List[str]
    positions: Dict[str, str]
    disagreement_level: float = 0.0
    final_consensus_hypothesis: str
    created_at_utc: str


class MutationHistoryRecord(BaseModel):
    """Historial de mutación estructural de una regla AST."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    mutation_id: str
    parent_hash: str
    child_hash: str
    changed_fields: List[str]
    complexity_delta: int = 0
    outcome_verdict: str = "PENDING"
    created_at_utc: str


class SQXFeedbackRecord(BaseModel):
    """Registro de fertilidad y feedback de búsqueda para StrategyQuant X."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    feedback_id: str
    cohort_id: str
    symbol: str
    timeframe: str
    route: str
    fertility_score: float
    evidence_summary: Dict[str, Any] = Field(default_factory=dict)
    recommendation: str
    created_at_utc: str


class RevalidationQueueItem(BaseModel):
    """Elemento en cola de revalidación por cambio material de política o motor."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    queue_id: str
    strategy_id: str
    version: str
    strategy_hash: str
    invalidation_reason: str
    required_policies: List[str]
    status: str = "PENDING"
    scheduled_at_utc: str
    processed_at_utc: Optional[str] = None


class LearningPatternRecord(BaseModel):
    """Patrón de aprendizaje relacional que conecta causas de fallo con reparaciones exitosas."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    pattern_signature: str
    category: FailureCategory
    failure_count: int
    successful_repairs: int
    confidence_score: float
    evidence_refs: List[str] = Field(default_factory=list)
    suggested_mutation_priors: Dict[str, float] = Field(default_factory=dict)
    last_updated_utc: str


class KnowledgeLinkRecord(BaseModel):
    """Enlace relacional explícito en la cadena de conocimiento (Knowledge Link Graph)."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    link_id: str
    failure_id: Optional[str] = None
    proposal_id: Optional[str] = None
    experiment_id: Optional[str] = None
    mutation_id: Optional[str] = None
    strategy_version_id: Optional[str] = None
    validation_snapshot_id: Optional[str] = None
    created_at_utc: str
