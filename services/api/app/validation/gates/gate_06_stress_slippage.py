"""services/api/app/validation/gates/gate_06_stress_slippage.py
Gate 6: Prueba de Estrés de Fricción, Deslizamiento (Slippage) y Shocks de Liquidez.
Modela el impacto de comisiones elevadas, ensanchamiento de spreads y shocks adversos
en 4 escenarios cuantitativos: Base, +1-Sigma, +2-Sigma y +3-Sigma.
"""

from __future__ import annotations

from typing import Any, Dict, List
import numpy as np


class Gate06StressSlippage:
    GATE_ID = 6
    NAME = "STRESS_SLIPPAGE"
    LABEL = "6. STRESS SLIPPAGE & LIQUIDITY SHOCKS"

    def evaluate(
        self,
        oos_trades: List[float],
        base_friction_usd: float | None = None,
        is_ultra: bool = True,
    ) -> Dict[str, Any]:
        if base_friction_usd is None:
            base_friction_usd = 0.35 if is_ultra else 3.0
        if not oos_trades or len(oos_trades) < 5:
            return {
                "gate_id": self.GATE_ID,
                "name": self.NAME,
                "passed": False,
                "score": 0.0,
                "verdict": "RECHAZADO: Trades insuficientes para prueba de estrés de fricción",
                "evidence": {"stressed_scenarios": []},
            }

        trades_arr = np.array(oos_trades, dtype=np.float64)
        max_val = float(np.max(np.abs(trades_arr))) if len(trades_arr) > 0 else 0.0

        # Auto-calibración dimensional de la penalización base
        if max_val <= 1.0:
            # Retornos fraccionales puros (ej. 0.075 = +7.5%)
            base_penalty = 0.0035 if is_ultra else 0.0006
            unit_label = "fractional"
        elif max_val <= 100.0:
            # Retornos porcentuales directos (ej. 7.5 = +7.5%)
            base_penalty = 0.35 if is_ultra else 0.06
            unit_label = "percentage"
        else:
            # Dólares nominales brutos
            base_penalty = 0.35 if is_ultra else 3.0
            unit_label = "nominal_usd"

        std_trade_pnl = float(np.std(trades_arr)) if len(trades_arr) > 1 else (0.01 if max_val <= 1.0 else 1.0)

        # Modelado de 4 Escenarios de Estrés Progresivo
        scenarios = {
            "Base": base_penalty,
            "+1_Sigma": base_penalty * 2.0 + (std_trade_pnl * 0.02),
            "+2_Sigma": base_penalty * 3.5 + (std_trade_pnl * 0.05),
            "+3_Sigma": base_penalty * 5.0 + (std_trade_pnl * 0.10),
        }

        scenario_results = {}
        passed_scenarios_count = 0

        for sc_name, penalty in scenarios.items():
            stressed_trades = trades_arr - penalty
            wins = stressed_trades[stressed_trades > 0]
            losses = stressed_trades[stressed_trades <= 0]
            
            pf = float(np.sum(wins) / max(0.01, abs(np.sum(losses)))) if len(losses) > 0 else (2.0 if len(wins) > 0 else 0.0)
            net_pnl = float(np.sum(stressed_trades))
            survival = (net_pnl > 0) and (pf >= (1.05 if is_ultra else 1.15))

            if survival:
                passed_scenarios_count += 1

            scenario_results[sc_name] = {
                "friction_penalty_per_trade_usd": round(penalty, 2),
                "stressed_net_pnl_usd": round(net_pnl, 2),
                "stressed_profit_factor": round(pf, 2),
                "survived": survival,
            }

        # Criterio: Debe sobrevivir al menos hasta el escenario +1_Sigma (Fondeo requiere hasta +2_Sigma)
        min_required_scenarios = 2 if is_ultra else 3
        passed = (passed_scenarios_count >= min_required_scenarios)
        
        score = min(100.0, (passed_scenarios_count / 4.0) * 100.0) if passed else max(0.0, (passed_scenarios_count / 4.0) * 60.0)

        verdict_msg = (
            f"PASSED: Resistencia a fricción verificada ({passed_scenarios_count}/4 escenarios aprobados, PF +1σ: {scenario_results['+1_Sigma']['stressed_profit_factor']:.2f})"
            if passed
            else f"FALLO: Estrategia vulnerable a deslizamiento y spread ({passed_scenarios_count}/4 escenarios superados)"
        )

        return {
            "gate_id": self.GATE_ID,
            "name": self.NAME,
            "passed": passed,
            "score": round(score, 1),
            "verdict": verdict_msg,
            "evidence": {
                "scenarios": scenario_results,
                "passed_scenarios_count": passed_scenarios_count,
                "min_required_scenarios": min_required_scenarios,
                "base_friction_usd": base_friction_usd,
            },
        }
