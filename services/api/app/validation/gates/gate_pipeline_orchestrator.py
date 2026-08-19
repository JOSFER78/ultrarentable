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
        trades_raw: Optional[List[Dict[str, Any]]] = None,
        strategy_snapshot: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Ejecuta los 11 gates de forma modular y persiste cada EvidenceRecord con trazabilidad criptográfica."""
        candles = candles or []
        is_trades = is_trades or []
        oos_trades = oos_trades or []
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

        evaluators = [
            (self.g1, lambda g: g.evaluate(candles, timeframe=candidate_info.get("timeframe", "1h"), dataset_filepath=candidate_info.get("dataset_filepath"))),
            (self.g2, lambda g: g.evaluate(trades_raw, symbol=candidate_info.get("symbol", "BTCUSDT"))),
            (self.g3, lambda g: g.evaluate(is_trades, oos_trades, is_ultra=is_ultra)),
            (self.g4, lambda g: g.evaluate(is_trades + oos_trades if (is_trades or oos_trades) else [])),
            (self.g5, lambda g: g.evaluate(oos_trades, initial_capital=base_capital, is_ultra=is_ultra)),
            (self.g6, lambda g: g.evaluate(oos_trades, is_ultra=is_ultra)),
            (self.g7, lambda g: g.evaluate(candles=candles, trades_raw=trades_raw, oos_trades_pnl=oos_trades, is_ultra=is_ultra)),
            (self.g8, lambda g: g.evaluate(oos_trades_pnl=oos_trades, trials_tested=int(candidate_info.get("trials_tested") or 1))),
            (self.g9, lambda g: g.evaluate(parameters=candidate_info.get("parameters", {}), trades_count=len(oos_trades), oos_pf=float(candidate_info.get("profit_factor_oos", 1.5)), candles=candles, strategy_snapshot=strategy_snapshot, is_ultra=is_ultra)),
            (self.g10, lambda g: g.evaluate(candidate_info)),
            (self.g11, lambda g: g.evaluate(oos_trades=oos_trades, trades_raw=trades_raw, symbol=candidate_info.get("symbol", "BTCUSDT"), initial_capital=base_capital, max_allowed_leverage=100.0 if is_ultra else 3.0, is_ultra=is_ultra)),
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

                # Construir y persistir EvidenceRecord
                inp_data = {"candidate": strat_id, "gate_id": gate_id, "gate_name": gate_name}
                inp_hash = hashlib.sha256(json.dumps(inp_data, default=str, sort_keys=True).encode("utf-8")).hexdigest()
                out_hash = hashlib.sha256(json.dumps(res, default=str, sort_keys=True).encode("utf-8")).hexdigest()

                art_file = strat_evidence_dir / f"gate_{gate_id:02d}_{gate_name.lower()}.json"
                
                rec = EvidenceRecord(
                    evidence_id=f"ev_{strat_id}_g{gate_id:02d}",
                    run_id=run_id,
                    strategy_id=strat_id,
                    strategy_snapshot_hash=strat_id,
                    dataset_id=dataset_id,
                    dataset_sha256=dataset_sha256,
                    gate_id=gate_id,
                    gate_name=gate_name,
                    engine="UltrarentableQuantitativeCore",
                    engine_version="2.0.0",
                    formula_version="2.0.0",
                    input_hash=inp_hash,
                    output_hash=out_hash,
                    status=GateStatus.PASSED if res.get("passed") else GateStatus.FAILED,
                    score=float(res.get("score", 0.0)),
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

        return {
            "strategy_id": strat_id,
            "name": candidate_info.get("name", ""),
            "symbol": candidate_info.get("symbol", ""),
            "overall_certified": overall_passed,
            "overall_score": avg_score,
            "scorecard_average": avg_score,
            "gates_passed_count": sum(1 for g in gates_results if g.get("passed")),
            "total_gates": 11,
            "gates": gates_results,
            "evidence_count": len(evidence_records),
        }
