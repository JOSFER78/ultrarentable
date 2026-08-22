"""services/api/app/main.py
Backend Central de Ultrarentable V2 (FastAPI + SQLite WAL + EventBus + SystemSupervisor).
Expone APIs V1 y V2 con soporte para streaming SSE y gobernanza Zero-Trust.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Config & Base de datos
from services.api.app.config import LOCAL_WEB_ORIGINS
from services.api.app.db.database import init_db

# Routers V1 Legados
from services.api.app.api.routes import router as legacy_routes
from services.api.app.api.sqx_router import sqx_router
from services.api.app.api.providers_router import providers_router
from services.api.app.api.candidates_router import candidates_router
from services.api.app.api.execution_router import execution_router
from services.api.app.api.audit_router import audit_router
from services.api.app.api.system_health_router import system_health_router
from services.api.app.api.real_data_router import router as real_data_router
from services.api.app.api.gates_router import gates_router
from services.api.app.api.firebase_sync_router import firebase_sync_router
from services.api.app.api.version_router import version_router
from services.api.app.api.discovery_router import router as discovery_router
from services.api.app.api.portfolios_router import portfolios_router
from services.api.app.api.research_router import router as research_router

# Routers V2 Modulares
from services.monitoring.telemetry_router import router as telemetry_router, supervisor_instance
from services.validation.validation_router import router as validation_router
from services.semantic_ai.semantic_router import router as semantic_router
from services.exploitation_engines.ultra_router import router as ultra_router
from services.portfolio.portfolio_router import router as portfolio_router
from services.paper.paper_router import router as paper_router

logger = logging.getLogger("UltrarentableAPI")


from services.sqx_bridge.sqx_sync_worker import SQXSyncWorker
from services.sqx_bridge.sqx_client import SQXMCPClient
from services.api.app.factory.continuous_search_daemon import continuous_search_daemon
from services.api.app.api.search_router import router as search_router

async def _periodic_sqx_sync():
    """Sincroniza continuamente los databanks de SQX y garantiza que el proyecto esté corriendo 24/7."""
    worker = SQXSyncWorker()
    client = SQXMCPClient()
    
    # Auto-conectar y asegurar que Ultra_Auto_Pilot esté corriendo en SQX (sin bloquear el event loop)
    try:
        await asyncio.to_thread(client.run_project, "Ultra_Auto_Pilot")
        logger.info("SQX Auto-Connect: Proyecto Ultra_Auto_Pilot lanzado en VPS.")
    except Exception as e:
        logger.debug(f"SQX initial launch note: {e}")

    while True:
        try:
            await asyncio.to_thread(worker.sync_databank, "Ultra_Auto_Pilot", "Results")
            await asyncio.to_thread(worker.sync_databank, "Ultra_Auto_Pilot", "Last generation")
        except Exception as e:
            logger.debug(f"SQX periodic sync notice: {e}")
        await asyncio.sleep(30)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Ciclo de vida de FastAPI: Inicializa DB, arranca workers, demonio 24/7 y sincronizador SQX."""
    print("DEBUG LIFESPAN: 1. Iniciando DB...", flush=True)
    logger.info("Iniciando infraestructura Ultrarentable V2...")
    init_db()
    print("DEBUG LIFESPAN: 2. DB inicializada. Arrancando supervisor...", flush=True)
    await supervisor_instance.start_all()
    logger.info("SystemSupervisor activo: 8 workers operando y emitiendo heartbeats.")
    print("DEBUG LIFESPAN: 3. Supervisor iniciado. Arrancando continuous_search_daemon...", flush=True)
    
    # Arrancar Demonio de Búsqueda y Optimización Continua 24/7
    try:
        continuous_search_daemon.start()
        logger.info("24/7 Continuous Strategy Search & Mining Daemon ACTIVO.")
    except Exception as e:
        logger.error(f"Error iniciando continuous_search_daemon: {e}")

    print("DEBUG LIFESPAN: 4. continuous_search_daemon iniciado. Arrancando continuous_research_daemon...", flush=True)
    # Arrancar Demonio de Refinamiento Cuantitativo & Bucle Autónomo 24/7 (Panel 4)
    from services.optimization.continuous_research_daemon import continuous_research_daemon
    try:
        continuous_research_daemon.start_autonomous()
        logger.info("24/7 Continuous Research & Refinement Daemon (Panel 4) ACTIVO.")
    except Exception as e:
        logger.error(f"Error iniciando continuous_research_daemon: {e}")

    print("DEBUG LIFESPAN: 5. continuous_research_daemon iniciado. Arrancando ha_watchdog...", flush=True)
    # Iniciar Watchdog de Alta Disponibilidad y Self-Healing 24/7
    from services.monitoring.high_availability_watchdog import ha_watchdog
    ha_watchdog.start()

    print("DEBUG LIFESPAN: 6. ha_watchdog iniciado. Arrancando periodic SQX sync...", flush=True)
    # Iniciar tarea asíncrona de sincronización y supervisión 24/7 con StrategyQuant X
    sync_task = asyncio.create_task(_periodic_sqx_sync())
    
    print("DEBUG LIFESPAN: 7. Yielding to FastAPI/Uvicorn server...", flush=True)
    yield
    print("DEBUG LIFESPAN: 8. Apagando infraestructura...", flush=True)
    
    sync_task.cancel()
    ha_watchdog.stop()
    continuous_research_daemon.pause()
    continuous_search_daemon.stop()
    logger.info("Deteniendo SystemSupervisor y cerrando conexiones...")
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

# Configuración CORS para Next.js 14/16
app.add_middleware(
    CORSMiddleware,
    allow_origins=LOCAL_WEB_ORIGINS or ["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)

# ----------------------------------------------------------------------------
# REGISTRO DE ROUTERS V1 (LEGACY COMPATIBILITY)
# ----------------------------------------------------------------------------
app.include_router(legacy_routes, prefix="/api/v1", tags=["v1-core"])
app.include_router(sqx_router, prefix="/api/v1", tags=["v1-sqx"])
app.include_router(search_router, tags=["v1-search"])
app.include_router(providers_router, prefix="/api/v1", tags=["v1-providers"])
app.include_router(candidates_router, prefix="/api/v1", tags=["v1-candidates"])
app.include_router(execution_router, prefix="/api/v1", tags=["v1-execution"])
app.include_router(audit_router, prefix="/api/v1", tags=["v1-audit"])
app.include_router(system_health_router, prefix="/api/v1", tags=["v1-health"])
app.include_router(gates_router, prefix="/api/v1", tags=["v1-gates"])
app.include_router(firebase_sync_router, prefix="/api/v1", tags=["v1-firebase-sync"])
app.include_router(version_router, prefix="/api/v1", tags=["v1-versions"])
app.include_router(discovery_router)
app.include_router(portfolios_router)
app.include_router(research_router)

# ----------------------------------------------------------------------------
# REGISTRO DE ROUTERS V2 (CLEAN ARCHITECTURE & DUAL-TRACK)
# ----------------------------------------------------------------------------
app.include_router(telemetry_router, prefix="/api/v2/telemetry", tags=["v2-telemetry"])
app.include_router(validation_router, prefix="/api/v2/validation", tags=["v2-validation"])
app.include_router(semantic_router, prefix="/api/v2/semantic", tags=["v2-semantic"])
app.include_router(ultra_router, prefix="/api/v2/ultra", tags=["v2-ultra"])
app.include_router(portfolio_router, prefix="/api/v2/portfolio", tags=["v2-portfolio"])
app.include_router(paper_router, prefix="/api/v2/paper", tags=["v2-paper"])

# Montar real_data_router en /api/v2 y en /api/v2/real
app.include_router(real_data_router, prefix="/api/v2", tags=["v2-real-data"])
app.include_router(real_data_router, prefix="/api/v2/real", tags=["v2-real-data-alias"])


@app.get("/", tags=["system"])
def read_root() -> Dict[str, Any]:
    """Estado global del sistema y capacidades de la versión 2.2.0."""
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
        "v2_endpoints": [
            "/api/v2/telemetry/health",
            "/api/v2/telemetry/stream",
            "/api/v2/validation/evaluate",
            "/api/v2/semantic/failures/stats",
            "/api/v2/ultra/vault/config",
            "/api/v2/portfolio/weights",
            "/api/v2/paper/orders",
            "/api/v2/candidates/approved",
            "/api/v2/portfolio/combine",
        ],
    }
