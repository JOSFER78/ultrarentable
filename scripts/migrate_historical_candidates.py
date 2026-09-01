#!/usr/bin/env python3
"""scripts/migrate_historical_candidates.py
Migración canónica de candidatos históricos y saneamiento de estados bajo v5.4.0.

W4.2 (AG-C, 2026-09-01): este script NO es un job idempotente re-ejecutable en cualquier
momento -- es el saneamiento HISTÓRICO de un evento puntual (el lanzamiento de motor v5.4.0,
2026-08-25). El paso 2 estampa `engine_version = '5.4.0'` EN TODOS los candidatos de la BD
viva sin condición; con el motor ya en v5.17.0 (services/engine_version.py), volver a
ejecutar este script hoy sobrescribiría el engine_version REAL (correcto) de cada candidato
certificado con el motor vigente por el literal histórico '5.4.0', y todo pasaría a
descartarse como STALE aguas abajo (is_version_stale, gobernanza_regla26) -- el mismo bug de
fondo que motivó esta tarea, pero en sentido inverso y sobre datos ya certificados. Por eso
`run_migration()` se niega a correr salvo que el motor vigente siga siendo exactamente el de
la migración; para un saneamiento equivalente sobre el motor vigente, escribe un script
nuevo scoped a esa versión -- no reutilices este.
"""
import sqlite3
import json
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from services.api.app.config import STATE_DB_PATH
from services.engine_version import CURRENT_ENGINE_VERSION

DB_PATH = STATE_DB_PATH

# Ámbito histórico de ESTE saneamiento concreto (no confundir con el motor vigente).
_MIGRACION_ENGINE_VERSION_OBJETIVO = "5.4.0"


def run_migration() -> int:
    if CURRENT_ENGINE_VERSION != _MIGRACION_ENGINE_VERSION_OBJETIVO:
        print(
            f"ABORTADO (fail-closed, W4.2): esta migración es el saneamiento HISTÓRICO del "
            f"lanzamiento de motor v{_MIGRACION_ENGINE_VERSION_OBJETIVO}. El motor vigente es "
            f"v{CURRENT_ENGINE_VERSION} (SSOT: services/engine_version.py). Ejecutar este "
            f"script ahora sobrescribiría el engine_version REAL de cada candidato de la BD "
            f"viva con el literal histórico '{_MIGRACION_ENGINE_VERSION_OBJETIVO}', "
            f"descartando como STALE todo lo certificado con el motor vigente. No se ejecuta. "
            f"Si hace falta un saneamiento equivalente para v{CURRENT_ENGINE_VERSION}, escribe "
            f"un script nuevo scoped a esa versión."
        )
        return 1
    if not DB_PATH.exists():
        print(f"Base de datos no encontrada en {DB_PATH}, omitiendo.")
        return 0

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
    return 0

if __name__ == "__main__":
    raise SystemExit(run_migration())
