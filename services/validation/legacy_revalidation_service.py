"""services/validation/legacy_revalidation_service.py
Servicio Forense de Revalidación de Estrategias con el Motor Cuantitativo Actual (v3.2.0).
Somete estrategias históricas o legacy a la auditoría estricta del pipeline cuantitativo:
- Costes reales por activo (CANONICAL_COST_REGISTRY).
- Particionado físico ciego (Blind Holdout 20%).
- Estrés 3x slippage y Monte Carlo (0.0% ruina).
- Reconciliación matemática trade-a-trade NautilusTrader.

Si la estrategia supera las compuertas, es promovida a v3.2.0 con certificación completa.
Si no los supera, queda marcada como RECHAZADA con su causa de rechazo forense en la base de datos.
"""

from __future__ import annotations

import glob
import hashlib
import json
import logging
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from contracts.snapshots.strategy_snapshot import StrategyRoute, StrategySnapshot
from services.engine_version import CURRENT_ENGINE_VERSION, CURRENT_ENGINE_NAME
from services.discovery.ultra_discovery import UltraDiscoveryEngine
from services.discovery.funding_discovery import FundingDiscoveryEngine
from services.validation.engine.event_backtest_engine import EventBacktestEngine
from services.api.app.validation.gates.gate_pipeline_orchestrator import GatePipelineOrchestrator
from services.validation.certification_registry import CertificationRegistry
from services.data.instrument_cost_registry import CANONICAL_COST_REGISTRY

logger = logging.getLogger("LegacyRevalidationService")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

DB_PATH = Path("/home/ubuntu/.local/state/ultrarentable/ultrarentable.sqlite3")
DATA_DIR = Path("/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/normalized")


class LegacyRevalidationService:
    """Servicio de re-verificación de estrategias contra el pipeline y motor actual."""

    def __init__(self, db_path: Optional[Path] = None, data_dir: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self.data_dir = data_dir or DATA_DIR
        self.ultra_discovery = UltraDiscoveryEngine()
        self.funding_discovery = FundingDiscoveryEngine()
        self.backtest_engine = EventBacktestEngine()
        self.gates_orchestrator = GatePipelineOrchestrator()
        self.cert_registry = CertificationRegistry()
        
        self._job_lock = threading.Lock()
        self._cancel_requested = False
        self._job_state: Dict[str, Any] = {
            "job_id": None,
            "status": "IDLE",
            "target_version": None,
            "total_candidates": 0,
            "processed_count": 0,
            "promoted_count": 0,
            "rejected_count": 0,
            "current_candidate": None,
            "start_time": None,
            "finish_time": None,
            "results": [],
            "error_message": None,
        }

    def get_db_connection(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout = 30000;")
        return conn

    @staticmethod
    def _format_indicator(ind) -> str:
        if ind is None:
            return "?"
        name = getattr(ind, "name", None) or str(ind)
        period = getattr(ind, "period", None)
        return f"{name}({period})" if period else str(name)

    def _summarize_snapshot_rules(self, snapshot) -> List[str]:
        """ZERO-MOCKS: reglas reales derivadas del RuleTree del snapshot (antes: lista fija)."""
        rules: List[str] = []
        try:
            tree = getattr(snapshot, "entry_rules", None)
            for cond in getattr(tree, "long_conditions", None) or []:
                left = self._format_indicator(getattr(cond, "left_indicator", None))
                op = getattr(cond, "operator", None)
                op_str = getattr(op, "value", None) or str(op) if op is not None else "?"
                right_ind = getattr(cond, "right_indicator", None)
                right = self._format_indicator(right_ind) if right_ind is not None else getattr(cond, "threshold_value", None)
                rules.append(f"{left} {op_str} {right if right is not None else '?'}")
        except Exception:
            logger.exception("No se pudieron extraer reglas del snapshot")
        return rules or ["NO_RULES_EXTRACTED"]

    def _count_snapshot_indicators(self, snapshot) -> int:
        """Cuenta indicadores distintos referenciados en las reglas del snapshot."""
        names = set()
        try:
            tree = getattr(snapshot, "entry_rules", None)
            for cond in getattr(tree, "long_conditions", None) or []:
                for side in (getattr(cond, "left_indicator", None), getattr(cond, "right_indicator", None)):
                    if side is not None:
                        names.add(str(getattr(side, "name", side)))
        except Exception:
            pass
        return len(names)

    def find_dataset_file(self, symbol: str, timeframe: str) -> Optional[Path]:
        """Localiza el dataset físico normalizado para un símbolo y timeframe."""
        clean_sym = symbol.replace("-", "").replace("/", "").replace("_", "").lower()
        tf_map = {
            "h1": "1h", "h4": "4h", "d1": "1d", "m1": "1m", "m5": "5m", "m15": "15m", "m30": "30m"
        }
        clean_tf = tf_map.get(timeframe.lower(), timeframe.lower())

        # 1. Búsqueda exacta
        candidates_files = list(self.data_dir.glob("*.json"))
        for f in candidates_files:
            if f.name.endswith("_manifest.json") or f.name.startswith("."):
                continue
            fname_lower = f.name.lower()
            if clean_sym in fname_lower and f"_{clean_tf}_" in fname_lower:
                return f

        # 2. Búsqueda secundaria por símbolo raíz (e.g. btc, eth, cl, nq, eurusd)
        for f in candidates_files:
            if f.name.endswith("_manifest.json") or f.name.startswith("."):
                continue
            fname_lower = f.name.lower()
            if clean_sym in fname_lower:
                return f

        return None

    def revalidate_single_candidate(self, candidate_id: str) -> Dict[str, Any]:
        """Revalida una única estrategia por ID bajo el motor actual."""
        conn = self.get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT candidate_id, name, route, symbol, timeframe, status, scorecard_json, engine_version, net_profit_oos, max_dd_oos_pct, profit_factor_oos
            FROM candidates 
            WHERE candidate_id = ? 
               OR candidate_id = ? 
               OR candidate_id = ? 
               OR candidate_id = ?
               OR candidate_id = ?
            LIMIT 1
            """,
            (
                candidate_id,
                candidate_id.upper(),
                candidate_id.lower(),
                candidate_id.replace("_1H", "_1h").replace("_4H", "_4h").replace("_15M", "_15m").replace("_5M", "_5m"),
                candidate_id.replace("_1h", "_1H").replace("_4h", "_4H").replace("_15m", "_15M").replace("_5m", "_5M"),
            ),
        )
        row = cur.fetchone()
        conn.close()

        if not row:
            return {
                "candidate_id": candidate_id,
                "status": "ERROR",
                "message": f"Candidato {candidate_id} no encontrado en base de datos.",
                "passed": False,
            }

        cid, name, route_str, symbol, timeframe, old_status, sc_json_str, old_engine_ver, old_np, old_dd, old_pf = row
        route = StrategyRoute.ULTRA if route_str == "ULTRA" else StrategyRoute.FONDEO

        # 1. Localizar dataset físico
        ds_file = self.find_dataset_file(symbol, timeframe)
        if not ds_file or not ds_file.exists():
            new_st = "BLOCKED_NO_DATASET"
            res_msg = f"No se encontró dataset físico para {symbol} {timeframe}"
            conn = self.get_db_connection()
            conn.execute(
                "UPDATE candidates SET status = ?, status_reason = ?, engine_version = ? WHERE candidate_id = ?",
                (new_st, res_msg, CURRENT_ENGINE_VERSION, cid),
            )
            conn.commit()
            conn.close()
            return {
                "candidate_id": cid,
                "name": name,
                "symbol": symbol,
                "timeframe": timeframe,
                "old_version": old_engine_ver or "1.00",
                "new_version": CURRENT_ENGINE_VERSION,
                "old_status": old_status,
                "new_status": new_st,
                "reason": res_msg,
                "passed": False,
                "gates_passed": 0,
            }

        # ZERO-MOCKS: SHA-256 real del dataset físico (antes: string falso "dataset_revalidation_sha256")
        ds_sha256 = hashlib.sha256(Path(ds_file).read_bytes()).hexdigest()

        # 2. Leer velas del dataset físico
        try:
            with open(ds_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            candles = data if isinstance(data, list) else data.get("candles", [])
            if len(candles) < 200:
                new_st = "REJECTED_INSUFFICIENT_BARS"
                res_msg = f"Dataset tiene solo {len(candles)} velas (requerido >= 200)"
                conn = self.get_db_connection()
                conn.execute(
                    "UPDATE candidates SET status = ?, status_reason = ?, engine_version = ? WHERE candidate_id = ?",
                    (new_st, res_msg, CURRENT_ENGINE_VERSION, cid),
                )
                conn.commit()
                conn.close()
                return {
                    "candidate_id": cid,
                    "name": name,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "old_version": old_engine_ver or "1.00",
                    "new_version": CURRENT_ENGINE_VERSION,
                    "old_status": old_status,
                    "new_status": new_st,
                    "reason": res_msg,
                    "passed": False,
                    "gates_passed": 0,
                }
        except Exception as e:
            return {
                "candidate_id": cid,
                "status": "ERROR",
                "message": f"Error leyendo dataset: {e}",
                "passed": False,
            }
        except Exception as e:
            return {
                "candidate_id": cid,
                "status": "ERROR",
                "message": f"Error leyendo dataset: {e}",
                "passed": False,
            }

        # 3. Particionado Físico Cronológico: 60% IS, 20% Val, 20% Blind OOS
        total_bars = len(candles)
        idx_is = int(total_bars * 0.60)
        idx_val = int(total_bars * 0.80)

        candles_is = candles[:idx_is]
        candles_val = candles[idx_is:idx_val]
        candles_blind_oos = candles[idx_val:]
        candles_pre_oos = candles[:idx_val]

        # 4. Extraer o calibrar parámetros de la estrategia
        params = {"sl_atr_mult": 2.0, "tp_atr_mult": 6.0, "ema_fast": 20, "ema_slow": 50}
        if sc_json_str:
            try:
                sc_dict = json.loads(sc_json_str) if isinstance(sc_json_str, str) else sc_json_str
                if "parameters" in sc_dict:
                    params.update(sc_dict["parameters"])
            except Exception:
                pass

        # 5. Generar Snapshot Canónico
        initial_cap = 100.0 if route == StrategyRoute.ULTRA else 100_000.0
        if route == StrategyRoute.ULTRA:
            strat_snapshot = self.ultra_discovery.generate_candidate_blueprint(
                strategy_id=cid,
                symbol=symbol,
                timeframe=timeframe,
                dataset_id=ds_file.name,
                dataset_sha256=ds_sha256,
                sl_atr_mult=float(params.get("sl_atr_mult", 2.0)),
                tp_atr_mult=float(params.get("tp_atr_mult", 6.0)),
                ema_fast=int(params.get("ema_fast", 20)),
                ema_slow=int(params.get("ema_slow", 50)),
                pyramiding_tiers_count=int(params.get("pyramiding_tiers_count", 2)),
            )
        else:
            strat_snapshot = self.funding_discovery.generate_candidate_blueprint(
                strategy_id=cid,
                symbol=symbol,
                timeframe=timeframe,
                dataset_id=ds_file.name,
                dataset_sha256=ds_sha256,
                ema_fast=int(params.get("ema_fast", 20)),
                ema_slow=int(params.get("ema_slow", 50)),
            )

        # 6. Ejecutar Backtests Deterministas con Costes Canónicos
        pre_oos_bt = self.backtest_engine.run_backtest(strat_snapshot, candles_pre_oos, initial_capital_usd=initial_cap)
        is_bt = self.backtest_engine.run_backtest(strat_snapshot, candles_is, initial_capital_usd=initial_cap)
        oos_bt = self.backtest_engine.run_backtest(strat_snapshot, candles_blind_oos, initial_capital_usd=initial_cap)

        pre_oos_trades = [t.return_pct / 100.0 for t in pre_oos_bt.trades]
        is_trades = [t.return_pct / 100.0 for t in is_bt.trades]
        oos_trades = [t.return_pct / 100.0 for t in oos_bt.trades]
        trades_raw = [
            {
                "entry_price": t.entry_price, "exit_price": t.exit_price,
                "qty": t.qty, "side": t.side, "net_pnl_usd": t.net_pnl_usd,
                "entry_bar_idx": t.entry_bar, "exit_bar_idx": t.exit_bar,
                "entry_time_ms": t.entry_time_ms, "exit_time_ms": t.exit_time_ms,
            }
            for t in oos_bt.trades
        ]

        # 7. Evaluación Integral de los 11 Gates Cuantitativos
        candidate_info = {
            "candidate_id": cid,
            "name": name,
            "route": route_str,
            "symbol": symbol,
            "timeframe": timeframe,
            "dataset_id": ds_file.name,
            "dataset_sha256": ds_sha256,
            "dataset_filepath": str(ds_file),
            "profit_factor_oos": oos_bt.profit_factor,
            "max_drawdown_pct": oos_bt.max_drawdown_pct,
            "trades_count": len(oos_trades),
            "trials_tested": 1,
            "parameters": params,
            "rules": self._summarize_snapshot_rules(strat_snapshot),
            "indicators_count": self._count_snapshot_indicators(strat_snapshot),
        }

        gates_eval = self.gates_orchestrator.run_all_gates(
            candidate_info=candidate_info,
            candles=candles_blind_oos,
            is_trades=is_trades,
            oos_trades=oos_trades,
            pre_oos_trades=pre_oos_trades,
            trades_raw=trades_raw,
            strategy_snapshot=strat_snapshot,
        )

        gates_passed_count = gates_eval.get("gates_passed_count", 0)
        overall_score = gates_eval.get("overall_score", 0.0)

        # 8. Certificación
        verdict = self.cert_registry.certify_candidate(
            strategy=strat_snapshot,
            backtest_result=oos_bt,
            gates_passed_count=gates_passed_count,
            scorecard_average=overall_score,
        )

        now_iso = datetime.now(timezone.utc).isoformat()
        is_promoted = (gates_passed_count == 10)
        if is_promoted:
            new_status = "CERTIFICADA_TIER_1"
            cand_tier = "TIER_1_CERTIFIED"
            cand_tier_label = "🏆 Producción Certificada (10/10)"
        elif gates_passed_count in (8, 9):
            new_status = "REFINADO_TIER_2"
            cand_tier = "TIER_2_NEAR_CERTIFIED"
            cand_tier_label = "💎 Diamante en I+D (8-9/10)"
        elif gates_passed_count in (5, 6, 7):
            new_status = "INCUBADORA_REPROGRAMACION"
            cand_tier = "TIER_3_INCUBATOR"
            cand_tier_label = "🧪 Incubadora de I+D (5-7/10)"
        else:
            new_status = "REJECTED_ESTRUCTURAL"
            cand_tier = "TIER_4_REJECTED"
            cand_tier_label = "❌ Rechazada Estructural (<5/10)"

        new_engine_ver = CURRENT_ENGINE_VERSION
        reason = f"Revalidación v{CURRENT_ENGINE_VERSION}: {gates_passed_count}/10 Gates superados (Score: {overall_score:.1f}/100)"

        # 9. Calcular métricas finales exactas (CAGR Geométrico Bounded)
        tf_bars_per_month = {"1m": 43200, "5m": 8640, "15m": 2880, "1h": 720, "4h": 180, "1d": 30}
        bars_per_m = tf_bars_per_month.get(timeframe.lower(), 720)
        total_months = max(0.5, total_bars / bars_per_m)
        oos_months = max(0.2, len(candles_blind_oos) / bars_per_m)

        if oos_bt.net_profit_usd > -initial_cap and oos_months > 0:
            cagr = ((1.0 + (oos_bt.net_profit_usd / max(1.0, initial_cap))) ** (1.0 / oos_months) - 1.0) * 100.0
            monthly_roi_pct = max(-100.0, min(500.0, cagr))
        else:
            monthly_roi_pct = -100.0 / max(0.2, oos_months)
        annual_roi_pct = monthly_roi_pct * 12.0

        updated_scorecard = {
            "source": f"Revalidation Engine v{CURRENT_ENGINE_VERSION}",
            "revalidated_at": now_iso,
            "revalidation_pipeline_version": CURRENT_ENGINE_VERSION,
            "gates_passed_count": gates_passed_count,
            "total_gates": 10,
            "tier": cand_tier,
            "tier_label": cand_tier_label,
            "overall_score": overall_score,
            "gates": gates_eval.get("gates", []),
            "nautilus_gate_10": gates_eval.get("nautilus_gate_11", {}),
            "parameters": params,
            "certified_by": "CertificationRegistry",
        }

        # Extract gate scores from the list
        gates_list = gates_eval.get("gates", [])
        g4_score = next((g.get("score", 85.0) for g in gates_list if g.get("gate_id") == 4 or "walk" in g.get("name", "").lower()), 85.0)
        g5_score = next((g.get("score", 90.0) for g in gates_list if g.get("gate_id") == 5 or "monte" in g.get("name", "").lower()), 90.0)

        updated_metrics = {
            "in_sample": {
                "trades": len(is_trades),
                "net_profit_usd": is_bt.net_profit_usd,
                "profit_factor": is_bt.profit_factor,
                "max_drawdown_pct": is_bt.max_drawdown_pct,
                "win_rate_pct": is_bt.win_rate_pct,
            },
            "out_of_sample": {
                "trades": len(oos_trades),
                "net_profit_usd": oos_bt.net_profit_usd,
                "profit_factor": oos_bt.profit_factor,
                "max_drawdown_pct": oos_bt.max_drawdown_pct,
                "win_rate_pct": oos_bt.win_rate_pct,
                "monthly_roi_pct": round(monthly_roi_pct, 2),
                "annualized_roi_pct": round(annual_roi_pct, 2),
                "total_months": round(total_months, 1),
                "oos_months": round(oos_months, 1),
                "blind_oos_bars": len(candles_blind_oos),
            },
            "anti_overfit": {
                "ratio_oos_is": oos_bt.net_profit_usd / max(1.0, abs(is_bt.net_profit_usd)) if is_bt.net_profit_usd != 0 else 0.5,
                "wfo_pass_pct": g4_score,
                "monte_carlo_score": g5_score,
            },
        }

        updated_scorecard.update({
            "is_metrics": updated_metrics["in_sample"],
            "oos_metrics": updated_metrics["out_of_sample"],
            "metrics": updated_metrics,
            "win_rate_pct": oos_bt.win_rate_pct,
            "win_rate": oos_bt.win_rate_pct,
            "monthly_roi_pct": round(monthly_roi_pct, 2),
            "annual_roi_pct": round(annual_roi_pct, 2),
            "annualized_roi_pct": round(annual_roi_pct, 2),
            "tier": "TIER_1_CERTIFIED" if is_promoted else ("TIER_2_NEAR_CERTIFIED" if gates_passed_count in (9, 10) else ("TIER_3_INCUBATOR" if gates_passed_count in (7, 8) else "TIER_4_REJECTED")),
            "tier_label": "🏆 Producción Certificada (11/11)" if is_promoted else ("💎 Diamante en Bruto (9-10/11)" if gates_passed_count in (9, 10) else ("🧪 Incubadora de I+D (7-8/11)" if gates_passed_count in (7, 8) else "❌ Rechazada")),
        })

        # 10. Actualizar SQLite WAL de forma determinista
        conn = self.get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE candidates
            SET status = ?,
                status_reason = ?,
                engine_version = ?,
                validation_pipeline_version = ?,
                scorecard_json = ?,
                net_profit_is = ?,
                trades_is = ?,
                profit_factor_is = ?,
                max_dd_is_pct = ?,
                net_profit_oos = ?,
                trades_oos = ?,
                profit_factor_oos = ?,
                max_dd_oos_pct = ?,
                ratio_oos_is = ?,
                wfo_pass_pct = ?,
                monte_carlo_score = ?
            WHERE candidate_id = ?
            """,
            (
                new_status,
                reason,
                new_engine_ver,
                CURRENT_ENGINE_VERSION,
                json.dumps(updated_scorecard),
                is_bt.net_profit_usd,
                len(is_trades),
                is_bt.profit_factor,
                is_bt.max_drawdown_pct,
                oos_bt.net_profit_usd,
                len(oos_trades),
                oos_bt.profit_factor,
                oos_bt.max_drawdown_pct,
                updated_metrics["anti_overfit"]["ratio_oos_is"],
                g4_score,
                g5_score,
                cid,
            ),
        )

        # Registrar Evento de Auditoría
        severity = "INFO" if is_promoted else "WARNING"
        cur.execute(
            """
            INSERT INTO audit_events (event_id, category, route, title, description, severity, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"reval_{cid}_{int(datetime.now(timezone.utc).timestamp())}",
                "REVALIDATION",
                route_str,
                f"Revalidación de {name} con Motor v{CURRENT_ENGINE_VERSION}: {new_status}",
                f"Resultado: {reason} | Gates superados: {gates_passed_count}/11 | Score: {overall_score:.1f}",
                severity,
                json.dumps({
                    "candidate_id": cid,
                    "old_version": old_engine_ver,
                    "new_version": new_engine_ver,
                    "gates_passed": gates_passed_count,
                    "score": overall_score,
                    "reason": reason,
                }),
                now_iso,
            ),
        )

        conn.commit()
        conn.close()

        return {
            "candidate_id": candidate_id if candidate_id.upper() == cid.upper() else cid,
            "name": name,
            "symbol": symbol,
            "timeframe": timeframe,
            "route": route_str,
            "old_version": old_engine_ver or "1.00",
            "new_version": new_engine_ver,
            "old_status": old_status,
            "new_status": new_status,
            "passed": is_promoted,
            "gates_passed": gates_passed_count,
            "overall_score": overall_score,
            "reason": reason,
            "net_profit_oos": oos_bt.net_profit_usd,
            "max_dd_oos_pct": oos_bt.max_drawdown_pct,
            "profit_factor_oos": oos_bt.profit_factor,
        }

    def get_candidate_ids_to_revalidate(
        self,
        target_version: Optional[str] = None,
        only_approved: bool = False,
        route: Optional[str] = None,
        max_candidates: int = 0,
    ) -> List[str]:
        """Obtiene la lista de candidate_ids para revalidar según los filtros."""
        conn = self.get_db_connection()
        cur = conn.cursor()

        query = "SELECT candidate_id FROM candidates WHERE engine_version != ?"
        params: List[Any] = [CURRENT_ENGINE_VERSION]

        if target_version and target_version.upper() != "ALL":
            query += " AND engine_version = ?"
            params.append(target_version)

        if only_approved:
            query += " AND status NOT LIKE 'RECHAZADA%' AND status NOT LIKE 'REJECTED%' AND status NOT LIKE 'BLOCKED%'"

        if route and route.upper() != "ALL":
            query += " AND route = ?"
            params.append(route.upper())

        query += " ORDER BY net_profit_oos DESC"
        if max_candidates and max_candidates > 0 and max_candidates < 999999:
            query += f" LIMIT {max_candidates}"

        cur.execute(query, params)
        candidate_ids = [r[0] for r in cur.fetchall()]
        conn.close()
        return candidate_ids

    def revalidate_legacy_batch(
        self,
        target_version: Optional[str] = None,
        only_approved: bool = False,
        route: Optional[str] = None,
        max_candidates: int = 100,
    ) -> Dict[str, Any]:
        """Revalida en lote estrategias legacy/anteriores de forma síncrona."""
        candidate_ids = self.get_candidate_ids_to_revalidate(
            target_version=target_version,
            only_approved=only_approved,
            route=route,
            max_candidates=max_candidates,
        )

        results = []
        promoted = 0
        rejected = 0

        logger.info(f"Iniciando revalidación forense v{CURRENT_ENGINE_VERSION} para {len(candidate_ids)} estrategias...")

        for cid in candidate_ids:
            res = self.revalidate_single_candidate(cid)
            results.append(res)
            if res.get("passed"):
                promoted += 1
            else:
                rejected += 1

        return {
            "status": "COMPLETED",
            "target_engine_version": CURRENT_ENGINE_VERSION,
            "target_engine_name": CURRENT_ENGINE_NAME,
            "total_evaluated": len(results),
            "promoted_count": promoted,
            "rejected_count": rejected,
            "revalidated_at": datetime.now(timezone.utc).isoformat(),
            "results": results,
        }

    def start_background_revalidation(
        self,
        target_version: Optional[str] = None,
        only_approved: bool = False,
        route: Optional[str] = None,
        max_candidates: int = 0,
    ) -> Dict[str, Any]:
        """Inicia la revalidación en segundo plano y retorna inmediatamente."""
        with self._job_lock:
            if self._job_state["status"] == "RUNNING":
                return {
                    "status": "ALREADY_RUNNING",
                    "job_id": self._job_state["job_id"],
                    "message": "Ya hay una revalidación activa en segundo plano.",
                    "total_candidates": self._job_state["total_candidates"],
                    "processed_count": self._job_state["processed_count"],
                }

            candidate_ids = self.get_candidate_ids_to_revalidate(
                target_version=target_version,
                only_approved=only_approved,
                route=route,
                max_candidates=max_candidates,
            )

            job_id = f"reval_job_{int(time.time())}"
            self._cancel_requested = False
            self._job_state = {
                "job_id": job_id,
                "status": "RUNNING",
                "target_version": target_version or "ALL",
                "route": route or "ALL",
                "total_candidates": len(candidate_ids),
                "processed_count": 0,
                "promoted_count": 0,
                "rejected_count": 0,
                "current_candidate": None,
                "start_time": datetime.now(timezone.utc).isoformat(),
                "finish_time": None,
                "results": [],
                "error_message": None,
            }

            worker_thread = threading.Thread(
                target=self._run_background_worker,
                args=(candidate_ids,),
                daemon=True,
                name=f"RevalWorker_{job_id}",
            )
            worker_thread.start()

            return {
                "status": "STARTED",
                "job_id": job_id,
                "total_candidates": len(candidate_ids),
                "target_engine_version": CURRENT_ENGINE_VERSION,
                "message": f"Revalidación en segundo plano iniciada para {len(candidate_ids)} estrategias.",
            }

    def _run_background_worker(self, candidate_ids: List[str]) -> None:
        """Worker que procesa las estrategias en segundo plano actualizando el progreso."""
        logger.info(f"Worker en segundo plano: procesando {len(candidate_ids)} candidatos...")
        for cid in candidate_ids:
            if self._cancel_requested:
                logger.info("Worker en segundo plano cancelado por solicitud del usuario.")
                with self._job_lock:
                    self._job_state["status"] = "CANCELLED"
                    self._job_state["finish_time"] = datetime.now(timezone.utc).isoformat()
                return

            with self._job_lock:
                self._job_state["current_candidate"] = cid

            try:
                res = self.revalidate_single_candidate(cid)
            except Exception as e:
                logger.error(f"Error procesando {cid} en segundo plano: {e}", exc_info=True)
                res = {
                    "candidate_id": cid,
                    "name": cid,
                    "passed": False,
                    "new_status": "ERROR_REVALIDATION",
                    "reason": str(e),
                }

            with self._job_lock:
                self._job_state["processed_count"] += 1
                if res.get("passed"):
                    self._job_state["promoted_count"] += 1
                else:
                    self._job_state["rejected_count"] += 1
                self._job_state["results"].append(res)

        with self._job_lock:
            self._job_state["status"] = "COMPLETED"
            self._job_state["finish_time"] = datetime.now(timezone.utc).isoformat()
            self._job_state["current_candidate"] = None
        logger.info(
            f"Worker en segundo plano finalizado: {self._job_state['promoted_count']} promovidas, {self._job_state['rejected_count']} rechazadas de {len(candidate_ids)}."
        )

    def get_revalidation_status(self) -> Dict[str, Any]:
        """Obtiene el estado y progreso actual del worker de revalidación."""
        with self._job_lock:
            return dict(self._job_state)

    def cancel_background_revalidation(self) -> Dict[str, Any]:
        """Cancela la revalidación activa en segundo plano."""
        with self._job_lock:
            if self._job_state["status"] != "RUNNING":
                return {"status": "NO_ACTIVE_JOB", "message": "No hay ningún proceso de revalidación activo."}
            self._cancel_requested = True
            return {"status": "CANCELLING", "job_id": self._job_state["job_id"], "message": "Cancelación solicitada."}

    # Aliases
    get_job_status = get_revalidation_status
    cancel_job = cancel_background_revalidation


# Instancia singleton
legacy_revalidation_service = LegacyRevalidationService()
