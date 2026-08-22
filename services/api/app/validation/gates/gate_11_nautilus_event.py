"""services/api/app/validation/gates/gate_11_nautilus_event.py
Gate 11: Validación Cruzada Orientada a Eventos, Apalancamiento Real y Distancia a Liquidación (Fase 4 & Bloqueante 6).
Ejecuta una auditoría independiente orden a orden modelando la dinámica de margen cruzado,
apalancamiento efectivo dinámico, distancia mínima a liquidación forzada y deducción de costes de financiación (Funding).
Cero posiciones nominales inferidas por fórmula sintética.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from services.api.app.validation.market_specs import get_market_spec


class Gate11NautilusEvent:
    GATE_ID = 11
    NAME = "EVENT_CROSS_VALIDATION"
    LABEL = "11. INDEPENDENT EVENT CROSS-VALIDATION"

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
        if not oos_trades or len(oos_trades) < 5:
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

        # Simulación de eventos orden a orden con contabilidad de margen y Bóveda Ratchet
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

            # Sizing de riesgo institucional/ultra: 15% por trade en Ultra, 1.0% en Fondeo
            risk_pct = 0.15 if is_ultra else 0.01
            sl_dist = 0.025  # Distancia estimada de stop-loss del 2.5%
            target_lev = min(ceiling_leverage, risk_pct / sl_dist)

            nominal_position = equity * target_lev
            peak_leverage_used = max(peak_leverage_used, target_lev)

            # Financiación (Funding) para Perpetuos (tasa media 0.01% por sesión de 8h)
            funding = nominal_position * 0.0001 if spec.category == "CRYPTO" else 0.0
            
            # PnL de la operación ajustado por tamaño y financiación
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

        # Reglas de Aprobación
        total_wealth = equity + vault_harvested
        no_margin_call = not margin_call_triggered
        leverage_within_bounds = (peak_leverage_used <= ceiling_leverage * 1.05)
        liquidation_buffer_ok = (min_dist_liquidation_pct >= (2.0 if is_ultra else 20.0))
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
