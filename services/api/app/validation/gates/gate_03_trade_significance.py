"""services/api/app/validation/gates/gate_03_trade_significance.py
Gate 3: Significancia Estadística de Muestra (N_OOS >= 20, N_IS >= 30).
Garantiza que los resultados no dependan de 3 o 4 operaciones de suerte.
"""

from typing import Any, Dict, List
import numpy as np


class Gate03TradeSignificance:
    GATE_ID = 3
    NAME = "TRADE_SIGNIFICANCE"
    LABEL = "3. TRADE SIGNIFICANCE"

    def evaluate(self, is_trades: List[float], oos_trades: List[float]) -> Dict[str, Any]:
        n_is = len(is_trades) if is_trades else 0
        n_oos = len(oos_trades) if oos_trades else 0

        # Outlier Dependency Check (Top 2 trades ratio)
        pos_oos = [t for t in (oos_trades or []) if t > 0]
        total_win_pnl = sum(pos_oos)
        top2_win_pnl = sum(sorted(pos_oos, reverse=True)[:2]) if len(pos_oos) >= 2 else total_win_pnl
        top2_ratio = (top2_win_pnl / total_win_pnl * 100.0) if total_win_pnl > 0 else 100.0

        is_sample_ok = (n_is >= 30)
        oos_sample_ok = (n_oos >= 20)
        outlier_ok = (top2_ratio <= 50.0) or (n_oos >= 50)  # Si hay 50+ trades, top 2 es menos crítico

        passed = is_sample_ok and oos_sample_ok and outlier_ok
        score = min(100.0, (n_oos / 40.0) * 100.0) if passed else max(10.0, (n_oos / 20.0) * 50.0)

        return {
            "gate_id": self.GATE_ID,
            "name": self.NAME,
            "passed": passed,
            "score": round(score, 1),
            "verdict": f"PASSED: Muestra robusta ({n_is} IS / {n_oos} OOS)" if passed else f"FALLO: Muestra insuficiente ({n_is} IS < 30 ó {n_oos} OOS < 20)",
            "evidence": {
                "trades_is": n_is,
                "trades_oos": n_oos,
                "top2_outlier_dependency_pct": round(top2_ratio, 1),
                "min_is_required": 30,
                "min_oos_required": 20,
            },
        }
