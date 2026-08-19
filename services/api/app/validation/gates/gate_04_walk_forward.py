"""services/api/app/validation/gates/gate_04_walk_forward.py
Gate 4: Eficiencia Walk-Forward Auténtica (Rolling WFO) y Anti-Degradación Temporal.
Evalúa la estrategia a través de múltiples ventanas rodantes temporales sucesivas (Rolling WFO).
Calcula la Walk-Forward Efficiency (WFE) agregada y la consistencia entre ventanas OOS.
"""

from __future__ import annotations

from typing import Any, Dict, List
import numpy as np


class Gate04WalkForward:
    GATE_ID = 4
    NAME = "WALK_FORWARD"
    LABEL = "4. WALK-FORWARD (ROLLING WFO)"

    def evaluate(
        self,
        trades_pnl: List[float],
        num_windows: int = 5,
        is_ratio: float = 0.70,
    ) -> Dict[str, Any]:
        if not trades_pnl or len(trades_pnl) < 20:
            return {
                "gate_id": self.GATE_ID,
                "name": self.NAME,
                "passed": False,
                "score": 0.0,
                "verdict": "RECHAZADO: Trades insuficientes para Rolling Walk-Forward (< 20 trades)",
                "evidence": {
                    "total_trades": len(trades_pnl) if trades_pnl else 0,
                    "windows_evaluated": 0,
                    "walk_forward_efficiency": 0.0,
                },
            }

        total_trades = len(trades_pnl)
        window_size = total_trades // num_windows
        if window_size < 4:
            num_windows = max(2, total_trades // 6)
            window_size = total_trades // num_windows

        windows_data = []
        wfe_list = []
        profitable_oos_count = 0

        for w in range(num_windows):
            start_idx = w * (window_size // 2) if num_windows > 2 else 0
            end_idx = min(total_trades, start_idx + window_size)
            sub_trades = trades_pnl[start_idx:end_idx]

            if len(sub_trades) < 4:
                continue

            split = int(len(sub_trades) * is_ratio)
            is_sub = sub_trades[:split]
            oos_sub = sub_trades[split:]

            if not is_sub or not oos_sub:
                continue

            # Profit Factor IS
            g_is = [t for t in is_sub if t > 0]
            l_is = [t for t in is_sub if t <= 0]
            pf_is = float(sum(g_is) / max(0.01, abs(sum(l_is)))) if l_is else (2.0 if g_is else 0.0)

            # Profit Factor OOS
            g_oos = [t for t in oos_sub if t > 0]
            l_oos = [t for t in oos_sub if t <= 0]
            pf_oos = float(sum(g_oos) / max(0.01, abs(sum(l_oos)))) if l_oos else (2.0 if g_oos else 0.0)
            net_oos = float(sum(oos_sub))

            window_wfe = float(pf_oos / max(0.1, pf_is))
            wfe_list.append(window_wfe)

            if net_oos > 0:
                profitable_oos_count += 1

            windows_data.append({
                "window_index": w + 1,
                "is_trades_count": len(is_sub),
                "oos_trades_count": len(oos_sub),
                "pf_is": round(pf_is, 2),
                "pf_oos": round(pf_oos, 2),
                "net_profit_oos_usd": round(net_oos, 2),
                "wfe": round(window_wfe, 2),
            })

        if not wfe_list:
            return {
                "gate_id": self.GATE_ID,
                "name": self.NAME,
                "passed": False,
                "score": 0.0,
                "verdict": "RECHAZADO: No fue posible calcular ventanas WFO válidas",
                "evidence": {"total_trades": total_trades},
            }

        avg_wfe = float(np.mean(wfe_list))
        consistency_pct = (profitable_oos_count / len(wfe_list)) * 100.0

        # Criterios rigurosos de aprobación WFO:
        # 1. WFE media >= 0.50 (menos de 50% de degradación respecto al In-Sample)
        # 2. Al menos el 50% de las ventanas OOS deben ser rentables
        passed = (avg_wfe >= 0.50) and (consistency_pct >= 50.0)
        score = min(100.0, max(0.0, (avg_wfe * 60.0) + (consistency_pct * 0.40))) if passed else max(0.0, avg_wfe * 50.0)

        verdict_msg = (
            f"PASSED: Rolling WFO verificado ({len(windows_data)} ventanas, WFE media: {avg_wfe:.2f}, Consistencia: {consistency_pct:.1f}%)"
            if passed
            else f"FALLO: Degradación temporal excesiva (WFE {avg_wfe:.2f} < 0.50 ó Consistencia {consistency_pct:.1f}% < 50%)"
        )

        return {
            "gate_id": self.GATE_ID,
            "name": self.NAME,
            "passed": passed,
            "score": round(score, 1),
            "verdict": verdict_msg,
            "evidence": {
                "total_trades_analyzed": total_trades,
                "windows_count": len(windows_data),
                "walk_forward_efficiency": round(avg_wfe, 2),
                "oos_consistency_pct": round(consistency_pct, 1),
                "min_wfe_required": 0.50,
                "windows_details": windows_data,
            },
        }
