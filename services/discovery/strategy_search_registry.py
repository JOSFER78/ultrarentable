"""Registro forense de búsqueda y espacio de parámetros de Discovery.

Cada hipótesis/trial queda ligada a dataset, hash físico, ejecución y generación.
El espacio de búsqueda es explícito y limitado por un presupuesto reproducible.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.api.app.config import STATE_DB_PATH


@dataclass(frozen=True)
class SearchTrialRecord:
    trial_id: str
    run_id: str
    generation: int
    parent_trial_id: Optional[str]
    symbol: str
    timeframe: str
    route: str
    archetype: str
    parameters: Dict[str, Any]
    rules_json: str
    dataset_id: str
    dataset_sha256: str
    discovery_engine: str
    in_sample_pf: float
    in_sample_dd_pct: float
    created_at_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class StrategySearchRegistry:
    """Registro de trials explorados; la selección de candidatos no puede ocultar trials."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(STATE_DB_PATH)
        self._init_db()

    def _init_db(self) -> None:
        db = Path(self.db_path).expanduser()
        db.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(db, timeout=30.0) as conn:
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA busy_timeout = 30000;")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS discovery_search_trials (
                    trial_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    generation INTEGER NOT NULL,
                    parent_trial_id TEXT,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    route TEXT NOT NULL,
                    archetype TEXT NOT NULL,
                    parameters_json TEXT NOT NULL,
                    rules_json TEXT NOT NULL,
                    dataset_id TEXT NOT NULL,
                    dataset_sha256 TEXT NOT NULL,
                    discovery_engine TEXT NOT NULL,
                    in_sample_pf REAL NOT NULL,
                    in_sample_dd_pct REAL NOT NULL,
                    created_at_utc TEXT NOT NULL
                );
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_trials_symbol_tf ON discovery_search_trials (symbol, timeframe);"
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trials_run_id ON discovery_search_trials (run_id);")
            conn.commit()

    def record_trial(self, trial: SearchTrialRecord) -> None:
        with sqlite3.connect(self.db_path, timeout=30.0) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO discovery_search_trials (
                    trial_id, run_id, generation, parent_trial_id,
                    symbol, timeframe, route, archetype,
                    parameters_json, rules_json,
                    dataset_id, dataset_sha256, discovery_engine,
                    in_sample_pf, in_sample_dd_pct, created_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trial.trial_id,
                    trial.run_id,
                    trial.generation,
                    trial.parent_trial_id,
                    trial.symbol.upper(),
                    trial.timeframe.lower(),
                    trial.route.upper(),
                    trial.archetype,
                    json.dumps(trial.parameters, sort_keys=True),
                    trial.rules_json,
                    trial.dataset_id,
                    trial.dataset_sha256,
                    trial.discovery_engine,
                    float(trial.in_sample_pf),
                    float(trial.in_sample_dd_pct),
                    trial.created_at_utc,
                ),
            )
            conn.commit()

    def get_total_trials_count(self, symbol: Optional[str] = None, timeframe: Optional[str] = None) -> int:
        with sqlite3.connect(self.db_path, timeout=30.0) as conn:
            cur = conn.cursor()
            if symbol and timeframe:
                cur.execute(
                    "SELECT COUNT(*) FROM discovery_search_trials WHERE symbol = ? AND timeframe = ?",
                    (symbol.upper(), timeframe.lower()),
                )
            elif symbol:
                cur.execute("SELECT COUNT(*) FROM discovery_search_trials WHERE symbol = ?", (symbol.upper(),))
            else:
                cur.execute("SELECT COUNT(*) FROM discovery_search_trials")
            row = cur.fetchone()
            return int(row[0]) if row else 0

    def get_trials_for_run(self, run_id: str) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path, timeout=30.0) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM discovery_search_trials WHERE run_id = ? ORDER BY generation ASC, trial_id ASC",
                (run_id,),
            )
            return [dict(row) for row in cur.fetchall()]

    def get_all_trials(self, limit: int = 1000) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path, timeout=30.0) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM discovery_search_trials ORDER BY created_at_utc DESC LIMIT ?", (limit,))
            return [dict(row) for row in cur.fetchall()]

    @staticmethod
    def _deterministic_budget(
        space: List[Dict[str, Any]], max_trials: Optional[int], campaign_seed: str
    ) -> List[Dict[str, Any]]:
        if max_trials is None or max_trials <= 0 or len(space) <= max_trials:
            return space
        ranked = sorted(
            space,
            key=lambda item: hashlib.sha256(
                f"{campaign_seed}|{json.dumps(item, sort_keys=True, separators=(',', ':'))}".encode("utf-8")
            ).hexdigest(),
        )
        return ranked[:max_trials]

    def generate_combinatorial_parameter_space(
        self,
        symbol: str,
        timeframe: str,
        route: str = "ULTRA",
        max_trials: int = 256,
        campaign_seed: str = "PHASE2_V1",
    ) -> List[Dict[str, Any]]:
        """Construye un espacio donde cada dimensión usada por discovery tiene efecto real."""
        route_upper = route.upper()
        tf_lower = str(timeframe).lower()
        space: List[Dict[str, Any]] = []

        if tf_lower in ["1m", "5m"]:
            fast_emas_f = [3, 5, 8, 9, 12, 13, 20]
            slow_emas_f = [15, 21, 30, 34, 50, 80]
            fast_emas_u = [3, 5, 8, 12, 20]
            slow_emas_u = [15, 21, 30, 50, 80]
            rsi_periods = [7, 10, 14, 21]
            threshold_pairs = [(50.0, 50.0), (52.0, 48.0), (55.0, 45.0), (60.0, 40.0)]
            atr_sl_f = [1.0, 1.5, 2.0, 2.5, 3.0]
            atr_tp_f = [1.5, 2.0, 3.0, 4.5, 6.0]
            atr_sl_u = [1.0, 1.5, 2.0, 3.0]
            atr_tp_u = [2.0, 3.0, 4.0, 6.0, 8.0]
        elif tf_lower in ["15m", "1h"]:
            fast_emas_f = [5, 9, 13, 20]
            slow_emas_f = [21, 34, 50, 80, 100]
            fast_emas_u = [8, 12, 20]
            slow_emas_u = [30, 50, 80, 100]
            rsi_periods = [10, 14, 21]
            threshold_pairs = [(50.0, 50.0), (52.0, 48.0), (55.0, 45.0), (60.0, 40.0)]
            atr_sl_f = [1.5, 2.0, 2.5, 3.0]
            atr_tp_f = [2.5, 3.0, 4.5, 6.0, 8.0]
            atr_sl_u = [1.5, 2.0, 3.0]
            atr_tp_u = [4.0, 6.0, 8.0]
        else:  # 4h y fallbacks
            fast_emas_f = [8, 12, 20, 34]
            slow_emas_f = [34, 50, 80, 100, 200]
            fast_emas_u = [8, 12, 20, 34]
            slow_emas_u = [34, 50, 80, 100, 200]
            rsi_periods = [10, 14, 21]
            threshold_pairs = [(52.0, 48.0), (55.0, 45.0), (60.0, 40.0)]
            atr_sl_f = [1.5, 2.0, 2.5, 3.0]
            atr_tp_f = [3.0, 4.5, 6.0, 8.0]
            atr_sl_u = [1.5, 2.0, 3.0]
            atr_tp_u = [4.0, 6.0, 8.0]

        if route_upper == "FONDEO":
            archetypes = ["INSTITUTIONAL_SESSION_MOMENTUM", "TREND_FOLLOWING", "RSI_MOMENTUM", "MEAN_REVERSION"]
            for archetype in archetypes:
                for f in fast_emas_f:
                    for s in slow_emas_f:
                        if f >= s:
                            continue
                        for sl in atr_sl_f:
                            for tp in atr_tp_f:
                                for rp in rsi_periods:
                                    for r_long, r_short in threshold_pairs:
                                        space.append(
                                            {
                                                "ema_fast": f,
                                                "ema_slow": s,
                                                "rsi_period": rp,
                                                "rsi_threshold_long": r_long,
                                                "rsi_threshold_short": r_short,
                                                "sl_atr_mult": sl,
                                                "tp_atr_mult": tp,
                                                "stop_loss_ticks": sl * 10.0,
                                                "target_profit_ticks": tp * 10.0,
                                                "archetype": archetype,
                                                "route": route_upper,
                                                "symbol": symbol,
                                                "timeframe": timeframe,
                                            }
                                        )
        else:
            pyramiding_counts = [0, 1, 2, 3]
            archetypes = ["MOMENTUM_BREAKOUT", "TREND_FOLLOWING", "RSI_MOMENTUM", "MEAN_REVERSION"]
            for archetype in archetypes:
                for f in fast_emas_u:
                    for s in slow_emas_u:
                        if f >= s:
                            continue
                        for sl in atr_sl_u:
                            for tp in atr_tp_u:
                                for rp in rsi_periods:
                                    for r_long, r_short in threshold_pairs:
                                        for tiers in pyramiding_counts:
                                            space.append(
                                                {
                                                    "ema_fast": f,
                                                    "ema_slow": s,
                                                    "sl_atr_mult": sl,
                                                    "tp_atr_mult": tp,
                                                    "rsi_period": rp,
                                                    "rsi_threshold_long": r_long,
                                                    "rsi_threshold_short": r_short,
                                                    "pyramiding_tiers_count": tiers,
                                                    "route": route_upper,
                                                    "archetype": archetype,
                                                    "symbol": symbol,
                                                    "timeframe": timeframe,
                                                }
                                            )

        return self._deterministic_budget(space, max_trials, campaign_seed)
