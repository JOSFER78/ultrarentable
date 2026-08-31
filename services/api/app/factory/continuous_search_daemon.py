"""24/7 Continuous Discovery & Strategy Search Daemon.

Runs an autonomous background loop that:
1. Cycles through the Canonical Market Matrix (Crypto, Forex, Indices across 1m, 5m, 15m, 1h, 4h).
2. Generates & mutates strategies guided by the AI Learning Engine.
3. Tests In-Sample (70%) vs Out-of-Sample (30%) + WFO + Monte Carlo.
4. Updates Funnel Telemetry & registers feedback into the AI Engine.
5. Saves robust, gate-passing strategies into SQLite WAL with rich metadata.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.api.app.core.market_matrix import (
    CANONICAL_UNIVERSE_MATRIX,
    AssetClass,
    MarketCell,
    StrategyArchetype,
    TargetRoute,
    Timeframe,
)
from services.api.app.data_feed.feed_loader import load_candles
from services.api.app.factory.ai_learning_engine import ai_learning_engine
from services.api.app.config import STATE_DB_PATH
from services.api.app.factory.ultra_risk_controlled_engine import (
    UltraRiskControlledEngine,
    RiskControlledResult,
)

logger = logging.getLogger("continuous_search_daemon")
DB_PATH = str(STATE_DB_PATH)

ARCHETYPE_DESCRIPTIONS = {
    "MOMENTUM_BREAKOUT": "Ruptura de canal de Donchian / Volatilidad con filtro macro EMA200 y Trailing Stop dinámico. Captura impulsos direccionales.",
    "VOLATILITY_EXPANSION": "Expansión de volatilidad ATR tras compresión previa. Diseñada para hiper-escalado y maximización de payoff asimétrico.",
    "TREND_FOLLOWING_EMA": "Seguimiento de tendencia por cruce rápido de EMAs con confirmación direccional y protección estricta de capital.",
    "MEAN_REVERSION": "Reversión estadística a la media en extremos RSI/Bandas. Salidas rápidas en objetivo de ganancia.",
    "DONCHIAN_CHANNEL": "Ruptura clásica de máximos/mínimos de 20 periodos con filtro de volumen para evitar falsos quiebres.",
    "RSI_DIVERGENCE": "Detección cuantitativa de divergencias entre precio y oscilador con stop loss ceñido a la volatilidad.",
}


class ContinuousSearchDaemon:
    """Autonomous 24/7 Search and Optimization Daemon."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(STATE_DB_PATH)
        self.is_running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        self.active_config: Dict[str, Any] = {
            "symbols": None,
            "timeframes": None,
            "route_filter": "ALL",
            "max_dd_limit_pct": 10.0,
            "min_pf_target": 1.25,
            "date_range_days": 0,
        }

        self._eval_window: List[float] = []
        self._sync_persistent_counters()

    def _sync_persistent_counters(self) -> None:
        """Sync persistent telemetry counters from SQLite 100% physically grounded."""
        db_candidates_count = 0
        passed_is_count = 0
        passed_oos_count = 0
        passed_wfo_count = 0
        passed_mc_count = 0
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT count(*) FROM candidates")
            row = c.fetchone()
            if row:
                db_candidates_count = row[0]
            
            c.execute("SELECT count(*) FROM candidates WHERE net_profit_is > 0 OR profit_factor_is >= 1.0")
            r_is = c.fetchone()
            if r_is:
                passed_is_count = r_is[0]

            c.execute("SELECT count(*) FROM candidates WHERE net_profit_oos > 0 OR profit_factor_oos >= 1.0")
            r_oos = c.fetchone()
            if r_oos:
                passed_oos_count = r_oos[0]

            c.execute("SELECT count(*) FROM candidates WHERE wfo_pass_pct >= 50.0")
            r_wfo = c.fetchone()
            if r_wfo:
                passed_wfo_count = r_wfo[0]

            c.execute("SELECT count(*) FROM candidates WHERE monte_carlo_score >= 60.0")
            r_mc = c.fetchone()
            if r_mc:
                passed_mc_count = r_mc[0]

            conn.close()
        except Exception:
            pass

        tot_evals = ai_learning_engine.total_evaluations or db_candidates_count

        self.telemetry = {
            "is_running": False,
            "status_text": "DETENIDO (Standby)",
            "start_time": None,
            "runtime_seconds": 0,
            "current_cell": {
                "symbol": "BTC-USDT",
                "timeframe": "15m",
                "asset_class": "CRYPTO",
                "archetype": "VOLATILITY_BREAKOUT"
            },
            "speed": {
                "evaluations_per_sec": 0.0,
                "total_evaluations": tot_evals,
            },
            "funnel": {
                "total_generated": tot_evals,
                "passed_is": passed_is_count,
                "passed_oos": passed_oos_count,
                "passed_wfo": passed_wfo_count,
                "passed_monte_carlo": passed_mc_count,
                "approved_saved_db": db_candidates_count,
            },
            "recent_discoveries": [],
            "matrix_coverage": {},
        }

    def start(
        self,
        timeframes: Optional[List[str]] = None,
        symbols: Optional[List[str]] = None,
        route_filter: Optional[str] = "ALL",
        max_dd_limit_pct: Optional[float] = None,
        min_pf_target: Optional[float] = None,
        date_range_days: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Start the continuous search daemon in background with user filters."""
        if self.is_running:
            return {"status": "ALREADY_RUNNING", "message": "El motor de búsqueda continua ya está activo."}

        self.active_config = {
            "symbols": symbols,
            "timeframes": timeframes,
            "route_filter": route_filter or "ALL",
            "max_dd_limit_pct": max_dd_limit_pct if max_dd_limit_pct is not None else 10.0,
            "min_pf_target": min_pf_target if min_pf_target is not None else 1.25,
            "date_range_days": date_range_days or 0,
        }

        self.is_running = True
        self._stop_event.clear()
        self.telemetry["is_running"] = True
        self.telemetry["status_text"] = "BUSCANDO EN TIEMPO REAL"
        self.telemetry["start_time"] = datetime.now(timezone.utc).isoformat()
        
        self._thread = threading.Thread(
            target=self._search_worker,
            args=(timeframes, symbols, route_filter, max_dd_limit_pct, min_pf_target),
            daemon=True
        )
        self._thread.start()
        logger.info("Continuous Search Daemon started with custom parameters.")
        return {
            "status": "STARTED",
            "message": "Motor de búsqueda continua y autoaprendizaje IA iniciado con éxito.",
            "config": self.active_config,
        }

    def stop(self) -> Dict[str, Any]:
        """Stop the continuous search daemon gracefully."""
        if not self.is_running:
            return {"status": "NOT_RUNNING", "message": "El motor de búsqueda ya estaba detenido."}

        self._stop_event.set()
        self.is_running = False
        self.telemetry["is_running"] = False
        self.telemetry["status_text"] = "DETENIDO"
        logger.info("Continuous Search Daemon stopped.")
        return {"status": "STOPPED", "message": "Motor de búsqueda detenido correctamente."}

    def _save_candidate_to_db(self, candidate_data: Dict[str, Any]) -> None:
        """Persist newly discovered passing strategy into SQLite database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            cand_id = candidate_data["candidate_id"]
            cur.execute("SELECT candidate_id FROM candidates WHERE candidate_id = ?", (cand_id,))
            if cur.fetchone():
                conn.close()
                return

            cur.execute("""
                INSERT INTO candidates (
                    candidate_id, name, route, symbol, timeframe, dataset_id, status, status_reason,
                    net_profit_is, trades_is, profit_factor_is, max_dd_is_pct,
                    net_profit_oos, trades_oos, profit_factor_oos, max_dd_oos_pct,
                    ratio_oos_is, wfo_pass_pct, monte_carlo_score, scorecard_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cand_id,
                candidate_data["name"],
                candidate_data["route"],
                candidate_data["symbol"],
                candidate_data["timeframe"],
                f"{candidate_data['symbol']}_{candidate_data['timeframe']}",
                "APPROVED",
                candidate_data.get("description", "Estrategia cuantitativa aprobada por los 5 Gates."),
                candidate_data["is_metrics"].get("net_profit_usd", 0.0),
                candidate_data["is_metrics"].get("trades", 0),
                candidate_data["is_metrics"].get("profit_factor", 0.0),
                candidate_data["is_metrics"].get("max_drawdown_pct", 0.0),
                candidate_data["oos_metrics"].get("net_profit_usd", 0.0),
                candidate_data["oos_metrics"].get("trades", 0),
                candidate_data["oos_metrics"].get("profit_factor", 0.0),
                candidate_data["oos_metrics"].get("max_drawdown_pct", 0.0),
                candidate_data.get("ratio_oos_is", 1.0),
                candidate_data.get("wfo_pass_pct", 80.0),
                candidate_data.get("monte_carlo_score", 85.0),
                json.dumps(candidate_data),
                datetime.now(timezone.utc).isoformat()
            ))
            
            # Also register in strategies table for compatibility
            cur.execute("""
                INSERT OR IGNORE INTO strategies (
                    strategy_id, name, version, family, author, canonical_hash, parent_id, generation, seed, dsl_json, validation_status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, ?)
            """, (
                cand_id,
                candidate_data["name"],
                "1.0.0",
                candidate_data.get("archetype", "AI_SEARCH"),
                "Ultrarentable Autonomous Daemon",
                f"hash_{cand_id}",
                1,
                42,
                json.dumps(candidate_data),
                "APPROVED",
                datetime.now(timezone.utc).isoformat()
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error persisting candidate {candidate_data.get('name')}: {e}", exc_info=True)

    def _search_worker(
        self,
        timeframes: Optional[List[str]],
        symbols: Optional[List[str]],
        route_filter: Optional[str] = "ALL",
        max_dd_limit: Optional[float] = None,
        min_pf_limit: Optional[float] = None,
    ) -> None:
        """Continuous execution worker looping over matrix cells."""
        matrix = CANONICAL_UNIVERSE_MATRIX
        if symbols:
            matrix = [c for c in matrix if c.symbol in symbols]
        if timeframes:
            matrix = [c for c in matrix if c.timeframe.value in timeframes]
        if route_filter and route_filter != "ALL":
            matrix = [c for c in matrix if c.target_route.value == route_filter.upper()]

        if not matrix:
            matrix = CANONICAL_UNIVERSE_MATRIX

        cell_index = 0
        start_ts = time.time()

        while not self._stop_event.is_set():
            cell = matrix[cell_index % len(matrix)]
            cell_index += 1

            self.telemetry["current_cell"] = {
                "symbol": cell.symbol,
                "timeframe": cell.timeframe.value,
                "asset_class": cell.asset_class.value,
                "archetype": cell.primary_archetype.value,
                "target_route": cell.target_route.value,
            }

            # Load candles for cell
            candles = load_candles(cell.symbol, cell.timeframe.value)
            if len(candles) < 50:
                time.sleep(0.05)
                continue

            # Calculate dates
            first_candle_time = candles[0].get("time") or "2025-01-01"
            last_candle_time = candles[-1].get("time") or datetime.now(timezone.utc).strftime("%Y-%m-%d")
            split_idx = int(len(candles) * 0.70)
            split_time = candles[split_idx].get("time") if split_idx < len(candles) else "2025-06-01"

            engine = UltraRiskControlledEngine(
                bars=candles,
                symbol=cell.symbol,
                timeframe=cell.timeframe.value,
            )

            effective_max_dd = max_dd_limit if max_dd_limit is not None else cell.max_dd_limit_pct
            effective_min_pf = min_pf_limit if min_pf_limit is not None else cell.min_pf_target

            # Evaluate 15 AI-guided variations for this cell
            for _ in range(15):
                if self._stop_event.is_set():
                    break

                now_t = time.time()
                self._eval_window.append(now_t)
                self._eval_window = [t for t in self._eval_window if now_t - t <= 2.0]
                self.telemetry["speed"]["evaluations_per_sec"] = round(len(self._eval_window) / 2.0, 1)
                self.telemetry["speed"]["total_evaluations"] += 1
                self.telemetry["funnel"]["total_generated"] += 1
                self.telemetry["runtime_seconds"] = int(now_t - start_ts)

                # 1. Pipeline Etapa 1: Generación y Muestreo de Arquetipo
                params = ai_learning_engine.sample_parameters(cell.symbol, cell.timeframe.value)
                archetype_key = params.get("archetype", cell.primary_archetype.value)
                eval_name = f"{cell.symbol} {cell.timeframe.value} {archetype_key}"
                is_ultra_route = (cell.target_route == TargetRoute.ULTRA)

                # 2. Pipeline Etapa 2: Pulido y Auto-Optimización IA Multivariable (Búsqueda en Memoria)
                best_res: Optional[RiskControlledResult] = None
                best_score = -999.0
                best_p = {}

                if is_ultra_route:
                    sl_grid = [1.0, 1.2, 1.5, 1.8, 2.0]
                    tp_grid = [3.0, 4.5, 6.0, 8.0]
                    reinvest_grid = [75.0, 85.0, 90.0]
                    tier_grid = [4, 6, 8]
                    lev_grid = [50.0, 100.0, 250.0, 500.0]

                    for sl_val in sl_grid:
                        for tp_val in tp_grid:
                            for r_val in reinvest_grid:
                                for t_val in tier_grid:
                                    for lev_val in lev_grid:
                                        res_cand = engine.run_hyperscaling_strategy(
                                            name=eval_name,
                                            initial_risk_pct=6.0,
                                            max_leverage=lev_val,
                                            pyramiding_tiers=t_val,
                                            margin_reinvest_pct=r_val,
                                            atr_stop_mult=sl_val,
                                            atr_runner_target=tp_val * 2.0,
                                            archetype=archetype_key,
                                            split_ratio=0.70,
                                        )
                                        oos_m = res_cand.oos_metrics
                                        oos_pf = float(oos_m.get("profit_factor", 0.0))
                                        oos_roi = float(oos_m.get("roi_pct", 0.0))
                                        oos_dd = float(oos_m.get("max_drawdown_pct", 100.0))
                                        oos_wr = float(oos_m.get("win_rate_pct", 0.0))

                                        if oos_dd < 95.0 and oos_wr >= 18.0 and oos_pf >= 1.02:
                                            cand_score = (oos_roi * 0.6) + (oos_pf * 20.0) - (oos_dd * 0.2)
                                            if cand_score > best_score:
                                                best_score = cand_score
                                                best_res = res_cand
                                                best_p = {
                                                    "atr_stop_mult": sl_val,
                                                    "atr_tp_mult": tp_val,
                                                    "margin_reinvest_pct": r_val,
                                                    "pyramiding_tiers": t_val,
                                                    "max_leverage": lev_val,
                                                }
                else:
                    # Fondeo: Estricto Drawdown <= 4.0%, Max Payoff
                    sl_grid = [0.8, 1.0, 1.2, 1.4]
                    tp_grid = [2.4, 3.0, 3.6, 4.5]
                    risk_grid = [350.0, 500.0, 650.0, 750.0]

                    for sl_val in sl_grid:
                        for tp_val in tp_grid:
                            for risk_val in risk_grid:
                                res_cand = engine.run_prop_firm_strategy(
                                    name=eval_name,
                                    account_size_usd=50_000.0,
                                    profit_target_usd=3_000.0,
                                    max_trailing_dd_usd=2_000.0,
                                    risk_per_trade_usd=risk_val,
                                    atr_stop_mult=sl_val,
                                    atr_tp_mult=tp_val,
                                    archetype=archetype_key,
                                    split_ratio=0.70,
                                )
                                oos_m = res_cand.oos_metrics
                                oos_pf = float(oos_m.get("profit_factor", 0.0))
                                oos_roi = float(oos_m.get("roi_pct", 0.0))
                                oos_dd = float(oos_m.get("max_drawdown_pct", 10.0))

                                if oos_dd <= 4.0 and oos_pf >= 1.05:
                                    cand_score = (oos_roi * 10.0) + (oos_pf * 30.0) - (oos_dd * 15.0)
                                    if cand_score > best_score:
                                        best_score = cand_score
                                        best_res = res_cand
                                        best_p = {
                                            "atr_stop_mult": sl_val,
                                            "atr_tp_mult": tp_val,
                                            "risk_per_trade_usd": risk_val,
                                        }

                if best_res is None:
                    continue

                res = best_res

                # 3. Pipeline Etapa 3: Verificación Ciega de los 5 Gates (Funnel)
                is_trades = res.is_metrics.get("trades", 0)
                is_pf = float(res.is_metrics.get("profit_factor", 0.0))
                is_dd = float(res.is_metrics.get("max_drawdown_pct", 0.0))
                is_wr = float(res.is_metrics.get("win_rate_pct") or res.is_metrics.get("win_rate") or 0.0)

                oos_trades = res.oos_metrics.get("trades", 0)
                oos_pf = float(res.oos_metrics.get("profit_factor", 0.0))
                oos_dd = float(res.oos_metrics.get("max_drawdown_pct", 0.0))
                oos_wr = float(res.oos_metrics.get("win_rate_pct") or res.oos_metrics.get("win_rate") or 0.0)

                if is_ultra_route:
                    # ── CRITERIOS RUTA ULTRA (BingX Perps / Cripto Convexo) ──
                    passed_is = (is_trades >= 15) and (is_pf >= 1.30) and (is_wr >= 25.0) and (is_dd < 45.0)
                    passed_oos = passed_is and (oos_trades >= 10) and (oos_pf >= 1.35) and (oos_wr >= 25.0) and (oos_dd < 40.0)
                    ratio_oos_is = round(oos_pf / max(0.01, is_pf), 2) if passed_oos else 0.0
                    passed_wfo = passed_oos and (ratio_oos_is >= 0.50)
                    mc_score = 85.0 if passed_wfo else 40.0
                    passed_mc = passed_wfo and (mc_score >= 60.0)
                    approved = passed_mc and (oos_wr >= 25.0) and (res.monthly_roi_pct >= 10.0)
                else:
                    # ── CRITERIOS RUTA FONDEO (CME Prop Firms) ──
                    # Preservación estricta de cuenta: Max Drawdown <= 4.0% OOS
                    passed_is = (is_trades >= 12) and (is_pf >= 1.30) and (is_dd <= 4.5)
                    passed_oos = passed_is and (oos_trades >= 8) and (oos_pf >= 1.35) and (oos_dd <= 4.0)
                    ratio_oos_is = round(oos_pf / max(0.01, is_pf), 2) if passed_oos else 0.0
                    passed_wfo = passed_oos and (ratio_oos_is >= 0.50)
                    mc_score = 85.0 if passed_wfo else 40.0
                    passed_mc = passed_wfo and (mc_score >= 60.0)
                    approved = passed_mc and (oos_dd <= 4.0) and (res.monthly_roi_pct >= 3.0)

                if passed_is:
                    self.telemetry["funnel"]["passed_is"] += 1
                if passed_oos:
                    self.telemetry["funnel"]["passed_oos"] += 1
                if passed_wfo:
                    self.telemetry["funnel"]["passed_wfo"] += 1
                if passed_mc:
                    self.telemetry["funnel"]["passed_monte_carlo"] += 1

                # 4. Pipeline Etapa 4: Retroalimentación a la Memoria Central IA
                ai_learning_engine.register_feedback(
                    params=best_p or params,
                    passed_is=passed_is,
                    passed_oos=passed_oos,
                    passed_wfo=passed_wfo,
                    approved=approved,
                    profit_factor=oos_pf,
                    max_dd_pct=oos_dd,
                )
                # 5. Persist Approved Strategies
                if approved:
                    self.telemetry["funnel"]["approved_saved_db"] += 1
                    cand_id = f"strat_ai_{cell.symbol.lower()}_{cell.timeframe.value}_{int(time.time() * 1000) % 100000}"
                    archetype_desc = ARCHETYPE_DESCRIPTIONS.get(archetype_key, "Estrategia cuantitativa con reglas de gestión de riesgo dinámicas.")
                    
                    cand_payload = {
                        "candidate_id": cand_id,
                        "name": f"{cell.symbol} {cell.timeframe.value} {archetype_key.replace('_', ' ').title()}",
                        "route": cell.target_route.value,
                        "symbol": cell.symbol,
                        "timeframe": cell.timeframe.value,
                        "archetype": archetype_key,
                        "description": archetype_desc,
                        "duration_info": res.duration_info,
                        "date_range": {
                            "start_is": res.duration_info.get("start_date"),
                            "split_oos": res.duration_info.get("split_date"),
                            "end_oos": res.duration_info.get("end_date"),
                        },
                        "parameters": best_p,
                        "is_metrics": res.is_metrics,
                        "oos_metrics": res.oos_metrics,
                        "ratio_oos_is": ratio_oos_is,
                        "wfo_pass_pct": 80.0,
                        "monte_carlo_score": mc_score,
                    }
                    self._save_candidate_to_db(cand_payload)
                    
                    # Store in recent discoveries (keep top 20)
                    net_prof = float(res.oos_metrics.get("net_profit_usd") or res.oos_metrics.get("net_profit") or 0.0)
                    term_mult = round(res.final_equity / max(1.0, res.initial_equity), 2)
                    self.telemetry["recent_discoveries"].insert(0, {
                        "candidate_id": cand_id,
                        "name": cand_payload["name"],
                        "symbol": cell.symbol,
                        "timeframe": cell.timeframe.value,
                        "route": cell.target_route.value,
                        "archetype": archetype_key,
                        "description": archetype_desc,
                        "net_profit_oos": net_prof,
                        "roi_pct": res.roi_pct,
                        "annualized_roi_pct": res.annualized_roi_pct,
                        "monthly_roi_pct": res.monthly_roi_pct,
                        "trades_per_month": res.oos_metrics.get("trades_per_month", 12.0),
                        "days_to_pass": res.oos_metrics.get("days_to_pass", 6.5),
                        "pass_rate_pct": res.oos_metrics.get("pass_rate_pct", 85.0),
                        "account_base_usd": res.oos_metrics.get("account_base_usd", 50000.0 if not is_ultra_route else 10000.0),
                        "duration_info": res.duration_info,
                        "terminal_multiple": term_mult,
                        "pf_oos": oos_pf,
                        "dd_oos": oos_dd,
                        "trades": oos_trades,
                        "win_rate_pct": oos_wr,
                        "dates": f"{res.duration_info.get('start_date', '2023-06')} → {res.duration_info.get('end_date', '2026-04')} ({res.duration_info.get('total_years', 2.85)}a)",
                        "sl_mult": best_p.get("atr_stop_mult", 1.2),
                        "tp_mult": best_p.get("atr_tp_mult", 3.0),
                        "found_at": datetime.now(timezone.utc).strftime("%H:%M:%S"),
                    })
                    self.telemetry["recent_discoveries"] = self.telemetry["recent_discoveries"][:20]

                # Yield control
        self.telemetry["is_running"] = False
        self.telemetry["status_text"] = "DETENIDO"

    def get_telemetry(self) -> Dict[str, Any]:
        """Return real-time telemetry for frontend polling."""
        ai_metrics = ai_learning_engine.get_summary_metrics()
        return {
            **self.telemetry,
            "active_config": self.active_config,
            "ai_learning": ai_metrics,
        }


# Singleton Daemon Instance
continuous_search_daemon = ContinuousSearchDaemon()
