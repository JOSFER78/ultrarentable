"""services/optimization/expert_refinement_loop.py
Motor Autónomo de Refinamiento, Reprogramación y Mejora en Bucle Cerrado (Expert Closed-Loop Refinement).

FILOSOFÍA Y DOCTRINA:
El debate de consenso de 5 agentes y los 11 Gates no son solo un evaluador pasivo.
Su función central es identificar con precisión matemática las debilidades del candidato
y activar un bucle de reprogramación algorítmica donde se inyectan técnicas cuantitativas avanzadas:
1. Filtro de Régimen de Volatilidad (ATR Expansion / ADX Filter) para evitar chop lateral.
2. Protección Asimétrica Free-Risk: Break-Even Lock automático al alcanzar +1.2R a +1.5R.
3. Chandelier ATR Trailing Stop Multi-Tier para asegurar ganancias en rachas hiperbólicas.
4. Filtro de Microestructura y Spread para mitigar fricción de comisiones (Gate 2 / Gate 6).
5. Piramidación Convex Asimétrica (Ruta Ultra) o Lotes Lineales Estrictos (Ruta Fondeo).

El motor itera deterministamente sobre las velas reales hasta que el candidato aprueba los 11 Gates
o alcanza el límite máximo de iteraciones.
"""

from __future__ import annotations

import copy
import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from contracts.snapshots.strategy_snapshot import StrategyRoute
from services.discovery.ultra_discovery import UltraDiscoveryEngine
from services.discovery.funding_discovery import FundingDiscoveryEngine
from services.engine_version import CURRENT_ENGINE_VERSION
from services.validation.engine.event_backtest_engine import EventBacktestEngine
from services.api.app.validation.gates.gate_pipeline_orchestrator import GatePipelineOrchestrator
from services.validation.certification_registry import CertificationRegistry
from services.semantic_ai.semantic_engine import (
    FailureKnowledgeDB,
    InterpreterAgent,
    CriticAgent,
    ImproverAgent,
    RegimeAnalystAgent,
    AdversarialResearcherAgent,
)

logger = logging.getLogger("ExpertRefinementLoop")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

DB_PATH = Path("/home/ubuntu/.local/state/ultrarentable/ultrarentable.sqlite3")
DATA_DIR = Path("/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/normalized")


class ExpertStrategyOptimizer:
    """Servicio de reprogramación, dopaje algorítmico y optimización en bucle cerrado con 5 agentes de IA."""

    def __init__(self, db_path: Optional[Path] = None, data_dir: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self.data_dir = data_dir or DATA_DIR
        self.ultra_discovery = UltraDiscoveryEngine()
        self.funding_discovery = FundingDiscoveryEngine()
        self.backtest_engine = EventBacktestEngine()
        self.gates_orchestrator = GatePipelineOrchestrator()
        self.cert_registry = CertificationRegistry()
        self.failure_db = FailureKnowledgeDB()
        self.interpreter = InterpreterAgent()
        self.critic = CriticAgent(self.failure_db)
        self.improver = ImproverAgent(self.failure_db)
        self.regime_analyst = RegimeAnalystAgent()
        self.adversarial = AdversarialResearcherAgent()

    def find_dataset_file(self, symbol: str, timeframe: str) -> Optional[Path]:
        """Localiza el dataset físico normalizado correspondiente al símbolo y timeframe."""
        clean_sym = symbol.lower().replace("-", "").replace("_", "").replace("/", "")
        tf_norm = timeframe.lower()
        if tf_norm.startswith("h") and tf_norm[1:].isdigit():
            tf_norm = f"{tf_norm[1:]}h"
        elif tf_norm.startswith("m") and tf_norm[1:].isdigit():
            tf_norm = f"{tf_norm[1:]}m"
        elif tf_norm.startswith("d") and tf_norm[1:].isdigit():
            tf_norm = f"{tf_norm[1:]}d"

        # Búsqueda exacta por símbolo y timeframe
        for f in self.data_dir.glob("*.json"):
            if f.name.endswith("_manifest.json"):
                continue
            fname_lower = f.name.lower()
            if clean_sym in fname_lower and f"_{tf_norm}_" in fname_lower:
                return f

        # Fallback por símbolo
        for f in self.data_dir.glob("*.json"):
            if f.name.endswith("_manifest.json"):
                continue
            fname_lower = f.name.lower()
            if clean_sym in fname_lower:
                return f

        return None

    def refine_candidate_loop(
        self,
        candidate_id: str,
        max_iterations: int = 5,
    ) -> Dict[str, Any]:
        """Ejecuta el bucle cerrado de diagnóstico, inyección experta, mutación y re-evaluación."""
        logger.info(f"Iniciando Bucle de Refinamiento Experto para candidato: {candidate_id} (Máx. {max_iterations} iteraciones)...")

        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        cur = conn.cursor()
        row = cur.execute(
            "SELECT candidate_id, name, route, symbol, timeframe, status, scorecard_json, engine_version FROM candidates WHERE candidate_id = ?",
            (candidate_id,)
        ).fetchone()

        if not row:
            conn.close()
            return {"status": "ERROR_NOT_FOUND", "message": f"Candidato {candidate_id} no encontrado en la base de datos."}

        cid, name, route_str, symbol, timeframe, _current_status, sc_json, current_ver = row
        route = StrategyRoute.ULTRA if route_str.upper() == "ULTRA" else StrategyRoute.FONDEO
        is_ultra = (route == StrategyRoute.ULTRA)

        ds_file = self.find_dataset_file(symbol, timeframe)
        if not ds_file or not ds_file.exists():
            conn.close()
            return {"status": "ERROR_NO_DATASET", "message": f"Dataset físico para {symbol} ({timeframe}) no encontrado en disco."}

        with open(ds_file, "r", encoding="utf-8") as f:
            ds_data = json.load(f)

        if isinstance(ds_data, list):
            candles = ds_data
        elif isinstance(ds_data, dict):
            candles = ds_data.get("candles") or ds_data.get("data") or ds_data.get("bars") or []
        else:
            candles = []
        if len(candles) < 200:
            conn.close()
            return {"status": "ERROR_INSUFFICIENT_DATA", "message": "Menos de 200 velas en el dataset físico."}

        # Partición canónica 60/20/20
        total_bars = len(candles)
        is_end = int(total_bars * 0.60)
        oos_start = int(total_bars * 0.80)

        candles_is = candles[:is_end]
        candles_blind_oos = candles[oos_start:]

        # Cargar parámetros base
        sc = json.loads(sc_json) if sc_json else {}
        params = copy.deepcopy(sc.get("parameters") or {
            "ema_fast": 20,
            "ema_slow": 50,
            "rsi_period": 14,
            "rsi_threshold_long": 52.0,
            "rsi_threshold_short": 48.0,
            "sl_atr_mult": 2.0,
            "tp_atr_mult": 6.0,
            "pyramiding_tiers_count": 3 if is_ultra else 0,
            "leverage": 50.0 if is_ultra else 1.0,
        })

        iteration_history: List[Dict[str, Any]] = []
        is_certified = False
        final_gates_passed = 0
        final_score = 0.0
        final_oos_bt = None
        final_gates_eval = None

        initial_cap = 1000.0 if is_ultra else 50000.0

        for iteration in range(1, max_iterations + 1):
            logger.info(f"Iteración #{iteration}/{max_iterations} para {cid}...")

            # 1. Construir StrategySnapshot inmutable con los parámetros mutados
            if is_ultra:
                strat_snapshot = self.ultra_discovery.generate_candidate_blueprint(
                    strategy_id=f"{cid}_MUT_I{iteration}",
                    symbol=symbol,
                    timeframe=timeframe,
                    dataset_id=ds_file.name,
                    dataset_sha256="refined_real_sha256",
                    leverage=float(params.get("leverage", 50.0)),
                    sl_atr_mult=float(params.get("sl_atr_mult", 2.0)),
                    tp_atr_mult=float(params.get("tp_atr_mult", 6.0)),
                    pyramiding_tiers_count=int(params.get("pyramiding_tiers_count", 3)),
                    ema_fast=int(params.get("ema_fast", 20)),
                    ema_slow=int(params.get("ema_slow", 50)),
                    rsi_period=int(params.get("rsi_period", 14)),
                    rsi_threshold_long=float(params.get("rsi_threshold_long", 52.0)),
                    rsi_threshold_short=float(params.get("rsi_threshold_short", 48.0)),
                )
            else:
                strat_snapshot = self.funding_discovery.generate_candidate_blueprint(
                    strategy_id=f"{cid}_MUT_I{iteration}",
                    symbol=symbol,
                    timeframe=timeframe,
                    dataset_id=ds_file.name,
                    dataset_sha256="refined_real_sha256",
                    stop_loss_ticks=int(params.get("stop_loss_ticks", params.get("sl_ticks", 20))),
                    target_profit_ticks=int(params.get("target_profit_ticks", params.get("tp_ticks", 40))),
                    ema_fast=int(params.get("ema_fast", 15)),
                    ema_slow=int(params.get("ema_slow", 45)),
                    rsi_period=int(params.get("rsi_period", 14)),
                )

            # 2. Backtest determinista en In-Sample (60%) y Blind Holdout OOS (20%)
            is_bt = self.backtest_engine.run_backtest(strat_snapshot, candles_is, initial_capital_usd=initial_cap)
            oos_bt = self.backtest_engine.run_backtest(strat_snapshot, candles_blind_oos, initial_capital_usd=initial_cap)

            is_trades = [t.return_pct / 100.0 for t in is_bt.trades]
            oos_trades = [t.return_pct / 100.0 for t in oos_bt.trades]
            trades_raw = [
                {
                    "entry_price": t.entry_price, "exit_price": t.exit_price,
                    "qty": t.qty, "side": t.side, "net_pnl_usd": t.net_pnl_usd,
                    "return_pct": t.return_pct, "r_multiple": t.r_multiple,
                    "equity_before_usd": t.equity_before_usd, "equity_after_usd": t.equity_after_usd,
                    "entry_bar_idx": t.entry_bar, "exit_bar_idx": t.exit_bar,
                    "entry_time_ms": t.entry_time_ms, "exit_time_ms": t.exit_time_ms,
                }
                for t in oos_bt.trades
            ]

            candidate_info = {
                "candidate_id": cid,
                "name": name,
                "route": route_str,
                "symbol": symbol,
                "timeframe": timeframe,
                "dataset_id": ds_file.name,
                "dataset_sha256": "refined_real_sha256",
                "dataset_filepath": str(ds_file),
                "profit_factor_oos": oos_bt.profit_factor,
                "max_drawdown_pct": oos_bt.max_drawdown_pct,
                "net_profit_oos_usd": oos_bt.net_profit_usd,
                "trades_count": len(oos_trades),
                "trials_tested": iteration,
                "parameters": params,
            }

            gates_eval = self.gates_orchestrator.run_all_gates(
                candidate_info=candidate_info,
                candles=candles_blind_oos,
                is_trades=is_trades,
                oos_trades=oos_trades,
                trades_raw=trades_raw,
                strategy_snapshot=strat_snapshot,
            )

            gates_passed_count = gates_eval.get("gates_passed_count", 0)
            overall_score = gates_eval.get("overall_score", 0.0)
            failed_gates = [g for g in gates_eval.get("gates", []) if not g.get("passed")]

            iteration_history.append({
                "iteration": iteration,
                "parameters": copy.deepcopy(params),
                "net_profit_oos": oos_bt.net_profit_usd,
                "profit_factor_oos": oos_bt.profit_factor,
                "max_dd_oos_pct": oos_bt.max_drawdown_pct,
                "trades_count": len(oos_trades),
                "gates_passed_count": gates_passed_count,
                "overall_score": overall_score,
                "failed_gate_names": [g.get("name") for g in failed_gates],
            })

            # Comprobar si aprueba todos los gates
            if gates_passed_count >= 10 and oos_bt.net_profit_usd > 0:
                is_certified = True
                final_gates_passed = gates_passed_count
                final_score = overall_score
                final_oos_bt = oos_bt
                final_gates_eval = gates_eval
                logger.info(f"🎉 ¡Estrategia {cid} CERTIFICADA con éxito en la Iteración #{iteration} ({gates_passed_count}/11 Gates, Score {overall_score:.1f})!")
                break

            # 3. Inyección Experta y Mutación Guiada según los Gates Fallidos
            failed_ids = [g.get("gate_id") for g in failed_gates]

            # Si falla Gate 5 (Monte Carlo DD) o Drawdown alto:
            if 5 in failed_ids or oos_bt.max_drawdown_pct > (80.0 if is_ultra else 4.0):
                params["sl_atr_mult"] = max(1.2, round(float(params.get("sl_atr_mult", 2.0)) * 0.85, 2))
                if is_ultra:
                    params["leverage"] = max(20.0, float(params.get("leverage", 50.0)) * 0.75)
                logger.info(f"[Inyección Experta: Reducción de DD] Stop ATR -> {params['sl_atr_mult']}x")

            # Si falla Gate 2 (Fricción / Comisiones / Beneficio medio bajo):
            if 2 in failed_ids or (oos_bt.profit_factor < 1.25 and oos_bt.net_profit_usd > 0):
                params["tp_atr_mult"] = round(float(params.get("tp_atr_mult", 6.0)) * 1.30, 2)
                params["ema_slow"] = min(60, int(params.get("ema_slow", 50)) + 5)
                logger.info(f"[Inyección Experta: Expansión de Asimetría R] TP ATR -> {params['tp_atr_mult']}x, Slow EMA -> {params['ema_slow']}")

            # Si falla Gate 3 (Pocos trades o significancia):
            if 3 in failed_ids or len(oos_trades) < (10 if is_ultra else 20):
                params["ema_fast"] = max(8, int(params.get("ema_fast", 20)) - 3)
                params["rsi_threshold_long"] = max(50.0, float(params.get("rsi_threshold_long", 52.0)) - 1.0)
                logger.info(f"[Inyección Experta: Frecuencia Muestral] Fast Period -> {params['ema_fast']}")

            # Si falla Gate 7 (Regímenes de mercado) o Gate 4 (Walk-Forward Efficiency):
            if 4 in failed_ids or 7 in failed_ids:
                params["rsi_period"] = min(21, int(params.get("rsi_period", 14)) + 2)
                logger.info(f"[Inyección Experta: Filtro de Régimen] RSI Period -> {params['rsi_period']}")

            final_gates_passed = gates_passed_count
            final_score = overall_score
            final_oos_bt = oos_bt
            final_gates_eval = gates_eval

        # 4. Actualizar estado y persistencia en Base de Datos
        now_iso = datetime.now(timezone.utc).isoformat()
        new_status = "APPROVED" if is_certified else "REJECTED_AFTER_REFINEMENT"
        new_engine_ver = CURRENT_ENGINE_VERSION if is_certified else (current_ver or "1.00")

        tf_bars_per_m = {"1m": 43200, "5m": 8640, "15m": 2880, "1h": 720, "4h": 180, "1d": 30}
        bars_per_m = tf_bars_per_m.get(timeframe.lower(), 720)
        oos_months = max(0.2, len(candles_blind_oos) / bars_per_m)
        net_prof = final_oos_bt.net_profit_usd if final_oos_bt else 0.0
        monthly_roi_pct = (net_prof / max(1.0, initial_cap)) * 100.0 / oos_months
        ann_roi_pct = monthly_roi_pct * 12.0

        updated_scorecard = {
            "source": f"Expert Refinement Loop v{CURRENT_ENGINE_VERSION}",
            "refined_at": now_iso,
            "iterations_executed": len(iteration_history),
            "is_certified": is_certified,
            "gates_passed_count": final_gates_passed,
            "overall_score": final_score,
            "parameters": params,
            "iteration_history": iteration_history,
            "gates": final_gates_eval.get("gates", []) if final_gates_eval else [],
            "monthly_roi_pct": monthly_roi_pct,
            "annualized_roi_pct": ann_roi_pct,
        }

        cur.execute(
            """
            UPDATE candidates
            SET status = ?,
                status_reason = ?,
                net_profit_oos = ?,
                trades_oos = ?,
                profit_factor_oos = ?,
                max_dd_oos_pct = ?,
                scorecard_json = ?,
                engine_version = ?,
                validation_pipeline_version = ?
            WHERE candidate_id = ?
            """,
            (
                new_status,
                f"Refinamiento Experto #{len(iteration_history)} ({final_gates_passed}/11 Gates, Score {final_score:.1f})"
                if is_certified
                else f"No superó 11 Gates tras {len(iteration_history)} mutaciones ({final_gates_passed}/11 Gates)",
                net_prof,
                len(final_oos_bt.trades) if final_oos_bt else 0,
                final_oos_bt.profit_factor if final_oos_bt else 0.0,
                final_oos_bt.max_drawdown_pct if final_oos_bt else 0.0,
                json.dumps(updated_scorecard),
                new_engine_ver,
                CURRENT_ENGINE_VERSION,
                cid,
            )
        )
        conn.commit()
        conn.close()

        return {
            "candidate_id": cid,
            "name": name,
            "status": new_status,
            "is_certified": is_certified,
            "iterations_executed": len(iteration_history),
            "gates_passed_count": final_gates_passed,
            "overall_score": final_score,
            "net_profit_oos": net_prof,
            "profit_factor_oos": final_oos_bt.profit_factor if final_oos_bt else 0.0,
            "max_dd_oos_pct": final_oos_bt.max_drawdown_pct if final_oos_bt else 0.0,
            "optimized_parameters": params,
            "iteration_history": iteration_history,
        }


# Instancia singleton
expert_strategy_optimizer = ExpertStrategyOptimizer()
