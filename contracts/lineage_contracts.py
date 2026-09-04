"""Canonical immutable contracts for strategy lineage, certification and policy impact.

CanonicalStrategy remains the source of truth for trading rules. These records describe
version/certification context and must never be used as a second strategy definition.
"""

from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CertificationStatus(str, Enum):
    APPROVED = "APPROVED"
    ULTRA_CERTIFIED = "ULTRA_CERTIFIED"
    FUNDING_CERTIFIED = "FUNDING_CERTIFIED"
    PORTFOLIO_CERTIFIED = "PORTFOLIO_CERTIFIED"
    CERTIFIED_CURRENT = "CERTIFIED_CURRENT"
    CERTIFIED_LEGACY = "CERTIFIED_LEGACY"
    STALE = "STALE"
    REVALIDATION_REQUIRED = "REVALIDATION_REQUIRED"
    REVALIDATION_RUNNING = "REVALIDATION_RUNNING"
    REJECTED_ALTO_DRAWDOWN = "REJECTED_ALTO_DRAWDOWN"
    REJECTED_LOW_PF = "REJECTED_LOW_PF"
    REJECTED_OVERFITTING = "REJECTED_OVERFITTING"
    REJECTED_LOW_TRADES = "REJECTED_LOW_TRADES"
    REJECTED_LOW_CALMAR = "REJECTED_LOW_CALMAR"
    BLOCKED_DATASET_UNAPPROVED = "BLOCKED_DATASET_UNAPPROVED"
    BLOCKED_MISSING_FEE_SNAPSHOT = "BLOCKED_MISSING_FEE_SNAPSHOT"
    PENDING_EVALUATION = "PENDING_EVALUATION"


class CertificationRecord(BaseModel):
    """Immutable certificate for one exact strategy/policy/data context."""
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
    route: str
    metrics_snapshot: Dict[str, float]
    scorecard: Dict[str, Any] = Field(default_factory=dict)
    status: CertificationStatus
    certified_at_utc: str
    certificate_hash: str
    trial_id: Optional[str] = None

    dataset_policy_version: Optional[str] = None
    execution_policy_version: Optional[str] = None
    risk_policy_version: Optional[str] = None
    gate_policy_version: Optional[str] = None
    evidence_bundle_hash: Optional[str] = None
    ledger_hash: Optional[str] = None

    def context_hash(self) -> str:
        """Deterministic hash of certification identity and policy context."""
        payload = {
            "strategy_id": self.strategy_id,
            "version": self.version,
            "strategy_hash": self.strategy_hash,
            "dataset_id": self.dataset_id,
            "dataset_checksum_sha256": self.dataset_checksum_sha256,
            "engine_version": self.engine_version,
            "codebase_fingerprint": self.codebase_fingerprint,
            "rules_snapshot_id": self.rules_snapshot_id,
            "fee_snapshot_id": self.fee_snapshot_id,
            "route": self.route,
            "dataset_policy_version": self.dataset_policy_version,
            "execution_policy_version": self.execution_policy_version,
            "risk_policy_version": self.risk_policy_version,
            "gate_policy_version": self.gate_policy_version,
            "evidence_bundle_hash": self.evidence_bundle_hash,
            "ledger_hash": self.ledger_hash,
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def is_current(self, *, engine_version: str, gate_policy_version: Optional[str] = None) -> bool:
        """A legacy certificate can never be current when critical policy context differs."""
        if self.status != CertificationStatus.CERTIFIED_CURRENT:
            return False
        if self.engine_version != engine_version:
            return False
        if gate_policy_version is not None and self.gate_policy_version != gate_policy_version:
            return False
        return True


class LineageNode(BaseModel):
    """Node in the immutable DAG of strategy versions."""
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
    model_config = ConfigDict(frozen=True, extra="forbid")

    root_strategy_id: str
    total_nodes: int
    nodes: Dict[str, LineageNode]
    generations: List[List[str]] = Field(default_factory=list)
    certified_descendants: List[str] = Field(default_factory=list)


class PolicyTransitionType(str, Enum):
    CONSISTENT_PASS = "CONSISTENT_PASS"
    CONSISTENT_FAIL = "CONSISTENT_FAIL"
    REVOKED = "REVOKED"
    NEWLY_QUALIFIED = "NEWLY_QUALIFIED"


class StrategyPolicyTransition(BaseModel):
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
    model_config = ConfigDict(extra="forbid")

    target_route: str = "fondeo"
    new_max_drawdown_pct: Optional[float] = None
    new_min_profit_factor: Optional[float] = None
    new_min_calmar: Optional[float] = None
    new_min_trades: Optional[int] = None
    new_min_net_return_pct: Optional[float] = None
    cohort_ids: Optional[List[str]] = None


class PolicyImpactResult(BaseModel):
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
