"""contracts/evidence_bundle.py
Contrato Canónico de Paquete Completo de Evidencia Cuantitativa (EvidenceBundle v3.0.0).

DOCTRINA ZERO-MOCKS & SCIENTIFIC REPRODUCIBILITY:
- Empaqueta y sella criptográficamente la evidencia integral de descubrimiento y validación.
- Contiene los hashes SHA-256 inmutables de: estrategia, datasets IS/OOS, costes de microestructura,
  versión del motor, commit Git, ledger secuencial Merkle y decisiones de los 11 gates.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class EvidenceBundle(BaseModel):
    """Paquete Canónico Inmutable de Evidencia Científica para Ultrarentable V2."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    bundle_id: str = Field(..., description="ID unívoco del paquete e.g. bnd_UR-001_1770000000")
    strategy_id: str = Field(..., description="ID de la estrategia canónica")
    strategy_sha256: str = Field(..., description="Hash SHA-256 del AST canónico inmutable")
    
    dataset_id: str = Field(...)
    dataset_is_sha256: str = Field(..., description="Hash SHA-256 de los datos In-Sample")
    dataset_oos_sha256: str = Field(..., description="Hash SHA-256 de los datos Out-of-Sample")
    
    symbol: str = Field(...)
    timeframe: str = Field(...)
    target_track: str = Field(..., description="FONDEO / ULTRA")
    
    execution_config_hash: str = Field(..., description="Hash de la microestructura y costes reales")
    engine_name: str = Field(default="UniversalDeterministicBacktestEngine")
    engine_version: str = Field(default="3.0.0")
    commit_sha: str = Field(..., description="Commit Git exacto del código que generó la evidencia")
    
    initial_capital_usd: float = Field(...)
    is_trades_count: int = Field(...)
    oos_trades_count: int = Field(...)
    
    is_metrics: Dict[str, Any] = Field(default_factory=dict)
    oos_metrics: Dict[str, Any] = Field(default_factory=dict)
    
    ledger_hash: str = Field(..., description="Hash Merkle secuencial trade a trade")
    gates_evaluation: Dict[str, Any] = Field(default_factory=dict, description="Veredictos y métricas de los 11 gates")
    
    created_at_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    bundle_signature_sha256: str = Field(default="", description="Firma criptográfica global del paquete")

    def __init__(self, **data: Any):
        super().__init__(**data)
        if not self.bundle_signature_sha256:
            sig = self._compute_signature()
            object.__setattr__(self, "bundle_signature_sha256", sig)

    def _compute_signature(self) -> str:
        payload = {
            "strategy_id": self.strategy_id,
            "strategy_sha256": self.strategy_sha256,
            "dataset_is_sha256": self.dataset_is_sha256,
            "dataset_oos_sha256": self.dataset_oos_sha256,
            "execution_config_hash": self.execution_config_hash,
            "engine_version": self.engine_version,
            "commit_sha": self.commit_sha,
            "ledger_hash": self.ledger_hash,
            "initial_capital_usd": self.initial_capital_usd,
        }
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def verify_integrity(self, expected_strategy_sha256: Optional[str] = None) -> bool:
        """Verifica criptográfica y forensemente la validez integral del EvidenceBundle."""
        # 1. Validación de formato de hashes (64 hex characters)
        def _is_hex64(val: str) -> bool:
            return bool(isinstance(val, str) and len(val) == 64 and all(c in "0123456789abcdefABCDEF" for c in val))

        if not _is_hex64(self.strategy_sha256):
            raise ValueError(f"VIOLACION_HASH_ESTRATEGIA: strategy_sha256 inválido ('{self.strategy_sha256}').")

        if not _is_hex64(self.dataset_is_sha256):
            raise ValueError(f"VIOLACION_HASH_DATASET_IS: dataset_is_sha256 inválido ('{self.dataset_is_sha256}').")

        if not _is_hex64(self.dataset_oos_sha256):
            raise ValueError(f"VIOLACION_HASH_DATASET_OOS: dataset_oos_sha256 inválido ('{self.dataset_oos_sha256}').")

        if not _is_hex64(self.ledger_hash):
            raise ValueError(f"VIOLACION_HASH_LEDGER: ledger_hash inválido ('{self.ledger_hash}').")

        # 2. Verificación de firma criptográfica
        expected_signature = self._compute_signature()
        if self.bundle_signature_sha256 != expected_signature:
            raise ValueError(
                f"VIOLACION_FIRMA_EVIDENCIA: Firma recibida '{self.bundle_signature_sha256}' "
                f"no coincide con la firma computada '{expected_signature}'."
            )

        # 3. Verificación de concordancia de estrategia si se provee
        if expected_strategy_sha256 is not None:
            if self.strategy_sha256 != expected_strategy_sha256:
                raise ValueError(
                    f"DISCREPANCIA_LINEAJE: EvidenceBundle.strategy_sha256 ('{self.strategy_sha256}') "
                    f"no coincide con el SHA-256 canónico esperado ('{expected_strategy_sha256}')."
                )

        # 4. Verificación de veredictos de gates
        if not self.gates_evaluation or not isinstance(self.gates_evaluation, dict):
            raise ValueError("VIOLACION_EVALUACION_GATES: 'gates_evaluation' está ausente o no es un diccionario válido.")

        # Verificar si hay veredicto general o gates individuales
        if "approved" in self.gates_evaluation and not self.gates_evaluation["approved"]:
            raise ValueError("RECHAZO_GATES: 'gates_evaluation' indica que la estrategia fue rechazada.")
        if "is_certified" in self.gates_evaluation and not self.gates_evaluation["is_certified"]:
            raise ValueError("RECHAZO_CERTIFICACION: 'gates_evaluation' indica que la estrategia no está certificada.")

        # Verificar lista o mapa de gates individuales
        for k, v in self.gates_evaluation.items():
            if isinstance(v, str) and v.upper() in ("FAILED", "REJECTED", "FAIL", "DISQUALIFIED"):
                raise ValueError(f"RECHAZO_GATE_INDIVIDUAL: Gate '{k}' tiene veredicto fallido ('{v}').")
            elif isinstance(v, dict):
                gate_status = v.get("status") or v.get("verdict")
                gate_passed = v.get("passed")
                if gate_passed is False:
                    raise ValueError(f"RECHAZO_GATE_INDIVIDUAL: Gate '{k}' no superó el umbral (passed=False).")
                if isinstance(gate_status, str) and gate_status.upper() in ("FAILED", "REJECTED", "FAIL"):
                    raise ValueError(f"RECHAZO_GATE_INDIVIDUAL: Gate '{k}' tiene status '{gate_status}'.")

        return True
