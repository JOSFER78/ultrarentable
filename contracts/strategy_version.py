"""Immutable strategy versioning and certification lineage contracts.

This module defines lifecycle metadata without duplicating the strategy definition.
CanonicalStrategy remains the source of truth for trading rules. StrategyVersion is
an immutable envelope linking that definition to its parent, policies and evidence.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class CertificationState(str, Enum):
    UNTESTED = "UNTESTED"
    TESTED = "TESTED"
    CERTIFIED_CURRENT = "CERTIFIED_CURRENT"
    CERTIFIED_LEGACY = "CERTIFIED_LEGACY"
    STALE = "STALE"
    REVALIDATION_REQUIRED = "REVALIDATION_REQUIRED"
    REVALIDATION_RUNNING = "REVALIDATION_RUNNING"
    FAILED_CURRENT_POLICY = "FAILED_CURRENT_POLICY"
    RETIRED = "RETIRED"


class StrategyVersion(BaseModel):
    """Immutable lineage record for one concrete strategy definition."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    strategy_id: str
    version: str = Field(..., min_length=1)
    strategy_hash: str = Field(..., min_length=64, max_length=64)
    parent_strategy_id: Optional[str] = None
    parent_version: Optional[str] = None
    parent_strategy_hash: Optional[str] = None

    engine_version: str
    compiler_version: str
    dataset_policy_version: str
    execution_policy_version: str
    risk_policy_version: str
    gate_policy_version: str

    certification_state: CertificationState = CertificationState.UNTESTED
    certification_snapshot_hash: Optional[str] = None
    evidence_bundle_hash: Optional[str] = None

    created_at_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    created_by: str
    change_reason: str
    changed_fields: Dict[str, str] = Field(default_factory=dict)

    def lineage_hash(self) -> str:
        payload = self.model_dump(exclude={"created_at_utc", "certification_state"})
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def is_currently_certified(self) -> bool:
        return self.certification_state == CertificationState.CERTIFIED_CURRENT

    def is_stale(self) -> bool:
        return self.certification_state in {
            CertificationState.CERTIFIED_LEGACY,
            CertificationState.STALE,
            CertificationState.REVALIDATION_REQUIRED,
            CertificationState.REVALIDATION_RUNNING,
        }
