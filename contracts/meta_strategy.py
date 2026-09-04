"""Canonical Meta-Strategy composition contract.

A meta-strategy is a strategy-of-strategies: it combines compatible immutable
strategy versions across assets/timeframes using real joint evidence, explicit
risk budgets and compensation rules. It is not an average of stale metrics.
"""
from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CompensationMethod(str, Enum):
    CORRELATION = "CORRELATION"
    RISK_PARITY = "RISK_PARITY"
    EXPOSURE_BALANCING = "EXPOSURE_BALANCING"
    DRAWDOWN_COMPENSATION = "DRAWDOWN_COMPENSATION"
    REGIME_BALANCING = "REGIME_BALANCING"


class MetaConstituent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    strategy_id: str
    strategy_version: str
    strategy_hash: str = Field(..., min_length=64, max_length=64)
    route: str
    symbol: str
    timeframe: str
    allocation_cap_pct: float = Field(..., ge=0.0, le=100.0)
    risk_budget_pct: float = Field(..., ge=0.0, le=100.0)


class MetaStrategyPolicy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    max_pairwise_correlation: float = Field(0.70, ge=-1.0, le=1.0)
    max_single_strategy_risk_pct: float = Field(25.0, gt=0.0, le=100.0)
    max_aggregate_drawdown_pct: float = Field(..., gt=0.0, le=100.0)
    compensation_methods: List[CompensationMethod] = Field(default_factory=list)
    require_current_certification: bool = True
    require_joint_oos_evidence: bool = True


class MetaStrategyDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    meta_strategy_id: str
    version: str
    route: str
    constituents: List[MetaConstituent] = Field(..., min_length=2)
    policy: MetaStrategyPolicy
    joint_dataset_hash: str = Field(..., min_length=64, max_length=64)
    joint_evidence_hash: str = Field(..., min_length=64, max_length=64)
    provenance_hash: str = Field(..., min_length=64, max_length=64)
    created_at_utc: str

    def composition_hash(self) -> str:
        payload = self.model_dump(exclude={"created_at_utc", "provenance_hash"})
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
