"""services/validation/engines/gate_04_walk_forward_efficiency.py
Motor 4 de Validación: Walk-Forward Efficiency & Degradación OOS.
Evalúa la pérdida de rendimiento entre In-Sample y Out-of-Sample para detectar sobreajuste (curve-fitting).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List


@dataclass
class WalkForwardEfficiencyResult:
    passed: bool
    is_profit_factor: float
    oos_profit_factor: float
    walk_forward_efficiency: float
    degradation_pct: float
    error_reasons: List[str]


class WalkForwardEfficiencyEngine:
    """Motor independiente para calcular Walk-Forward Efficiency (WFE) y degradación OOS."""

    def __init__(
        self,
        min_wfe: float = 0.50,
        min_oos_profit_factor: float = 1.20,
        max_degradation_pct: float = 50.0,
    ) -> None:
        self.min_wfe = min_wfe
        self.min_oos_profit_factor = min_oos_profit_factor
        self.max_degradation_pct = max_degradation_pct

    def evaluate(
        self,
        is_profit_factor: float,
        oos_profit_factor: float,
    ) -> WalkForwardEfficiencyResult:
        errors: List[str] = []

        wfe = (oos_profit_factor / is_profit_factor) if is_profit_factor > 0 else 0.0
        degradation = max(0.0, (1.0 - wfe) * 100.0) if is_profit_factor > 0 else 100.0

        if oos_profit_factor < self.min_oos_profit_factor:
            errors.append(f"Profit Factor OOS deficiente: {oos_profit_factor:.2f} < {self.min_oos_profit_factor:.2f}")

        if wfe < self.min_wfe:
            errors.append(f"Walk-Forward Efficiency insuficiente: {wfe:.2f} < {self.min_wfe:.2f} (Degradación: {degradation:.1f}%)")

        if degradation > self.max_degradation_pct:
            errors.append(f"Degradación OOS excesiva: {degradation:.1f}% > {self.max_degradation_pct:.1f}% máx tolerado.")

        passed = len(errors) == 0
        return WalkForwardEfficiencyResult(
            passed=passed,
            is_profit_factor=round(is_profit_factor, 2),
            oos_profit_factor=round(oos_profit_factor, 2),
            walk_forward_efficiency=round(wfe, 2),
            degradation_pct=round(degradation, 1),
            error_reasons=errors,
        )
