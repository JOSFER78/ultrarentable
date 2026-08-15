"""Search & Strategy Discovery API Router.

Exposes REST endpoints for querying the Universe Search Matrix,
triggering multi-market exploration runs (1m, 5m, 15m, 1h, 4h),
and monitoring real-time discovery telemetry.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from services.api.app.core.market_matrix import (
    CANONICAL_UNIVERSE_MATRIX,
    AssetClass,
    Timeframe,
)
from services.api.app.factory.universe_searcher import (
    UniverseSearchEngine,
    universe_search_engine,
)

router = APIRouter(prefix="/api/v1/search", tags=["Search & Discovery"])


class SearchRequest(BaseModel):
    symbols: Optional[List[str]] = Field(default=None, description="Filtrar por símbolos (ej. ['BTC-USDT', 'EURUSD', 'NQ'])")
    timeframes: Optional[List[str]] = Field(default=None, description="Filtrar por temporalidades (ej. ['1m', '5m', '15m', '1h', '4h'])")
    max_variations_per_cell: int = Field(default=25, ge=5, le=100)


@router.get("/matrix")
def get_universe_matrix() -> List[Dict[str, Any]]:
    """Return all cells in the Canonical Universe Search Matrix."""
    return [
        {
            "symbol": cell.symbol,
            "asset_class": cell.asset_class.value,
            "timeframe": cell.timeframe.value,
            "target_route": cell.target_route.value,
            "archetype": cell.primary_archetype.value,
            "description": cell.description,
            "max_dd_limit_pct": cell.max_dd_limit_pct,
            "min_pf_target": cell.min_pf_target,
        }
        for cell in CANONICAL_UNIVERSE_MATRIX
    ]


@router.get("/status")
def get_search_status() -> Dict[str, Any]:
    """Get current state and progress of the Universe Search Engine."""
    return {
        "is_running": universe_search_engine.is_running,
        "stats": universe_search_engine.stats,
        "supported_timeframes": [t.value for t in Timeframe],
        "supported_asset_classes": [a.value for a in AssetClass],
    }


def _run_search_task(timeframes: Optional[List[str]], max_variations: int):
    universe_search_engine.run_full_universe_matrix(
        timeframes=timeframes,
        max_variations_per_cell=max_variations
    )


@router.post("/run")
def trigger_matrix_search(
    req: SearchRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Trigger an asynchronous multi-market search run across selected matrix cells."""
    if universe_search_engine.is_running:
        return {
            "status": "ALREADY_RUNNING",
            "message": "La búsqueda en segundo plano ya está en curso.",
            "current_cell": universe_search_engine.stats.get("current_cell")
        }

    background_tasks.add_task(
        _run_search_task,
        req.timeframes,
        req.max_variations_per_cell
    )

    return {
        "status": "STARTED",
        "message": f"Búsqueda multi-mercado iniciada para temporalidades: {req.timeframes or 'Todas (1m, 5m, 15m, 1h, 4h)'}",
        "max_variations_per_cell": req.max_variations_per_cell
    }
