#!/usr/bin/env python3
"""Regla #26 de la doctrina: reclasificación de aprobaciones con motor no vigente.

Al subir CURRENT_ENGINE_VERSION, toda candidata en estado aprobado cuya engine_version
no sea la vigente deja de contar como aprobada: pasa a LEGACY_MOTOR_<motivo> con su razón
escrita y un evento en audit_events. Nunca se borra nada.

Uso:
    python scripts/gobernanza_regla26.py            # dry-run: muestra lo que cambiaría
    python scripts/gobernanza_regla26.py --aplicar  # ejecuta la reclasificación
    python scripts/gobernanza_regla26.py --motivo LEGACY_MOTOR_SIN_POINT_VALUE  # motivo específico
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from services.engine_version import CURRENT_ENGINE_VERSION  # noqa: E402
from services.api.app.config import STATE_DB_PATH  # noqa: E402

DB_PATH = STATE_DB_PATH
APPROVED_STATUSES = ("APPROVED", "APPROVED_CURRENT_ENGINE")
MOTIVO_DEFECTO = "LEGACY_MOTOR_VERSION_OBSOLETA"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aplicar", action="store_true", help="Ejecuta la reclasificación (sin esto: dry-run)")
    parser.add_argument("--motivo", default=MOTIVO_DEFECTO, help="Estado destino LEGACY_MOTOR_<motivo>")
    parser.add_argument("--db", default=str(DB_PATH), help="Ruta de la BD canónica")
    args = parser.parse_args()

    if not args.motivo.startswith("LEGACY_MOTOR_"):
        print(f"ERROR: el estado destino debe empezar por LEGACY_MOTOR_ (recibido: {args.motivo})")
        return 2

    db_file = Path(args.db)
    if not db_file.exists():
        print(f"ERROR: BD no encontrada: {db_file}")
        return 2

    conn = sqlite3.connect(str(db_file), timeout=15.0)
    conn.row_factory = sqlite3.Row
    try:
        placeholders = ",".join("?" for _ in APPROVED_STATUSES)
        rows = conn.execute(
            f"SELECT candidate_id, route, status, status_reason, engine_version, "
            f"COALESCE(gates_passed, 0) AS gates_passed FROM candidates "
            f"WHERE status IN ({placeholders}) AND engine_version <> ?",
            (*APPROVED_STATUSES, CURRENT_ENGINE_VERSION),
        ).fetchall()

        print(f"Motor vigente: {CURRENT_ENGINE_VERSION}")
        print(f"Aprobadas con motor no vigente: {len(rows)}")
        for r in rows[:10]:
            print(f"  {r['candidate_id']} [{r['route']}] motor={r['engine_version']} gates={r['gates_passed']}")
        if len(rows) > 10:
            print(f"  ... y {len(rows) - 10} más")

        if not rows:
            print("Nada que reclasificar: la regla #26 ya se cumple.")
            return 0

        if not args.aplicar:
            print("\nDRY-RUN: no se ha modificado nada. Ejecuta con --aplicar para reclasificar "
                  f"a {args.motivo}.")
            return 0

        now_iso = datetime.now(timezone.utc).isoformat()
        with conn:  # transacción única
            for r in rows:
                razon = (
                    f"Regla #26: aprobada con motor {r['engine_version']} != {CURRENT_ENGINE_VERSION} vigente; "
                    f"gates_passed={r['gates_passed']}. Razon previa: {r['status_reason'] or '(sin razon)'}"
                )
                conn.execute(
                    "UPDATE candidates SET status = ?, status_reason = ? WHERE candidate_id = ?",
                    (args.motivo, razon, r["candidate_id"]),
                )
                conn.execute(
                    "INSERT INTO audit_events (event_id, category, route, title, description, "
                    "severity, metadata_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        f"legacy26_{r['candidate_id']}_{now_iso}",
                        "GOVERNANCE",
                        r["route"],
                        f"Regla #26: {r['candidate_id']} {r['status']}@{r['engine_version']} -> {args.motivo}",
                        razon,
                        "WARNING",
                        json.dumps({
                            "candidate_id": r["candidate_id"],
                            "old_status": r["status"],
                            "old_version": r["engine_version"],
                            "new_version": CURRENT_ENGINE_VERSION,
                            "gates_passed": r["gates_passed"],
                            "regla": "#26 DOCTRINA_ORQUESTADOR",
                        }),
                        now_iso,
                    ),
                )

        restantes = conn.execute(
            f"SELECT COUNT(*) AS n FROM candidates WHERE status IN ({placeholders})",
            APPROVED_STATUSES,
        ).fetchone()["n"]
        print(f"\nAPLICADO: {len(rows)} candidatas -> {args.motivo} (con evento de auditoría cada una).")
        print(f"Aprobadas restantes tras la regla #26: {restantes}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
