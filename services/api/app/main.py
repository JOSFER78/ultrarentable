from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.api.app.api.routes import router
from services.api.app.api.sqx_router import sqx_router
from services.api.app.api.providers_router import providers_router
from services.api.app.api.candidates_router import candidates_router
from services.api.app.api.execution_router import execution_router
from services.api.app.api.audit_router import audit_router
from services.api.app.api.system_health_router import system_health_router
from services.api.app.api.search_router import router as search_router
from services.api.app.config import LOCAL_WEB_ORIGINS
from services.api.app.db.database import init_db

init_db()

app = FastAPI(
    title="Ultrarentable Dual-Engine Strategy Lab — Local Backend",
    version="3.1.0",
    description=(
        "Backend local REAL-ONLY sin Docker. FastAPI + SQLite WAL + StrategyQuant X MCP Bridge. "
        "Dos flujos completamente desacoplados: ULTRA (BingX Crypto Perps) y FONDEO (Prop Firms CME)."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=LOCAL_WEB_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(router, prefix="/api/v1")
app.include_router(sqx_router, prefix="/api/v1")
app.include_router(providers_router, prefix="/api/v1")
app.include_router(candidates_router, prefix="/api/v1")
app.include_router(execution_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")
app.include_router(system_health_router, prefix="/api/v1")
app.include_router(search_router)


@app.get("/")
def read_root():
    return {
        "service": "BingX Ultra Strategy Lab Local Backend",
        "status": "RUNNING",
        "mode": "LOCAL_REAL_ONLY",
        "infrastructure": "NO_DOCKER_SQLITE_WAL",
        "implementation": {
            "data_pipeline": "REAL_VERIFIED",
            "strategy_registry": "IMPLEMENTED",
            "dsl_compiler": "IMPLEMENTED_SEMANTIC_VALIDATION",
            "backtest_engine": "FAST_DETERMINISTIC_APPROXIMATE",
            "campaign_orchestrator": "IMPLEMENTED_MULTIROUND",
            "adversarial_validation": "IMPLEMENTED",
        },
    }
