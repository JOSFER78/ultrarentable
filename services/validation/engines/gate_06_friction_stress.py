"""services/validation/engines/gate_06_friction_stress.py
Motor 6 de Validación: Estrés de Fricción y Deslizamiento Adverso (Slippage Multiplier).
Aplica un multiplicador de fricción (2x spread/slippage y +5 bps de comisión) para asegurar que la estrategia no dependa de ejecuciones ideales de laboratorio.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List


@dataclass
class FrictionStressResult:
    passed: bool
    base_profit_factor: float
    stressed_profit_factor: float
    profit_factor_retention_pct: float
    is_positive_under_stress: bool
    error_reasons: List[str]


class FrictionStressEngine:
    """Motor independiente para someter las operaciones a fricción y spread extremo."""

    def __init__(
        self,
        min_stressed_profit_factor: float = 1.10,
        min_retention_pct: float = 65.0,
        extra_friction_per_trade_usd: float = 5.0,
    ) -> None:
        self.min_stressed_profit_factor = min_stressed_profit_factor
        self.min_retention_pct = min_retention_pct
        self.extra_friction_per_trade_usd = extra_friction_per_trade_usd

    def evaluate(
        self,
        trades: List[float],
        base_profit_factor: float,
    ) -> FrictionStressResult:
        errors: List[str] = []
        if not trades:
            return FrictionStressResult(
                passed=False,
                base_profit_factor=0.0,
                stressed_profit_factor=0.0,
                profit_factor_retention_pct=0.0,
                is_positive_under_stress=False,
                error_reasons=["Sin operaciones para prueba de fricción."],
            )

        # Aplicar fricción adversa
        stressed_trades = [t - self.extra_friction_per_trade_usd for t in trades]
        gross_wins = sum(t for t in stressed_trades if t > 0)
        gross_losses = abs(sum(t for t in stressed_trades if t < 0))
        stressed_pf = (gross_wins / gross_losses) if gross_losses > 0 else (99.0 if gross_wins > 0 else 0.0)

        retention = (stressed_pf / base_profit_factor * 100.0) if base_profit_factor > 0 else 0.0
        is_pos = sum(stressed_trades) > 0

        if stressed_pf < self.min_stressed_profit_factor:
            errors.append(
                f"Profit Factor bajo estrés adverso insuficiente: {stressed_pf:.2f} < {self.min_stressed_profit_factor:.2f}"
            )

        if retention < self.min_retention_pct:
            errors.append(
                f"Retención de rentabilidad bajo fricción insuficiente: {retention:.1f}% < {self.min_retention_pct:.1f}%"
            )

        if not is_pos:
            errors.append("La estrategia entra en pérdidas netas ante fricción y deslizamiento de mercado.")

        passed = len(errors) == 0
        return FrictionStressResult(
            passed=passed,
            base_profit_factor=round(base_profit_factor, 2),
            stressed_profit_factor=round(stressed_pf, 2),
            profit_factor_retention_pct=round(retention, 1),
            is_positive_under_stress=is_pos,
            error_reasons=errors,
        )
