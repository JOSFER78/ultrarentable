"""FastAPI Router for Engine & Quantitative Model Versions."""

from __future__ import annotations

import sqlite3
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from services.api.app.db.database import get_db, CandidateModel
from services.engine_version import (
    CURRENT_ENGINE_VERSION,
    CURRENT_ENGINE_NAME,
    CURRENT_VALIDATION_PIPELINE_VERSION,
    VERSION_HISTORY,
    get_current_version_info,
)

version_router = APIRouter(prefix="/versions", tags=["Engine & Model Versioning"])


@version_router.get("")
def get_engine_versions_summary(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Return active engine version, changelog history and strategy counts per version."""
    # Count strategies in database grouped by engine_version
    version_counts: Dict[str, int] = {}
    try:
        from sqlalchemy import func
        rows = db.query(CandidateModel.engine_version, func.count(CandidateModel.candidate_id)).group_by(CandidateModel.engine_version).all()
        for v, count in rows:
            version_counts[v or "1.00"] = count
    except Exception:
        version_counts = {"1.02": 0, "1.00": 0}

    # Enrich history with live strategy counts
    enriched_history = []
    for item in VERSION_HISTORY:
        h = dict(item)
        h["strategy_count"] = version_counts.get(item["version"], 0)
        enriched_history.append(h)

    return {
        "current_version": CURRENT_ENGINE_VERSION,
        "current_name": CURRENT_ENGINE_NAME,
        "pipeline_version": CURRENT_VALIDATION_PIPELINE_VERSION,
        "history": enriched_history,
        "version_distribution": version_counts,
    }


@version_router.get("/current")
def get_current_version() -> Dict[str, str]:
    """Quick check for the current engine and pipeline version."""
    return {
        "engine_version": CURRENT_ENGINE_VERSION,
        "engine_name": CURRENT_ENGINE_NAME,
        "pipeline_version": CURRENT_VALIDATION_PIPELINE_VERSION,
    }
