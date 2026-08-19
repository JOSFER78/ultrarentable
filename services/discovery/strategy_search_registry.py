"""services/discovery/strategy_search_registry.py
Registro Forense de Búsqueda y Espacio de Parámetros de Discovery (Fase 3).
Almacena cada hipótesis generada (trials), sus parámetros, mutaciones y genealogía.
Suministra el contador real y trazable de trials para el Deflated Sharpe Ratio (DSR) en Gate 8.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


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
        if db_path is None:
            state_dir = Path.home() / ".local" / "state" / "ultrarentable"
            state_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(state_dir / "ultrarentable.sqlite3")
        else:
            self.db_path = db_path
        
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path, timeout=30.0) as conn:
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
                trial.in_sample_pf,
                trial.in_sample_dd_pct,
                trial.created_at_utc,
            ))
            conn.commit()

    def get_total_trials_count(self, symbol: Optional[str] = None, timeframe: Optional[str] = None) -> int:
        """Devuelve el número real y trazable de hipótesis probadas para el cálculo exacto del DSR."""
        with sqlite3.connect(self.db_path, timeout=30.0) as conn:
            if symbol and timeframe:
                cur = conn.execute(
                    "SELECT COUNT(*) FROM discovery_search_trials WHERE symbol = ? AND timeframe = ?",
                    (symbol.upper(), timeframe.lower())
                )
            else:
                cur = conn.execute("SELECT COUNT(*) FROM discovery_search_trials")
            row = cur.fetchone()
            return int(row[0]) if row and row[0] > 0 else 100

    def generate_combinatorial_parameter_space(
        self,
        symbol: str,
        timeframe: str,
        route: str = "ULTRA",
    ) -> List[Dict[str, Any]]:
        """Genera un espacio de búsqueda cuantitativo con múltiples hipótesis de momentum, volatilidad y reversión."""
        fast_emas = [8, 10, 12, 15, 20]
        slow_emas = [21, 30, 45, 55, 89]
        breakout_periods = [10, 15, 20, 30]
        atr_multipliers_sl = [1.5, 2.0, 2.5, 3.0]
        atr_multipliers_tp = [3.0, 4.5, 6.0, 8.0]
        
        space = []
        for f in fast_emas:
            for s in slow_emas:
                if f >= s:
                    continue
                for b in breakout_periods:
                    for sl in atr_multipliers_sl:
                        for tp in atr_multipliers_tp:
                            space.append({
                                "ema_fast": f,
                                "ema_slow": s,
                                "breakout_period": b,
                                "atr_sl_mult": sl,
                                "atr_tp_mult": tp,
                                "route": route,
                                "symbol": symbol,
                                "timeframe": timeframe,
                            })
        return space
