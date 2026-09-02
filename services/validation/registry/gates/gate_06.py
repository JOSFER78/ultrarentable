"""services/validation/registry/gates/gate_06.py
Gate 6: Prueba de Estrés de Fricción, Deslizamiento (Slippage) y Shocks de Liquidez.
Modela el impacto de comisiones elevadas, ensanchamiento de spreads y shocks adversos
en 4 escenarios cuantitativos: Base, +1-Sigma, +2-Sigma y +3-Sigma.
"""

from __future__ import annotations

from typing import Any, Dict, List
import numpy as np

from services.validation.registry.contratos import Evidencia, GateBase, GateResult


class Gate06StressSlippage(GateBase):
    GATE_ID = 6
    NAME = "STRESS_SLIPPAGE"
    LABEL = "6. STRESS SLIPPAGE & LIQUIDITY SHOCKS"
    VERSION = "1.0.0"  # 1.0.0 (2026-09-02): paridad exacta con la suite B en motor 5.17.0 (D5)
    UMBRALES = {
        "min_trades": 5,
        "min_survival_pf_ultra": 1.00,
        "min_survival_pf_fondeo": 1.05,
        "min_required_scenarios_ultra": 1,
        "min_required_scenarios_fondeo": 2,
    }

    def evaluar(self, ev: Evidencia) -> GateResult:
        return self._resultado(
            self.evaluate(
                ev.oos_trades or [],
                is_ultra=ev.is_ultra,
            )
        )

    def evaluate(
        self,
        oos_trades: List[float],
        base_friction_usd: float | None = None,
        is_ultra: bool = True,
    ) -> Dict[str, Any]:
        if base_friction_usd is None:
            base_friction_usd = 0.35 if is_ultra else 3.0
        if not oos_trades or len(oos_trades) < self.UMBRALES["min_trades"]:
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

        # Retornos fraccionales normalizados (ej. 0.025 = +2.5%, 2.21 = +221.0%)
        # Penalización base por estrés de deslizamiento (3x slippage real del broker)
        base_penalty = 0.0005 if is_ultra else 0.0001

        std_trade_pnl = float(np.std(trades_arr)) if len(trades_arr) > 1 else 0.01

        # Modelado de 4 Escenarios de Estrés Progresivo
        scenarios = {
            "Base": base_penalty,
            "+1_Sigma": base_penalty * 2.0 + (std_trade_pnl * 0.005),
            "+2_Sigma": base_penalty * 3.5 + (std_trade_pnl * 0.010),
            "+3_Sigma": base_penalty * 5.0 + (std_trade_pnl * 0.020),
        }

        scenario_results = {}
        passed_scenarios_count = 0

        for sc_name, penalty in scenarios.items():
            stressed_trades = trades_arr - penalty
            wins = stressed_trades[stressed_trades > 0]
            losses = stressed_trades[stressed_trades <= 0]
            
            pf = float(np.sum(wins) / max(0.01, abs(np.sum(losses)))) if len(losses) > 0 else (2.0 if len(wins) > 0 else 0.0)
            net_pnl = float(np.sum(stressed_trades))
            survival = (net_pnl > 0) and (pf >= (self.UMBRALES["min_survival_pf_ultra"] if is_ultra else self.UMBRALES["min_survival_pf_fondeo"]))

            if survival:
                passed_scenarios_count += 1

            scenario_results[sc_name] = {
                "friction_penalty_per_trade_usd": round(penalty, 2),
                "stressed_net_pnl_usd": round(net_pnl, 2),
                "stressed_profit_factor": round(pf, 2),
                "survived": survival,
            }

        # Criterio cuantitativo graduado (100% Real):
        # Sobrevivir al menos al escenario Base (+1σ en Fondeo)
        min_required_scenarios = self.UMBRALES["min_required_scenarios_ultra"] if is_ultra else self.UMBRALES["min_required_scenarios_fondeo"]
        passed = (passed_scenarios_count >= min_required_scenarios)

        score = min(100.0, (passed_scenarios_count / 4.0) * 100.0) if passed else max(0.0, (passed_scenarios_count / 4.0) * 60.0)

        if passed and passed_scenarios_count >= 3:
            verdict_msg = f"PASSED (ALTA ROBUSTEZ): Resistencia a fricción verificada ({passed_scenarios_count}/4 escenarios aprobados)"
        elif passed:
            verdict_msg = f"PASSED (MODERADO): Resiste fricción base con observación ({passed_scenarios_count}/4 escenarios superados)"
        else:
            verdict_msg = f"FALLO: Vulnerabilidad a deslizamiento extremo ({passed_scenarios_count}/4 escenarios superados)"

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
