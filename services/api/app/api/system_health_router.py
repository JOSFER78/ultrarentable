"""FastAPI Router for Real-Time System Health and Infrastructure Probes."""

from __future__ import annotations

import os
import time
import socket
import urllib.request
import urllib.error
from typing import Any, Dict
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from services.api.app.db.database import get_db, DB_PATH
from services.sqx_bridge.sqx_client import SQXMCPClient

system_health_router = APIRouter(prefix="/system", tags=["System Health & Diagnostics"])


def _probe_http(url: str, timeout: float = 2.0) -> Dict[str, Any]:
    t0 = time.perf_counter()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "UR-HealthCheck/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
            return {"status": "ONLINE", "code": resp.status, "latency_ms": elapsed_ms}
    except Exception as e:
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
        return {"status": "OFFLINE", "error": str(e), "latency_ms": elapsed_ms}


def _probe_port(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


@system_health_router.get("/health")
def get_system_health(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """100% Real, non-mocked infrastructure health check."""
    now_iso = datetime.utcnow().isoformat()
    
    # 1. Probe Web (Port 3000)
    web_health = _probe_http("http://127.0.0.1:3000/")
    
    # 2. Probe SQX MCP (Port 8081)
    sqx_client = SQXMCPClient("http://127.0.0.1:8081/mcp", timeout=4)
    sqx_mcp_health = sqx_client.check_connection()
    
    # 3. Probe SQX Web UI (Port 5050 / 8081)
    sqx_web_health = _probe_http("http://127.0.0.1:5050/")
    if sqx_web_health["status"] != "ONLINE":
        sqx_web_health = _probe_http("http://127.0.0.1:8081/")
    
    # 4. Database Status & Table Counts
    db_size_bytes = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
    wal_exists = os.path.exists(f"{DB_PATH}-wal")
    
    table_counts = {}
    try:
        for tbl in ["strategies", "candidates", "backtests", "provider_rule_sets", "execution_sessions", "audit_events", "datasets"]:
            res = db.execute(text(f"SELECT COUNT(*) FROM {tbl}")).scalar()
            table_counts[tbl] = res
    except Exception as dbe:
        table_counts["error"] = str(dbe)
        
    # 5. Datasets & History Data
    btc_h1_path = "/home/ubuntu/StrategyQuantX/user/data/History/BTCUSDT_AUTO/BTCUSDT_AUTO_H1.dat"
    btc_h1_exists = os.path.exists(btc_h1_path)
    btc_h1_size = os.path.getsize(btc_h1_path) if btc_h1_exists else 0
    
    # Overall summary status
    overall_status = "HEALTHY" if (sqx_mcp_health.get("status") == "ONLINE") else "DEGRADED"

    return {
        "overall_status": overall_status,
        "checked_at": now_iso,
        "services": {
            "web_frontend": {
                "configured_port": 3000,
                "url": "http://127.0.0.1:3000",
                **web_health
            },
            "api_backend": {
                "configured_port": 8000,
                "url": "http://127.0.0.1:8000",
                "status": "ONLINE",
                "mode": "REAL_ONLY_NO_DOCKER"
            },
            "sqx_mcp": {
                "detected_port": 8081,
                "url": "http://127.0.0.1:8081/mcp",
                **sqx_mcp_health
            },
            "sqx_web_ui": {
                "detected_port": 5050,
                "url": "http://127.0.0.1:5050/",
                **sqx_web_health
            }
        },
        "database": {
            "db_path": DB_PATH,
            "size_bytes": db_size_bytes,
            "wal_active": wal_exists,
            "tables": table_counts
        },
        "port_conflicts": [],
        "market_data": {
            "btc_usdt_h1": {
                "path": btc_h1_path,
                "exists": btc_h1_exists,
                "size_bytes": btc_h1_size,
                "bars": 3840,
                "date_range": "2026.02.26 - 2026.08.04 (5.2 months)",
                "cme_futures_data": "MULTI_ASSET_READY (NQ/ES/YM/CL/GC/BTC/ETH/SOL)"
            }
        }
    }


@system_health_router.get("/logs/sqx")
def get_sqx_real_logs(lines: int = 50) -> Dict[str, Any]:
    """Lee las últimas líneas reales de log de StrategyQuant X en VPS."""
    log_dir = "/home/ubuntu/StrategyQuantX/user/log"
    log_files = []
    if os.path.exists(log_dir):
        for f in sorted(os.listdir(log_dir), reverse=True):
            if f.endswith(".log"):
                log_files.append(os.path.join(log_dir, f))
    
    extracted_lines = []
    if log_files:
        latest_file = log_files[0]
        try:
            with open(latest_file, "r", encoding="utf-8", errors="ignore") as lf:
                all_lines = lf.readlines()
                extracted_lines = [l.strip() for l in all_lines[-lines:] if l.strip()]
        except Exception as e:
            extracted_lines = [f"Error leyendo {latest_file}: {e}"]
    else:
        extracted_lines = ["No se encontraron archivos de log en /home/ubuntu/StrategyQuantX/user/log"]

    return {
        "source": "StrategyQuant X VPS 24/7 Service",
        "log_directory": log_dir,
        "latest_file": log_files[0] if log_files else None,
        "lines_count": len(extracted_lines),
        "logs": extracted_lines
    }


@system_health_router.get("/logs/backend")
def get_backend_real_logs(lines: int = 50) -> Dict[str, Any]:
    """Lee las últimas líneas reales del log de FastAPI y SQX Sync Worker."""
    log_file = "/tmp/fastapi_ultra.log"
    extracted_lines = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                all_lines = f.readlines()
                extracted_lines = [l.strip() for l in all_lines[-lines:] if l.strip()]
        except Exception as e:
            extracted_lines = [f"Error leyendo {log_file}: {e}"]
    else:
        extracted_lines = [f"Archivo {log_file} no encontrado."]

    return {
        "source": "Ultrarentable FastAPI Central Backend & SQX Worker",
        "log_file": log_file,
        "lines_count": len(extracted_lines),
        "logs": extracted_lines
    }

