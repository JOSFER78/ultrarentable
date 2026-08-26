"""Registro Forense de Búsqueda y Espacio de Parámetros de Discovery.
Almacena cada hipótesis generada (trials), sus parámetros, mutaciones y genealogía.
"""

from __future__ import annotations

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
    """Registro inmutable de trials explorados para cálculo de DSR y trazabilidad."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(STATE_DB_PATH)
        self._init_db()

    def _init_db(self) -> None:
        db = Path(self.db_path).expanduser()
        db.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(db, timeout=30.0) as conn:
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA busy_timeout = 30000;")
            conn.execute("""
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
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trials_symbol_tf ON discovery_search_trials (symbol, timeframe);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trials_run_id ON discovery_search_trials (run_id);")
            conn.commit()

    def record_trial(self, trial: SearchTrialRecord) -> None:
        with sqlite3.connect(self.db_path, timeout=30.0) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO discovery_search_trials (
                    trial_id, run_id, generation, parent_trial_id,
                    symbol, timeframe, route, archetype,
                    parameters_json, rules_json,
                    dataset_id, dataset_sha256, discovery_engine,
                    in_sample_pf, in_sample_dd_pct, created_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trial.trial_id, trial.run_id, trial.generation, trial.parent_trial_id,
                trial.symbol.upper(), trial.timeframe.lower(), trial.route.upper(), trial.archetype,
                json.dumps(trial.parameters, sort_keys=True), trial.rules_json,
                trial.dataset_id, trial.dataset_sha256, trial.discovery_engine,
                float(trial.in_sample_pf), float(trial.in_sample_dd_pct), trial.created_at_utc,
            ))
            conn.commit()

    def get_total_trials_count(self, symbol: Optional[str] = None, timeframe: Optional[str] = None) -> int:
        with sqlite3.connect(self.db_path, timeout=30.0) as conn:
            cur = conn.cursor()
            if symbol and timeframe:
                cur.execute("SELECT COUNT(*) FROM discovery_search_trials WHERE symbol = ? AND timeframe = ?", (symbol.upper(), timeframe.lower()))
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
            cur.execute("SELECT * FROM discovery_search_trials WHERE run_id = ? ORDER BY generation ASC, trial_id ASC", (run_id,))
            return [dict(row) for row in cur.fetchall()]

    def get_all_trials(self, limit: int = 1000) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path, timeout=30.0) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM discovery_search_trials ORDER BY created_at_utc DESC LIMIT ?", (limit,))
            return [dict(row) for row in cur.fetchall()]

    def generate_combinatorial_parameter_space(self, symbol: str, timeframe: str, route: str = "ULTRA") -> List[Dict[str, Any]]:
        """Espacio real diversificado: familias semánticas distintas + parámetros de entrada/salida."""
        fast_emas = [8, 12, 20]
        slow_emas = [30, 50, 80]
        atr_multipliers_sl = [1.5, 2.0, 3.0]
        atr_multipliers_tp = [4.0, 6.0, 8.0]
        rsi_periods = [10, 14, 21]
        rsi_long = [52.0, 55.0, 60.0]
        rsi_short = [48.0, 45.0, 40.0]
        archetypes = ["MOMENTUM_BREAKOUT", "TREND_FOLLOWING", "RSI_MOMENTUM", "MEAN_REVERSION"]

        space: List[Dict[str, Any]] = []
        for archetype in archetypes:
            for f in fast_emas:
                for s in slow_emas:
                    if f >= s:
                        continue
                    for sl in atr_multipliers_sl:
                        for tp in atr_multipliers_tp:
                            for rp, rl, rs in zip(rsi_periods, rsi_long, rsi_short):
                                space.append({
                                    "ema_fast": f,
                                    "ema_slow": s,
                                    "sl_atr_mult": sl,
                                    "tp_atr_mult": tp,
                                    "rsi_period": rp,
                                    "rsi_threshold_long": rl,
                                    "rsi_threshold_short": rs,
                                    "archetype": archetype,
                                    "pyramiding_tiers_count": 3 if route == "ULTRA" else 1,
                                    "route": route,
                                    "symbol": symbol,
                                    "timeframe": timeframe,
                                })
        return space
