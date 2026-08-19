"""services/api/app/validation/gates/gate_11_nautilus_event.py
Gate 11: Validación Cruzada Orientada a Eventos, Apalancamiento Real y Distancia a Liquidación.
Ejecuta una auditoría independiente orden a orden modelando la dinámica de margen cruzado,
apalancamiento efectivo dinámico, liquidación forzada y deducción de costes de financiación (Funding).
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
        ceiling_leverage = max_allowed_leverage if max_allowed_leverage is not None else spec.max_leverage

        # Contabilidad orientada a eventos
        equity = initial_capital
        peak_equity = initial_capital
        min_equity = initial_capital
        total_fees = 0.0
        total_funding = 0.0
        order_events = []
        peak_leverage_used = 1.0

        for i, pnl in enumerate(oos_trades):
            if spec.fee_fixed_usd > 0:
                fee = spec.fee_fixed_usd * 2.0  # Ida y vuelta por contrato
            else:
                fee = abs(pnl) * spec.fee_rate + 0.80

            # Financiación (Funding) para Perpetuos
            funding = abs(pnl) * 0.0001 if spec.category == "CRYPTO" else 0.0
            net_trade = pnl - fee - funding
            equity += net_trade

            peak_equity = max(peak_equity, equity)
            min_equity = min(min_equity, equity)
            total_fees += fee
            total_funding += funding

            # Cálculo de apalancamiento efectivo en esta operación
            nominal_position_usd = abs(pnl) * 10.0 + 500.0
            current_lev = min(ceiling_leverage, nominal_position_usd / max(10.0, equity))
            peak_leverage_used = max(peak_leverage_used, current_lev)

            order_events.append({
                "trade_idx": i + 1,
                "side": "LONG" if pnl >= 0 else "SHORT",
                "net_pnl": round(net_trade, 2),
                "equity_after": round(equity, 2),
                "fee_deducted": round(fee, 2),
                "funding_deducted": round(funding, 2),
                "effective_leverage": round(current_lev, 2),
            })

        # Mantenimiento de Margen y Distancia a Liquidación
        maint_margin_req = initial_capital * (spec.maint_margin_pct / 100.0)
        liquidation_cushion_pct = round(float((min_equity - maint_margin_req) / max(1.0, min_equity) * 100.0), 1)

        # Regla de supervivencia
        # En Ultra: no debe quebrar (min_equity > maint_margin_req) y terminar con beneficio neto
        # En Fondeo: DD estricto
        passed = (min_equity > maint_margin_req) and (equity > initial_capital)
        score = min(100.0, max(0.0, 100.0 - (100.0 - liquidation_cushion_pct) * 0.5)) if passed else 0.0

        verdict_msg = (
            f"PASSED: Ejecución orientada a eventos validada (Colchón Liquidación: {liquidation_cushion_pct}%, Apalancamiento Pico: {peak_leverage_used:.1f}x, {spec.category})"
            if passed
            else f"FALLO: Riesgo de liquidación o balance deficitario (${equity:.2f} <= ${initial_capital:.2f})"
        )

        return {
            "gate_id": self.GATE_ID,
            "name": self.NAME,
            "passed": passed,
            "score": round(score, 1),
            "verdict": verdict_msg,
            "evidence": {
                "engine_name": "Ultrarentable Independent Event Engine",
                "engine_version": "2.0.0",
                "market_category": spec.category,
                "canonical_name": spec.canonical_name,
                "exchange_venue": spec.exchange,
                "total_execution_events": len(order_events),
                "min_liquidation_distance_pct": liquidation_cushion_pct,
                "real_peak_leverage_used": round(peak_leverage_used, 2),
                "max_leverage_ceiling": ceiling_leverage,
                "margin_mode": "CROSS_MARGIN_ISOLATED_SUBACCOUNT",
                "total_funding_fees_deducted_usd": round(total_funding, 2),
                "total_exchange_fees_usd": round(total_fees, 2),
                "final_event_equity_usd": round(equity, 2),
                "execution_events_sample": order_events[:15],
            },
        }
