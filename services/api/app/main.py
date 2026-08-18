"""services/api/app/main.py
Backend Central de Ultrarentable V2 (FastAPI + SQLite WAL + EventBus + SystemSupervisor).
Expone APIs V1 y V2 con soporte para streaming SSE y gobernanza Zero-Trust.
"""

from __future__ import annotations

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
    """Ciclo de vida de FastAPI: Inicializa DB y arranca el pool de 8 workers del Supervisor."""
    logger.info("Iniciando infraestructura Ultrarentable V2...")
    init_db()
    await supervisor_instance.start_all()
    logger.info("SystemSupervisor activo: 8 workers operando y emitiendo heartbeats.")
    yield
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
app.include_router(providers_router, prefix="/api/v1", tags=["v1-providers"])
app.include_router(candidates_router, prefix="/api/v1", tags=["v1-candidates"])
app.include_router(execution_router, prefix="/api/v1", tags=["v1-execution"])
app.include_router(audit_router, prefix="/api/v1", tags=["v1-audit"])
app.include_router(system_health_router, prefix="/api/v1", tags=["v1-health"])

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
    }
