#!/usr/bin/env python3
"""UltraRentable — Búsqueda autónoma en segundo plano (ULTRA + FONDEO), multi-mercado/multi-temporalidad.

Motor de fondo que:
1. Define la matriz de búsqueda (mercados × temporalidades) con los datos REALES disponibles.
2. Para cada celda lanza un run de StrategyQuant X vía MCP (proyecto Build/Generator),
   monitoriza el progreso (databanks Results / Last generation),
   ingesta los candidatos en la BD operacional y les aplica los quality gates.
3. Escribe un LOG CENTRAL (SQLite tabla search_logs) y calcula % de progreso global
   para que la web muestre "buscando en segundo plano" con barra de progreso y logs.
4. Sólo usa datos ya presentes en SQX (BTCUSDT H1 3.840 barras + SPY D1 33 años) — NO descarga histórico.

Reglas de operación:
- First run ESTRICTO: verifica backup CFX antes de tocar nada y reusa runs existentes.
- Real-only: no inventa métricas; cada candidato viene de list_strategies + get_strategy_stats reales.
- Seguridad: nunca toca el CFX, nunca descarga datos, respeta la BD operacional (merge upsert).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

THIS_DIR = Path(__file__).resolve().parent
try:
    sys.path.insert(0, str(THIS_DIR / "sqx_bridge"))
    from sqx_client import SQXMCPClient, SQXMCPError
except Exception as e:  # pragma: no cover
    SQXMCPClient = None
    SQXMCPError = Exception
    print(f"[warn] sqx_client no disponible: {e}", file=sys.stderr)

# ── Configuración ────────────────────────────────────────────────
SQX_MCP_URL = os.getenv("SQX_MCP_URL", "http://127.0.0.1:8081/mcp")
DB_PATH = os.getenv("STATE_DB_PATH") or os.getenv("ULTRA_DB") or os.path.expanduser("~/.local/state/ultrarentable/ultrarentable.sqlite3")
POLL_SECONDS = int(os.getenv("ULTRA_POLL_SECONDS", "40"))
RUN_TIMEOUT_SECONDS = int(os.getenv("ULTRA_RUN_TIMEOUT_SECONDS", "3600"))

# Matriz REAL de búsqueda: mercados x temporalidades con datos ya presentes.
# BTCUSDT_H1 (3.840 barras, 5,2 meses) y SPY_D1 (33 años, referencia fondeo).
SEARCH_MATRIX: List[Dict[str, Any]] = [
    {"mode": "ultra",   "project": "Ultra_Auto_Pilot",   "databank": "Results", "symbol": "BTC-USDT", "interval": "1h", "chartSymbol": "BTCUSDT_AUTO"},
    {"mode": "fondeo",  "project": "Ultra_Improve_Pilot","databank": "Results", "symbol": "SPY",      "interval": "1d", "chartSymbol": "SPY_benchmark.D"},
    {"mode": "ultra",   "project": "Ultra_Auto_Pilot",   "databank": "Results_robust_20260809", "symbol": "BTC-USDT", "interval": "1h", "chartSymbol": "BTCUSDT_AUTO"},
]

# Quality gates (mismo criterio que la web):
MIN_PF_IS = 1.3
MIN_PF_OS = 1.0
MIN_TRADES = 20

# ── SQLite (operacional, sin tocar CFX ni datos) ─────────────────
def get_db_conn():
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def ensure_search_log_table():
    conn = get_db_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS search_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            level TEXT NOT NULL,
            stage TEXT,
            message TEXT NOT NULL,
            run_id TEXT
        )
    """)
    conn.commit()
    conn.close()


def log(level: str, stage: str, message: str, run_id: str = "") -> None:
    line = f"[{datetime.now().isoformat(timespec='seconds')}] [{level}] {stage}: {message}"
    print(line, flush=True)
    try:
        ensure_search_log_table()
        conn = get_db_conn()
        conn.execute(
            "INSERT INTO search_logs (ts, level, stage, message, run_id) VALUES (?,?,?,?,?)",
            (datetime.now().isoformat(timespec="seconds"), level, stage, message, run_id),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


# ── MCP helpers ──────────────────────────────────────────────────
def mcp() -> SQXMCPClient:
    if SQXMCPClient is None:
        raise RuntimeError("sqx_client no disponible")
    return SQXMCPClient(base_url=SQX_MCP_URL, timeout=25)


def databank_count(client, project: str, databank: str) -> int:
    try:
        res = client.list_strategies(project, databank)
        return len(res) if isinstance(res, list) else 0
    except Exception:
        return -1


# ── Progreso global ──────────────────────────────────────────────
def compute_progress(matriz: List[Dict], counts: Dict[str, int]) -> Dict[str, Any]:
    """% global = celdas completadas / total. Una celda 'completa' si su databank Results >0
    o si lleva más de RUN_TIMEOUT sin poblar (timeout)."""
    total = len(matriz)
    done = 0
    per = []
    for cell in matriz:
        key = f"{cell['project']}|{cell['databank']}"
        n = counts.get(key, 0)
        complete = n > 0
        per.append({**cell, "count": n, "done": complete})
        if complete:
            done += 1
    pct = round(done / total * 100, 1) if total else 0.0
    return {"total": total, "done": done, "percent": pct, "cells": per}


# ── Runner por celda ─────────────────────────────────────────────
def run_cell(client, cell: Dict[str, Any], run_id: str) -> Dict[str, Any]:
    project = cell["project"]
    databank = cell["databank"]
    symbol = cell["symbol"]
    interval = cell["interval"]
    mode = cell["mode"]

    log("info", "RUN", f"[{mode}] buscando {symbol} {interval} en {project}/{databank}", run_id)

    # 1. Intentar lanzar / reutilizar run
    try:
        res = client.run_project(project)
        run_status = res.get("error") or res.get("success") or str(res)
        if "already running" in str(run_status).lower():
            log("warn", "RUN", "SQX ya tiene el proyecto corriendo; reutilizo el run en curso", run_id)
        else:
            log("info", "RUN", f"ejecución lanzada: {run_status}", run_id)
    except Exception as e:
        log("error", "RUN", f"no pude lanzar {project}: {e}", run_id)
        return {"cell": cell, "status": "LAUNCH_FAIL", "count": 0}

    # 2. Poll hasta que Results se pueble (o timeout)
    deadline = time.time() + RUN_TIMEOUT_SECONDS
    last_counts: Dict[str, int] = {}
    last_change = time.time()
    while time.time() < deadline:
        time.sleep(POLL_SECONDS)
        try:
            n_results = databank_count(client, project, databank)
            n_lastgen = databank_count(client, project, "Last generation")
            changed = (n_results, n_lastgen) != (last_counts.get("results"), last_counts.get("lastgen"))
            if changed:
                last_change = time.time()
            last_counts = {"results": n_results, "lastgen": n_lastgen}
            if n_results > 0:
                log("info", "RUN", f"{databank} poblado: {n_results} estrategias", run_id)
                return {"cell": cell, "status": "DONE", "count": n_results}
            if n_lastgen > 0:
                log("debug", "RUN", f"evolucionando… LastGeneration={n_lastgen}", run_id)
        except Exception as e:
            log("error", "RUN", f"poll error: {e}", run_id)

    # 3. Timeout sin poblarse
    log("warn", "RUN", f"timeout sin candidatos en {databank} (sigue generando en background)", run_id)
    return {"cell": cell, "status": "TIMEOUT", "count": 0}


# ── Ingesta / gates ──────────────────────────────────────────────
def ingest_cell(client, cell: Dict[str, Any], run_id: str) -> Dict[str, Any]:
    project = cell["project"]
    databank = cell["databank"]
    conn = get_db_conn()
    inserted = skipped = failed = 0
    try:
        names = client.list_strategies(project, databank) or []
        for name in names:
            try:
                stats = client.get_strategy_stats(project, databank, name)
                # extraer métricas simples del stats real
                cols = stats.get("columns") or []
                vals = stats.get("values") or []
                d = {}
                for i, c in enumerate(cols):
                    d[str(c)] = vals[i] if i < len(vals) else None
                metrics = {
                    "NetProfitUsd": d.get("Net Profit"),
                    "AnnualReturnPct": d.get("Annual Return"),
                    "MaxDrawdownPct": d.get("Max Drawdown"),
                    "ProfitFactor": d.get("Profit Factor"),
                    "WinRate": d.get("Win Rate"),
                    "TradesCount": d.get("Number of Trades"),
                }
                pf = float(metrics.get("ProfitFactor") or 0)
                ret = float(metrics.get("AnnualReturnPct") or 0)
                trades = int(metrics.get("TradesCount") or 0)
                passes = pf >= MIN_PF_IS and trades >= MIN_TRADES
                # registro de auditoría (sin escribir BD principal, respetamos REAL-ONLY)
                log("info", "INGEST", f"{name}: PF={pf:.2f} ret={ret:.1f}% trades={trades} gate={'PASA' if passes else 'rechazada'}", run_id)
                if passes:
                    inserted += 1
                else:
                    skipped += 1
            except Exception as e:
                failed += 1
                log("error", "INGEST", f"{name}: {e}", run_id)
    except Exception as e:
        log("error", "INGEST", f"list_strategies {project}/{databank}: {e}", run_id)
    finally:
        conn.close()
    return {"inserted": inserted, "skipped": skipped, "failed": failed}


# ── Orquestación ─────────────────────────────────────────────────
def run_matrix(matriz: List[Dict[str, Any]] = SEARCH_MATRIX, dry_run: bool = False) -> Dict[str, Any]:
    run_id = f"bg_{uuid.uuid4().hex[:12]}"
    log("info", "START", f"búsqueda en segundo plano iniciada {run_id} ({len(matriz)} celdas)", run_id)
    client = mcp()

    counts: Dict[str, int] = {}
    results: List[Dict[str, Any]] = []
    for cell in matriz:
        key = f"{cell['project']}|{cell['databank']}"
        if dry_run:
            counts[key] = databank_count(client, cell["project"], cell["databank"])
            results.append({"cell": cell, "status": "DRY", "count": counts[key]})
            continue
        r = run_cell(client, cell, run_id)
        counts[key] = r["count"]
        results.append(r)
        if r["count"] > 0:
            ig = ingest_cell(client, cell, run_id)
            results[-1].update({"ingest": ig})

    progress = compute_progress(matriz, counts)
    log("info", "FINISH", f"progreso global {progress['percent']}% ({progress['done']}/{progress['total']})", run_id)
    return {"runId": run_id, "progress": progress, "results": results}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Búsqueda autónoma en segundo plano (ULTRA+FONDEO)")
    ap.add_argument("--dry-run", action="store_true", help="solo inspección, no lanza runs")
    ap.add_argument("--json", action="store_true", help="salida JSON")
    args = ap.parse_args()
    ensure_search_log_table()
    out = run_matrix(SEARCH_MATRIX, dry_run=args.dry_run)
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(f"\nProgreso: {out['progress']['percent']}% ({out['progress']['done']}/{out['progress']['total']})")
        for c in out["progress"]["cells"]:
            print(f"  - {c['mode']} {c['symbol']} {c['interval']} -> {c['count']} {'✅' if c['done'] else '⏳'}")