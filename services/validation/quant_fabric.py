"""services/validation/quant_fabric.py
QuantValidationFabric bifurcado: despacha validaciones a FondeoEvidenceGate o UltraEvidenceGate y emite EvidenceGateDecision.
"""

from __future__ import annotations

import hashlib
import time
from typing import Optional

from contracts.backtest import BacktestResult
from contracts.canonical_strategy import CanonicalStrategy, ExecutionTrack
from contracts.validation_contracts import (
    EvidenceGateDecision,
    FondeoValidationCriteria,
    UltraValidationCriteria,
    ValidationTrack,
)
from services.validation.fondeo_gate import FondeoEvidenceGate
from services.validation.ultra_gate import UltraEvidenceGate


class QuantValidationFabric:
    """Motor central unificado de validación cuantitativa bifurcada y compuertas de evidencia."""

    def __init__(
        self,
        fondeo_gate: Optional[FondeoEvidenceGate] = None,
        ultra_gate: Optional[UltraEvidenceGate] = None,
    ) -> None:
        self.fondeo_gate = fondeo_gate or FondeoEvidenceGate()
        self.ultra_gate = ultra_gate or UltraEvidenceGate()

    def validate_strategy(
        self,
        strategy: CanonicalStrategy,
        backtest_result: BacktestResult,
        fondeo_criteria: Optional[FondeoValidationCriteria] = None,
        ultra_criteria: Optional[UltraValidationCriteria] = None,
    ) -> EvidenceGateDecision:
        """Valida una estrategia contra su track objetivo y genera la decisión de compuerta inmutable."""
        now_ms = int(time.time() * 1000)
        track = strategy.target_track

        if track == ExecutionTrack.TRACK_FONDEO:
            crit = fondeo_criteria or FondeoValidationCriteria()
            res = self.fondeo_gate.evaluate(strategy.strategy_id, backtest_result, crit)
            val_track = ValidationTrack.TRACK_FONDEO
        else:
            crit = ultra_criteria or UltraValidationCriteria()
            res = self.ultra_gate.evaluate(strategy.strategy_id, backtest_result, crit)
            val_track = ValidationTrack.TRACK_ULTRA

        payload = f"{strategy.strategy_id}:{val_track.value}:{res.passed}:{now_ms}:{strategy.compute_sha256()}"
        provenance_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

        return EvidenceGateDecision(
            decision_id=f"gate_dec_{strategy.strategy_id}_{now_ms % 100000}",
            strategy_id=strategy.strategy_id,
            track=val_track,
            approved=res.passed,
            timestamp_ms=now_ms,
            provenance_hash_sha256=provenance_hash,
            details=res,
        )
