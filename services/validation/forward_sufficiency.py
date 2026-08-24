"""services/validation/forward_sufficiency.py
Medidor Cuantitativo Adaptativo de Suficiencia Forward.
Evalúa la significancia estadística y la estabilidad temporal en tiempo real de estrategias en ejecución forward.
Especificación oficial según Sección 7 y 8 del Informe Maestro v5.3.0.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from contracts.queue_contracts import (
    ForwardSufficiencyRequest,
    ForwardSufficiencyResult,
    ForwardSufficiencyVerdict,
)
from services.api.app.factory.quality_gates import (
    MAX_ACCEPTABLE_DRAWDOWN_PCT_FONDEO,
    MAX_ACCEPTABLE_DRAWDOWN_PCT_ULTRA,
)


class AdaptiveForwardSufficiency:
    """Motor de Evaluación Adaptativa de Datos Forward."""

    @staticmethod
    def evaluate(req: ForwardSufficiencyRequest) -> ForwardSufficiencyResult:
        route = req.route.lower()
        now_utc = datetime.now(timezone.utc).isoformat()
        diagnostics: List[str] = []

        # 1. Parámetros según ruta
        if route == "fondeo":
            req_days = 20
            req_trades = 30
            max_allowed_dd = MAX_ACCEPTABLE_DRAWDOWN_PCT_FONDEO  # 4.50%
        else:  # ultra / kamikaze
            req_days = 10
            req_trades = 20
            max_allowed_dd = MAX_ACCEPTABLE_DRAWDOWN_PCT_ULTRA  # 75.0%

        # 2. Consumo de banda de Drawdown
        dd_consumption = round((req.forward_max_dd_pct / max_allowed_dd * 100.0), 2) if max_allowed_dd > 0 else 100.0

        # 3. Ratio de retorno Forward vs In-Sample
        return_ratio = (
            round(req.forward_net_profit_pct / req.is_expected_return_pct, 3)
            if req.is_expected_return_pct > 0
            else 0.0
        )

        # 4. Evaluación de Ruina o Degradación Crítica
        if req.forward_max_dd_pct > max_allowed_dd:
            diagnostics.append(
                f"Degradación crítica: Drawdown forward ({req.forward_max_dd_pct:.2f}%) supera el límite estricto ({max_allowed_dd:.2f}%)."
            )
            return ForwardSufficiencyResult(
                strategy_id=req.strategy_id,
                route=route,
                verdict=ForwardSufficiencyVerdict.FORWARD_DEGRADED_ABORT,
                forward_days_completed=req.forward_days,
                required_forward_days=req_days,
                forward_trades_completed=req.forward_trades,
                required_forward_trades=req_trades,
                drawdown_consumption_pct=dd_consumption,
                forward_to_is_return_ratio=return_ratio,
                is_certified_ready=False,
                diagnostics=diagnostics,
                evaluated_at_utc=now_utc,
            )

        # 5. Evaluación de muestra mínima
        if req.forward_days < 3 or req.forward_trades < 5:
            diagnostics.append(
                f"Datos preliminares insuficientes: {req.forward_days} días y {req.forward_trades} trades acumulados."
            )
            return ForwardSufficiencyResult(
                strategy_id=req.strategy_id,
                route=route,
                verdict=ForwardSufficiencyVerdict.INSUFFICIENT_DATA,
                forward_days_completed=req.forward_days,
                required_forward_days=req_days,
                forward_trades_completed=req.forward_trades,
                required_forward_trades=req_trades,
                drawdown_consumption_pct=dd_consumption,
                forward_to_is_return_ratio=return_ratio,
                is_certified_ready=False,
                diagnostics=diagnostics,
                evaluated_at_utc=now_utc,
            )

        # 6. Evaluación de acumulación en progreso
        if req.forward_days < req_days or req.forward_trades < req_trades:
            diagnostics.append(
                f"Acumulando evidencia: {req.forward_days}/{req_days} días ({req.forward_days/req_days*100:.0f}%) "
                f"y {req.forward_trades}/{req_trades} trades ({req.forward_trades/req_trades*100:.0f}%)."
            )
            if return_ratio < 0.0:
                diagnostics.append("Retorno forward actual en terreno negativo, requiere monitoreo estrecho.")

            return ForwardSufficiencyResult(
                strategy_id=req.strategy_id,
                route=route,
                verdict=ForwardSufficiencyVerdict.FORWARD_ACCUMULATING,
                forward_days_completed=req.forward_days,
                required_forward_days=req_days,
                forward_trades_completed=req.forward_trades,
                required_forward_trades=req_trades,
                drawdown_consumption_pct=dd_consumption,
                forward_to_is_return_ratio=return_ratio,
                is_certified_ready=False,
                diagnostics=diagnostics,
                evaluated_at_utc=now_utc,
            )

        # 7. Verificación de Certificación Completa
        if return_ratio < 0.30:
            diagnostics.append(
                f"Muestra temporal completa pero persistencia de retorno baja (Ratio Forward/IS: {return_ratio:.2f} < 0.30)."
            )
            verdict = ForwardSufficiencyVerdict.FORWARD_ACCUMULATING
            certified = False
        else:
            diagnostics.append("Suficiencia estadística y temporal forward validada al 100%. Lista para producción.")
            verdict = ForwardSufficiencyVerdict.FORWARD_CERTIFIED
            certified = True

        return ForwardSufficiencyResult(
            strategy_id=req.strategy_id,
            route=route,
            verdict=verdict,
            forward_days_completed=req.forward_days,
            required_forward_days=req_days,
            forward_trades_completed=req.forward_trades,
            required_forward_trades=req_trades,
            drawdown_consumption_pct=dd_consumption,
            forward_to_is_return_ratio=return_ratio,
            is_certified_ready=certified,
            diagnostics=diagnostics,
            evaluated_at_utc=now_utc,
        )
