"""services/api/app/main.py
Backend Central de Ultrarentable V2 (FastAPI + SQLite WAL + EventBus + SystemSupervisor).
Expone APIs V1 y V2 con soporte para streaming SSE y gobernanza Zero-Trust.

Autonomous runtime is explicitly opt-in via ULTRARENTABLE_AUTONOMOUS_RUNTIME=true.
Local development must remain independently startable without launching the 24/7 worker fleet.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator, Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from services.api.app.config import LOCAL_WEB_ORIGINS
from services.api.app.db.database import init_db, SessionLocal
from services.api.app.db.truth_guard import purge_legacy_demo_records

from services.api.app.api.version_router import version_router
from services.api.app.api.lineage_router import lineage_router
from services.api.app.api.policy_router import policy_router
from services.api.app.api.research_lab_router import research_lab_router
from services.api.app.api.job_queue_router import job_queue_router, forward_router
from services.api.app.api.strategy_lab_router import router as strategy_lab_router

# Routers V1 Legados
from services.api.app.api.routes import router as legacy_routes
from services.api.app.api.discovery_router import router as discovery_router
from services.api.app.api.sqx_router import sqx_router
from services.api.app.api.providers_router import providers_router
from services.api.app.api.candidates_router import candidates_router
from services.api.app.api.execution_router import execution_router
from services.api.app.api.audit_router import audit_router
from services.api.app.api.system_health_router import system_health_router
from services.api.app.api.real_data_router import router as real_data_router
from services.api.app.api.research_router import router as research_router
from services.api.app.api.gates_router import gates_router
from services.api.app.api.firebase_sync_router import firebase_sync_router
from services.api.app.api.certified_summary_router import certified_summary_router

# Routers V2 Modulares
from services.monitoring.telemetry_router import router as telemetry_router, supervisor_instance
from services.validation.validation_router import router as validation_router
from services.semantic_ai.semantic_router import router as semantic_router
from services.exploitation_engines.ultra_router import router as ultra_router
from services.portfolio.portfolio_router import router as portfolio_router
from services.paper.paper_router import router as paper_router

logger = logging.getLogger("UltrarentableAPI")


def _autonomous_runtime_enabled() -> bool:
    raw = os.getenv("ULTRARENTABLE_AUTONOMOUS_RUNTIME", "false").strip().lower()
    return raw in {"1", "true", "yes", "on"}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Iniciando infraestructura Ultrarentable V2...")
    init_db()

    with SessionLocal() as db:
        purge_result = purge_legacy_demo_records(db)
        if any(purge_result.values()):
            logger.warning("Eliminados registros bootstrap sintéticos legacy: %s", purge_result)

    autonomous_enabled = _autonomous_runtime_enabled()
    app.state.autonomous_runtime_enabled = autonomous_enabled

    if autonomous_enabled:
        await supervisor_instance.start_all()
        logger.info("SystemSupervisor activo: 8 workers operando y emitiendo heartbeats.")

        try:
            from services.optimization.continuous_research_daemon import continuous_research_daemon
            continuous_research_daemon.start_autonomous()
            logger.info("ContinuousResearchDaemon iniciado autónomamente 24/7.")
        except Exception as de:
            logger.error("Error iniciando ContinuousResearchDaemon: %s", de)

        try:
            from services.portfolio.autonomous_meta_daemon import autonomous_meta_daemon
            autonomous_meta_daemon.start_autonomous(interval_seconds=60)
            logger.info("AutonomousMetaDaemon iniciado autónomamente 24/7.")
        except Exception as me:
            logger.error("Error iniciando AutonomousMetaDaemon: %s", me)

        try:
            from services.monitoring.high_availability_watchdog import ha_watchdog
            ha_watchdog.start()
            logger.info("HighAvailabilityWatchdog iniciado.")
        except Exception as we:
            logger.error("Error iniciando HighAvailabilityWatchdog: %s", we)
    else:
        logger.info("Modo local/dev: ULTRARENTABLE_AUTONOMOUS_RUNTIME=false; worker fleet 24/7 no se inicia.")

    yield

    if autonomous_enabled:
        logger.info("Deteniendo servicios y cerrando conexiones...")
        try:
            from services.monitoring.high_availability_watchdog import ha_watchdog
            ha_watchdog.stop()
        except Exception:
            pass
        try:
            from services.portfolio.autonomous_meta_daemon import autonomous_meta_daemon
            autonomous_meta_daemon.stop_autonomous()
        except Exception:
            pass
        try:
            from services.optimization.continuous_research_daemon import continuous_research_daemon
            continuous_research_daemon.pause()
        except Exception:
            pass
        await supervisor_instance.stop_all()
        logger.info("Apagado ordenado completado.")


app = FastAPI(
    title="Ultrarentable Dual-Engine Multi-Asset Quantitative Platform",
    version="2.2.0",
    description=(
        "Plataforma Cuantitativa Dual REAL-ONLY: "
        "TRACK_FONDEO (CME Futures / Preservación de Capital) & "
        "TRACK_ULTRA (Multi-Asset Registry-Driven). "
        "Motor desacoplado con AsyncEventBus, QVF Evidence Gate y Streaming SSE."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=LOCAL_WEB_ORIGINS or ["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# REGISTRO DE ROUTERS V1
app.include_router(legacy_routes, prefix="/api/v1", tags=["v1-core"])
app.include_router(sqx_router, prefix="/api/v1", tags=["v1-sqx"])
app.include_router(providers_router, prefix="/api/v1", tags=["v1-providers"])
app.include_router(candidates_router, prefix="/api/v1", tags=["v1-candidates"])
app.include_router(execution_router, prefix="/api/v1", tags=["v1-execution"])
app.include_router(audit_router, prefix="/api/v1", tags=["v1-audit"])
app.include_router(discovery_router, tags=["v1-discovery"])
app.include_router(system_health_router, prefix="/api/v1", tags=["v1-health"])
app.include_router(research_router, tags=["v1-research"])
app.include_router(gates_router, prefix="/api/v1", tags=["v1-gates"])
app.include_router(firebase_sync_router, prefix="/api/v1", tags=["v1-firebase"])
app.include_router(portfolio_router, prefix="/api/v1/portfolio", tags=["v1-portfolio"])
app.include_router(version_router, prefix="/api/v1", tags=["v1-version"])
app.include_router(lineage_router, prefix="/api/v1", tags=["v1-lineage"])
app.include_router(policy_router, prefix="/api/v1", tags=["v1-policy"])
app.include_router(research_lab_router, prefix="/api/v1", tags=["v1-research-lab"])
app.include_router(telemetry_router, prefix="/api/v1/telemetry", tags=["v1-telemetry"])
app.include_router(job_queue_router, prefix="/api/v1/jobs", tags=["v1-jobs"])
app.include_router(forward_router, prefix="/api/v1/forward", tags=["v1-forward"])
app.include_router(certified_summary_router, prefix="/api/v1", tags=["v1-certified"])

# REGISTRO DE ROUTERS V2
app.include_router(strategy_lab_router, prefix="/api/v2", tags=["v2-strategy-lab"])
app.include_router(telemetry_router, prefix="/api/v2/telemetry", tags=["v2-telemetry"])
app.include_router(validation_router, prefix="/api/v2/validation", tags=["v2-validation"])
app.include_router(semantic_router, prefix="/api/v2/semantic", tags=["v2-semantic"])
app.include_router(ultra_router, prefix="/api/v2/ultra", tags=["v2-ultra"])
app.include_router(portfolio_router, prefix="/api/v2/portfolio", tags=["v2-portfolio"])
app.include_router(paper_router, prefix="/api/v2/paper", tags=["v2-paper"])
app.include_router(lineage_router, prefix="/api/v2", tags=["v2-lineage"])
app.include_router(policy_router, prefix="/api/v2", tags=["v2-policy"])
app.include_router(research_lab_router, prefix="/api/v2", tags=["v2-research-lab"])
app.include_router(job_queue_router, prefix="/api/v2", tags=["v2-jobs"])
app.include_router(forward_router, prefix="/api/v2", tags=["v2-forward"])
app.include_router(certified_summary_router, prefix="/api/v2", tags=["v2-certified"])
app.include_router(real_data_router, prefix="/api/v2", tags=["v2-real-data"])
app.include_router(real_data_router, prefix="/api/v2/real", tags=["v2-real-data-alias"])


@app.get("/api/v1/version", tags=["system"])
@app.get("/api/v1/versions", tags=["system"])
@app.get("/api/v2/versions", tags=["system"])
def versions() -> Dict[str, Any]:
    return {
        "api_version": app.version,
        "autonomous_runtime_enabled": bool(getattr(app.state, "autonomous_runtime_enabled", False)),
        "runtime_mode": "AUTONOMOUS_24X7" if getattr(app.state, "autonomous_runtime_enabled", False) else "LOCAL_API_ONLY",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
