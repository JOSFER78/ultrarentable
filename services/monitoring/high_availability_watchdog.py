"""services/monitoring/high_availability_watchdog.py
High Availability Watchdog Daemon 24/7 para supervisión, failover y auto-recuperación de SQLite WAL.
ZERO-MOCKS · REAL-ONLY · FAIL-CLOSED · 24/7 AUTONOMOUS SELF-HEALING
"""
from __future__ import annotations

import logging
import socket
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from services.queue.durable_job_queue import durable_job_queue, DurableJobQueue

logger = logging.getLogger("HAWatchdog")


class HAWatchdog:
    """Watchdog de alta disponibilidad 24/7 que monitoriza el estado de la cola y realiza auto-sanación."""

    def __init__(self, queue: Optional[DurableJobQueue] = None, interval_seconds: float = 10.0):
        self.queue = queue or durable_job_queue
        self.interval_seconds = interval_seconds
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._is_running = False
        self.last_check_timestamp: Optional[str] = None
        self.failover_active = False
        self.recovery_history: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        return self._is_running

    def start(self) -> None:
        if self._is_running:
            return
        self._is_running = True
        self._stop_event.clear()
        # Barrido inicial inmediato de recuperación ante reinicio
        try:
            self._run_health_and_recovery_cycle()
        except Exception as e:
            logger.error("Error en barrido inicial de HAWatchdog: %s", e)

        self._thread = threading.Thread(target=self._loop, daemon=True, name="HAWatchdogThread")
        self._thread.start()
        logger.info("🟢 HAWatchdog iniciado 24/7 (intervalo de supervisión: %ss).", self.interval_seconds)

    def stop(self) -> None:
        if not self._is_running:
            return
        self._stop_event.set()
        self._is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("🛑 HAWatchdog detenido.")

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._run_health_and_recovery_cycle()
            except Exception as e:
                logger.error("Error en ciclo de HAWatchdog: %s", e)
            self._stop_event.wait(self.interval_seconds)

    def _probe_port(self, host: str, port: int, timeout: float = 0.5) -> bool:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except Exception:
            return False

    def _run_health_and_recovery_cycle(self) -> None:
        now_utc = datetime.now(timezone.utc).isoformat()

        # 1. Comprobar conectividad y failover de SQX
        sqx_up = self._probe_port("127.0.0.1", 8081) or self._probe_port("127.0.0.1", 5050)
        self.failover_active = not sqx_up

        # 2. Recuperar jobs huérfanos en SQLite WAL
        report = self.queue.recover_orphaned_jobs(max_in_progress_seconds=300)
        if report.recovered_jobs_count > 0:
            with self._lock:
                self.recovery_history.append({
                    "timestamp_utc": now_utc,
                    "recovered_jobs_count": report.recovered_jobs_count,
                    "orphaned_jobs_reset": report.orphaned_jobs_reset,
                    "message": report.message,
                })
                if len(self.recovery_history) > 50:
                    self.recovery_history = self.recovery_history[-50:]
            logger.info("🛡️ HAWatchdog recuperó %d jobs huérfanos: %s", report.recovered_jobs_count, report.orphaned_jobs_reset)

        self.last_check_timestamp = now_utc

    def manual_system_reset(self) -> Dict[str, Any]:
        """Fuerza un barrido inmediato de recuperación y reseteo de jobs huérfanos."""
        now_utc = datetime.now(timezone.utc).isoformat()
        report = self.queue.recover_orphaned_jobs(max_in_progress_seconds=0)
        self._run_health_and_recovery_cycle()
        return {
            "status": "SUCCESS",
            "reset_timestamp_utc": now_utc,
            "recovered_jobs": report.recovered_jobs_count,
            "reset_job_ids": report.orphaned_jobs_reset,
            "failover_active": self.failover_active,
            "engine_mode": "FASTENGINE_24_7_AUTONOMOUS" if self.failover_active else "HYBRID_SQX_FASTENGINE",
        }


ha_watchdog = HAWatchdog()
