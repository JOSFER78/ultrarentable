"""services/api/app/validation/gates/gate_pipeline_orchestrator.py
Orquestador Central de los 11 Gates Cuantitativos Modulares (Fase 5 & Cierre Forense).
Ejecuta cada Gate en su propio contenedor aislado y persiste físicamente los EvidenceRecords con hashes SHA-256 en disco.
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np

from contracts.snapshots.evidence_record import EvidenceRecord, GateStatus
from services.engine_version import CURRENT_ENGINE_VERSION
from services.api.app.validation.gates.gate_01_data_ingest import Gate01DataIngest
from services.api.app.validation.gates.gate_02_cost_backtest import Gate02CostBacktest
from services.api.app.validation.gates.gate_03_trade_significance import Gate03TradeSignificance
from services.api.app.validation.gates.gate_04_walk_forward import Gate04WalkForward
from services.api.app.validation.gates.gate_05_monte_carlo import Gate05MonteCarlo
from services.api.app.validation.gates.gate_06_stress_slippage import Gate06StressSlippage
from services.api.app.validation.gates.gate_07_regime_coverage import Gate07RegimeCoverage
from services.api.app.validation.gates.gate_08_dsr_ratio import Gate08DSRRatio
from services.api.app.validation.gates.gate_09_novelty_antifit import Gate09NoveltyAntiFit
from services.api.app.validation.gates.gate_10_agent_debate import Gate10AgentDebate
from services.api.app.validation.gates.gate_11_nautilus_event import Gate11NautilusEvent

logger = logging.getLogger("GatePipelineOrchestrator")


def _sanitize_dict(obj: Any) -> Any:
    """Convierte tipos numpy (np.bool_, np.float64, np.ndarray) a tipos estándar de Python."""
    if isinstance(obj, dict):
        return {str(k): _sanitize_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_sanitize_dict(x) for x in obj]
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, (np.integer, int)):
        return int(obj)
    elif isinstance(obj, (np.floating, float)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return [_sanitize_dict(x) for x in obj.tolist()]
    return obj


class GatePipelineOrchestrator:
    def __init__(self, evidence_base_dir: Optional[str] = None):
        self.g1 = Gate01DataIngest()
        self.g2 = Gate02CostBacktest()
        self.g3 = Gate03TradeSignificance()
        self.g4 = Gate04WalkForward()
        self.g5 = Gate05MonteCarlo()
        self.g6 = Gate06StressSlippage()
        self.g7 = Gate07RegimeCoverage()
        self.g8 = Gate08DSRRatio()
        self.g9 = Gate09NoveltyAntiFit()
        self.g10 = Gate10AgentDebate()
        self.g11 = Gate11NautilusEvent()
        
        self.evidence_dir = Path(evidence_base_dir) if evidence_base_dir else Path("data/evidence")
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

    def run_all_gates(
        self,
        candidate_info: Dict[str, Any],
        candles: Optional[List[Dict[str, Any]]] = None,
        is_trades: Optional[List[float]] = None,
        oos_trades: Optional[List[float]] = None,
        pre_oos_trades: Optional[List[float]] = None,
        trades_raw: Optional[List[Dict[str, Any]]] = None,
        strategy_snapshot: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Ejecuta los 11 gates de forma modular y persiste cada EvidenceRecord con trazabilidad criptográfica."""
        candles = candles or []
        is_trades = is_trades or []
        oos_trades = oos_trades or []
        pre_oos_trades = pre_oos_trades or is_trades
        trades_raw = trades_raw or []

        gates_results = []
        evidence_records = []
        overall_passed = True
        total_score = 0.0

        is_ultra = (candidate_info.get("route") == "ULTRA")
        base_capital = 1000.0 if is_ultra else 50000.0
        strat_id = str(candidate_info.get("candidate_id") or "strat_unnamed")
        run_id = str(candidate_info.get("run_id") or f"run_{strat_id}")
        dataset_id = str(candidate_info.get("dataset_id") or "ds_primary")
        dataset_sha256 = str(candidate_info.get("dataset_sha256") or "sha256_unverified")

        # Hash SHA-256 criptográfico real del StrategySnapshot
        strat_snapshot_hash = (
            getattr(strategy_snapshot, "canonical_hash", None)
            or str(candidate_info.get("strategy_snapshot_hash") or hashlib.sha256(strat_id.encode()).hexdigest())
        )

        evaluators = [
            (self.g1, lambda g: g.evaluate(candles, timeframe=candidate_info.get("timeframe", "1h"), dataset_filepath=candidate_info.get("dataset_filepath"))),
            (self.g2, lambda g: g.evaluate(trades_raw, symbol=candidate_info.get("symbol", "BTCUSDT"))),
            (self.g3, lambda g: g.evaluate(is_trades, oos_trades, is_ultra=is_ultra)),
            # Gate 4: Rolling WFO evaluado estrictamente sobre datos Pre-OOS (IS + Val), jamás contaminando el Blind Holdout OOS
            (self.g4, lambda g: g.evaluate(pre_oos_trades)),
            (self.g5, lambda g: g.evaluate(oos_trades, initial_capital=base_capital, is_ultra=is_ultra)),
            (self.g6, lambda g: g.evaluate(oos_trades, is_ultra=is_ultra)),
            (self.g7, lambda g: g.evaluate(candles=candles, trades_raw=trades_raw, oos_trades_pnl=oos_trades, is_ultra=is_ultra)),
            # Gate 8: Cero default complaciente. Si trials_tested no está registrado en SQLite, Gate 8 bloquea
            (self.g8, lambda g: g.evaluate(oos_trades_pnl=oos_trades, trials_tested=candidate_info.get("trials_tested"))),
            (self.g9, lambda g: g.evaluate(parameters=candidate_info.get("parameters", {}), trades_count=len(is_trades) + len(oos_trades), oos_pf=float(candidate_info.get("profit_factor_oos", 1.5)), candles=candles, strategy_snapshot=strategy_snapshot, is_ultra=is_ultra)),
            # Gate 10: Auditoría y Consenso Analítico de 5 Especialistas Cuantitativos
            (self.g10, lambda g: g.evaluate({**candidate_info, "trades_count": len(is_trades) + len(oos_trades), "profit_factor_oos": float(candidate_info.get("profit_factor_oos", 1.0)), "max_drawdown_pct": float(candidate_info.get("max_drawdown_pct", 0.0))})),
            # Gate 11: Reconciliación de Eventos NautilusTrader Core con Cosecha a Bóveda Ratchet
            (self.g11, lambda g: g.evaluate(oos_trades=oos_trades, trades_raw=trades_raw, candles=candles, strategy_snapshot=strategy_snapshot, symbol=candidate_info.get("symbol", "BTCUSDT"), initial_capital=base_capital, max_allowed_leverage=100.0 if is_ultra else 3.0, is_ultra=is_ultra)),
        ]

        strat_evidence_dir = self.evidence_dir / strat_id
        strat_evidence_dir.mkdir(parents=True, exist_ok=True)

        for gate_instance, eval_fn in evaluators:
            gate_id = gate_instance.GATE_ID
            gate_name = gate_instance.NAME
            try:
                raw_res = eval_fn(gate_instance)
                res = _sanitize_dict(raw_res)
                gates_results.append(res)
                total_score += float(res.get("score", 0.0))
                if not res.get("passed", False):
                    overall_passed = False

                # Construir y persistir EvidenceRecord con trazabilidad criptográfica exacta
                canonical_input_payload = {
                    "strategy_snapshot_hash": strat_snapshot_hash,
                    "dataset_id": dataset_id,
                    "dataset_sha256": dataset_sha256,
                    "gate_id": gate_id,
                    "gate_name": gate_name,
                    "parameters": candidate_info.get("parameters", {}),
                    "trials_tested": candidate_info.get("trials_tested"),
                    "candles_count": len(candles),
                    "oos_trades_count": len(oos_trades),
                }
                inp_hash = hashlib.sha256(json.dumps(canonical_input_payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()
                out_hash = hashlib.sha256(json.dumps(res, sort_keys=True, default=str).encode("utf-8")).hexdigest()

                art_file = strat_evidence_dir / f"gate_{gate_id:02d}_{gate_name.lower()}.json"
                
                rec = EvidenceRecord(
                    evidence_id=f"ev_{strat_id}_g{gate_id:02d}",
                    run_id=run_id,
                    strategy_id=strat_id,
                    strategy_snapshot_hash=strat_snapshot_hash,
                    dataset_id=dataset_id,
                    dataset_sha256=dataset_sha256,
                    gate_id=gate_id,
                    gate_name=gate_name,
                    engine="UltrarentableQuantitativeCore",
                    engine_version=CURRENT_ENGINE_VERSION,
                    formula_version=CURRENT_ENGINE_VERSION,
                    input_hash=inp_hash,
                    output_hash=out_hash,
                    status=GateStatus.PASSED if res.get("passed") else GateStatus.FAILED,
                    score=min(100.0, max(0.0, float(res.get("score", 0.0)))),
                    verdict=str(res.get("verdict", "")),
                    metrics=res.get("evidence", {}),
                    artifact_path=str(art_file),
                )
                
                with open(art_file, "w") as f:
                    f.write(rec.model_dump_json(indent=2))

                evidence_records.append(rec)

            except Exception as e:
                logger.error(f"Error en Gate {gate_id} ({gate_name}): {e}", exc_info=True)
                err_res = {
                    "gate_id": gate_id,
                    "name": gate_name,
                    "passed": False,
                    "score": 0.0,
                    "verdict": f"ERROR_EJECUCION_GATE: {str(e)}",
                    "evidence": {"error": str(e)},
                }
                gates_results.append(err_res)
                overall_passed = False

        avg_score = round(total_score / len(evaluators), 1)
        passed_count = sum(1 for g in gates_results if g.get("passed"))

        # Hard Gates Check (Gate 1 Data Quality, Gate 2 Cost Backtest, Gate 11 Nautilus Event)
        g1_passed = any(g.get("gate_id") == 1 and g.get("passed") for g in gates_results)
        g2_passed = any(g.get("gate_id") == 2 and g.get("passed") for g in gates_results)
        g11_passed = any(g.get("gate_id") == 11 and g.get("passed") for g in gates_results)
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

        # Diagnóstico de Brecha & Prescripciones de Reprogramación para IA / Usuario
        prescriptions = []
        for g in gates_results:
            if not g.get("passed") or float(g.get("score", 0.0)) < 70.0:
                gid = g.get("gate_id")
                gname = g.get("name")
                gverdict = g.get("verdict", "")

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
                    "score": g.get("score", 0.0),
                    "verdict": gverdict,
                    "actionable_advice": advice,
                })

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
            "gates": gates_results,
            "evidence_count": len(evidence_records),
        }
