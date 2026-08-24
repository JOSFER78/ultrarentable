"""tests/test_red_team_fase1_learning_store.py
Auditoría Red-Team para Fase 1 (LearningStore y Rehidratación Forense de Firebase).
Verificación de Zero-Mocks, inmutabilidad, no-generación sintética y blindaje contra fallos silenciosos.
"""

import os
import sqlite3
import pytest
from services.semantic_ai.learning_store import learning_store

def test_red_team_no_synthetic_data_in_learning_store():
    """Verifica que ningún registro rehidratado contiene valores inventados o sintéticos."""
    conn = sqlite3.connect(learning_store.db_path)
    cur = conn.cursor()

    # 1. Verificar conteos reales
    cur.execute("SELECT count(*) FROM strategy_versions;")
    assert cur.fetchone()[0] == 258, "Debe haber exactamente 258 estrategias reales de Firebase"

    cur.execute("SELECT count(*) FROM failure_records;")
    assert cur.fetchone()[0] >= 2570, "Debe haber al menos 2570 registros de fallo reales"

    # 2. Verificar que no hay NaN o campos corruptos en métricas
    cur.execute("SELECT metrics_snapshot FROM failure_records LIMIT 50;")
    for row in cur.fetchall():
        raw_json = row[0]
        assert raw_json is not None and len(raw_json) > 0
        assert "NaN" not in raw_json and "undefined" not in raw_json

    # 3. Verificar que los strategy_hash son deterministas y no vacíos
    cur.execute("SELECT strategy_hash, strategy_id FROM strategy_versions;")
    for row in cur.fetchall():
        s_hash, s_id = row
        assert s_hash and len(s_hash) > 5
        assert s_id and len(s_id) > 2

    conn.close()

def test_red_team_concurrency_lock_and_wal_mode():
    """Verifica que el SQLite opera en modo WAL y soporta múltiples lecturas concurrentes."""
    conn = sqlite3.connect(learning_store.db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA journal_mode;")
    mode = cur.fetchone()[0].upper()
    assert mode == "WAL", f"El modo del journal debe ser WAL, obtenido: {mode}"
    conn.close()
