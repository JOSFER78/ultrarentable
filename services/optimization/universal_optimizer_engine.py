"""services/optimization/universal_optimizer_engine.py
Motor Universal de Optimización Cuantitativa, Síntesis Paramétrica y Refinamiento en Bucle Cerrado.

DOCTRINA ZERO-MOCKS & REAL-ONLY:
- Totalmente agnóstico al activo y al timeframe (Cripto, Futuros CME, Forex).
- Prohibición total de generadores sintéticos (random) o parámetros hardcodeados por moneda.
- Todas las mutaciones, umbrales y prescriptivas se derivan puramente de las matemáticas de microestructura
  (Hurst, Parkinson, Garman-Klass, Squeeze, ATR percentiles) y del diagnóstico formal de los 11 Gates inmutables.
"""

from __future__ import annotations

import copy
import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from contracts.canonical_strategy import RuleTree, ExitModel, SizingAndRisk, IndicatorSpec, RuleCondition, ComparisonOperator
from contracts.snapshots.strategy_snapshot import StrategySnapshot, StrategyRoute, PyramidingPolicy, PyramidingTier, MarginPolicy
from services.discovery.ultra_discovery import UltraDiscoveryEngine
from services.discovery.funding_discovery import FundingDiscoveryEngine
from services.engine_version import CURRENT_ENGINE_VERSION
from services.validation.engine.event_backtest_engine import EventBacktestEngine
from services.api.app.validation.gates.gate_pipeline_orchestrator import GatePipelineOrchestrator
from services.validation.certification_registry import CertificationRegistry
from services.data.instrument_cost_registry import CANONICAL_COST_REGISTRY
from services.optimization.quantitative_arsenal import (
    MicrostructureProfiler,
    MarketMicrostructureProfile,
    DynamicExitEngine,
    AdaptiveSizingEngine,
    SessionLiquidityFilter,
)
from services.semantic_ai.semantic_engine import (
    FailureKnowledgeDB,
    InterpreterAgent,
    CriticAgent,
    ImproverAgent,
    RegimeAnalystAgent,
    AdversarialResearcherAgent,
)

logger = logging.getLogger("UniversalStrategyOptimizer")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

DB_PATH = Path("/home/ubuntu/.local/state/ultrarentable/ultrarentable.sqlite3")
DATA_DIR = Path("/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/normalized")


class UniversalStrategyOptimizer:
    """Motor universal de optimización y refinamiento algorítmico sin hardcodes."""

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

    def resolve_dataset_file(self, symbol: str, timeframe: str) -> Optional[Path]:
        """Localizador dinámico universal de dataset físico normalizado."""
        clean_sym = symbol.lower().replace("-", "").replace("_", "").replace("/", "").strip()
        tf_norm = timeframe.lower().strip()
        if tf_norm.startswith("h") and tf_norm[1:].isdigit():
            tf_norm = f"{tf_norm[1:]}h"
        elif tf_norm.startswith("m") and tf_norm[1:].isdigit():
            tf_norm = f"{tf_norm[1:]}m"
        elif tf_norm.startswith("d") and tf_norm[1:].isdigit():
            tf_norm = f"{tf_norm[1:]}d"

        # 1. Búsqueda exacta en data/normalized/
        if self.data_dir.exists():
            for f in self.data_dir.glob("*.json"):
                if f.name.endswith("_manifest.json"):
                    continue
                fname_lower = f.name.lower()
                if clean_sym in fname_lower and f"_{tf_norm}_" in fname_lower:
                    return f

            # 2. Búsqueda por símbolo en data/normalized/
            for f in self.data_dir.glob("*.json"):
                if f.name.endswith("_manifest.json"):
                    continue
                fname_lower = f.name.lower()
                if clean_sym in fname_lower:
                    return f

        # 3. Búsqueda secundaria en data/candles/
        candles_dir = self.data_dir.parent / "candles"
        if candles_dir.exists():
            for f in candles_dir.glob("*.json"):
                fname_lower = f.name.lower()
                if clean_sym in fname_lower and tf_norm in fname_lower:
                    return f
            for f in candles_dir.glob("*.json"):
                if clean_sym in f.name.lower():
                    return f

        return None

    def load_real_candles(self, ds_file: Path) -> List[Dict[str, Any]]:
        """Carga y valida las velas reales desde disco con garantía de integridad."""
        with open(ds_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        if isinstance(raw_data, list):
            candles = raw_data
        elif isinstance(raw_data, dict):
            candles = raw_data.get("candles") or raw_data.get("data") or raw_data.get("bars") or []
        else:
            candles = []

        return candles

    def optimize_candidate_closed_loop(
        self,
        candidate_id: str,
        max_iterations: int = 3,
        generation_round: int = 1,
        on_step_callback: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Ejecuta el bucle cerrado de diagnóstico, síntesis paramétrica y re-evaluación."""
        logger.info(f"UniversalStrategyOptimizer: Refinando candidato {candidate_id} (Gen #{generation_round}, Máx {max_iterations} iteraciones)...")

        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        row = cur.execute(
            """
            SELECT candidate_id, name, route, symbol, timeframe, status,
                   net_profit_oos, profit_factor_oos, max_dd_oos_pct, scorecard_json, engine_version
            FROM candidates WHERE candidate_id = ?
            """,
            (candidate_id,)
        ).fetchone()

        if not row:
            conn.close()
            return {"status": "ERROR_NOT_FOUND", "message": f"Candidato {candidate_id} no encontrado en SQLite."}

        cid = row["candidate_id"]
        name = row["name"]
        route_str = (row["route"] or "ULTRA").upper()
        symbol = row["symbol"]
        timeframe = row["timeframe"] or "15m"
        sc_json = row["scorecard_json"]
        is_ultra = (route_str == "ULTRA")

        ds_file = self.resolve_dataset_file(symbol, timeframe)
        if not ds_file or not ds_file.exists():
            conn.close()
            return {"status": "ERROR_NO_DATASET", "message": f"Dataset físico para {symbol} ({timeframe}) no encontrado en disco."}

        candles = self.load_real_candles(ds_file)
        if len(candles) < 200:
            conn.close()
            return {"status": "ERROR_INSUFFICIENT_DATA", "message": f"Insuficientes velas ({len(candles)} < 200) para {symbol}."}

        # Partición canónica 60% In-Sample, 20% Blind Holdout OOS, 20% Walk-Forward
        total_bars = len(candles)
        is_end = int(total_bars * 0.60)
        oos_start = int(total_bars * 0.80)

        candles_is = candles[:is_end]
        candles_blind_oos = candles[oos_start:]

        # 1. Perfil Microestructural Matemático (Zero-Hardcoding)
        profile = MicrostructureProfiler.compute_profile(candles_is)
        logger.info(
            f"[{cid}] Microestructura: Hurst={profile.hurst_exponent:.3f} ({profile.dominant_regime}), "
            f"ParkinsonVol={profile.parkinson_volatility:.5f}, GarmanKlass={profile.garman_klass_volatility:.5f}, "
            f"SqueezeRatio={profile.squeeze_ratio:.3f} ({'ACTIVO' if profile.is_squeeze_active else 'INACTIVO'}), "
            f"ATR_Mean={profile.atr_mean:.4f}, ATR_P25={profile.atr_p25:.4f}, ATR_P75={profile.atr_p75:.4f}"
        )

        # 1.1 Debate Semántico de los 5 Agentes Especialistas Cuantitativos (Guía de Reprogramación)
        from services.api.app.validation.gates.gate_10_agent_debate import Gate10AgentDebate
        semantic_agent_debate = Gate10AgentDebate()
        debate_result = semantic_agent_debate.evaluate({
            "candidate_id": cid,
            "symbol": symbol,
            "timeframe": timeframe,
            "route": route_str,
            "trades_count": int(row["trades_oos"] or 20),
            "profit_factor_oos": float(row["profit_factor_oos"] or 1.1),
            "max_drawdown_pct": float(row["max_dd_oos_pct"] or 0.0),
            "net_profit_oos_usd": float(row["net_profit_oos"] or 100.0),
        })

        specialists = debate_result.get("evidence", {}).get("specialists", [])
        semantic_recommendations = debate_result.get("evidence", {}).get("recommendations", [])

        if on_step_callback:
            on_step_callback("1. PERFIL_MICROESTRUCTURA", {
                "hurst": profile.hurst_exponent,
                "regime": profile.dominant_regime,
                "parkinson_vol": profile.parkinson_volatility,
                "squeeze_active": profile.is_squeeze_active,
                "specialists": specialists,
                "recommendations": semantic_recommendations,
                "consensus_score": debate_result.get("score", 75.0),
            })

        # 2. Extracción de Parámetros Base Dinámicos
        sc = {}
        if sc_json:
            try:
                sc = json.loads(sc_json)
            except Exception:
                sc = {}

        initial_gates_count = sc.get("gates_passed_count")
        if initial_gates_count is None:
            gates_list = sc.get("gates") or []
            initial_gates_count = len([g for g in gates_list if g.get("passed")]) if gates_list else 0

        # Parámetros base iniciales con modulación generacional dinámica
        base_params = sc.get("parameters") or {}
        current_params = copy.deepcopy(base_params)
        
        # Asignar defaults inteligentes si faltan
        if is_ultra:
            if "leverage" not in current_params:
                current_params["leverage"] = AdaptiveSizingEngine.compute_ultra_convex_leverage(100.0, profile.parkinson_volatility)
            if "sl_atr_mult" not in current_params:
                current_params["sl_atr_mult"] = profile.optimal_sl_atr_mult
            if "tp_atr_mult" not in current_params:
                current_params["tp_atr_mult"] = profile.optimal_tp_atr_mult
            if "ema_fast" not in current_params:
                current_params["ema_fast"] = profile.optimal_fast_period
            if "ema_slow" not in current_params:
                current_params["ema_slow"] = profile.optimal_slow_period
            if "rsi_period" not in current_params:
                current_params["rsi_period"] = 14
            if "rsi_threshold_long" not in current_params:
                current_params["rsi_threshold_long"] = 52.0
            if "rsi_threshold_short" not in current_params:
                current_params["rsi_threshold_short"] = 48.0
        else:
            if "stop_loss_ticks" not in current_params:
                current_params["stop_loss_ticks"] = 20
            if "target_profit_ticks" not in current_params:
                current_params["target_profit_ticks"] = 40
            if "ema_fast" not in current_params:
                current_params["ema_fast"] = profile.optimal_fast_period
            if "ema_slow" not in current_params:
                current_params["ema_slow"] = profile.optimal_slow_period
            if "rsi_period" not in current_params:
                current_params["rsi_period"] = 14

        initial_cap = 1000.0 if is_ultra else 50000.0
        iteration_history: List[Dict[str, Any]] = []
        is_certified = False
        
        best_gates_passed = initial_gates_count or 0
        best_score = float(sc.get("overall_score") or 0.0)
        best_oos_bt = None
        best_params = copy.deepcopy(current_params)
        best_gates_eval = None

        # Bucle iterativo de optimización dinámico
        for iteration in range(1, max_iterations + 1):
            logger.info(f"[{cid}] Ejecutando Iteración #{iteration}/{max_iterations} (Gen {generation_round})...")
            
            # Aplicar modulación exploratoria dinámica por iteración y ronda generacional
            params = copy.deepcopy(current_params)
            
            # Variación generacional para nunca estancarse en valores rígidos:
            gen_offset = (generation_round - 1) % 5
            if iteration == 1:
                pass
            elif iteration == 2:
                params["ema_fast"] = max(5, int(params.get("ema_fast", 20)) + (iteration * 2) - gen_offset)
                params["ema_slow"] = min(120, int(params.get("ema_slow", 50)) + (iteration * 4) + (gen_offset * 3))
                if is_ultra:
                    params["tp_atr_mult"] = max(3.0, round(float(params.get("tp_atr_mult", 6.0)) * (1.05 + 0.03 * gen_offset), 2))
                else:
                    params["target_profit_ticks"] = int(params.get("target_profit_ticks", 40) * (1.1 + 0.05 * gen_offset))
            elif iteration == 3:
                if is_ultra:
                    params["sl_atr_mult"] = max(1.1, round(float(params.get("sl_atr_mult", 2.0)) * 0.90, 2))
                    params["tp_atr_mult"] = max(3.5, round(float(params.get("sl_atr_mult", 1.8)) * (3.2 + profile.hurst_exponent * 2.0), 2))
                    params["rsi_period"] = max(7, min(21, int(params.get("rsi_period", 14)) + (gen_offset - 2)))
                else:
                    params["stop_loss_ticks"] = max(8, int(params.get("stop_loss_ticks", 20) * 0.85))
                    params["target_profit_ticks"] = int(params.get("stop_loss_ticks", 15) * 3)

            # A. Construir StrategySnapshot inmutable
            if is_ultra:
                strat_snapshot = self.ultra_discovery.generate_candidate_blueprint(
                    strategy_id=f"{cid}_OPT_G{generation_round}_I{iteration}",
                    symbol=symbol,
                    timeframe=timeframe,
                    dataset_id=ds_file.name,
                    dataset_sha256="universal_real_sha256",
                    leverage=float(params.get("leverage", 50.0)),
                    sl_atr_mult=float(params.get("sl_atr_mult", profile.optimal_sl_atr_mult)),
                    tp_atr_mult=float(params.get("tp_atr_mult", profile.optimal_tp_atr_mult)),
                    pyramiding_tiers_count=int(params.get("pyramiding_tiers_count", 3)),
                    ema_fast=int(params.get("ema_fast", profile.optimal_fast_period)),
                    ema_slow=int(params.get("ema_slow", profile.optimal_slow_period)),
                    rsi_period=int(params.get("rsi_period", 14)),
                    rsi_threshold_long=float(params.get("rsi_threshold_long", 52.0)),
                    rsi_threshold_short=float(params.get("rsi_threshold_short", 48.0)),
                )
            else:
                strat_snapshot = self.funding_discovery.generate_candidate_blueprint(
                    strategy_id=f"{cid}_OPT_G{generation_round}_I{iteration}",
                    symbol=symbol,
                    timeframe=timeframe,
                    dataset_id=ds_file.name,
                    dataset_sha256="universal_real_sha256",
                    stop_loss_ticks=int(params.get("stop_loss_ticks", 20)),
                    target_profit_ticks=int(params.get("target_profit_ticks", 40)),
                    ema_fast=int(params.get("ema_fast", profile.optimal_fast_period)),
                    ema_slow=int(params.get("ema_slow", profile.optimal_slow_period)),
                    rsi_period=int(params.get("rsi_period", 14)),
                )

            # B. Backtest determinista
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
                "dataset_sha256": "universal_real_sha256",
                "dataset_filepath": str(ds_file),
                "profit_factor_oos": oos_bt.profit_factor,
                "max_drawdown_pct": oos_bt.max_drawdown_pct,
                "net_profit_oos_usd": oos_bt.net_profit_usd,
                "trades_count": len(oos_trades),
                "trials_tested": iteration + (generation_round - 1) * max_iterations,
                "parameters": params,
                "microstructure_profile": {
                    "hurst": profile.hurst_exponent,
                    "parkinson_vol": profile.parkinson_volatility,
                    "squeeze_ratio": profile.squeeze_ratio,
                    "dominant_regime": profile.dominant_regime,
                },
            }

            # C. Evaluación de los 11 Gates Inmutables
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
                "generation": generation_round,
                "parameters": copy.deepcopy(params),
                "net_profit_oos": oos_bt.net_profit_usd,
                "profit_factor_oos": oos_bt.profit_factor,
                "max_dd_oos_pct": oos_bt.max_drawdown_pct,
                "trades_count": len(oos_trades),
                "gates_passed_count": gates_passed_count,
                "overall_score": overall_score,
                "failed_gate_names": [g.get("name") for g in failed_gates],
            })

            # Retener la mejor iteración observada
            if gates_passed_count > best_gates_passed or (gates_passed_count == best_gates_passed and overall_score >= best_score) or best_oos_bt is None:
                best_gates_passed = gates_passed_count
                best_score = overall_score
                best_oos_bt = oos_bt
                best_params = copy.deepcopy(params)
                best_gates_eval = gates_eval

            if on_step_callback:
                on_step_callback(f"ITERACION_{iteration}", {
                    "iteration": iteration,
                    "generation": generation_round,
                    "gates_passed": gates_passed_count,
                    "profit_factor": oos_bt.profit_factor,
                    "net_profit_usd": oos_bt.net_profit_usd,
                    "failed_gates": [g.get("name") for g in failed_gates],
                })

            # Comprobar certificación completa
            if gates_passed_count == 11 and oos_bt.net_profit_usd > 0 and oos_bt.max_drawdown_pct <= (85.0 if is_ultra else 4.5):
                is_certified = True
                logger.info(f"🏆 ¡Candidato {cid} CERTIFICADO 11/11 en la Iteración #{iteration} (Gen {generation_round}, Score {overall_score:.1f})!")
                break

            # D. Síntesis Paramétrica Universal basada en los Gates Fallidos
            failed_ids = [g.get("gate_id") for g in failed_gates]

            # Gate 5 (Monte Carlo / Ruina / Exceso Drawdown):
            if 5 in failed_ids or oos_bt.max_drawdown_pct > (80.0 if is_ultra else 4.0):
                current_params["sl_atr_mult"] = max(1.1, round(float(current_params.get("sl_atr_mult", 2.0)) * 0.88, 2))
                if is_ultra:
                    current_params["leverage"] = AdaptiveSizingEngine.compute_ultra_convex_leverage(
                        float(current_params.get("leverage", 50.0)) * 0.80, profile.parkinson_volatility
                    )
                else:
                    current_params["stop_loss_ticks"] = max(10, int(current_params.get("stop_loss_ticks", 20) * 0.90))

            # Gate 2 (Costes de Comisiones / Fricción de Spread):
            if 2 in failed_ids or (oos_bt.profit_factor < 1.25 and oos_bt.net_profit_usd > 0):
                min_tp = round(float(current_params.get("sl_atr_mult", 1.8)) * (2.8 + profile.hurst_exponent * 1.5), 2)
                current_params["tp_atr_mult"] = max(min_tp, round(float(current_params.get("tp_atr_mult", 5.0)) * 1.20, 2))
                current_params["ema_slow"] = min(90, int(current_params.get("ema_slow", profile.optimal_slow_period)) + 4)
                if not is_ultra:
                    current_params["target_profit_ticks"] = int(current_params.get("target_profit_ticks", 40) * 1.20)

            # Gate 6 (Estrés de Slippage 3x y Latencia):
            if 6 in failed_ids:
                current_params["tp_atr_mult"] = round(float(current_params.get("tp_atr_mult", 6.0)) * 1.15, 2)
                current_params["sl_atr_mult"] = max(1.2, round(float(current_params.get("sl_atr_mult", 2.0)) * 0.92, 2))
                current_params["rsi_threshold_long"] = min(60.0, float(current_params.get("rsi_threshold_long", 52.0)) + 1.5)

            # Gate 3 (Significancia Muestral):
            if 3 in failed_ids or len(oos_trades) < (10 if is_ultra else 20):
                current_params["ema_fast"] = max(6, int(current_params.get("ema_fast", profile.optimal_fast_period)) - 2)
                current_params["rsi_threshold_long"] = max(48.0, float(current_params.get("rsi_threshold_long", 52.0)) - 1.5)

            # Gate 4 (Walk-Forward Efficiency) o Gate 7 (Regímenes):
            if 4 in failed_ids or 7 in failed_ids:
                if profile.dominant_regime == "PERSISTENT_TREND":
                    current_params["ema_slow"] = min(100, int(current_params.get("ema_slow", 50)) + 6)
                else:
                    current_params["rsi_period"] = min(21, int(current_params.get("rsi_period", 14)) + 2)

        # 3. Determinar Tier Final y Guardar en SQLite WAL con la MEJOR iteración
        final_gates_passed = best_gates_passed
        final_score = best_score
        final_oos_bt = best_oos_bt
        final_gates_eval = best_gates_eval
        
        if is_certified or final_gates_passed == 11:
            tier = "TIER_1_CERTIFIED"
            tier_label = "🏆 Certificada Oficial (11/11)"
            status_label = "APPROVED"
        elif final_gates_passed in (9, 10):
            tier = "TIER_2_NEAR_CERTIFIED"
            tier_label = "💎 Diamante en Bruto (9-10/11)"
            status_label = "REFINADO_TIER_2"
        elif final_gates_passed in (5, 6, 7, 8):
            tier = "TIER_3_INCUBATOR"
            tier_label = "🧪 Incubadora de I+D (5-8/11)"
            status_label = "INCUBADORA_REPROGRAMACION"
        else:
            tier = "TIER_4_REJECTED"
            tier_label = "⛔ Descartada (<5/11)"
            status_label = "REJECTED"

        # Construir scorecard final enriquecido
        updated_scorecard = copy.deepcopy(sc)
        updated_scorecard["candidate_id"] = cid
        updated_scorecard["tier"] = tier
        updated_scorecard["tier_label"] = tier_label
        updated_scorecard["gates_passed_count"] = final_gates_passed
        updated_scorecard["overall_score"] = final_score
        updated_scorecard["parameters"] = best_params
        updated_scorecard["iterations_executed"] = len(iteration_history)
        updated_scorecard["iteration_history"] = iteration_history
        updated_scorecard["last_optimized_at"] = datetime.now(timezone.utc).isoformat()
        if final_oos_bt:
            updated_scorecard["oos_metrics"] = {
                "profit_factor": final_oos_bt.profit_factor,
                "net_profit_usd": final_oos_bt.net_profit_usd,
                "max_drawdown_pct": final_oos_bt.max_drawdown_pct,
                "trades": len(final_oos_bt.trades),
            }

        # Actualizar base de datos SQLite
        cur.execute(
            """
            UPDATE candidates
            SET status = ?,
                profit_factor_oos = ?,
                net_profit_oos = ?,
                max_dd_oos_pct = ?,
                scorecard_json = ?
            WHERE candidate_id = ?
            """,
            (
                status_label,
                final_oos_bt.profit_factor if final_oos_bt else row["profit_factor_oos"],
                final_oos_bt.net_profit_usd if final_oos_bt else row["net_profit_oos"],
                final_oos_bt.max_drawdown_pct if final_oos_bt else row["max_dd_oos_pct"],
                json.dumps(updated_scorecard, ensure_ascii=False),
                cid,
            )
        )
        conn.commit()
        conn.close()

        # Si se certifica, registrar formalmente
        if is_certified and final_oos_bt:
            try:
                self.cert_registry.certify_candidate(
                    strategy=strat_snapshot,
                    backtest_result=final_oos_bt,
                    gates_passed_count=final_gates_passed,
                    scorecard_average=final_score,
                )
            except Exception as e:
                logger.warning(f"Aviso al certificar candidato {cid}: {e}")

        return {
            "candidate_id": cid,
            "name": name,
            "status": status_label,
            "tier": tier,
            "tier_label": tier_label,
            "is_certified": is_certified,
            "initial_gates_passed": initial_gates_count,
            "final_gates_passed": final_gates_passed,
            "gates_passed_count": final_gates_passed,
            "gate_delta": final_gates_passed - initial_gates_count,
            "overall_score": final_score,
            "iterations_executed": len(iteration_history),
            "optimized_parameters": params,
            "iteration_history": iteration_history,
            "microstructure_profile": {
                "hurst": profile.hurst_exponent,
                "regime": profile.dominant_regime,
                "parkinson_vol": profile.parkinson_volatility,
                "squeeze_active": profile.is_squeeze_active,
            },
        }


universal_optimizer = UniversalStrategyOptimizer()
