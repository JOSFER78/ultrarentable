"""contracts/snapshots/evidence_record.py
Contrato Inmutable de Registro de Evidencia Forense (Fase 1).
Cada Gate de validación produce un EvidenceRecord con trazabilidad criptográfica SHA-256
sobre sus inputs, outputs, dataset físico, versión de fórmula y veredicto.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class GateStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class EvidenceRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    evidence_id: str = Field(..., description="ID unívoco del registro de evidencia")
    run_id: str = Field(..., description="ID de ejecución de la sesión o pipeline")
    strategy_id: str = Field(..., description="ID unívoco de la estrategia evaluada")
    strategy_snapshot_hash: str = Field(..., description="Hash SHA-256 del StrategySnapshot inmutable")
    dataset_id: str = Field(..., description="ID del dataset físico utilizado")
    dataset_sha256: str = Field(..., description="Hash SHA-256 real de los bytes del dataset en disco")
    
    gate_id: int = Field(..., ge=1, le=11, description="Número del Gate (1 a 11)")
    gate_name: str = Field(..., description="Nombre canónico del Gate")
    engine: str = Field(..., description="Nombre del motor cuantitativo ejecutor")
    engine_version: str = Field(default="2.0.0", description="Versión del motor")
    formula_version: str = Field(default="2.0.0", description="Versión de la fórmula matemática")
    
    input_hash: str = Field(..., description="Hash SHA-256 de los inputs suministrados al gate")
    output_hash: str = Field(..., description="Hash SHA-256 de los resultados brutos producidos")
    
    status: GateStatus = Field(..., description="Estado determinista: PASSED, FAILED, BLOCKED o ERROR")
    score: float = Field(..., ge=0.0, le=100.0, description="Score cuantitativo de 0 a 100")
    verdict: str = Field(..., description="Veredicto textual detallado con causa raíz")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Diccionario de métricas auditables")
    artifact_path: Optional[str] = Field(None, description="Ruta al artefacto JSON persistido en disco")
    created_at_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def create(
        cls,
        evidence_id: str,
        run_id: str,
        strategy_id: str,
        strategy_snapshot_hash: str,
        dataset_id: str,
        dataset_sha256: str,
        gate_id: int,
        gate_name: str,
        engine: str,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        status: GateStatus,
        score: float,
        verdict: str,
        metrics: Dict[str, Any],
        engine_version: str = "2.0.0",
        formula_version: str = "2.0.0",
        artifact_path: Optional[str] = None,
    ) -> EvidenceRecord:
        """Construye un EvidenceRecord calculando los hashes criptográficos deterministas de inputs y outputs."""
        input_bytes = json.dumps(inputs, sort_keys=True, default=str).encode("utf-8")
        output_bytes = json.dumps(outputs, sort_keys=True, default=str).encode("utf-8")
        
        input_hash = hashlib.sha256(input_bytes).hexdigest()
        output_hash = hashlib.sha256(output_bytes).hexdigest()

        return cls(
            evidence_id=evidence_id,
            run_id=run_id,
            strategy_id=strategy_id,
            strategy_snapshot_hash=strategy_snapshot_hash,
            dataset_id=dataset_id,
            dataset_sha256=dataset_sha256,
            gate_id=gate_id,
            gate_name=gate_name,
            engine=engine,
            engine_version=engine_version,
            formula_version=formula_version,
            input_hash=input_hash,
            output_hash=output_hash,
            status=status,
            score=round(float(score), 2),
            verdict=verdict,
            metrics=metrics,
            artifact_path=artifact_path,
        )
