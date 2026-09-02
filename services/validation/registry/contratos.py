"""services/validation/registry/contratos.py
Contratos canónicos y clase base para el registro unificado de 11 gates v1.
Paridad exacta con la suite B (D5) en motor 5.17.0.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import numpy as np

from contracts.snapshots.evidence_record import GateStatus


def _sanitize_dict(obj: Any) -> Any:
    """Convierte tipos numpy (np.bool_, np.float64, np.ndarray) a tipos estándar de Python."""
    if isinstance(obj, dict):
        return {str(k): _sanitize_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_sanitize_dict(x) for x in obj]
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, (np.integer, int)):
        return int(obj)
    elif isinstance(obj, (np.floating, float)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return [_sanitize_dict(x) for x in obj.tolist()]
    return obj


@dataclass(frozen=True)
class Evidencia:
    candidate_info: Dict[str, Any]
    candles: Optional[List[Dict[str, Any]]] = None
    is_trades: Optional[List[float]] = None
    oos_trades: Optional[List[float]] = None
    pre_oos_trades: Optional[List[float]] = None
    trades_raw: Optional[List[Dict[str, Any]]] = None
    strategy_snapshot: Optional[Any] = None

    @property
    def is_ultra(self) -> bool:
        return self.candidate_info.get("route") == "ULTRA"

    @property
    def base_capital(self) -> float:
        return 1000.0 if self.is_ultra else 50000.0


@dataclass
class GateResult:
    gate_id: int
    name: str
    gate_version: str
    passed: bool
    score: float
    verdict: str
    evidence: Dict[str, Any]
    status: GateStatus

    def como_dict_b(self) -> Dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "name": self.name,
            "passed": self.passed,
            "score": self.score,
            "verdict": self.verdict,
            "evidence": self.evidence,
        }


class GateBase:
    GATE_ID: int = 0
    NAME: str = ""
    LABEL: str = ""
    VERSION: str = "1.0.0"
    UMBRALES: Dict[str, Any] = {}

    def evaluar(self, ev: Evidencia) -> GateResult:
        raise NotImplementedError

    def _resultado(self, raw: dict) -> GateResult:
        sanitized = _sanitize_dict(raw)
        passed = bool(sanitized.get("passed", False))
        return GateResult(
            gate_id=int(sanitized.get("gate_id", self.GATE_ID)),
            name=str(sanitized.get("name", self.NAME)),
            gate_version=self.VERSION,
            passed=passed,
            score=float(sanitized.get("score", 0.0)),
            verdict=str(sanitized.get("verdict", "")),
            evidence=dict(sanitized.get("evidence", {})),
            status=GateStatus.PASSED if passed else GateStatus.FAILED,
        )
