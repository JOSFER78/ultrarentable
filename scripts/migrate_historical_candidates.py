#!/usr/bin/env python3
"""scripts/migrate_historical_candidates.py
Migración canónica de candidatos históricos y saneamiento de estados bajo v5.4.0.
"""
import sqlite3
import json
import time
from pathlib import Path

DB_PATH = Path.home() / ".local" / "state" / "ultrarentable" / "ultrarentable.sqlite3"

def run_migration():
    if not DB_PATH.exists():
        print(f"Base de datos no encontrada en {DB_PATH}, omitiendo.")
        return

    conn = sqlite3.connect(str(DB_PATH), timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    cur = conn.cursor()

    # 1. Corregir cualquier candidato de Fondeo con status APPROVED pero DD > 4.5%
    cur.execute("""
        UPDATE candidates
        SET status = 'RECHAZADA_MARGIN_CALL',
            status_reason = 'Max DD OOS (' || ROUND(max_dd_oos_pct, 2) || '%) excede el limite estricto de Fondeo (<= 4.5%).'
        WHERE route = 'FONDEO' AND max_dd_oos_pct > 4.5 AND status = 'APPROVED'
    """)
    print(f"Fondeo invalidos corregidos: {cur.rowcount}")

    # 1c. Corregir cualquier candidato APPROVED con max_dd_oos_pct >= 95.0% (Margin Call)
    cur.execute("""
        UPDATE candidates
        SET status = 'RECHAZADA_MARGIN_CALL',
            status_reason = 'Max DD OOS (' || ROUND(max_dd_oos_pct, 2) || '%) excede el 95% (Margin Call / Ruina).'
        WHERE status = 'APPROVED' AND max_dd_oos_pct >= 95.0
    """)
    print(f"Candidatos con Margin Call corregidos: {cur.rowcount}")

    # 2. Estampar engine_version a 5.4.0 en todos los candidatos
    cur.execute("""
        UPDATE candidates
        SET engine_version = '5.4.0'
        WHERE engine_version != '5.4.0'
    """)
    print(f"Candidatos estampados a v5.4.0: {cur.rowcount}")

    conn.commit()
    conn.close()
    print("Saneamiento completado exitosamente.")

if __name__ == "__main__":
    run_migration()
