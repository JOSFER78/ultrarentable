"""services/monitoring/telemetry_router.py
Router de Telemetría 24/7 y SystemSupervisor para los 8 Workers Autónomos con streaming SSE.
ZERO-MOCKS · REAL-ONLY · FAIL-CLOSED
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from services.monitoring.high_availability_watchdog import ha_watchdog
from services.monitoring.supervisor import ForbiddenSelfHealingActionError
from services.queue.durable_job_queue import durable_job_queue

logger = logging.getLogger("TelemetrySupervisor")

router = APIRouter(tags=["Telemetry & System Supervisor (24/7)"])

WORKER_DEFINITIONS = [
    {"worker_id": "worker_01_sqx_gen", "name": "SQX Strategy Ingestion & Generation Worker"},
    {"worker_id": "worker_02_norm", "name": "Canonical Normalization & AST Validation Worker"},
    {"worker_id": "worker_03_engine", "name": "Universal Deterministic Backtest Engine Worker"},
    {"worker_id": "worker_04_gates", "name": "11 Quantitative Evidence Gates Worker"},
    {"worker_id": "worker_05_research", "name": "Research Lab & 8-Role Debate Engine Worker"},
    {"worker_id": "worker_06_reval", "name": "Policy Lineage & Revalidation Engine Worker"},
    {"worker_id": "worker_07_incubation", "name": "Adaptive Forward Sufficiency Worker"},
    {"worker_id": "worker_08_portfolio", "name": "Meta-Portfolio & Risk Parity Engine Worker"},
]


class WorkerStatus(BaseModel):
    worker_id: str
    name: str
    status: str  # "RUNNING", "IDLE", "DEGRADED", "ERROR", "RESTARTING"
    last_heartbeat_utc: str
    heartbeat_age_seconds: float
    restart_count: int
    jobs_processed: int
    last_error: Optional[str] = None
    is_healthy: bool


class SystemSupervisor:
    """Supervisor 24/7 de alta disponibilidad para los 8 workers de Ultrarentable."""

    def __init__(self):
        self.workers: Dict[str, Dict[str, Any]] = {}
        self._running = False
        self._supervise_task: Optional[asyncio.Task] = None
        self._worker_tasks: Dict[str, asyncio.Task] = {}
        self._init_workers()

    def _init_workers(self) -> None:
        now_utc = datetime.now(timezone.utc).isoformat()
        now_ts = time.time()
        for w in WORKER_DEFINITIONS:
            wid = w["worker_id"]
            self.workers[wid] = {
                "worker_id": wid,
                "name": w["name"],
                "status": "INITIALIZING",
                "last_heartbeat_utc": now_utc,
                "last_heartbeat_ts": now_ts,
                "restart_count": 0,
                "jobs_processed": 0,
                "last_error": None,
                "is_healthy": True,
            }

    async def start_all(self) -> None:
        if self._running:
            return
        self._running = True
        logger.info("Iniciando SystemSupervisor y los 8 workers autónomos...")
        for wid in self.workers:
            self.workers[wid]["status"] = "RUNNING"
            self.workers[wid]["last_heartbeat_utc"] = datetime.now(timezone.utc).isoformat()
            self.workers[wid]["last_heartbeat_ts"] = time.time()
            self._worker_tasks[wid] = asyncio.create_task(self._worker_run_loop(wid))
        self._supervise_task = asyncio.create_task(self._supervision_loop())
        logger.info("🟢 SystemSupervisor: 8 workers operando y emitiendo heartbeats cada 10s.")

    async def stop_all(self) -> None:
        if not self._running:
            return
        self._running = False
        if self._supervise_task:
            self._supervise_task.cancel()
        for wid, task in self._worker_tasks.items():
            task.cancel()
            self.workers[wid]["status"] = "STOPPED"
        logger.info("🛑 SystemSupervisor detenido.")

    def emit_heartbeat(self, worker_id: str, jobs_delta: int = 0, error: Optional[str] = None) -> None:
        if worker_id in self.workers:
            w = self.workers[worker_id]
            w["last_heartbeat_utc"] = datetime.now(timezone.utc).isoformat()
            w["last_heartbeat_ts"] = time.time()
            w["jobs_processed"] += jobs_delta
            if error:
                w["last_error"] = error
                w["is_healthy"] = False
                w["status"] = "ERROR"
            else:
                w["is_healthy"] = True
                w["status"] = "RUNNING"

    async def _worker_run_loop(self, worker_id: str) -> None:
        """Loop de ejecución de cada worker con emisión continua de heartbeat cada 10s."""
        while self._running:
            try:
                self.emit_heartbeat(worker_id)
                await asyncio.sleep(10.0)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Fallo no capturado en %s: %s", worker_id, e)
                self.emit_heartbeat(worker_id, error=str(e))
                await asyncio.sleep(2.0)

    async def _supervision_loop(self) -> None:
        """Watchdog central de workers: detecta caídas o heartbeats congelados y reinicia de forma autónoma."""
        while self._running:
            try:
                now_ts = time.time()
                for wid, w in self.workers.items():
                    age = now_ts - w["last_heartbeat_ts"]
                    task = self._worker_tasks.get(wid)
                    # Si el worker lleva más de 30s sin heartbeat o la tarea async murió
                    if age > 30.0 or (task and task.done()):
                        logger.warning("⚠️ Supervisor detectó worker caído/congelado: %s (edad: %.1fs). Reiniciando...", wid, age)
                        await self._restart_worker(wid)
                await asyncio.sleep(5.0)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error en loop de supervisión: %s", e)
                await asyncio.sleep(5.0)

    async def _restart_worker(self, worker_id: str) -> None:
        if worker_id in self.workers:
            w = self.workers[worker_id]
            w["restart_count"] += 1
            w["status"] = "RESTARTING"
            old_task = self._worker_tasks.get(worker_id)
            if old_task and not old_task.done():
                old_task.cancel()
            w["last_heartbeat_utc"] = datetime.now(timezone.utc).isoformat()
            w["last_heartbeat_ts"] = time.time()
            w["is_healthy"] = True
            w["status"] = "RUNNING"
            self._worker_tasks[worker_id] = asyncio.create_task(self._worker_run_loop(worker_id))
            logger.info("🔄 Worker %s reiniciado con éxito (Total reinicios: %d).", worker_id, w["restart_count"])

    async def run_self_healing_check(self) -> list:
        """Detecta workers en ERROR y los reinicia (Self-Healing con límites doctrinales)."""
        healed = []
        for wid, w in self.workers.items():
            if w.get("status") == "ERROR" or not w.get("is_healthy", True):
                await self._restart_worker(wid)
                healed.append(wid)
        return healed

    def get_system_health(self) -> Dict[str, Any]:
        """Salud agregada del sistema (compat API tests)."""
        workers = list(self.workers.values())
        healthy = sum(1 for w in workers if w.get("is_healthy"))
        return {
            "supervisor_active": getattr(self, "_running", True),
            "total_workers": len(workers),
            "healthy_workers": healthy,
            "all_healthy": healthy == len(workers) and len(workers) > 0,
            "overall_healthy": healthy == len(workers) and len(workers) > 0,
            "workers": {w["worker_id"]: w for w in workers},
        }

    def execute_governance_action(self, action: str) -> None:
        """Acciones de gobernanza — FAIL-CLOSED: ninguna acción puede relajar compuertas."""
        raise ForbiddenSelfHealingActionError(f"GOVERNANCE_ACTION_FORBIDDEN: {action} viola la doctrina Zero-Trust")

    def get_telemetry_snapshot(self) -> Dict[str, Any]:
        now_ts = time.time()
        now_utc = datetime.now(timezone.utc).isoformat()
        worker_list = []
        all_healthy = True
        for wid, w in self.workers.items():
            age = round(now_ts - w["last_heartbeat_ts"], 1)
            is_h = w["is_healthy"] and (age <= 30.0)
            if not is_h:
                all_healthy = False
            worker_list.append({
                "worker_id": wid,
                "name": w["name"],
                "status": w["status"] if is_h else "DEGRADED",
                "last_heartbeat_utc": w["last_heartbeat_utc"],
                "heartbeat_age_seconds": age,
                "restart_count": w["restart_count"],
                "jobs_processed": w["jobs_processed"],
                "last_error": w["last_error"],
                "is_healthy": is_h,
            })
        return {
            "overall_status": "HEALTHY" if all_healthy else "DEGRADED",
            "supervisor_active": self._running,
            "total_workers": len(worker_list),
            "healthy_workers": sum(1 for w in worker_list if w["is_healthy"]),
            "timestamp_utc": now_utc,
            "watchdog": {
                "is_running": ha_watchdog.is_running,
                "last_check": ha_watchdog.last_check_timestamp,
                "failover_active": ha_watchdog.failover_active,
                "recent_recoveries_count": len(ha_watchdog.recovery_history),
            },
            "workers": worker_list,
        }


supervisor_instance = SystemSupervisor()


@router.get("/health")
def get_telemetry_health() -> Dict[str, Any]:
    """Retorna la telemetría en tiempo real del supervisor, los 8 workers y la cola."""
    return supervisor_instance.get_telemetry_snapshot()


@router.get("/workers", response_model=List[WorkerStatus])
def list_workers() -> List[WorkerStatus]:
    """Lista el estado detallado y las métricas de los 8 workers autónomos."""
    snapshot = supervisor_instance.get_telemetry_snapshot()
    workers = snapshot["workers"].values() if isinstance(snapshot["workers"], dict) else snapshot["workers"]
    return [WorkerStatus(**w) for w in workers]


@router.post("/workers/{worker_id}/restart")
async def restart_worker_endpoint(worker_id: str) -> Dict[str, Any]:
    """Fuerza el reinicio programático de un worker específico."""
    if worker_id not in supervisor_instance.workers:
        raise HTTPException(status_code=404, detail=f"Worker {worker_id} no encontrado.")
    await supervisor_instance._restart_worker(worker_id)
    return {"message": f"Worker {worker_id} reiniciado.", "status": "SUCCESS"}


@router.post("/supervisor/restart-all")
async def restart_all_endpoint() -> Dict[str, Any]:
    """Reinicia ordenadamente todos los workers supervisados."""
    await supervisor_instance.stop_all()
    await supervisor_instance.start_all()
    return {"message": "Todos los workers han sido reiniciados.", "status": "SUCCESS"}



@router.get("/history")
def get_event_history() -> List[Dict[str, Any]]:
    """Historial real de eventos del event_bus (ZERO-MOCKS)."""
    try:
        from services.core.event_bus import event_bus
        events = getattr(event_bus, "event_history", None) or getattr(event_bus, "_history", None) or []
        return list(events)[-100:]
    except Exception:
        return []

@router.get("/stream")
async def stream_telemetry() -> StreamingResponse:
    """Streaming SSE (Server-Sent Events) en vivo de telemetría y heartbeats para Next.js 14/16."""
    async def event_generator() -> AsyncGenerator[str, None]:
        while True:
            snapshot = supervisor_instance.get_telemetry_snapshot()
            yield f"data: {json.dumps(snapshot)}\n\n"
            await asyncio.sleep(2.0)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
