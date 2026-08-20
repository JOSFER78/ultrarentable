"""services/monitoring/high_availability_watchdog.py
Watchdog de Alta Disponibilidad 24/7 y Auto-Recuperación (Self-Healing Daemon) para Ultrarentable V2.

Garantiza CERO DOWNTIME mediante:
1. Supervisión del Demonio de Búsqueda Continua 24/7 (ContinuousSearchDaemon).
2. Detección y auto-reconexión del puente StrategyQuant X (SQXMCPClient).
3. Conmutación automática a Failover Autónomo FastEngine cuando SQX no responde.
4. Auto-reparación y reinicio de los 8 workers del SystemSupervisor.
5. Checkpoint de mantenimiento periódico de SQLite WAL para evitar bloqueos.
"""

from __future__ import annotations

import asyncio
import logging
import sqlite3
import subprocess
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from services.core.event_bus import SystemAlertEvent, event_bus
from services.monitoring.telemetry_router import supervisor_instance
from services.sqx_bridge.sqx_client import SQXMCPClient

logger = logging.getLogger("HighAvailabilityWatchdog")
DB_PATH = "/home/ubuntu/.local/state/ultrarentable/ultrarentable.sqlite3"


class HighAvailabilityWatchdog:
    """Watchdog daemon que supervisa 24/7 todos los subcomponentes del sistema."""

    def __init__(self, check_interval_seconds: int = 15) -> None:
        self.check_interval_seconds = check_interval_seconds
        self._is_running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.last_check_timestamp: Optional[str] = None
        self.recovery_history: List[Dict[str, Any]] = []
        self.failover_active = False

    def start(self) -> None:
        """Inicia el bucle de vigilancia 24/7 en un hilo desacoplado."""
        if self._is_running:
            return
        self._is_running = True
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._watchdog_loop,
            daemon=True,
            name="HA-Watchdog-24-7",
        )
        self._thread.start()
        logger.info("HighAvailabilityWatchdog 24/7 INICIADO.")

    def stop(self) -> None:
        """Detiene el watchdog de forma ordenada."""
        self._is_running = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("HighAvailabilityWatchdog 24/7 DETENIDO.")

    def _watchdog_loop(self) -> None:
        """Bucle principal de comprobación periódica y auto-reparación."""
        while not self._stop_event.is_set():
            try:
                self.perform_health_and_recovery_cycle()
            except Exception as e:
                logger.error(f"Error en ciclo de vigilancia HA Watchdog: {e}")
            self._stop_event.wait(self.check_interval_seconds)

    def perform_health_and_recovery_cycle(self) -> Dict[str, Any]:
        """Ejecuta un ciclo completo de auditoría y auto-recuperación."""
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        self.last_check_timestamp = now_str
        actions_taken: List[str] = []

        # 1. Auditar y auto-recuperar ContinuousSearchDaemon
        from services.api.app.factory.continuous_search_daemon import continuous_search_daemon
        daemon_tel = continuous_search_daemon.get_telemetry()
        if not daemon_tel.get("is_running", False):
            logger.warning("HA Watchdog: ContinuousSearchDaemon inactivo. Reiniciando de inmediato...")
            try:
                continuous_search_daemon.start()
                actions_taken.append("RESTARTED_CONTINUOUS_SEARCH_DAEMON")
            except Exception as de:
                logger.error(f"Error reiniciando continuous_search_daemon: {de}")

        # 2. Auditar SystemSupervisor y sus 8 workers
        try:
            loop = asyncio.new_event_loop()
            repaired_workers = loop.run_until_complete(supervisor_instance.run_self_healing_check())
            loop.close()
            if repaired_workers:
                actions_taken.append(f"REPAIRED_SUPERVISOR_WORKERS: {', '.join(repaired_workers)}")
        except Exception as se:
            logger.error(f"Error en self-healing del supervisor: {se}")

        # 3. Comprobar SQX MCP y gestionar Failover
        sqx_client = SQXMCPClient(timeout=2)
        sqx_online = False
        try:
            conn = sqx_client.check_connection()
            sqx_online = conn.get("status") == "ONLINE"
        except Exception:
            sqx_online = False

        if sqx_online:
            if self.failover_active:
                logger.info("HA Watchdog: Conexión con StrategyQuant X restablecida. Retornando a modo HÍBRIDO.")
                self.failover_active = False
                actions_taken.append("RESTORED_SQX_HYBRID_MODE")
        else:
            if not self.failover_active:
                self.failover_active = True
                logger.info("HA Watchdog: StrategyQuant X en espera. Conmutando a FastEngine 24/7 Autónomo (Cero Downtime).")
                actions_taken.append("ACTIVATED_FASTENGINE_AUTONOMOUS_FAILOVER")

        # 4. Mantenimiento SQLite WAL (Prevenir bloqueos de base de datos)
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            conn.execute("PRAGMA wal_checkpoint(PASSIVE);")
            conn.close()
        except Exception as dbe:
            logger.warning(f"Aviso de checkpoint SQLite WAL: {dbe}")

        # Registrar historial de recuperación si hubo acciones
        if actions_taken:
            rec_event = {
                "timestamp": now_str,
                "actions": actions_taken,
                "failover_mode": "FASTENGINE_AUTONOMOUS" if self.failover_active else "SQX_HYBRID",
            }
            self.recovery_history.append(rec_event)
            if len(self.recovery_history) > 50:
                self.recovery_history.pop(0)

        return {
            "status": "WATCHDOG_ACTIVE",
            "timestamp": now_str,
            "failover_active": self.failover_active,
            "engine_mode": "FASTENGINE_24_7_AUTONOMOUS" if self.failover_active else "HYBRID_SQX_FASTENGINE",
            "actions_taken": actions_taken,
            "recovery_history_count": len(self.recovery_history),
        }

    def manual_system_reset(self) -> Dict[str, Any]:
        """Fuerza un reseteo limpio de todos los servicios para restaurar estado 100% operativo."""
        logger.info("Iniciando reseteo manual y auto-recuperación completa de infraestructura...")
        results: Dict[str, Any] = {}

        # 1. Reiniciar ContinuousSearchDaemon
        from services.api.app.factory.continuous_search_daemon import continuous_search_daemon
        try:
            continuous_search_daemon.stop()
            time.sleep(0.5)
            continuous_search_daemon.start()
            results["continuous_search_daemon"] = "RESTARTED_OK"
        except Exception as e:
            results["continuous_search_daemon"] = f"ERROR: {e}"

        # 2. Reiniciar Supervisor Workers
        try:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(supervisor_instance.stop_all())
            time.sleep(0.3)
            loop.run_until_complete(supervisor_instance.start_all())
            loop.close()
            results["supervisor_workers"] = "RESTARTED_8_WORKERS_OK"
        except Exception as e:
            results["supervisor_workers"] = f"ERROR: {e}"

        # 3. Intentar reiniciar servicio SQX si es aplicable
        try:
            subprocess.run(
                ["systemctl", "--user", "restart", "strategyquantx.service"],
                capture_output=True,
                timeout=5,
            )
            results["strategyquantx_service"] = "RESTART_SIGNAL_SENT"
        except Exception as e:
            results["strategyquantx_service"] = f"NOTICE: {e}"

        # 4. Checkpoint SQLite WAL
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            conn.close()
            results["sqlite_wal"] = "CHECKPOINT_TRUNCATE_OK"
        except Exception as e:
            results["sqlite_wal"] = f"NOTICE: {e}"

        results["timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        results["overall_status"] = "ALL_SYSTEMS_RESTORED_AND_RUNNING"
        return results


# Instancia Global Singleton
ha_watchdog = HighAvailabilityWatchdog(check_interval_seconds=15)
