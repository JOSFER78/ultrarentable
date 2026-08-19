"""services/api/app/validation/gates/gate_05_monte_carlo.py
Gate 5: Prueba de Estrés Monte Carlo (1.000 iteraciones con remuestreo / barajado).
Calcula la probabilidad matemática de ruina (Ruin <= 1%) y el peor Drawdown con intervalo de confianza 95%.
"""

from typing import Any, Dict, List
import numpy as np


class Gate05MonteCarlo:
    GATE_ID = 5
    NAME = "MONTE_CARLO"
    LABEL = "5. MONTE CARLO"

    def evaluate(self, oos_trades: List[float], initial_capital: float = 10000.0, num_sims: int = 1000, ruin_drawdown_pct: float = 40.0) -> Dict[str, Any]:
        if not oos_trades or len(oos_trades) < 10:
            return {
                "gate_id": self.GATE_ID,
                "name": self.NAME,
                "passed": False,
                "score": 0.0,
                "verdict": "RECHAZADO: Trades insuficientes para simulación Monte Carlo",
                "evidence": {"simulations_run": 0},
            }

        trades_arr = np.array(oos_trades, dtype=np.float64)
        n_trades = len(trades_arr)
        max_dds = []
        ruin_count = 0

        rng = np.random.default_rng(42)

        for _ in range(num_sims):
            # Resample with replacement (Bootstrap)
            sim_trades = rng.choice(trades_arr, size=n_trades, replace=True)
            equity_curve = initial_capital + np.cumsum(np.insert(sim_trades, 0, 0.0))
            peak = np.maximum.accumulate(equity_curve)
            dd_series = (peak - equity_curve) / peak * 100.0
            max_sim_dd = float(np.max(dd_series))
            max_dds.append(max_sim_dd)

            if max_sim_dd >= ruin_drawdown_pct:
                ruin_count += 1

        ruin_prob_pct = (ruin_count / num_sims) * 100.0
        dd_95th = float(np.percentile(max_dds, 95))
        dd_median = float(np.median(max_dds))

        passed = (ruin_prob_pct <= 1.0) and (dd_95th <= 50.0)
        score = max(0.0, 100.0 - (ruin_prob_pct * 10) - (dd_95th * 0.5))

        return {
            "gate_id": self.GATE_ID,
            "name": self.NAME,
            "passed": passed,
            "score": round(score, 1),
            "verdict": f"PASSED: Riesgo de Ruina = {ruin_prob_pct:.1f}% (DD 95% = {dd_95th:.1f}%)" if passed else f"FALLO: Riesgo Ruina {ruin_prob_pct:.1f}% > 1.0%",
            "evidence": {
                "simulations_count": num_sims,
                "ruin_probability_pct": round(ruin_prob_pct, 2),
                "drawdown_median_pct": round(dd_median, 1),
                "drawdown_95th_percentile_pct": round(dd_95th, 1),
                "max_simulated_drawdown_pct": round(float(np.max(max_dds)), 1),
            },
        }
