"""services/api/app/validation/gates/gate_02_cost_backtest.py
Gate 2: Backtest con Fricción y Costes Reales (Comisiones 0.05% + Slippage 3 ticks).
Verifica que la estrategia mantenga Profit Factor positivo después de costes institucionales.
"""

from typing import Any, Dict, List
import numpy as np


class Gate02CostBacktest:
    GATE_ID = 2
    NAME = "BACKTEST_COSTES"
    LABEL = "2. BACKTEST COSTES"

    def evaluate(self, trades_raw: List[Dict[str, Any]], fee_rate: float = 0.0005, slippage_ticks: int = 3, tick_size: float = 0.1) -> Dict[str, Any]:
        if not trades_raw or len(trades_raw) < 10:
            return {
                "gate_id": self.GATE_ID,
                "name": self.NAME,
                "passed": False,
                "score": 0.0,
                "verdict": "RECHAZADO: Trades insuficientes para análisis de costes",
                "evidence": {"trades_count": len(trades_raw) if trades_raw else 0},
            }

        total_gross_pnl = 0.0
        total_fees = 0.0
        total_slippage = 0.0
        net_trades = []

        for t in trades_raw:
            entry_px = float(t.get("entry_price", 100.0))
            exit_px = float(t.get("exit_price", 101.0))
            qty = float(t.get("qty", 1.0))
            side = str(t.get("side", "LONG")).upper()

            gross = (exit_px - entry_px) * qty if side == "LONG" else (entry_px - exit_px) * qty
            fee = (entry_px * qty + exit_px * qty) * fee_rate
            slip = (slippage_ticks * tick_size) * qty * 2.0  # entry & exit
            net = gross - fee - slip

            total_gross_pnl += gross
            total_fees += fee
            total_slippage += slip
            net_trades.append(net)

        gains = [x for x in net_trades if x > 0]
        losses = [x for x in net_trades if x <= 0]
        net_pf = float(sum(gains) / max(0.01, abs(sum(losses)))) if losses else 2.5
        net_pnl = float(sum(net_trades))

        passed = (net_pf >= 1.10) and (net_pnl > 0)
        score = min(100.0, max(0.0, (net_pf - 1.0) * 100.0))

        return {
            "gate_id": self.GATE_ID,
            "name": self.NAME,
            "passed": passed,
            "score": round(score, 1),
            "verdict": f"PASSED: PF Neto tras costes = {net_pf:.2f}" if passed else f"FALLO: PF Neto {net_pf:.2f} < 1.10",
            "evidence": {
                "gross_pnl_usd": round(total_gross_pnl, 2),
                "total_fees_usd": round(total_fees, 2),
                "total_slippage_usd": round(total_slippage, 2),
                "net_pnl_usd": round(net_pnl, 2),
                "net_profit_factor": round(net_pf, 2),
                "drag_cost_pct": round(((total_fees + total_slippage) / max(1.0, abs(total_gross_pnl))) * 100.0, 2),
            },
        }
