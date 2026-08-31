#!/usr/bin/env python3
"""FASE 1 — Censo del catálogo con el criterio 1.1 sellado (plan v4).

Criterio de "base válida para ULTRA" (plan/bloques/F01_censo_catalogo.md — NO se relaja aquí):
  c1  >= 200 operaciones OOS
  c2  PF OOS >= 1.25
  c3  ratio OOS/IS >= 0.5
  c4  11 gates PASSED con evidencia física en data/evidence/<candidate_id>/
  c5  DSR positivo (si no es computable desde la BD: NO_EVALUABLE => fail-closed)
  c6  persistencia del edge entre mitades del OOS (ídem fail-closed)

Reclasificación (plan 1.2): lo que no cumple TODO y está en un estado no terminal pasa a
LEGACY_NO_CERTIFICADO con la lista de criterios incumplidos. Los estados terminales
(REJECTED_*, RECHAZADA_*, LEGACY_*, BLOCKED_*) conservan su etiqueta, que ya es honesta y
más granular. Nada se borra; cada cambio deja evento en audit_events.

Uso:
    python scripts/censo_f01.py                    # dry-run + informe
    python scripts/censo_f01.py --aplicar          # reclasifica y escribe informe
    python scripts/censo_f01.py --out informe.md   # ruta del informe (por defecto orchestration/results/censo_f01.md)
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
EVIDENCE_ROOT = REPO_ROOT / "data" / "evidence"

TERMINAL_PREFIXES = ("REJECTED", "RECHAZADA", "LEGACY_", "BLOCKED_")
APPROVED_STATUSES = ("APPROVED", "APPROVED_CURRENT_ENGINE")

MIN_TRADES_OOS = 200
MIN_PF_OOS = 1.25
MIN_RATIO_OOS_IS = 0.5
GATES_REQUIRED = 11


def evaluar(row: sqlite3.Row) -> dict:
    """Aplica el criterio 1.1. Devuelve dict con veredicto por criterio y global."""
    fallos: list[str] = []

    trades_oos = row["trades_oos"] or 0
    if trades_oos < MIN_TRADES_OOS:
        fallos.append(f"c1: trades_oos={trades_oos} < {MIN_TRADES_OOS}")

    pf_oos = row["profit_factor_oos"] or 0.0
    if pf_oos < MIN_PF_OOS:
        fallos.append(f"c2: pf_oos={pf_oos:.2f} < {MIN_PF_OOS}")

    ratio = row["ratio_oos_is"]
    if ratio is None or ratio < MIN_RATIO_OOS_IS:
        fallos.append(f"c3: ratio_oos_is={ratio if ratio is not None else 'NULL'} < {MIN_RATIO_OOS_IS}")

    gates = row["gates_passed"] or 0
    bundle = EVIDENCE_ROOT / row["candidate_id"] / "evidence_bundle.json"
    if gates < GATES_REQUIRED:
        fallos.append(f"c4: gates_passed={gates} < {GATES_REQUIRED}")
    elif not bundle.exists():
        fallos.append(f"c4: sin evidencia física ({bundle.relative_to(REPO_ROOT)})")

    # c5 y c6 requieren distribución de operaciones/trials; no computables desde columnas.
    # Fail-closed: NO_EVALUABLE cuenta como incumplido. El pipeline 5.6.0 los computará
    # para candidatas nuevas (F03).
    fallos.append("c5: DSR NO_EVALUABLE desde BD (fail-closed)")
    fallos.append("c6: persistencia OOS NO_EVALUABLE desde BD (fail-closed)")

    if row["engine_version"] != CURRENT_ENGINE_VERSION:
        fallos.append(f"motor: {row['engine_version']} != {CURRENT_ENGINE_VERSION} (regla #26)")

    return {"cumple": not fallos, "fallos": fallos}


def es_terminal(status: str) -> bool:
    return status.startswith(TERMINAL_PREFIXES)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aplicar", action="store_true")
    parser.add_argument("--db", default=str(DB_PATH))
    parser.add_argument("--out", default=str(REPO_ROOT / "orchestration/results/censo_f01.md"))
    args = parser.parse_args()

    conn = sqlite3.connect(args.db, timeout=15.0)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT candidate_id, route, symbol, timeframe, status, status_reason, "
            "COALESCE(gates_passed,0) AS gates_passed, trades_oos, profit_factor_oos, "
            "ratio_oos_is, engine_version FROM candidates"
        ).fetchall()

        antes: dict[str, int] = {}
        supervivientes: list[str] = []
        a_reclasificar: list[tuple[sqlite3.Row, list[str]]] = []
        terminales = 0

        for r in rows:
            antes[r["status"]] = antes.get(r["status"], 0) + 1
            v = evaluar(r)
            if v["cumple"]:
                supervivientes.append(r["candidate_id"])
            elif es_terminal(r["status"]):
                terminales += 1
            else:
                a_reclasificar.append((r, v["fallos"]))

        now_iso = datetime.now(timezone.utc).isoformat()
        if args.aplicar and a_reclasificar:
            with conn:
                for r, fallos in a_reclasificar:
                    razon = (
                        f"Censo F01 (criterio 1.1): {'; '.join(fallos)}. "
                        f"Estado previo: {r['status']}. Razon previa: {r['status_reason'] or '(sin razon)'}"
                    )
                    conn.execute(
                        "UPDATE candidates SET status='LEGACY_NO_CERTIFICADO', status_reason=? "
                        "WHERE candidate_id=?",
                        (razon[:2000], r["candidate_id"]),
                    )
                    conn.execute(
                        "INSERT INTO audit_events (event_id, category, route, title, description, "
                        "severity, metadata_json, created_at) VALUES (?,?,?,?,?,?,?,?)",
                        (
                            f"censoF01_{r['candidate_id']}_{now_iso}",
                            "GOVERNANCE",
                            r["route"],
                            f"Censo F01: {r['candidate_id']} {r['status']} -> LEGACY_NO_CERTIFICADO",
                            razon[:2000],
                            "INFO",
                            json.dumps({
                                "candidate_id": r["candidate_id"],
                                "old_status": r["status"],
                                "criterios_incumplidos": fallos,
                                "fase": "F01",
                            }),
                            now_iso,
                        ),
                    )

        despues: dict[str, int] = {}
        for r in conn.execute("SELECT status, COUNT(*) n FROM candidates GROUP BY status"):
            despues[r["status"]] = r["n"]

        # Informe
        lineas = [
            "# CENSO F01 — criterio 1.1 sellado",
            f"\nFecha: {now_iso} · Motor vigente: {CURRENT_ENGINE_VERSION} · "
            f"Modo: {'APLICADO' if args.aplicar else 'DRY-RUN'}",
            f"\nTotal candidatos: {len(rows)}",
            f"\n**Supervivientes del criterio 1.1: {len(supervivientes)}**",
        ]
        if supervivientes:
            lineas += [""] + [f"- {s}" for s in supervivientes]
        lineas += [
            f"\nEn estados terminales (conservan etiqueta): {terminales}",
            f"Reclasificados a LEGACY_NO_CERTIFICADO: {len(a_reclasificar)}"
            + ("" if args.aplicar else " (pendiente de --aplicar)"),
            "\n## Censo por estado (antes)",
            "| Estado | n |", "| :--- | ---: |",
        ]
        lineas += [f"| {k} | {v} |" for k, v in sorted(antes.items(), key=lambda kv: -kv[1])]
        lineas += ["\n## Censo por estado (después)", "| Estado | n |", "| :--- | ---: |"]
        lineas += [f"| {k} | {v} |" for k, v in sorted(despues.items(), key=lambda kv: -kv[1])]
        lineas += ["\n## Razones de descarte (muestra de 20)", ""]
        for r, fallos in a_reclasificar[:20]:
            lineas.append(f"- `{r['candidate_id']}` ({r['status']}): {'; '.join(fallos[:3])} ...")
        lineas += [
            "\n## Notas",
            "- c5 (DSR) y c6 (persistencia OOS) no son computables desde las columnas de la BD: "
            "se aplican fail-closed. El pipeline 5.6.0 debe computarlos para candidatas nuevas (F03).",
            "- Expectativa honesta del plan: pocos o ningún superviviente. El corpus base se "
            "construye en F03 con el motor realista, no rescatando el catálogo viejo.",
        ]

        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("\n".join(lineas), encoding="utf-8")
        print(f"Informe: {out}")
        print(f"Supervivientes: {len(supervivientes)} · Terminales: {terminales} · "
              f"Reclasificables: {len(a_reclasificar)} · Modo: {'APLICADO' if args.aplicar else 'DRY-RUN'}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
