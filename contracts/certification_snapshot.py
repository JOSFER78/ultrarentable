"""Certification snapshot contract.

A certification is valid only for the exact strategy, evidence, engine and policy
versions captured here. Historical certification cannot silently become current.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Dict

from pydantic import BaseModel, ConfigDict, Field


class CertificationSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    certification_id: str
    strategy_id: str
    strategy_version: str
    strategy_hash: str = Field(..., min_length=64, max_length=64)

    dataset_hash: str = Field(..., min_length=64, max_length=64)
    execution_hash: str = Field(..., min_length=64, max_length=64)
    risk_policy_hash: str = Field(..., min_length=64, max_length=64)
    engine_version: str
    compiler_version: str
    gate_policy_version: str

    evidence_bundle_hash: str = Field(..., min_length=64, max_length=64)
    ledger_hash: str = Field(..., min_length=64, max_length=64)
    verdict: str
    created_at_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    gate_verdicts: Dict[str, str]

    def snapshot_hash(self) -> str:
        payload = self.model_dump(exclude={"created_at_utc"})
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def is_current(self, *, engine_version: str, compiler_version: str, gate_policy_version: str) -> bool:
        return (
            self.engine_version == engine_version
            and self.compiler_version == compiler_version
            and self.gate_policy_version == gate_policy_version
        )
