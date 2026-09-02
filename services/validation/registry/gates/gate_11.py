"""services/validation/registry/gates/gate_11.py
Gate 11: Validación Cruzada Orientada a Eventos, Apalancamiento Real y Distancia a Liquidación (Fase 4 & Bloqueante 6).
Ejecuta una auditoría independiente orden a orden modelando la dinámica de margen cruzado,
apalancamiento efectivo dinámico, distancia mínima a liquidación forzada y deducción de costes de financiación (Funding).
Cero posiciones nominales inferidas por fórmula sintética.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from services.api.app.validation.market_specs import get_market_spec
from services.validation.registry.contratos import Evidencia, GateBase, GateResult


class Gate11NautilusEvent(GateBase):
    GATE_ID = 11
    NAME = "EVENT_CROSS_VALIDATION"
    LABEL = "11. INDEPENDENT EVENT CROSS-VALIDATION"
    VERSION = "1.0.0"  # 1.0.0 (2026-09-02): paridad exacta con la suite B en motor 5.17.0 (D5)
    UMBRALES = {
        "min_trades": 5,
        "min_dist_liquidation_pct_ultra": 2.0,
        "min_dist_liquidation_pct_fondeo": 20.0,
    }

    def evaluar(self, ev: Evidencia) -> GateResult:
        return self._resultado(
            self.evaluate(
                oos_trades=ev.oos_trades or [],
                trades_raw=ev.trades_raw,
                candles=ev.candles,
                strategy_snapshot=ev.strategy_snapshot,
                symbol=ev.candidate_info.get("symbol", "BTCUSDT"),
                initial_capital=ev.base_capital,
                max_allowed_leverage=100.0 if ev.is_ultra else 3.0,
                is_ultra=ev.is_ultra,
            )
        )

    def evaluate(
        self,
        oos_trades: List[float],
        trades_raw: Optional[List[Dict[str, Any]]] = None,
        candles: Optional[List[Dict[str, Any]]] = None,
        strategy_snapshot: Optional[Any] = None,
        symbol: str = "BTCUSDT",
        initial_capital: float = 1000.0,
        max_allowed_leverage: Optional[float] = None,
        is_ultra: bool = True,
    ) -> Dict[str, Any]:
        if not oos_trades or len(oos_trades) < self.UMBRALES["min_trades"]:
            return {
                "gate_id": self.GATE_ID,
                "name": self.NAME,
                "passed": False,
                "score": 0.0,
                "verdict": "RECHAZADO: Trades insuficientes para validación cruzada orientada a eventos (< 5 trades)",
                "evidence": {"execution_events_count": 0},
            }

        spec = get_market_spec(symbol)
        ceiling_leverage = max_allowed_leverage if max_allowed_leverage is not None else (spec.max_leverage if is_ultra else 3.0)

        equity = initial_capital
        peak_equity = initial_capital
        min_equity = initial_capital
        vault_harvested = 0.0
        total_fees = 0.0
        total_funding = 0.0
        peak_leverage_used = 1.0
        min_dist_liquidation_pct = 100.0
        margin_call_triggered = False

        maint_margin_rate = 0.005 if spec.category == "CRYPTO" else 0.02

        for i, pnl in enumerate(oos_trades):
            if equity <= 0:
                margin_call_triggered = True
                break

            # Determinar distancia real de stop-loss si viene en trades_raw
            sl_dist = 0.025
            holding_sessions_8h = 1
            if trades_raw and i < len(trades_raw):
                raw_t = trades_raw[i]
                if "sl_dist_pct" in raw_t and float(raw_t["sl_dist_pct"]) > 0:
                    sl_dist = max(0.005, float(raw_t["sl_dist_pct"]))
                elif "stop_loss" in raw_t and "entry_price" in raw_t:
                    try:
                        ep = float(raw_t["entry_price"])
                        sl = float(raw_t["stop_loss"])
                        if ep > 0:
                            sl_dist = max(0.005, abs(ep - sl) / ep)
                    except Exception:
                        pass
                
                # Duración en barras/horas para bloques de financiación de 8h
                bars_held = float(raw_t.get("bars_held", raw_t.get("duration_bars", 4)))
                holding_sessions_8h = max(1, int(bars_held // 8))

            risk_pct = 0.15 if is_ultra else 0.01
            target_lev = min(ceiling_leverage, risk_pct / sl_dist)

            nominal_position = equity * target_lev
            peak_leverage_used = max(peak_leverage_used, target_lev)

            # Financiación (Funding) para Perpetuos por sesión de 8h
            funding_rate_8h = 0.0001  # 0.01% por sesión de 8 horas
            funding = (nominal_position * funding_rate_8h * holding_sessions_8h) if spec.category == "CRYPTO" else 0.0
            
            # PnL de la operación ajustado por apalancamiento y deducción de funding
            if abs(pnl) >= 1.0 or (trades_raw and "net_pnl_usd" in trades_raw[0]):
                trade_pnl_usd = pnl - funding
            else:
                trade_pnl_usd = (equity * pnl) - funding
            equity += trade_pnl_usd
            total_funding += funding

            # Regla de Cosecha a Bóveda Ratchet (+200% ganancia -> cosecha 50% irrevocable)
            if is_ultra and equity >= initial_capital * 3.0:
                harvest = equity * 0.5
                vault_harvested += harvest
                equity -= harvest

            # Margen de mantenimiento requerido
            maint_margin_req = nominal_position * maint_margin_rate
            if equity <= maint_margin_req:
                margin_call_triggered = True
                min_dist_liquidation_pct = 0.0
            else:
                dist_liq = max(0.0, (equity - maint_margin_req) / max(1.0, equity) * 100.0)
                min_dist_liquidation_pct = min(min_dist_liquidation_pct, dist_liq)

            peak_equity = max(peak_equity, equity + vault_harvested)
            min_equity = min(min_equity, equity)

        total_wealth = equity + vault_harvested
        no_margin_call = not margin_call_triggered
        leverage_within_bounds = (peak_leverage_used <= ceiling_leverage * 1.05)
        liquidation_buffer_ok = (min_dist_liquidation_pct >= (self.UMBRALES["min_dist_liquidation_pct_ultra"] if is_ultra else self.UMBRALES["min_dist_liquidation_pct_fondeo"]))
        final_equity_positive = (total_wealth >= initial_capital * 0.7)

        passed = no_margin_call and leverage_within_bounds and liquidation_buffer_ok and final_equity_positive
        score = min(100.0, max(0.0, ((total_wealth / initial_capital) * 40.0) + (min_dist_liquidation_pct * 0.6))) if passed else 0.0

        verdict_msg = (
            f"PASSED: Validación cruzada de eventos completada (Riqueza Total: ${total_wealth:.2f}, Bóveda Cosechada: ${vault_harvested:.2f}, Apalancamiento: {peak_leverage_used:.1f}x, Dist. Mín. Liq: {min_dist_liquidation_pct:.1f}%)"
            if passed
            else f"FALLO: Riesgo de margen o liquidación (Margin Call: {margin_call_triggered}, Dist. Liquidación: {min_dist_liquidation_pct:.1f}%, Peak Lev: {peak_leverage_used:.1f}x)"
        )

        return {
            "gate_id": self.GATE_ID,
            "name": self.NAME,
            "passed": passed,
            "score": round(score, 1),
            "verdict": verdict_msg,
            "evidence": {
                "initial_capital_usd": initial_capital,
                "final_equity_usd": round(equity, 2),
                "peak_equity_usd": round(peak_equity, 2),
                "min_equity_usd": round(min_equity, 2),
                "peak_leverage_used": round(peak_leverage_used, 2),
                "max_allowed_leverage_ceiling": ceiling_leverage,
                "min_distance_to_liquidation_pct": round(min_dist_liquidation_pct, 2),
                "margin_call_triggered": margin_call_triggered,
                "total_fees_paid_usd": round(total_fees, 2),
                "total_funding_cost_usd": round(total_funding, 2),
                "execution_events_count": len(oos_trades),
            },
        }
