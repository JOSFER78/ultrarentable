"""services/api/app/main.py
Backend Central de Ultrarentable V2 (FastAPI + SQLite WAL + EventBus + SystemSupervisor).
Expone APIs V1 y V2 con soporte para streaming SSE y gobernanza Zero-Trust.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from services.api.app.config import LOCAL_WEB_ORIGINS
from services.api.app.db.database import init_db
from services.api.app.api.version_router import version_router
from services.api.app.api.lineage_router import lineage_router
from services.api.app.api.policy_router import policy_router
from services.api.app.api.research_lab_router import research_lab_router
from services.api.app.api.job_queue_router import job_queue_router, forward_router
from services.api.app.api.certified_summary_router import certified_summary_router

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

# Routers V2 Modulares
from services.monitoring.telemetry_router import router as telemetry_router, supervisor_instance
from services.validation.validation_router import router as validation_router
from services.semantic_ai.semantic_router import router as semantic_router
from services.exploitation_engines.ultra_router import router as ultra_router
from services.portfolio.portfolio_router import router as portfolio_router
from services.paper.paper_router import router as paper_router

logger = logging.getLogger("UltrarentableAPI")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Ciclo de vida de FastAPI: Inicializa DB y arranca el ecosistema autónomo 24/7."""
    logger.info("Iniciando infraestructura Ultrarentable V2...")
    init_db()

    await supervisor_instance.start_all()
    logger.info("SystemSupervisor activo: 8 workers operando y emitiendo heartbeats.")

    try:
        from services.optimization.continuous_research_daemon import continuous_research_daemon
        continuous_research_daemon.start_autonomous()
        logger.info("🟢 ContinuousResearchDaemon iniciado autónomamente 24/7 en arranque.")
    except Exception as de:
        logger.error(f"Error iniciando ContinuousResearchDaemon: {de}")

    try:
        from services.portfolio.autonomous_meta_daemon import autonomous_meta_daemon
        autonomous_meta_daemon.start_autonomous(interval_seconds=60)
        logger.info("🟢 AutonomousMetaDaemon iniciado autónomamente 24/7 en arranque.")
    except Exception as me:
        logger.error(f"Error iniciando AutonomousMetaDaemon: {me}")

    try:
        from services.monitoring.high_availability_watchdog import ha_watchdog
        ha_watchdog.start()
        logger.info("🟢 HighAvailabilityWatchdog iniciado (Supervisión 24/7 activa cada 10s).")
    except Exception as we:
        logger.error(f"Error iniciando HighAvailabilityWatchdog: {we}")

    yield

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
    title="Ultrarentable Dual-Engine Quantitative Platform",
    version="2.2.0",
    description=(
        "Plataforma Cuantitativa Dual REAL-ONLY: "
        "TRACK_FONDEO (CME Futures / Preservación de Capital / DSR > 2.0 / DLL Protection) & TRACK_ULTRA (BingX Crypto Perps / Asimetría Positiva). "
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

# V1
app.include_router(legacy_routes, prefix="/api/v1", tags=["v1-core"])
app.include_router(sqx_router, prefix="/api/v1", tags=["v1-sqx"])
app.include_router(providers_router, prefix="/api/v1", tags=["v1-providers"])
app.include_router(candidates_router, prefix="/api/v1", tags=["v1-candidates"])
# Canonical certification endpoint: independent from legacy candidate status/summary.
app.include_router(certified_summary_router, prefix="/api/v1", tags=["v1-certified-canonical"])
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
app.include_router(job_queue_router, prefix="/api/v1", tags=["v1-jobs"])
app.include_router(forward_router, prefix="/api/v1", tags=["v1-forward"])

# V2
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
app.include_router(real_data_router, prefix="/api/v2", tags=["v2-real-data"])
app.include_router(real_data_router, prefix="/api/v2/real", tags=["v2-real-data-alias"])


@app.get("/api/v1/version", tags=["system"])
@app.get("/api/v1/versions", tags=["system"])
@app.get("/api/v2/versions", tags=["system"])
def get_platform_versions() -> Dict[str, Any]:
    from services.version_control_manager import version_manager
    info = version_manager.get_full_version_info()
    return {
        "current_version": info.get("active_version", "5.3.0"),
        "current_name": info.get("active_name", "Ultrarentable V5.3.0"),
        "platform_version": info.get("active_version", "5.3.0"),
        "api_version": "2.2.0",
        "engine_version": info.get("active_version", "5.3.0"),
        "pipeline_version": info.get("pipeline_version", "5.3.0"),
        "meta_engine_version": info.get("active_version", "5.3.0"),
        "evidence_gate_version": info.get("active_version", "5.3.0"),
        "strategy_generator_version": info.get("active_version", "5.3.0"),
        "portfolio_version": info.get("active_version", "5.3.0"),
        "git_commit": info.get("git_commit", ""),
        "git_commit_short": info.get("git_commit_short", ""),
        "git_branch": info.get("git_branch", "main"),
        "git_message": info.get("git_message", ""),
        "git_author": info.get("git_author", ""),
        "git_date": info.get("git_date", ""),
        "git_is_dirty": info.get("git_is_dirty", False),
        "codebase_fingerprint": info.get("codebase_fingerprint", ""),
        "code_drift_detected": info.get("code_drift_detected", False),
        "last_bump_utc": info.get("last_bump_utc", ""),
        "history": info.get("history", []),
        "status": "HEALTHY",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/", tags=["system"])
def read_root() -> Dict[str, Any]:
    return {
        "platform": "Ultrarentable Dual-Engine Quantitative Strategy Platform",
        "version": "2.2.0",
        "status": "RUNNING",
        "mode": "REAL_ONLY",
        "architecture": "CLEAN_MODULAR_ASYNC_EVENT_BUS",
        "tracks": {
            "TRACK_FONDEO": "CME Futures / Preservación de Capital / DSR > 2.0 / DLL Protection",
            "TRACK_ULTRA": "BingX Crypto Perps / Margen Aislado 1R / Piramidación Free-Risk / Bóveda Ratchet",
        },
    }
