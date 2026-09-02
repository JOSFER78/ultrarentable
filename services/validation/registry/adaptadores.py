"""services/validation/registry/adaptadores.py
Adaptadores de compatibilidad hacia atrás para el pipeline de validación.
Conecta el importador de la suite A (validation_router.py) al RegistryPipeline v1.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Type

from contracts.snapshots.evidence_record import GateStatus
from services.validation.engines.pipeline_orchestrator import (
    FullValidationReport,
    GateExecutionReport,
)
from services.validation.registry.contratos import Evidencia, GateBase, GateResult
from services.validation.registry.pipeline import RegistryPipeline


class ModularValidationPipeline:
    """Adaptador de paridad hacia atrás que satisface la interfaz de la suite A."""

    def __init__(self, registry: Optional[Dict[int, Type[GateBase]]] = None) -> None:
        self.pipeline = RegistryPipeline(registry=registry)

    def validate_candidate(
        self,
        strategy_id: str,
        name: str,
        symbol: str,
        timeframe: str,
        route: str,
        raw_trades_is: List[float],
        raw_trades_oos: List[float],
        rules_text: str = "",
        regime_pnls: Optional[Dict[str, float]] = None,
    ) -> FullValidationReport:
        t0 = time.perf_counter()
        ev = Evidencia(
            candidate_info={
                "candidate_id": strategy_id,
                "name": name,
                "symbol": symbol,
                "timeframe": timeframe,
                "route": route,
            },
            is_trades=raw_trades_is,
            oos_trades=raw_trades_oos,
            pre_oos_trades=raw_trades_is,
        )

        reports: List[GateExecutionReport] = []
        all_passed = True
        failed_gate: Optional[int] = None

        for gid in sorted(self.pipeline.registry.keys()):
            gate_inst = self.pipeline.gate_instances.get(gid)
            if gate_inst is None:
                gate_cls = self.pipeline.registry[gid]
                gate_inst = gate_cls()
                self.pipeline.gate_instances[gid] = gate_inst

            gate_id = getattr(gate_inst, "GATE_ID", gid)
            gate_name = getattr(gate_inst, "NAME", f"GATE_{gid}")

            gt0 = time.perf_counter()
            try:
                res = gate_inst.evaluar(ev)
            except Exception as e:
                res = GateResult(
                    gate_id=gate_id,
                    name=gate_name,
                    gate_version=getattr(gate_inst, "VERSION", "1.0.0"),
                    passed=False,
                    score=0.0,
                    verdict=f"ERROR_EJECUCION_GATE: {str(e)}",
                    evidence={"error": str(e)},
                    status=GateStatus.FAILED,
                )
            gt1 = time.perf_counter()
            exec_time_ms = round((gt1 - gt0) * 1000.0, 3)

            rejection_reasons = [] if res.passed else [res.verdict]
            reports.append(
                GateExecutionReport(
                    gate_id=res.gate_id,
                    gate_name=res.name,
                    passed=res.passed,
                    execution_time_ms=exec_time_ms,
                    details=res.evidence,
                    rejection_reasons=rejection_reasons,
                )
            )

            if not res.passed and all_passed:
                all_passed = False
                failed_gate = res.gate_id

        total_time_ms = round((time.perf_counter() - t0) * 1000.0, 3)
        return FullValidationReport(
            strategy_id=strategy_id,
            name=name,
            route=route,
            all_passed=all_passed,
            failed_at_gate=failed_gate,
            total_execution_time_ms=total_time_ms,
            gate_reports=reports,
        )
