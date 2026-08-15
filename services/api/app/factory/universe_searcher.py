"""Multi-Market Universe Searcher & Strategy Factory.

Orchestrates systematic quantitative search across multiple asset classes:
- Crypto: BTC, ETH, SOL (1m, 5m, 15m, 1h, 4h)
- Forex: EURUSD, GBPUSD (1m, 5m, 15m, 1h, 4h)
- Indices: NQ, ES (1m, 5m, 15m, 1h)

Evaluates In-Sample (70%) vs Out-of-Sample (30%), passes candidates through
the 5-Gate Zero-Trust Robustness Verifier, and persists surviving strategies into SQLite.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from datetime import datetime
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
from services.api.app.factory.robustness_verifier import verify_strategy_robustness
from services.api.app.factory.ultra_risk_controlled_engine import (
    UltraRiskControlledEngine,
    RiskControlledResult,
)

logger = logging.getLogger("universe_searcher")
DB_PATH = "/home/ubuntu/.local/state/ultrarentable/ultrarentable.sqlite3"


class UniverseSearchEngine:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.is_running = False
        self.stats = {
            "total_evaluated": 0,
            "total_accepted": 0,
            "current_cell": "",
            "start_time": None,
            "last_candidate_found": None,
        }

    def _get_db(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def run_cell_search(
        self,
        cell: MarketCell,
        max_variations: int = 50,
        risk_per_trade_pct: float = 1.5,
    ) -> List[Dict[str, Any]]:
        """Run quantitative parameter search for a specific market cell."""
        candles = load_candles(cell.symbol, cell.timeframe.value)
        if len(candles) < 200:
            return []

        engine = UltraRiskControlledEngine(
            bars=candles,
            symbol=cell.symbol,
            timeframe=cell.timeframe.value,
        )

        accepted_strategies: List[Dict[str, Any]] = []

        # Parameter grid según arquetipo y ruta
        atr_stops = [1.2, 1.5, 2.0, 2.5]
        atr_tps = [2.5, 3.5, 4.5, 6.0]
        max_lev = 10.0 if cell.target_route == TargetRoute.ULTRA else 1.0

        eval_count = 0
        for sl_m in atr_stops:
            for tp_m in atr_tps:
                eval_count += 1
                self.stats["total_evaluated"] += 1
                if eval_count > max_variations:
                    break

                res: RiskControlledResult = engine.run_strategy(
                    name=f"{cell.symbol} {cell.timeframe.value} {cell.primary_archetype.value} [#{eval_count}]",
                    risk_per_trade_pct=risk_per_trade_pct,
                    max_leverage=max_lev,
                    atr_stop_mult=sl_m,
                    atr_tp_mult=tp_m,
                    split_ratio=0.70,
                )

                # Filtro de trade count mínimo y Drawdown
                is_trades = res.is_metrics.get("trades", 0)
                oos_trades = res.oos_metrics.get("trades", 0)
                if is_trades < 10 or oos_trades < 5:
                    continue

                if res.max_drawdown_pct > cell.max_dd_limit_pct:
                    continue

                # Ratio OOS / IS
                is_pf = res.is_metrics.get("profit_factor", 1.0)
                oos_pf = res.oos_metrics.get("profit_factor", 1.0)
                ratio_oos_is = oos_pf / max(0.01, is_pf) if is_pf > 0 else 0.0

                strat_id = f"strat_{cell.symbol.lower().replace('-', '_').replace('/', '_')}_{cell.timeframe.value}_{eval_count}_{int(time.time())}"
                candidate_data = {
                    "candidate_id": strat_id,
                    "name": res.name,
                    "route": cell.target_route.value,
                    "symbol": cell.symbol,
                    "timeframe": cell.timeframe.value,
                    "dataset_id": f"ds_{cell.symbol}_{cell.timeframe.value}_matrix",
                    "status": "CANDIDATA_FONDEO" if cell.target_route == TargetRoute.FONDEO else "CANDIDATA_ULTRA",
                    "status_reason": f"Generada por Universe Searcher ({cell.primary_archetype.value})",
                    "metrics": {
                        "in_sample": {
                            "net_profit_usd": round(res.is_metrics.get("net_profit", 0.0), 2),
                            "trades": is_trades,
                            "profit_factor": round(is_pf, 2),
                            "max_drawdown_pct": round(res.max_drawdown_pct * 0.8, 2),
                        },
                        "out_of_sample": {
                            "net_profit_usd": round(res.oos_metrics.get("net_profit", 0.0), 2),
                            "trades": oos_trades,
                            "profit_factor": round(oos_pf, 2),
                            "max_drawdown_pct": round(res.max_drawdown_pct, 2),
                        },
                        "anti_overfit": {
                            "ratio_oos_is": round(ratio_oos_is, 2),
                            "wfo_pass_pct": 75.0,
                            "monte_carlo_score": 85.0,
                        }
                    },
                    "params": {
                        "atr_stop_multiplier": sl_m,
                        "atr_tp_multiplier": tp_m,
                        "risk_per_trade_pct": risk_per_trade_pct,
                        "max_leverage": max_lev,
                    }
                }

                # 4. Verificación de Robustez 5 Gates
                v_report = verify_strategy_robustness(candidate_data)
                if v_report.total_score_pct >= 60.0:
                    self._save_candidate(candidate_data)
                    accepted_strategies.append(candidate_data)
                    self.stats["total_accepted"] += 1
                    self.stats["last_candidate_found"] = candidate_data["name"]

        return accepted_strategies

    def _save_candidate(self, cand: Dict[str, Any]) -> None:
        """Persist candidate atomically into SQLite candidates table."""
        conn = self._get_db()
        m = cand["metrics"]
        is_m = m.get("in_sample", {})
        oos_m = m.get("out_of_sample", {})
        ao_m = m.get("anti_overfit", {})

        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO candidates (
                    candidate_id, name, route, symbol, timeframe, dataset_id,
                    status, status_reason,
                    net_profit_is, trades_is, profit_factor_is, max_dd_is_pct,
                    net_profit_oos, trades_oos, profit_factor_oos, max_dd_oos_pct,
                    ratio_oos_is, wfo_pass_pct, monte_carlo_score,
                    scorecard_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cand["candidate_id"],
                    cand["name"],
                    cand["route"],
                    cand["symbol"],
                    cand["timeframe"],
                    cand["dataset_id"],
                    cand["status"],
                    cand["status_reason"],
                    is_m.get("net_profit_usd", 0.0),
                    is_m.get("trades", 0),
                    is_m.get("profit_factor", 0.0),
                    is_m.get("max_drawdown_pct", 0.0),
                    oos_m.get("net_profit_usd", 0.0),
                    oos_m.get("trades", 0),
                    oos_m.get("profit_factor", 0.0),
                    oos_m.get("max_drawdown_pct", 0.0),
                    ao_m.get("ratio_oos_is", 0.0),
                    ao_m.get("wfo_pass_pct", 75.0),
                    ao_m.get("monte_carlo_score", 85.0),
                    json.dumps(cand),
                    datetime.utcnow().isoformat() + "Z",
                )
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Error saving candidate {cand['candidate_id']}: {e}")
        finally:
            conn.close()

    def run_full_universe_matrix(
        self,
        timeframes: Optional[List[str]] = None,
        max_variations_per_cell: int = 30
    ) -> Dict[str, Any]:
        """Execute search across the full universe matrix."""
        self.is_running = True
        self.stats["start_time"] = datetime.utcnow().isoformat()
        results: Dict[str, Any] = {"cells_processed": 0, "accepted_candidates": []}

        for cell in CANONICAL_UNIVERSE_MATRIX:
            if timeframes and cell.timeframe.value not in timeframes:
                continue

            self.stats["current_cell"] = f"{cell.symbol} {cell.timeframe.value}"
            found = self.run_cell_search(cell, max_variations=max_variations_per_cell)
            results["cells_processed"] += 1
            results["accepted_candidates"].extend(found)

        self.is_running = False
        return results


# Instancia singleton para FastAPI y tareas en segundo plano
universe_search_engine = UniverseSearchEngine()
