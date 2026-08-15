from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.api.app.api.routes import router
from services.api.app.config import LOCAL_WEB_ORIGINS
from services.api.app.db.database import init_db

init_db()

app = FastAPI(
    title="BingX Ultra Strategy Lab — Local Backend",
    version="3.0.0-reviewed",
    description=(
        "Backend local REAL-ONLY sin Docker. FastAPI + SQLite WAL + filesystem local. "
        "Incluye DSL validado, backtest determinista, juez de evidencia y campañas evolutivas multirronda."
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
