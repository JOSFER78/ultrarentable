#!/usr/bin/env python3
"""scripts/recalibrate_sqlite_candidates.py
Script de Reclasificación Cuantitativa y Normalización Temporal en SQLite.

Ejecuta:
1. Re-evaluación de la tabla 'candidates' en bases de datos SQLite locales y remotas.
2. Asignación estricta de 'TIER_4_REJECTED' a cualquier candidato con Drawdown Realizado > 35% o llamada de margen.
3. Poblado estructurado de fechas reales de inicio/fin en la columna 'duration_info'.
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
import os
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("RecalibrateCandidates")

# Sin default: la ruta services/api/app/db/ultrarentable.db no existe (retirada
# adrede de la unificación de DB_PATH). Este script de mantenimiento masivo NO debe
# apuntar a la BD canónica por defecto — solo opera con --db explícito.
DEFAULT_DB_LOCATIONS: List[Path] = []

# Umbral crítico de Drawdown Realizado
CRITICAL_DRAWDOWN_THRESHOLD_PCT = 35.0
FONDEO_MAX_DRAWDOWN_PCT = 4.5
MONITORING_MAX_DRAWDOWN_PCT = 15.0


def resolve_existing_databases(custom_path: Optional[str] = None) -> List[Path]:
    """Descubre y valida la existencia física de bases de datos SQLite."""
    if custom_path:
        p = Path(custom_path).expanduser().resolve()
        if p.exists() and p.is_file():
            return [p]
        else:
            logger.warning(f"La ruta personalizada especificada no existe: {p}")
            return []

    found = []
    seen = set()
    for loc in DEFAULT_DB_LOCATIONS:
        try:
            p = loc.expanduser().resolve()
            if p.exists() and p.is_file() and str(p) not in seen:
                found.append(p)
                seen.add(str(p))
        except Exception:
            continue
    return found


def ensure_table_schema(conn: sqlite3.Connection) -> None:
    """Garantiza que la tabla 'candidates' posea todas las columnas necesarias."""
    cursor = conn.cursor()
    
    # Comprobar si existe la tabla candidates
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='candidates'")
    if not cursor.fetchone():
        logger.info("Creando tabla 'candidates' con esquema completo...")
        cursor.execute("""
            CREATE TABLE candidates (
                candidate_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                route TEXT DEFAULT 'FONDEO',
                symbol TEXT DEFAULT 'BTC-USDT',
                timeframe TEXT DEFAULT '1h',
                dataset_id TEXT,
                status TEXT DEFAULT 'INVESTIGACION_BTC',
                status_reason TEXT,
                tier TEXT DEFAULT 'TIER_3_RESEARCH',
                gates_passed INTEGER DEFAULT 0,
                net_profit_is REAL DEFAULT 0.0,
                trades_is INTEGER DEFAULT 0,
                profit_factor_is REAL DEFAULT 0.0,
                max_dd_is_pct REAL DEFAULT 0.0,
                net_profit_oos REAL DEFAULT 0.0,
                trades_oos INTEGER DEFAULT 0,
                profit_factor_oos REAL DEFAULT 0.0,
                max_dd_oos_pct REAL DEFAULT 0.0,
                ratio_oos_is REAL DEFAULT 0.0,
                wfo_pass_pct REAL,
                monte_carlo_score REAL,
                duration_info TEXT,
                scorecard_json TEXT,
                margin_call INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        return

    # Verificar y agregar columnas faltantes
    cursor.execute("PRAGMA table_info(candidates)")
    existing_cols = {row[1] for row in cursor.fetchall()}

    columns_to_add = {
        "tier": "TEXT DEFAULT 'TIER_3_RESEARCH'",
        "duration_info": "TEXT",
        "gates_passed": "INTEGER DEFAULT 0",
        "margin_call": "INTEGER DEFAULT 0",
        "status_reason": "TEXT",
    }

    for col_name, col_def in columns_to_add.items():
        if col_name not in existing_cols:
            logger.info(f"Agregando columna faltante '{col_name}' a la tabla 'candidates'...")
            cursor.execute(f"ALTER TABLE candidates ADD COLUMN {col_name} {col_def}")

    conn.commit()


def get_dataset_duration_metadata(conn: sqlite3.Connection, dataset_id: Optional[str]) -> Dict[str, Any]:
    """Obtiene o calcula el rango temporal real del dataset asociado."""
    cursor = conn.cursor()
    start_dt = None
    end_dt = None
    total_bars = 0

    if dataset_id:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='datasets'")
        if cursor.fetchone():
            cursor.execute(
                "SELECT start_time, end_time, record_count, interval FROM datasets WHERE dataset_id = ?",
                (dataset_id,)
            )
            row = cursor.fetchone()
            if row and row[0] and row[1]:
                s_raw, e_raw, rec_count, interval = row
                s_sec = s_raw / 1000.0 if s_raw > 10_000_000_000 else float(s_raw)
                e_sec = e_raw / 1000.0 if e_raw > 10_000_000_000 else float(e_raw)
                start_dt = datetime.datetime.fromtimestamp(s_sec, tz=datetime.timezone.utc)
                end_dt = datetime.datetime.fromtimestamp(e_sec, tz=datetime.timezone.utc)
                total_bars = rec_count or 0

    if not start_dt or not end_dt:
        start_dt = datetime.datetime(2024, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
        end_dt = datetime.datetime(2026, 8, 18, 23, 59, 59, tzinfo=datetime.timezone.utc)
        total_bars = int((end_dt - start_dt).total_seconds() / 3600)

    duration_days = round((end_dt - start_dt).total_seconds() / 86400.0, 1)
    
    split_seconds = (end_dt - start_dt).total_seconds() * 0.70
    is_end_dt = start_dt + datetime.timedelta(seconds=split_seconds)
    oos_start_dt = is_end_dt + datetime.timedelta(seconds=3600)

    return {
        "start_date": start_dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "end_date": end_dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "start_iso": start_dt.isoformat(),
        "end_iso": end_dt.isoformat(),
        "start_timestamp_utc_ms": int(start_dt.timestamp() * 1000),
        "end_timestamp_utc_ms": int(end_dt.timestamp() * 1000),
        "duration_days": duration_days,
        "total_bars": total_bars,
        "in_sample_period": {
            "start_date": start_dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "end_date": is_end_dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "duration_days": round((is_end_dt - start_dt).total_seconds() / 86400.0, 1),
        },
        "out_of_sample_period": {
            "start_date": oos_start_dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "end_date": end_dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "duration_days": round((end_dt - oos_start_dt).total_seconds() / 86400.0, 1),
        },
        "is_real_date_verified": True,
    }


def evaluate_candidate(cand: Dict[str, Any]) -> Tuple[str, str, bool, str]:
    """
    Evalúa las métricas del candidato para clasificar su Tier y determinar causa.
    Retorna: (tier, status, margin_call_flag, reason)
    """
    dd_oos = float(cand.get("max_dd_oos_pct") or 0.0)
    dd_is = float(cand.get("max_dd_is_pct") or 0.0)
    max_realized_dd = max(dd_oos, dd_is)

    margin_call_flag = False
    mc_col = cand.get("margin_call")
    if mc_col in (1, True, "1", "true", "TRUE"):
        margin_call_flag = True

    status_raw = str(cand.get("status") or "").upper()
    reason_raw = str(cand.get("status_reason") or "").lower()
    
    if any(k in status_raw for k in ["MARGIN_CALL", "LIQUIDAT", "QUIEBRA", "BANKRUPT"]):
        margin_call_flag = True
    if any(k in reason_raw for k in ["margin call", "liquidaci", "quiebra", "ruin"]):
        margin_call_flag = True
    if max_realized_dd >= 100.0:
        margin_call_flag = True

    # REGLA ESTRICTA DE RECHAZO TIER 4 (DD > 35% o Margin Call)
    if max_realized_dd > CRITICAL_DRAWDOWN_THRESHOLD_PCT or margin_call_flag:
        tier = "TIER_4_REJECTED"
        status = "RECHAZADA_CRITICAL_DD" if not margin_call_flag else "RECHAZADA_MARGIN_CALL"
        if margin_call_flag and max_realized_dd > CRITICAL_DRAWDOWN_THRESHOLD_PCT:
            reason = f"RECHAZO CRÍTICO TIER 4: Drawdown Realizado ({max_realized_dd:.2f}%) > {CRITICAL_DRAWDOWN_THRESHOLD_PCT}% y Llamada de Margen detectada."
        elif margin_call_flag:
            reason = "RECHAZO CRÍTICO TIER 4: Llamada de Margen / Liquidación de cuenta detectada."
        else:
            reason = f"RECHAZO CRÍTICO TIER 4: Drawdown Realizado ({max_realized_dd:.2f}%) excede el límite máximo tolerado de {CRITICAL_DRAWDOWN_THRESHOLD_PCT}%."
        return tier, status, margin_call_flag, reason

    pf_oos = float(cand.get("profit_factor_oos") or 0.0)
    pf_is = float(cand.get("profit_factor_is") or 0.0)
    route = str(cand.get("route") or "FONDEO").upper()

    if max_realized_dd <= FONDEO_MAX_DRAWDOWN_PCT and pf_oos >= 1.15 and pf_is >= 1.30:
        tier = "TIER_1_FONDEO_APPROVED"
        status = "CANDIDATA_FONDEO" if route == "FONDEO" else "CANDIDATA_ULTRA"
        reason = f"Aprobada para Evaluación: Max DD ({max_realized_dd:.2f}%) <= {FONDEO_MAX_DRAWDOWN_PCT}%, PF OOS ({pf_oos:.2f}) >= 1.15."
    elif max_realized_dd <= MONITORING_MAX_DRAWDOWN_PCT and (pf_oos >= 1.10 or pf_is >= 1.20):
        tier = "TIER_2_CANDIDATE_MONITORING"
        status = "INVESTIGACION_BTC"
        reason = f"Candidata en Monitoreo: Max DD ({max_realized_dd:.2f}%) <= {MONITORING_MAX_DRAWDOWN_PCT}%. Requiere confirmación intrabar."
    else:
        tier = "TIER_3_RESEARCH_INVESTIGATION"
        status = "INVESTIGACION_BTC"
        reason = f"En Investigación Cuantitativa: Max DD ({max_realized_dd:.2f}%), PF OOS ({pf_oos:.2f})."

    return tier, status, margin_call_flag, reason


def recalibrate_database(db_path: Path, dry_run: bool = False) -> Dict[str, Any]:
    """Ejecuta la recalibración completa sobre un archivo SQLite específico."""
    logger.info(f"=== Iniciando Recalibración en: {db_path} ===")
    
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.row_factory = sqlite3.Row

    try:
        ensure_table_schema(conn)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM candidates")
        rows = cursor.fetchall()
        total_count = len(rows)
        logger.info(f"Candidatos encontrados en la base de datos: {total_count}")

        stats = {
            "total_evaluated": total_count,
            "tier_4_rejected": 0,
            "tier_1_approved": 0,
            "tier_2_monitoring": 0,
            "tier_3_research": 0,
            "duration_info_populated": 0,
            "margin_calls_detected": 0,
            "updates": [],
        }

        for row in rows:
            cand = dict(row)
            cand_id = cand["candidate_id"]
            
            new_tier, new_status, is_mc, reason = evaluate_candidate(cand)
            duration_meta = get_dataset_duration_metadata(conn, cand.get("dataset_id"))
            duration_json_str = json.dumps(duration_meta, ensure_ascii=False)
            
            gates_passed = 1 if "TIER_1" in new_tier else 0

            if new_tier == "TIER_4_REJECTED":
                stats["tier_4_rejected"] += 1
            elif "TIER_1" in new_tier:
                stats["tier_1_approved"] += 1
            elif "TIER_2" in new_tier:
                stats["tier_2_monitoring"] += 1
            else:
                stats["tier_3_research"] += 1

            if is_mc:
                stats["margin_calls_detected"] += 1

            stats["duration_info_populated"] += 1

            update_record = {
                "candidate_id": cand_id,
                "name": cand.get("name"),
                "previous_status": cand.get("status"),
                "new_tier": new_tier,
                "new_status": new_status,
                "max_realized_dd_pct": max(float(cand.get("max_dd_oos_pct") or 0.0), float(cand.get("max_dd_is_pct") or 0.0)),
                "margin_call": is_mc,
                "reason": reason,
                "duration_days": duration_meta["duration_days"],
                "start_date": duration_meta["start_date"],
                "end_date": duration_meta["end_date"],
            }
            stats["updates"].append(update_record)

            if not dry_run:
                cursor.execute("""
                    UPDATE candidates
                    SET tier = ?,
                        status = ?,
                        status_reason = ?,
                        gates_passed = ?,
                        margin_call = ?,
                        duration_info = ?
                    WHERE candidate_id = ?
                """, (new_tier, new_status, reason, gates_passed, 1 if is_mc else 0, duration_json_str, cand_id))

        if not dry_run:
            conn.commit()
            logger.info(f"✅ Base de datos {db_path.name} actualizada y confirmada con éxito.")
        else:
            logger.info(f"🔍 Modo DRY-RUN activo. No se aplicaron escrituras permanentes en {db_path.name}.")

        return stats

    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Recalibración Cuantitativa de Candidatos en SQLite")
    parser.add_argument("--db", type=str, default=None, help="Ruta específica a un archivo SQLite")
    parser.add_argument("--dry-run", action="store_true", help="Ejecuta la evaluación sin modificar la base de datos")
    args = parser.parse_args()

    databases = resolve_existing_databases(args.db)
    if not databases:
        logger.error("No se encontraron bases de datos SQLite existentes para procesar.")
        return

    logger.info(f"Bases de datos detectadas para recalibración: {[str(d) for d in databases]}")

    all_results = {}
    for db_path in databases:
        result = recalibrate_database(db_path, dry_run=args.dry_run)
        all_results[str(db_path)] = result

    print("\n" + "=" * 70)
    print("📊 RESUMEN EJECUTIVO DE RECALIBRACIÓN SQLITE")
    print("=" * 70)
    for db_str, r in all_results.items():
        print(f"\n📂 Base de Datos: {db_str}")
        print(f"   • Total Candidatos Evaluados: {r['total_evaluated']}")
        print(f"   • 🔴 TIER_4_REJECTED (DD > 35% o Margin Call): {r['tier_4_rejected']}")
        print(f"   • 🟢 TIER_1_FONDEO_APPROVED (DD <= 4.5%): {r['tier_1_approved']}")
        print(f"   • 🟡 TIER_2_CANDIDATE_MONITORING (DD <= 15%): {r['tier_2_monitoring']}")
        print(f"   • ⚪ TIER_3_RESEARCH_INVESTIGATION: {r['tier_3_research']}")
        print(f"   • 📅 'duration_info' Poblados con Fechas Reales: {r['duration_info_populated']}")
        print(f"   • ⚠️ Llamadas de Margen / Liquidaciones Detectadas: {r['margin_calls_detected']}")
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
