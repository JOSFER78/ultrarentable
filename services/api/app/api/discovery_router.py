"""services/api/app/api/discovery_router.py
Router API para el control de Minería Continua y Telemetría de Discovery Real-Only.
"""

from __future__ import annotations

import logging
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from fastapi import APIRouter
from pydantic import BaseModel

from services.discovery.discovery_validation_pipeline import DiscoveryValidationPipeline

logger = logging.getLogger("DiscoveryRouter")

router = APIRouter(prefix="/api/v1/discovery", tags=["Discovery & Mining Engine"])

_discovery_lock = threading.Lock()
_discovery_thread: Optional[threading.Thread] = None
_stop_signal = threading.Event()

_discovery_state: Dict[str, Any] = {
    "status": "RUNNING",  # RUNNING por defecto en modo autónomo 24/7
    "started_at": datetime.now(timezone.utc).isoformat(),
    "last_updated": datetime.now(timezone.utc).isoformat(),
    "cycle_count": 1,
    "current_dataset": None,
    "total_trials_in_db": 0,
    "certified_in_session": 0,
    "rejected_in_session": 0,
    "message": "Minería 24/7 autónoma activa sobre datasets físicos.",
}


def _get_trials_count() -> int:
    db_file = Path.home() / ".local" / "state" / "ultrarentable" / "ultrarentable.sqlite3"
    if not db_file.exists():
        return 0
    try:
        with sqlite3.connect(str(db_file), timeout=5.0) as conn:
            cur = conn.cursor()
            cur.execute("SELECT count(*) FROM discovery_search_trials")
            row = cur.fetchone()
            return int(row[0]) if row else 0
    except Exception:
        return 0


def _run_discovery_worker():
    global _discovery_state
    logger.info("Discovery Worker iniciado en segundo plano.")
    pipeline = DiscoveryValidationPipeline()

    cycle = 0
    while not _stop_signal.is_set():
        cycle += 1
        with _discovery_lock:
            _discovery_state["status"] = "RUNNING"
            _discovery_state["cycle_count"] = cycle
            _discovery_state["total_trials_in_db"] = _get_trials_count()
            _discovery_state["last_updated"] = datetime.now(timezone.utc).isoformat()
            _discovery_state["message"] = f"Ejecutando ciclo #{cycle} de minería multiactivo sobre datasets físicos."

        try:
            pipeline.run_continuous_pipeline(max_datasets=5, max_cycles=1, sleep_between_cycles_sec=5)
        except Exception as e:
            logger.exception(f"Error en ciclo de minería: {e}")

        with _discovery_lock:
            _discovery_state["total_trials_in_db"] = _get_trials_count()
            _discovery_state["last_updated"] = datetime.now(timezone.utc).isoformat()

        for _ in range(10):
            if _stop_signal.is_set():
                break
            _stop_signal.wait(timeout=1.0)

    with _discovery_lock:
        _discovery_state["status"] = "STOPPED"
        _discovery_state["message"] = "Minería pausada por el usuario."
        _discovery_state["last_updated"] = datetime.now(timezone.utc).isoformat()
    logger.info("Discovery Worker finalizado limpiamente.")


class DiscoveryStartRequest(BaseModel):
    max_datasets_per_cycle: int = 5
    route: str = "ALL"


@router.get("/status")
def get_discovery_status() -> Dict[str, Any]:
    """Retorna la telemetría en tiempo real del motor de minería."""
    with _discovery_lock:
        state = dict(_discovery_state)
        state["total_trials_in_db"] = _get_trials_count()
        return state


@router.post("/start")
def start_discovery_engine(req: DiscoveryStartRequest = DiscoveryStartRequest()) -> Dict[str, Any]:
    """Inicia la minería continua en segundo plano."""
    global _discovery_thread, _stop_signal
    with _discovery_lock:
        if _discovery_state["status"] == "RUNNING" and _discovery_thread and _discovery_thread.is_alive():
            return {
                "status": "RUNNING",
                "message": "El motor de minería ya se encuentra en ejecución.",
                "total_trials_in_db": _get_trials_count(),
            }

        _stop_signal.clear()
        _discovery_state["status"] = "RUNNING"
        _discovery_state["started_at"] = datetime.now(timezone.utc).isoformat()
        _discovery_state["last_updated"] = datetime.now(timezone.utc).isoformat()
        _discovery_state["message"] = "Iniciando motor de minería sobre datasets físicos..."

        _discovery_thread = threading.Thread(target=_run_discovery_worker, daemon=True)
        _discovery_thread.start()

        return {
            "status": "RUNNING",
            "message": "Minería continua iniciada exitosamente en segundo plano.",
            "started_at": _discovery_state["started_at"],
            "total_trials_in_db": _get_trials_count(),
        }


@router.post("/stop")
def stop_discovery_engine() -> Dict[str, Any]:
    """Detiene la minería continua de forma limpia."""
    global _stop_signal
    with _discovery_lock:
        if _discovery_state["status"] != "RUNNING":
            return {
                "status": "STOPPED",
                "message": "El motor de minería ya está detenido.",
            }
        _stop_signal.set()
        _discovery_state["message"] = "Deteniendo minería..."

    return {
        "status": "STOPPING",
        "message": "Señal de parada enviada. El worker se detendrá al finalizar el dataset actual.",
    }


@router.get("/trials-summary")
def get_trials_summary() -> Dict[str, Any]:
    """Retorna un desglose de trials por símbolo y temporalidad desde SQLite."""
    db_file = Path.home() / ".local" / "state" / "ultrarentable" / "ultrarentable.sqlite3"
    if not db_file.exists():
        return {"total_trials": 0, "breakdown": []}

    try:
        with sqlite3.connect(str(db_file), timeout=5.0) as conn:
            cur = conn.cursor()
            cur.execute("SELECT symbol, timeframe, count(*), max(in_sample_pf), min(in_sample_dd_pct) FROM discovery_search_trials GROUP BY symbol, timeframe ORDER BY count(*) DESC")
            rows = cur.fetchall()
            summary = []
            for r in rows:
                summary.append({
                    "symbol": r[0],
                    "timeframe": r[1],
                    "trials_count": r[2],
                    "max_is_pf": round(r[3], 2) if r[3] else 0.0,
                    "min_is_dd_pct": round(r[4], 2) if r[4] else 0.0,
                })
            return {
                "total_trials": sum(s["trials_count"] for s in summary),
                "breakdown": summary,
            }
    except Exception as e:
        return {"total_trials": 0, "error": str(e), "breakdown": []}
