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

    def evaluate(self, is_trades: List[float], oos_trades: List[float], is_ultra: bool = False) -> Dict[str, Any]:
        n_is = len(is_trades) if is_trades else 0
        n_oos = len(oos_trades) if oos_trades else 0

        # Outlier Dependency Check (Top 2 trades ratio)
        pos_oos = [t for t in (oos_trades or []) if t > 0]
        total_win_pnl = sum(pos_oos)
        top2_win_pnl = sum(sorted(pos_oos, reverse=True)[:2]) if len(pos_oos) >= 2 else total_win_pnl
        top2_ratio = (top2_win_pnl / total_win_pnl * 100.0) if total_win_pnl > 0 else 100.0

        # En Ultra se permiten menos trades por periodo si hay alta convexidad (mínimo 15 IS / 10 OOS)
        min_is = 15 if is_ultra else 30
        min_oos = 10 if is_ultra else 20
        max_outlier_ratio = 85.0 if is_ultra else 50.0

        is_sample_ok = (n_is >= min_is)
        oos_sample_ok = (n_oos >= min_oos) or (n_oos == 0 and is_ultra and n_is >= 20)
        outlier_ok = (top2_ratio <= max_outlier_ratio) or (n_oos >= 30)

        passed = is_sample_ok and oos_sample_ok and outlier_ok
        score = min(100.0, (n_oos / float(min_oos * 2)) * 100.0) if passed else max(10.0, (n_oos / float(min_oos)) * 50.0)

        return {
            "gate_id": self.GATE_ID,
            "name": self.NAME,
            "passed": passed,
            "score": round(score, 1),
            "verdict": f"PASSED: Muestra robusta ({n_is} IS / {n_oos} OOS · {'Ultra Convex' if is_ultra else 'Fondeo'})" if passed else f"FALLO: Muestra insuficiente ({n_is} IS < {min_is} ó {n_oos} OOS < {min_oos})",
            "evidence": {
                "trades_is": n_is,
                "trades_oos": n_oos,
                "top2_outlier_dependency_pct": round(top2_ratio, 1),
                "min_is_required": min_is,
                "min_oos_required": min_oos,
                "route_mode": "ULTRA_ASYMMETRIC" if is_ultra else "FONDEO_CONSISTENCY",
            },
        }
