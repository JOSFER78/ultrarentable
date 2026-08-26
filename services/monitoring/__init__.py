"""services/monitoring/__init__.py
Módulo de Supervisión de Alta Disponibilidad, Telemetría 24/7 y Self-Healing.
"""
from services.monitoring.high_availability_watchdog import HAWatchdog, ha_watchdog
from services.monitoring.telemetry_router import SystemSupervisor, supervisor_instance, router as telemetry_router

__all__ = ["HAWatchdog", "ha_watchdog", "SystemSupervisor", "supervisor_instance", "telemetry_router"]

from services.monitoring.supervisor import (
    WorkerState,
    WorkerType,
    WorkerInfo,
    BaseWorker,
    ForbiddenSelfHealingActionError,
)

__all__ += ["WorkerState", "WorkerType", "WorkerInfo", "BaseWorker", "ForbiddenSelfHealingActionError"]
