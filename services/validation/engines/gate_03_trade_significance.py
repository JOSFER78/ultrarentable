"""services/validation/engines/gate_03_trade_significance.py
Motor 3 de Validación: Significancia Estadística del Tamaño Muestral.
Verifica que el número de operaciones y la cadencia mensual cumplan los umbrales mínimos de representatividad estadística.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List


@dataclass
class TradeSignificanceResult:
    passed: bool
    total_trades_is: int
    total_trades_oos: int
    trades_per_month: float
    error_reasons: List[str]


class TradeSignificanceEngine:
    """Motor independiente para validar el tamaño de muestra de trades."""

    def __init__(
        self,
        min_trades_total: int = 40,
        min_trades_oos: int = 20,
        min_trades_per_month: float = 2.5,
    ) -> None:
        self.min_trades_total = min_trades_total
        self.min_trades_oos = min_trades_oos
        self.min_trades_per_month = min_trades_per_month

    def evaluate(
        self,
        is_trades_count: int,
        oos_trades_count: int,
        duration_months: float = 5.2,
    ) -> TradeSignificanceResult:
        errors: List[str] = []
        total_trades = is_trades_count + oos_trades_count
        tpm = (total_trades / duration_months) if duration_months > 0 else 0.0

        if total_trades < self.min_trades_total:
            errors.append(f"Muestra global insuficiente: {total_trades} trades < {self.min_trades_total} mínimo requerido.")

        if oos_trades_count < self.min_trades_oos:
            errors.append(f"Muestra OOS insuficiente: {oos_trades_count} trades < {self.min_trades_oos} mínimo OOS requerido.")

        if tpm < self.min_trades_per_month:
            errors.append(f"Frecuencia operativa demasiado baja: {tpm:.1f} trades/mes < {self.min_trades_per_month} req.")

        passed = len(errors) == 0
        return TradeSignificanceResult(
            passed=passed,
            total_trades_is=is_trades_count,
            total_trades_oos=oos_trades_count,
            trades_per_month=round(tpm, 2),
            error_reasons=errors,
        )
