"""services/validation/registry/pipeline.py
Pipeline de ejecución y agregación de veredictos sobre los 11 Gates v1.
Paridad exacta con la lógica y formato de retorno de GatePipelineOrchestrator (suite B).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Type

from contracts.snapshots.evidence_record import GateStatus
from services.validation.registry.contratos import Evidencia, GateBase, GateResult
from services.validation.registry.registro import GATE_REGISTRY

logger = logging.getLogger("RegistryPipeline")


class RegistryPipeline:
    def __init__(self, registry: Optional[Dict[int, Type[GateBase]]] = None) -> None:
        self.registry: Dict[int, Type[GateBase]] = registry if registry is not None else GATE_REGISTRY
        self.gate_instances: Dict[int, GateBase] = {
            gid: cls() for gid, cls in sorted(self.registry.items())
        }

    def evaluar_todas(self, ev: Evidencia) -> List[GateResult]:
        """Ejecuta los 11 gates registrados en orden secuencial (1..11)."""
        results: List[GateResult] = []
        for gid in sorted(self.registry.keys()):
            gate_inst = self.gate_instances.get(gid)
            if gate_inst is None:
                gate_cls = self.registry[gid]
                gate_inst = gate_cls()
                self.gate_instances[gid] = gate_inst

            gate_id = getattr(gate_inst, "GATE_ID", gid)
            gate_name = getattr(gate_inst, "NAME", f"GATE_{gid}")
            gate_version = getattr(gate_inst, "VERSION", "1.0.0")

            try:
                res = gate_inst.evaluar(ev)
                results.append(res)
            except Exception as e:
                logger.error(f"Error en Gate {gate_id} ({gate_name}): {e}", exc_info=True)
                err_res = GateResult(
                    gate_id=gate_id,
                    name=gate_name,
                    gate_version=gate_version,
                    passed=False,
                    score=0.0,
                    verdict=f"ERROR_EJECUCION_GATE: {str(e)}",
                    evidence={"error": str(e)},
                    status=GateStatus.FAILED,
                )
                results.append(err_res)
        return results

    def veredicto(self, ev: Evidencia) -> Dict[str, Any]:
        """Ejecuta todos los gates y agrega los resultados con paridad exacta a la suite B."""
        results = self.evaluar_todas(ev)
        candidate_info = ev.candidate_info

        strat_id = str(candidate_info.get("candidate_id") or "strat_unnamed")
        total_score = sum(r.score for r in results)
        avg_score = round(total_score / len(results), 1) if results else 0.0
        passed_count = sum(1 for r in results if r.passed)
        overall_passed = all(r.passed for r in results)

        # Hard Gates Check (Gate 1 Data Quality, Gate 2 Cost Backtest, Gate 11 Nautilus Event)
        g1_passed = any(r.gate_id == 1 and r.passed for r in results)
        g2_passed = any(r.gate_id == 2 and r.passed for r in results)
        g11_passed = any(r.gate_id == 11 and r.passed for r in results)
        hard_gates_ok = g1_passed and g2_passed and g11_passed

        # Clasificación Cuantitativa Multi-Tier (100% Real, Cero Descarte Ciego)
        if passed_count == 11 and hard_gates_ok:
            tier = "TIER_1_CERTIFIED"
            tier_label = "🏆 Producción Certificada (11/11)"
            status_lifecycle = "APPROVED"
        elif passed_count in (9, 10) and hard_gates_ok:
            tier = "TIER_2_NEAR_CERTIFIED"
            tier_label = "💎 Diamante en Bruto (9-10/11)"
            status_lifecycle = "CANDIDATA_AVANZADA"
        elif passed_count in (7, 8) and hard_gates_ok:
            tier = "TIER_3_INCUBATOR"
            tier_label = "🧪 Incubadora de I+D (7-8/11)"
            status_lifecycle = "INCUBADORA_REPROGRAMACION"
        else:
            tier = "TIER_4_REJECTED"
            tier_label = "❌ Rechazada Estructural"
            status_lifecycle = "RECHAZADA"

        # Diagnóstico de Brecha & Prescripciones de Reprogramación
        prescriptions = []
        for r in results:
            if not r.passed or float(r.score) < 70.0:
                gid = r.gate_id
                gname = r.name
                gverdict = r.verdict

                if gid == 3:
                    advice = "Ampliar rango de fechas histórico o evaluar en temporalidad menor (ej. 15m) para incrementar muestra de trades."
                elif gid == 4:
                    advice = "Aumentar multiplicador de Take Profit (ATR) o incorporar filtro de volatilidad para reducir degradación OOS."
                elif gid == 5:
                    advice = "Reducir tamaño base de posición o ajustar Stop Loss para contener el Drawdown en remuestreo Monte Carlo."
                elif gid == 6:
                    advice = "Aumentar Take Profit mínimo para que la ganancia media por trade supere el deslizamiento y spread bajo estrés 3x."
                elif gid == 7:
                    advice = "Añadir condición simétrica short o filtro de régimen tendencial/lateral para operar en todos los ciclos."
                elif gid == 8:
                    advice = "Alinear ratio beneficio/riesgo (Payoff Ratio >= 2.5) para superar penalización de Deflated Sharpe."
                elif gid == 9:
                    advice = "Diferenciar condiciones de entrada mediante combinación de indicadores no colineales."
                elif gid == 10:
                    advice = "Revisar objeciones del comité de riesgo (Stop Loss obligatorio y cierre en fin de sesión)."
                else:
                    advice = f"Ajustar parámetros funcionales para resolver: {gverdict}"

                prescriptions.append({
                    "gate_id": gid,
                    "gate_name": gname,
                    "score": r.score,
                    "verdict": gverdict,
                    "actionable_advice": advice,
                })

        gates_formatted = [
            {**r.como_dict_b(), "gate_version": r.gate_version}
            for r in results
        ]

        return {
            "strategy_id": strat_id,
            "name": candidate_info.get("name", ""),
            "symbol": candidate_info.get("symbol", ""),
            "overall_certified": overall_passed and (passed_count == 11),
            "overall_score": avg_score,
            "scorecard_average": avg_score,
            "gates_passed_count": passed_count,
            "total_gates": 11,
            "tier": tier,
            "tier_label": tier_label,
            "status_lifecycle": status_lifecycle,
            "can_reprogram": (tier in ("TIER_2_NEAR_CERTIFIED", "TIER_3_INCUBATOR")),
            "prescriptions": prescriptions,
            "gates": gates_formatted,
            "evidence_count": 0,
        }
