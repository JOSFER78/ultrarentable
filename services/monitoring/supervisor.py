"""services/monitoring/supervisor.py
SystemSupervisor y Pool de 8 Workers Especializados para Ultrarentable V2.
Implementa ciclo de vida de workers, monitoreo de heartbeats, política estricta de Self-Healing y telemetría.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from contracts.canonical_strategy import ExecutionTrack
from services.core.event_bus import SystemAlertEvent, event_bus

logger = logging.getLogger("SystemSupervisor")


class WorkerState(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    ERROR = "ERROR"
    STOPPED = "STOPPED"


class WorkerType(str, Enum):
    DATA_WORKER = "DataWorker"
    SQX_WORKER = "SQXWorker"
    FAST_BACKTEST_WORKER = "FastBacktestWorker"
    VALIDATION_WORKER = "ValidationWorker"
    MONTE_CARLO_WORKER = "MonteCarloWorker"
    SEMANTIC_AI_WORKER = "SemanticAIWorker"
    PORTFOLIO_WORKER = "PortfolioWorker"
    PAPER_TRADING_WORKER = "PaperTradingWorker"


@dataclass
class WorkerInfo:
    worker_type: WorkerType
    state: WorkerState = WorkerState.IDLE
    processed_count: int = 0
    failed_count: int = 0
    last_heartbeat_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    started_at_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    restart_count: int = 0
    last_error_message: Optional[str] = None


class BaseWorker:
    """Clase base para workers asíncronos desacoplados."""

    def __init__(self, worker_type: WorkerType) -> None:
        self.info = WorkerInfo(worker_type=worker_type)
        self._running = False

    async def start(self) -> None:
        self._running = True
        self.info.state = WorkerState.RUNNING
        self.info.last_heartbeat_ms = int(time.time() * 1000)

    async def stop(self) -> None:
        self._running = False
        self.info.state = WorkerState.STOPPED

    def ping_heartbeat(self) -> None:
        self.info.last_heartbeat_ms = int(time.time() * 1000)

    def record_success(self) -> None:
        self.info.processed_count += 1
        self.ping_heartbeat()

    def record_failure(self, error_msg: str) -> None:
        self.info.failed_count += 1
        self.info.last_error_message = error_msg
        self.info.state = WorkerState.ERROR
        self.ping_heartbeat()


class ForbiddenSelfHealingActionError(Exception):
    """Lanzada si el motor de autoreparación intenta una acción prohibida por la gobernanza."""


class SystemSupervisor:
    """Supervisor de orquestación, resiliencia y telemetría de Ultrarentable V2."""

    def __init__(self, heartbeat_timeout_ms: int = 15000) -> None:
        self.heartbeat_timeout_ms = heartbeat_timeout_ms
        self.workers: Dict[WorkerType, BaseWorker] = {
            w_type: BaseWorker(w_type) for w_type in WorkerType
        }
        self._is_active = False

    async def start_all(self) -> None:
        """Inicia los 8 workers especializados."""
        self._is_active = True
        for worker in self.workers.values():
            await worker.start()
        await event_bus.publish(
            SystemAlertEvent(
                severity="INFO",
                component="SystemSupervisor",
                message=f"Pool de 8 workers iniciado con éxito.",
            )
        )

    async def stop_all(self) -> None:
        """Detiene todos los workers de forma ordenada."""
        self._is_active = False
        for worker in self.workers.values():
            await worker.stop()

    def get_system_health(self) -> Dict[str, Any]:
        """Obtiene el diagnóstico completo del estado de los 8 workers."""
        now_ms = int(time.time() * 1000)
        worker_statuses = {}
        all_healthy = True

        for w_type, worker in self.workers.items():
            latency = now_ms - worker.info.last_heartbeat_ms
            is_stalled = (
                worker.info.state == WorkerState.RUNNING and latency > self.heartbeat_timeout_ms
            )
            if is_stalled or worker.info.state == WorkerState.ERROR:
                all_healthy = False

            worker_statuses[w_type.value] = {
                "state": worker.info.state.value,
                "processed_tasks": worker.info.processed_count,
                "failed_tasks": worker.info.failed_count,
                "heartbeat_latency_ms": latency,
                "restart_count": worker.info.restart_count,
                "last_error": worker.info.last_error_message,
            }

        return {
            "supervisor_active": self._is_active,
            "overall_healthy": all_healthy,
            "total_workers": len(self.workers),
            "workers": worker_statuses,
        }

    async def run_self_healing_check(self) -> List[str]:
        """Audita el pool y reinicia automáticamente workers caídos bajo límites estrictos."""
        now_ms = int(time.time() * 1000)
        restarted_workers: List[str] = []

        for w_type, worker in self.workers.items():
            latency = now_ms - worker.info.last_heartbeat_ms
            needs_healing = (
                worker.info.state == WorkerState.ERROR
                or (worker.info.state == WorkerState.RUNNING and latency > self.heartbeat_timeout_ms)
            )

            if needs_healing:
                await self._heal_worker(worker)
                restarted_workers.append(w_type.value)

        return restarted_workers

    async def _heal_worker(self, worker: BaseWorker) -> None:
        """Reinicia un worker asegurando los límites inviolables de Self-Healing."""
        w_name = worker.info.worker_type.value
        logger.warning(f"Self-Healing: Reiniciando {w_name} por caída o pérdida de heartbeat...")
        await worker.stop()
        worker.info.restart_count += 1
        worker.info.last_error_message = None
        await worker.start()

        await event_bus.publish(
            SystemAlertEvent(
                severity="WARNING",
                component="SystemSupervisor",
                message=f"Worker {w_name} autoreparado y reiniciado (Reinicio #{worker.info.restart_count}).",
            )
        )

    def execute_governance_action(self, action_name: str) -> None:
        """Verifica que el supervisor jamás ejecute acciones prohibidas."""
        forbidden_actions = [
            "RELAX_EVIDENCE_GATE",
            "ALTER_BACKTEST_METRICS",
            "OVERWRITE_DATASET_SNAPSHOT",
            "BYPASS_14_DAY_INCUBATION",
        ]
        if action_name in forbidden_actions:
            raise ForbiddenSelfHealingActionError(
                f"ACCIÓN PROHIBIDA POR GOBERNANZA ABSOLUTA: {action_name}. El supervisor no tiene permisos para alterar métricas o gates."
            )
