"""
Gestor de Persistencia Dual Atómica (SQLite WAL + Atomic JSON Swap)
Ultrarentable V3.2.0 · Zero Mocks Architecture
"""

import sqlite3
import json
import os
import tempfile
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(
        self,
        db_path: str = "services/api/data/providers.db",
        json_path: str = "apps/web/data/providers.json",
    ):
        self.db_path = db_path
        self.json_path = json_path
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS prop_firm_updates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    firm_slug TEXT NOT NULL,
                    firm_name TEXT NOT NULL,
                    scraped_at TIMESTAMP NOT NULL,
                    raw_data TEXT NOT NULL,
                    changes_summary TEXT
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS update_runs (
                    run_id TEXT PRIMARY KEY,
                    started_at TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP,
                    status TEXT NOT NULL,
                    firms_scanned INTEGER DEFAULT 0,
                    firms_updated INTEGER DEFAULT 0,
                    changes_log TEXT
                );
                """
            )
            conn.commit()

    def record_run(self, run_id: str, status: str, changes: List[str]):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO update_runs (run_id, started_at, completed_at, status, changes_log)
                VALUES (?, ?, ?, ?, ?)
                """,
                (run_id, datetime.utcnow(), datetime.utcnow(), status, json.dumps(changes)),
            )
            conn.commit()

    def atomic_json_swap(self, data: Dict[str, Any]):
        os.makedirs(os.path.dirname(self.json_path), exist_ok=True)
        dir_name = os.path.dirname(self.json_path)
        with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False) as tf:
            json.dump(data, tf, indent=2)
            temp_name = tf.name
        os.replace(temp_name, self.json_path)
        logger.info(f"Atomic swap completed successfully for {self.json_path}")
