"""services/api/app/api/job_queue_router.py
Router FastAPI para la Cola Duradera de Trabajos 24/7, Watchdog de Recuperación y Suficiencia Forward.
Especificación oficial según Sección 7 y 8 del Informe Maestro v5.3.0.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from contracts.queue_contracts import (
    DurableJob,
    ForwardSufficiencyRequest,
    ForwardSufficiencyResult,
    JobStatus,
    JobType,
    WatchdogRecoveryReport,
)
from services.queue.durable_job_queue import durable_job_queue
from services.validation.forward_sufficiency import AdaptiveForwardSufficiency


job_queue_router = APIRouter(prefix="/jobs", tags=["Durable Job Queue & Watchdog (24/7)"])
forward_router = APIRouter(prefix="/forward", tags=["Adaptive Forward Sufficiency"])


class EnqueueJobRequest(BaseModel):
    job_type: JobType
    payload: Dict[str, Any]
    priority: int = Field(default=5, ge=1, le=10)
    max_attempts: int = Field(default=3, ge=1)


@job_queue_router.post("/enqueue", response_model=DurableJob)
def enqueue_job(req: EnqueueJobRequest) -> DurableJob:
    """Encola un nuevo trabajo persistente en SQLite WAL."""
    return durable_job_queue.enqueue(
        job_type=req.job_type,
        payload=req.payload,
        priority=req.priority,
        max_attempts=req.max_attempts,
    )


@job_queue_router.get("/{job_id}", response_model=DurableJob)
def get_job_status(job_id: str) -> DurableJob:
    """Consulta el estado en tiempo real de un trabajo."""
    job = durable_job_queue.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Trabajo {job_id} no encontrado en la cola persistente.")
    return job


@job_queue_router.get("", response_model=List[DurableJob])
def list_jobs(
    status: Optional[JobStatus] = None,
    limit: int = Query(50, ge=1, le=200),
) -> List[DurableJob]:
    """Lista trabajos persistidos según su estado."""
    return durable_job_queue.list_jobs(status=status, limit=limit)


@job_queue_router.post("/watchdog/recover", response_model=WatchdogRecoveryReport)
def trigger_watchdog_recovery(max_in_progress_seconds: int = 300) -> WatchdogRecoveryReport:
    """Ejecuta el protocolo de recuperación de jobs huérfanos tras una caída o bloqueo."""
    return durable_job_queue.recover_orphaned_jobs(max_in_progress_seconds=max_in_progress_seconds)


@forward_router.post("/evaluate", response_model=ForwardSufficiencyResult)
def evaluate_forward_sufficiency(req: ForwardSufficiencyRequest) -> ForwardSufficiencyResult:
    """Evalúa adaptativamente la suficiencia temporal y estadística forward de una estrategia."""
    return AdaptiveForwardSufficiency.evaluate(req)
