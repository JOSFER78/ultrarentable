"""services/api/app/validation/gates/gate_06_stress_slippage.py
Gate 6: Prueba de Estrés de Fricción Adversa (+5 bps + 2x Slippage).
Comprueba la supervivencia del sistema ante picos de volatilidad y falta de liquidez en el libro.
"""

from typing import Any, Dict, List
import numpy as np


class Gate06StressSlippage:
    GATE_ID = 6
    NAME = "STRESS_SLIPPAGE"
    LABEL = "6. STRESS SLIPPAGE"

    def evaluate(self, oos_trades: List[float], extra_friction_usd: float = 15.0) -> Dict[str, Any]:
        if not oos_trades or len(oos_trades) < 10:
            return {
                "gate_id": self.GATE_ID,
                "name": self.NAME,
                "passed": False,
                "score": 0.0,
                "verdict": "RECHAZADO: Trades insuficientes para Stress Test",
                "evidence": {"trades_count": 0},
            }

        stressed_trades = [t - extra_friction_usd for t in oos_trades]
        gains = [x for x in stressed_trades if x > 0]
        losses = [x for x in stressed_trades if x <= 0]

        stressed_pf = float(sum(gains) / max(0.01, abs(sum(losses)))) if losses else 2.0
        stressed_net = float(sum(stressed_trades))

        passed = (stressed_pf >= 1.10) and (stressed_net > 0)
        score = min(100.0, max(0.0, (stressed_pf - 1.0) * 100.0))

        return {
            "gate_id": self.GATE_ID,
            "name": self.NAME,
            "passed": passed,
            "score": round(score, 1),
            "verdict": f"PASSED: PF Estresado = {stressed_pf:.2f} (> 1.10)" if passed else f"FALLO: PF Estresado {stressed_pf:.2f} < 1.10",
            "evidence": {
                "stressed_profit_factor": round(stressed_pf, 2),
                "stressed_net_pnl_usd": round(stressed_net, 2),
                "friction_penalty_applied_usd": round(extra_friction_usd * len(oos_trades), 2),
                "survival_verdict": "RESISTENTE_A_DESLIZAMIENTO" if passed else "VULNERABLE_A_DESLIZAMIENTO",
            },
        }
