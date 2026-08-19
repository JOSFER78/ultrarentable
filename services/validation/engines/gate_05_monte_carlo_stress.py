"""services/validation/engines/gate_05_monte_carlo_stress.py
Motor 5 de Validación: Estrés de Robustez Monte Carlo y Probabilidad de Ruina.
Ejecuta 1.000 simulaciones de permutación y reordenamiento de trades para estimar la probabilidad de ruina y Max DD en el percentil 95.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List
import numpy as np


@dataclass
class MonteCarloStressResult:
    passed: bool
    ruin_probability_pct: float
    p95_max_drawdown_pct: float
    median_profit_usd: float
    worst_case_drawdown_pct: float
    error_reasons: List[str]


class MonteCarloStressEngine:
    """Motor independiente para simulación Monte Carlo sobre la secuencia de trades."""

    def __init__(
        self,
        num_simulations: int = 1000,
        max_allowed_ruin_pct: float = 1.0,
        max_allowed_p95_dd_pct: float = 8.0,
        ruin_dd_threshold_pct: float = 10.0,
    ) -> None:
        self.num_simulations = num_simulations
        self.max_allowed_ruin_pct = max_allowed_ruin_pct
        self.max_allowed_p95_dd_pct = max_allowed_p95_dd_pct
        self.ruin_dd_threshold_pct = ruin_dd_threshold_pct

    def evaluate(
        self,
        trades: List[float],
        initial_capital: float = 10000.0,
    ) -> MonteCarloStressResult:
        errors: List[str] = []
        if len(trades) < 10:
            return MonteCarloStressResult(
                passed=False,
                ruin_probability_pct=100.0,
                p95_max_drawdown_pct=100.0,
                median_profit_usd=0.0,
                worst_case_drawdown_pct=100.0,
                error_reasons=["Muestra insuficiente para simulación Monte Carlo (< 10 trades)."],
            )

        arr_trades = np.array(trades, dtype=np.float64)
        n = len(arr_trades)

        sim_max_dds = []
        sim_final_pnls = []
        ruin_count = 0

        rng = np.random.default_rng(seed=42)
        for _ in range(self.num_simulations):
            shuffled = rng.choice(arr_trades, size=n, replace=True)
            equity = initial_capital + np.cumsum(np.insert(shuffled, 0, 0.0))
            peak = np.maximum.accumulate(equity)
            dd = (peak - equity) / peak * 100.0
            max_dd = float(np.max(dd))
            sim_max_dds.append(max_dd)
            sim_final_pnls.append(float(equity[-1] - initial_capital))

            if max_dd >= self.ruin_dd_threshold_pct or equity[-1] <= 0:
                ruin_count += 1

        ruin_pct = (ruin_count / self.num_simulations) * 100.0
        p95_dd = float(np.percentile(sim_max_dds, 95))
        worst_dd = float(np.max(sim_max_dds))
        median_profit = float(np.median(sim_final_pnls))

        if ruin_pct > self.max_allowed_ruin_pct:
            errors.append(f"Probabilidad de Ruina MC excesiva: {ruin_pct:.2f}% > {self.max_allowed_ruin_pct:.2f}%")

        if p95_dd > self.max_allowed_p95_dd_pct:
            errors.append(f"Max DD MC al 95% excede el umbral: {p95_dd:.2f}% > {self.max_allowed_p95_dd_pct:.2f}%")

        passed = len(errors) == 0
        return MonteCarloStressResult(
            passed=passed,
            ruin_probability_pct=round(ruin_pct, 2),
            p95_max_drawdown_pct=round(p95_dd, 2),
            median_profit_usd=round(median_profit, 2),
            worst_case_drawdown_pct=round(worst_dd, 2),
            error_reasons=errors,
        )
