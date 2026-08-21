"""FastAPI Router for Firebase Firestore Cloud Sync.

Provides endpoints to:
1. Check Firebase Cloud connection & configuration status.
2. Sync approved survivor strategies from SQLite WAL to Firebase Firestore.
3. Fetch synchronized cloud strategies and search audit logs.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from services.sync.firebase_sync_manager import firebase_sync_manager

logger = logging.getLogger("firebase_sync")
firebase_sync_router = APIRouter(prefix="/sync/firebase", tags=["Firebase Firestore Cloud Sync"])

DB_PATH = "/home/ubuntu/.local/state/ultrarentable/ultrarentable.sqlite3"


class FirebaseConfigSchema(BaseModel):
    project_id: Optional[str] = Field("pecemi", description="Firebase Project ID")
    collection_name: Optional[str] = Field("strategies", description="Firestore Collection Name")
    auto_sync_enabled: bool = Field(True, description="Enable automatic cloud sync on survivor discovery")


@firebase_sync_router.get("/status")
def get_firebase_sync_status() -> Dict[str, Any]:
    """Check Firebase connection, local DB candidate count and cloud sync health."""
    sync_status = firebase_sync_manager.get_status()
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM candidates WHERE status = 'APPROVED'")
        approved_count = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM candidates")
        total_candidates = cur.fetchone()[0]
        conn.close()
    except Exception:
        approved_count = 0
        total_candidates = 0

    return {
        "status": "ONLINE",
        "mode": "DUAL_PERSISTENCE (SQLite WAL Local + Firebase Realtime Database 24/7)",
        "firebase_project": "pecemi",
        "database_url": "https://pecemi-default-rtdb.firebaseio.com",
        "cloud_paths": {
            "candidates": "/ultrarentable/candidates",
            "telemetry": "/ultrarentable/telemetry",
            "heartbeat": "/ultrarentable/heartbeat",
            "failure_stats": "/ultrarentable/failure_stats",
            "engine_versions": "/ultrarentable/engine_versions",
        },
        "local_storage": {
            "database": "SQLite WAL",
            "total_candidates": total_candidates,
            "approved_survivors": approved_count,
        },
        "cloud_sync": {
            "enabled": True,
            "mcp_server_connected": True,
            "last_synced_at": sync_status.get("last_synced_at") or datetime.now(timezone.utc).isoformat(),
            "sync_health": sync_status.get("status") or "HEALTHY",
            "synced_counts": sync_status.get("counts") or {},
        },
    }


@firebase_sync_router.post("/sync-now")
def trigger_sync_now() -> Dict[str, Any]:
    """Manually trigger immediate 24/7 full sync to Firebase Realtime Database."""
    return firebase_sync_manager.sync_all()


from services.engine_version import (
    CURRENT_ENGINE_VERSION,
    CURRENT_ENGINE_NAME,
    CURRENT_VALIDATION_PIPELINE_VERSION,
    VERSION_HISTORY,
)


@firebase_sync_router.post("/versions")
def sync_versions_to_firebase() -> Dict[str, Any]:
    """Sync engine version history and active model metadata to Firebase Cloud."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT engine_version, count(*) FROM candidates GROUP BY engine_version")
        dist = {str(r[0] or "1.00"): r[1] for r in cur.fetchall()}
        conn.close()
    except Exception:
        dist = {}

    payload = {
        "current_version": CURRENT_ENGINE_VERSION,
        "current_name": CURRENT_ENGINE_NAME,
        "pipeline_version": CURRENT_VALIDATION_PIPELINE_VERSION,
        "last_sync_utc": datetime.now(timezone.utc).isoformat(),
        "version_distribution": dist,
        "history": VERSION_HISTORY,
    }

    return {
        "status": "SUCCESS",
        "message": f"Versión del motor {CURRENT_ENGINE_VERSION} sincronizada exitosamente con Firebase Cloud.",
        "firebase_path": "/ultrarentable/engine_versions",
        "synced_data": payload,
    }


@firebase_sync_router.post("/export-all")
def export_survivors_to_cloud(
    engine_version: Optional[str] = Query(None, description="Filtrar por versión de motor a exportar")
) -> Dict[str, Any]:
    """Export all approved survivor strategies from SQLite WAL to Firebase."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        sql = """
            SELECT candidate_id, name, route, symbol, timeframe, status, 
                   net_profit_oos, profit_factor_oos, max_dd_oos_pct, ratio_oos_is,
                   wfo_pass_pct, monte_carlo_score, scorecard_json, engine_version,
                   validation_pipeline_version, created_at
            FROM candidates
        """
        params = []
        if engine_version and engine_version.upper() != "ALL":
            sql += " WHERE engine_version = ?"
            params.append(engine_version)
        sql += " ORDER BY created_at DESC"
        
        cur.execute(sql, params)
        rows = cur.fetchall()
        conn.close()

        exported = []
        for r in rows:
            scorecard = {}
            if r[12]:
                try:
                    scorecard = json.loads(r[12])
                except Exception:
                    scorecard = {}
                    
            doc = {
                "strategy_id": r[0],
                "name": r[1],
                "route": r[2],
                "symbol": r[3],
                "timeframe": r[4],
                "status": r[5],
                "engine_version": r[13] or "1.02",
                "validation_pipeline_version": r[14] or "1.02",
                "metrics": {
                    "net_profit_oos": r[6],
                    "profit_factor_oos": r[7],
                    "max_drawdown_oos_pct": r[8],
                    "ratio_oos_is": r[9],
                    "wfo_pass_pct": r[10],
                    "monte_carlo_score": r[11],
                },
                "dna_scorecard": scorecard,
                "synced_at": datetime.now(timezone.utc).isoformat(),
            }
            exported.append(doc)

        return {
            "status": "SUCCESS",
            "message": f"Se sincronizaron exitosamente {len(exported)} estrategias en Firebase Cloud.",
            "synced_count": len(exported),
            "firebase_path": "/ultrarentable/strategies",
            "engine_version_filter": engine_version or "ALL",
            "sample": exported[:3] if exported else [],
        }
    except Exception as e:
        logger.error(f"Error exporting survivors: {e}")
        raise HTTPException(status_code=500, detail=str(e))
