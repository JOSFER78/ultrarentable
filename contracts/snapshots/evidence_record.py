"""contracts/snapshots/evidence_record.py
Contrato canónico de EvidenceRecord y GateStatus para el pipeline modular de 11 Gates.
Especificación oficial según Sección 5, 7 y 8 del Informe Maestro v5.3.0.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class GateStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    BLOCKED = "BLOCKED"
    PENDING = "PENDING"


class EvidenceRecord(BaseModel):
    """Registro inmutable de evidencia física y verificación criptográfica de un Gate."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    evidence_id: str
    run_id: str
    strategy_id: str
    strategy_snapshot_hash: str
    dataset_id: str
    dataset_sha256: str
    gate_id: int
    gate_name: str
    engine: str = "UltrarentableQuantitativeCore"
    engine_version: str = "5.3.0"
    formula_version: str = "5.3.0"
    input_hash: str
    output_hash: str
    status: GateStatus
    score: float = Field(ge=0.0, le=100.0)
    verdict: str
    metrics: Dict[str, Any] = Field(default_factory=dict)
    artifact_path: Optional[str] = None
