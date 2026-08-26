from __future__ import annotations

from typing import Any

import numpy as np


class Gate05MonteCarlo:
    GATE_ID = 5
    NAME = "MONTE_CARLO"
    LABEL = "5. MONTE CARLO"

    def evaluate(
        self,
        oos_trades: list[float],
        initial_capital: float = 1000.0,
        num_sims: int = 1000,
        is_ultra: bool = True,
    ) -> dict[str, Any]:
        if not oos_trades or len(oos_trades) < 10:
            return {
                "gate_id": self.GATE_ID,
                "name": self.NAME,
                "passed": False,
                "score": 0.0,
                "verdict": "RECHAZADO: Trades insuficientes para simulación Monte Carlo (< 10 trades)",
                "evidence": {"simulations_run": 0},
            }

        ruin_drawdown_pct = 35.0 if is_ultra else 4.5
        max_allowed_dd_95 = 30.0 if is_ultra else 4.0

        n_trades = len(oos_trades)
        max_dds = []
        ruin_count = 0
        rng = np.random.default_rng(42)

        raw_arr = np.array(oos_trades, dtype=np.float64)
        # Si los valores vienen en porcentaje (ej. 7.5 para 7.5%), normalizar a retornos fraccionales (0.075)
        # Si vienen en dólares nominales brutos mayores a initial_capital * 0.5, normalizar por initial_capital
        if np.max(np.abs(raw_arr)) > 50.0 and np.max(np.abs(raw_arr)) > initial_capital * 0.1:
            # Entrada en dólares nominales
            if is_ultra:
                eq_trajectory = [initial_capital]
                for pnl in oos_trades:
                    eq_trajectory.append(max(1.0, eq_trajectory[-1] + pnl))
                returns_arr = np.array([oos_trades[i] / eq_trajectory[i] for i in range(n_trades)], dtype=np.float64)
            else:
                returns_arr = raw_arr / initial_capital
        elif np.max(np.abs(raw_arr)) > 1.0:
            # Entrada en porcentajes directos (ej. 7.5%)
            returns_arr = raw_arr / 100.0
        else:
            # Entrada ya en retornos fraccionales puros (ej. 0.075)
            returns_arr = raw_arr

        if is_ultra:
            # En la ruta ULTRA con reinversión geométrica (Compounding Dinámico)
            for _ in range(num_sims):
                sim_returns = rng.choice(returns_arr, size=n_trades, replace=True)
                sim_eq = [initial_capital]
                for r in sim_returns:
                    sim_eq.append(max(0.01, sim_eq[-1] * (1.0 + r)))
                sim_eq = np.array(sim_eq, dtype=np.float64)
                peak = np.maximum.accumulate(sim_eq)
                dd_series = (peak - sim_eq) / np.maximum(1.0, peak) * 100.0
                max_sim_dd = float(np.max(dd_series))
                max_dds.append(max_sim_dd)

                if max_sim_dd >= ruin_drawdown_pct:
                    ruin_count += 1
        else:
            # En la ruta FONDEO (CME Props), contratos de tamaño fijo (lineal aditivo)
            for _ in range(num_sims):
                sim_returns = rng.choice(returns_arr, size=n_trades, replace=True)
                sim_trades_usd = sim_returns * initial_capital
                equity_curve = initial_capital + np.cumsum(np.insert(sim_trades_usd, 0, 0.0))
                peak = np.maximum.accumulate(equity_curve)
                dd_series = (peak - equity_curve) / np.maximum(1.0, peak) * 100.0
                max_sim_dd = float(np.max(dd_series))
                max_dds.append(max_sim_dd)

                if max_sim_dd >= ruin_drawdown_pct:
                    ruin_count += 1

        ruin_prob_pct = (ruin_count / num_sims) * 100.0
        dd_95th = float(np.percentile(max_dds, 95))
        dd_median = float(np.median(max_dds))

        passed = (ruin_prob_pct <= (5.0 if is_ultra else 0.5)) and (dd_95th <= max_allowed_dd_95)
        score = max(0.0, min(100.0, 100.0 - (ruin_prob_pct * 10) - (dd_95th * (0.5 if is_ultra else 10.0)))) if passed else 0.0

        return {
            "gate_id": self.GATE_ID,
            "name": self.NAME,
            "passed": passed,
            "score": round(score, 1),
            "verdict": f"PASSED: Riesgo de Ruina = {ruin_prob_pct:.1f}% (DD 95% = {dd_95th:.1f}%)" if passed else f"FALLO: Riesgo Ruina {ruin_prob_pct:.1f}% > 1.0% (DD 95% = {dd_95th:.1f}%)",
            "evidence": {
                "simulations_count": num_sims,
                "ruin_probability_pct": round(ruin_prob_pct, 2),
                "drawdown_median_pct": round(dd_median, 1),
                "drawdown_95th_percentile_pct": round(dd_95th, 1),
                "max_simulated_drawdown_pct": round(float(np.max(max_dds)), 1),
            },
        }
