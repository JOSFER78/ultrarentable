"""services/api/app/validation/gates/gate_02_cost_backtest.py
Gate 2: Backtest con Fricción y Costes Reales Específicos por Mercado.
Soporta Cripto (0.05%), Índices CME ($2.50/ctto), Forex (spread + fee) y Commodities (COMEX/NYMEX).
"""

from typing import Any, Dict, List, Optional
from services.api.app.validation.market_specs import get_market_spec


class Gate02CostBacktest:
    GATE_ID = 2
    NAME = "BACKTEST_COSTES"
    LABEL = "2. BACKTEST COSTES"

    def evaluate(self, trades_raw: List[Dict[str, Any]], symbol: str = "BTCUSDT", fee_rate: Optional[float] = None, slippage_ticks: Optional[int] = None) -> Dict[str, Any]:
        if not trades_raw or len(trades_raw) < 10:
            return {
                "gate_id": self.GATE_ID,
                "name": self.NAME,
                "passed": False,
                "score": 0.0,
                "verdict": "RECHAZADO: Trades insuficientes para análisis de costes",
                "evidence": {"trades_count": len(trades_raw) if trades_raw else 0},
            }

        spec = get_market_spec(symbol)
        effective_fee_rate = fee_rate if fee_rate is not None else spec.fee_rate
        effective_slip_ticks = slippage_ticks if slippage_ticks is not None else spec.slippage_ticks

        total_gross_pnl = 0.0
        total_fees = 0.0
        total_slippage = 0.0
        net_trades = []

        for t in trades_raw:
            entry_px = float(t.get("entry_price", 100.0))
            exit_px = float(t.get("exit_price", 101.0))
            qty = float(t.get("qty", 1.0))
            side = str(t.get("side", "LONG")).upper()

            # Cálculo de PnL bruto ponderado por valor de punto
            diff = (exit_px - entry_px) if side == "LONG" else (entry_px - exit_px)
            gross = diff * qty * (spec.point_value if spec.category != "CRYPTO" else 1.0)
            
            # Fricción institucional específica
            if spec.fee_fixed_usd > 0:
                fee = spec.fee_fixed_usd * qty * 2.0  # ida y vuelta
            else:
                fee = (entry_px * qty + exit_px * qty) * effective_fee_rate

            slip = (effective_slip_ticks * spec.tick_size) * qty * (spec.point_value if spec.category != "CRYPTO" else 1.0) * 2.0
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
            "verdict": f"PASSED: PF Neto tras costes = {net_pf:.2f} ({spec.category})" if passed else f"FALLO: PF Neto {net_pf:.2f} < 1.10",
            "evidence": {
                "market_category": spec.category,
                "canonical_name": spec.canonical_name,
                "exchange": spec.exchange,
                "gross_pnl_usd": round(total_gross_pnl, 2),
                "total_fees_usd": round(total_fees, 2),
                "total_slippage_usd": round(total_slippage, 2),
                "net_pnl_usd": round(net_pnl, 2),
                "net_profit_factor": round(net_pf, 2),
                "drag_cost_pct": round(((total_fees + total_slippage) / max(1.0, abs(total_gross_pnl))) * 100.0, 2),
            },
        }

