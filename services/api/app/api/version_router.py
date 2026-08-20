"""FastAPI Router for Engine & Quantitative Model Versions."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from services.api.app.db.database import get_db, CandidateModel
from services.version_control_manager import version_manager


version_router = APIRouter(prefix="/versions", tags=["Engine & Model Versioning"])


class VersionBumpRequest(BaseModel):
    name: str = Field(..., description="Nombre descriptivo de la versión e.g. Ultrarentable V1.03 (Master Forensic Architecture)")
    description: str = Field(..., description="Descripción detallada de la arquitectura o cambios introducidos")
    changes: List[str] = Field(default_factory=list, description="Lista de cambios específicos")
    new_version: Optional[str] = Field(None, description="Número de versión opcional e.g. '1.03'. Si es None, se auto-incrementa.")


@version_router.get("")
def get_engine_versions_summary(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Return active engine version, changelog history and strategy counts per version."""
    info = version_manager.get_full_version_info()
    
    # Count strategies in database grouped by engine_version
    version_counts: Dict[str, int] = {}
    try:
        from sqlalchemy import func
        rows = db.query(CandidateModel.engine_version, func.count(CandidateModel.candidate_id)).group_by(CandidateModel.engine_version).all()
        for v, count in rows:
            version_counts[v or "1.00"] = count
    except Exception:
        version_counts = {info["active_version"]: 0, "1.00": 0}

    # Enrich history with live strategy counts
    enriched_history = []
    for item in info.get("history", []):
        h = dict(item)
        h["strategy_count"] = version_counts.get(item["version"], 0)
        enriched_history.append(h)

    return {
        "current_version": info["active_version"],
        "current_name": info["active_name"],
        "pipeline_version": info["pipeline_version"],
        "codebase_fingerprint": info["codebase_fingerprint"],
        "code_drift_detected": info["code_drift_detected"],
        "git_commit": info["git_commit"],
        "last_bump_utc": info["last_bump_utc"],
        "history": enriched_history,
        "version_distribution": version_counts,
    }


@version_router.get("/current")
def get_current_version() -> Dict[str, Any]:
    """Quick check for the current engine and pipeline version."""
    info = version_manager.get_full_version_info()
    return {
        "engine_version": info["active_version"],
        "engine_name": info["active_name"],
        "pipeline_version": info["pipeline_version"],
        "codebase_fingerprint": info["codebase_fingerprint"],
        "code_drift_detected": info["code_drift_detected"],
    }


@version_router.get("/drift")
def check_code_drift() -> Dict[str, Any]:
    """Inspect if disk codebase has drifted from the active version fingerprint."""
    info = version_manager.get_full_version_info()
    return {
        "code_drift_detected": info["code_drift_detected"],
        "active_version": info["active_version"],
        "active_fingerprint": info["codebase_fingerprint"],
        "runtime_fingerprint": info["current_runtime_fingerprint"],
        "recommendation": "Ejecutar bump de versión a v1.03+ para registrar las modificaciones de código." if info["code_drift_detected"] else "Código sincronizado con la versión activa.",
    }


@version_router.post("/bump")
def bump_engine_version(payload: VersionBumpRequest) -> Dict[str, Any]:
    """Bump the engine version, update manifest, regenerate SSOT and record in SQLite."""
    try:
        updated = version_manager.bump_version(
            name=payload.name,
            description=payload.description,
            changes=payload.changes,
            new_version=payload.new_version,
        )
        return {
            "status": "SUCCESS",
            "message": f"Versión del motor incrementada exitosamente a v{updated['active_version']}",
            "active_version": updated["active_version"],
            "active_name": updated["active_name"],
            "codebase_fingerprint": updated["codebase_fingerprint"],
            "git_commit": updated["git_commit"],
            "last_bump_utc": updated["last_bump_utc"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error durante el bump de versión: {str(e)}")
