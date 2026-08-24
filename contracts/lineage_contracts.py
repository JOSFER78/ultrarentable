"""contracts/lineage_contracts.py
Contratos canónicos e inmutables para Linaje de Certificación, Versionado y Policy Impact Analyzer.
Especificación oficial según Sección 7 y 8 del Informe Maestro v5.3.0.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CertificationStatus(str, Enum):
    APPROVED = "APPROVED"
    ULTRA_CERTIFIED = "ULTRA_CERTIFIED"
    FUNDING_CERTIFIED = "FUNDING_CERTIFIED"
    PORTFOLIO_CERTIFIED = "PORTFOLIO_CERTIFIED"
    REJECTED_ALTO_DRAWDOWN = "REJECTED_ALTO_DRAWDOWN"
    REJECTED_LOW_PF = "REJECTED_LOW_PF"
    REJECTED_OVERFITTING = "REJECTED_OVERFITTING"
    REJECTED_LOW_TRADES = "REJECTED_LOW_TRADES"
    REJECTED_LOW_CALMAR = "REJECTED_LOW_CALMAR"
    BLOCKED_DATASET_UNAPPROVED = "BLOCKED_DATASET_UNAPPROVED"
    BLOCKED_MISSING_FEE_SNAPSHOT = "BLOCKED_MISSING_FEE_SNAPSHOT"
    PENDING_EVALUATION = "PENDING_EVALUATION"


class CertificationRecord(BaseModel):
    """Certificado inmutable y verificable criptográficamente de una evaluación cuantitativa."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    certificate_id: str
    strategy_id: str
    version: str
    strategy_hash: str
    dataset_id: str
    dataset_checksum_sha256: str
    engine_version: str
    codebase_fingerprint: str
    rules_snapshot_id: str
    fee_snapshot_id: str
    route: str  # "ultra" | "fondeo"
    metrics_snapshot: Dict[str, float]
    scorecard: Dict[str, Any] = Field(default_factory=dict)
    status: CertificationStatus
    certified_at_utc: str
    certificate_hash: str


class LineageNode(BaseModel):
    """Nodo en el grafo acíclico dirigido (DAG) de linaje de una estrategia."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    strategy_id: str
    version: str
    strategy_hash: str
    family: str
    venue: str
    symbol: str
    timeframe: str
    parent_ids: List[str] = Field(default_factory=list)
    mutation_type: Optional[str] = None
    mutation_reason: Optional[str] = None
    created_at_utc: str
    certifications: List[CertificationRecord] = Field(default_factory=list)
    children: List[str] = Field(default_factory=list)


class LineageTreeResponse(BaseModel):
    """Respuesta completa del árbol de linaje de una estrategia."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    root_strategy_id: str
    total_nodes: int
    nodes: Dict[str, LineageNode]
    generations: List[List[str]] = Field(default_factory=list)
    certified_descendants: List[str] = Field(default_factory=list)


class PolicyTransitionType(str, Enum):
    CONSISTENT_PASS = "CONSISTENT_PASS"
    CONSISTENT_FAIL = "CONSISTENT_FAIL"
    REVOKED = "REVOKED"                  # Pasaba antes, ahora cae
    NEWLY_QUALIFIED = "NEWLY_QUALIFIED"  # Caía antes, ahora pasa


class StrategyPolicyTransition(BaseModel):
    """Detalle de transición de una estrategia individual ante el cambio de política."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    strategy_id: str
    version: str
    family: str
    symbol: str
    route: str
    baseline_status: str
    new_status: str
    transition_type: PolicyTransitionType
    trigger_rule: Optional[str] = None
    metrics: Dict[str, float]


class PolicyImpactRequest(BaseModel):
    """Petición de simulación de impacto de cambio de política de calidad."""
    model_config = ConfigDict(extra="forbid")

    target_route: str = "fondeo"  # "fondeo" | "ultra" | "all"
    new_max_drawdown_pct: Optional[float] = None
    new_min_profit_factor: Optional[float] = None
    new_min_calmar: Optional[float] = None
    new_min_trades: Optional[int] = None
    new_min_net_return_pct: Optional[float] = None
    cohort_ids: Optional[List[str]] = None


class PolicyImpactResult(BaseModel):
    """Resultado determinista del análisis de impacto de política."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    analysis_id: str
    target_route: str
    analyzed_at_utc: str
    total_cohort_size: int
    baseline_policy: Dict[str, Any]
    new_policy: Dict[str, Any]
    baseline_passed_count: int
    new_policy_passed_count: int
    pass_rate_baseline_pct: float
    pass_rate_new_pct: float
    pass_rate_delta_pct: float
    transition_summary: Dict[str, int]
    revoked_count: int
    newly_qualified_count: int
    sample_revocations: List[StrategyPolicyTransition] = Field(default_factory=list)
    sample_new_qualifications: List[StrategyPolicyTransition] = Field(default_factory=list)
    recommendation: str
