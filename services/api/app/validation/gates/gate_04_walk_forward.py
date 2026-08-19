"""services/api/app/validation/gates/gate_04_walk_forward.py
Gate 4: Eficiencia Walk-Forward (WFE >= 0.50) y Anti-Curve Fitting.
Compara la degradación de rendimiento entre el periodo In-Sample y Out-Of-Sample.
"""

from typing import Any, Dict, List
import numpy as np


class Gate04WalkForward:
    GATE_ID = 4
    NAME = "WALK_FORWARD"
    LABEL = "4. WALK-FORWARD (WFE)"

    def evaluate(self, is_trades: List[float], oos_trades: List[float]) -> Dict[str, Any]:
        if not is_trades or not oos_trades:
            return {
                "gate_id": self.GATE_ID,
                "name": self.NAME,
                "passed": False,
                "score": 0.0,
                "verdict": "RECHAZADO: Faltan trades IS u OOS para WFE",
                "evidence": {"is_trades": len(is_trades or []), "oos_trades": len(oos_trades or [])},
            }

        g_is = [t for t in is_trades if t > 0]
        l_is = [t for t in is_trades if t <= 0]
        pf_is = float(sum(g_is) / max(0.01, abs(sum(l_is)))) if l_is else 1.5

        g_oos = [t for t in oos_trades if t > 0]
        l_oos = [t for t in oos_trades if t <= 0]
        pf_oos = float(sum(g_oos) / max(0.01, abs(sum(l_oos)))) if l_oos else 1.5

        wfe = float(pf_oos / pf_is) if pf_is > 0 else 0.0
        passed = (wfe >= 0.50) and (pf_oos >= 1.10)
        score = min(100.0, max(0.0, wfe * 90.0))

        return {
            "gate_id": self.GATE_ID,
            "name": self.NAME,
            "passed": passed,
            "score": round(score, 1),
            "verdict": f"PASSED: WFE = {wfe:.2f} (PF IS: {pf_is:.2f} ➔ OOS: {pf_oos:.2f})" if passed else f"FALLO: Degradación excesiva WFE {wfe:.2f} < 0.50",
            "evidence": {
                "profit_factor_is": round(pf_is, 2),
                "profit_factor_oos": round(pf_oos, 2),
                "walk_forward_efficiency": round(wfe, 2),
                "min_wfe_required": 0.50,
            },
        }
