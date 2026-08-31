#!/usr/bin/env python3
"""scripts/migrate_historical_candidates.py
Migración canónica de candidatos históricos y saneamiento de estados bajo v5.4.0.
"""
import sqlite3
import json
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from services.api.app.config import STATE_DB_PATH

DB_PATH = STATE_DB_PATH

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
            status_reason = 'Max DD OOS (' || ROUND(max_dd_oos_pct, 2) || '%) o IS (' || ROUND(max_dd_is_pct, 2) || '%) excede el limite estricto de Fondeo (<= 4.5%).'
        WHERE route = 'FONDEO' AND (max_dd_oos_pct > 4.5 OR max_dd_is_pct > 4.5) AND status = 'APPROVED'
    """)
    print(f"Fondeo invalidos corregidos: {cur.rowcount}")

    # 1b. Corregir cualquier candidato APPROVED con PF insuficiente (ambos < 1.20)
    cur.execute("""
        UPDATE candidates
        SET status = 'REVALIDATION_REQUIRED',
            status_reason = 'PF insuficiente (OOS ' || ROUND(COALESCE(profit_factor_oos, 0), 2) || ' / IS ' || ROUND(COALESCE(profit_factor_is, 0), 2) || ') para certificacion APPROVED (requiere >= 1.20).'
        WHERE status = 'APPROVED' AND NOT (COALESCE(profit_factor_oos, 0) >= 1.20 OR COALESCE(profit_factor_is, 0) >= 1.20)
    """)
    print(f"Candidatos APPROVED con PF insuficiente corregidos: {cur.rowcount}")

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
