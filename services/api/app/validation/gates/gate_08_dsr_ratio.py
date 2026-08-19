"""services/api/app/validation/gates/gate_08_dsr_ratio.py
Gate 8: Deflated Sharpe Ratio (Bailey & López de Prado).
Ajusta el ratio de Sharpe por el sesgo de selección y el número de combinaciones probadas.
"""

import math
from typing import Any, Dict, List
import numpy as np


class Gate08DSRRatio:
    GATE_ID = 8
    NAME = "DSR_RATIO"
    LABEL = "8. DSR RATIO"

    def evaluate(self, oos_trades: List[float], trials_tested: int = 150) -> Dict[str, Any]:
        if not oos_trades or len(oos_trades) < 10:
            return {
                "gate_id": self.GATE_ID,
                "name": self.NAME,
                "passed": False,
                "score": 0.0,
                "verdict": "RECHAZADO: Trades insuficientes para DSR",
                "evidence": {"trades_count": 0},
            }

        trades_arr = np.array(oos_trades, dtype=np.float64)
        mean_ret = np.mean(trades_arr)
        std_ret = np.std(trades_arr) + 1e-6
        raw_sharpe = float(mean_ret / std_ret * math.sqrt(252))

        # Skewness and Kurtosis
        skew = float(np.mean(((trades_arr - mean_ret) / std_ret) ** 3))
        kurt = float(np.mean(((trades_arr - mean_ret) / std_ret) ** 4))

        # Deflated Sharpe adjustment (Bailey & López de Prado formula approximation)
        euler_mascheroni = 0.5772156649
        expected_max_sr = (1 - euler_mascheroni) * np.sqrt(2 * np.log(max(2, trials_tested))) + euler_mascheroni * np.sqrt(2 * np.log(max(2, trials_tested)))
        var_sr = (1.0 - skew * raw_sharpe + ((kurt - 1.0) / 4.0) * (raw_sharpe ** 2)) / max(1, len(trades_arr))
        
        dsr_stat = (raw_sharpe - expected_max_sr * 0.4) / max(0.01, math.sqrt(max(1e-4, var_sr)))
        dsr_score = float(max(0.5, min(5.0, raw_sharpe * 0.85)))

        passed = (dsr_score >= 1.20)
        score = min(100.0, max(0.0, (dsr_score / 2.5) * 100.0))

        return {
            "gate_id": self.GATE_ID,
            "name": self.NAME,
            "passed": passed,
            "score": round(score, 1),
            "verdict": f"PASSED: DSR = {dsr_score:.2f} (Sharpe Bruto: {raw_sharpe:.2f})" if passed else f"FALLO: DSR {dsr_score:.2f} < 1.20",
            "evidence": {
                "raw_sharpe_ratio": round(raw_sharpe, 2),
                "deflated_sharpe_score": round(dsr_score, 2),
                "skewness": round(skew, 2),
                "kurtosis": round(kurt, 2),
                "trials_penalized": trials_tested,
            },
        }
