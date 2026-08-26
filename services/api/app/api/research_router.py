"""Research Lab API: real-only strategy research and improvement.

This router is orchestration only. It never invents metrics, never certifies a
candidate, and never overwrites measured results with defaults. Certification
remains exclusively owned by the canonical validation pipeline.
"""

from __future__ import annotations

import logging
import sqlite3
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.api.app.config import STATE_DB_PATH
from services.engine_version import CURRENT_ENGINE_VERSION
from services.optimization.continuous_research_daemon import continuous_research_daemon
from services.api.app.core.fast_cache import in_memory_cached

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/research", tags=["Research & Strategy Improvement"])


class ImproveRequest(BaseModel):
    technique: str = Field(default="REAL_ONLY_SEMANTIC_EVOLUTION")
    n_trials: int = Field(default=15, ge=1, le=500)


class EnqueueCandidateRequest(BaseModel):
    candidate_id: str
    priority: int = Field(default=1, ge=1, le=10)


@router.get("/daemon/status")
@in_memory_cached(key_prefix="research_daemon_status", ttl=1.5)
def get_daemon_status() -> Dict[str, Any]:
    try:
        status = dict(continuous_research_daemon.get_status())
        status["engine_version"] = CURRENT_ENGINE_VERSION
        status["mode"] = "REAL_ONLY"
        status["certification_authority"] = "canonical_validation_pipeline"
        return status
    except Exception as exc:
        logger.exception("Error al obtener estado del daemon")
        return {
            "is_running": False,
            "error": str(exc),
            "engine_version": CURRENT_ENGINE_VERSION,
            "mode": "REAL_ONLY",
            "certification_authority": "canonical_validation_pipeline",
        }


@router.post("/daemon/start")
def start_daemon() -> Dict[str, Any]:
    continuous_research_daemon.start_autonomous()
    return {
        "success": True,
        "message": "Bucle de investigación autónoma REAL-ONLY iniciado.",
        "engine_version": CURRENT_ENGINE_VERSION,
    }


@router.post("/daemon/stop")
def stop_daemon() -> Dict[str, Any]:
    continuous_research_daemon.stop()
    return {
        "success": True,
        "message": "Bucle de investigación autónoma detenido.",
        "engine_version": CURRENT_ENGINE_VERSION,
    }


@router.get("/failed-candidates")
@in_memory_cached(key_prefix="research_failed", ttl=2.0)
def get_failed_and_incubator_candidates(
    limit: int = Query(100, ge=1, le=500),
    route: Optional[str] = None,
) -> Dict[str, Any]:
    conn = sqlite3.connect(str(STATE_DB_PATH), timeout=15.0)
    conn.row_factory = sqlite3.Row
    try:
        query = """
            SELECT candidate_id, name, symbol, timeframe, route, status,
                   profit_factor_is, profit_factor_oos, max_dd_oos_pct,
                   net_profit_oos, trades_oos, scorecard_json,
                   engine_version, validation_pipeline_version, created_at
            FROM candidates
            WHERE status IN (
                'REJECTED', 'FAILED_GATE', 'INCUBADORA_REPROGRAMACION',
                'REFINADO_TIER_2', 'INVESTIGACION_BTC', 'RECHAZADA_FONDEO_DD',
                'REJECTED_GATES_INCOMPLETE'
            )
        """
        params: List[Any] = []
        if route:
            query += " AND UPPER(route) = UPPER(?)"
            params.append(route)
        query += " ORDER BY rowid DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(query, params).fetchall()

        candidates: List[Dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            item["engine_version_current"] = CURRENT_ENGINE_VERSION
            item["is_stale"] = str(item.get("engine_version") or "") != CURRENT_ENGINE_VERSION
            candidates.append(item)

        return {
            "total_failed_candidates": len(candidates),
            "engine_version": CURRENT_ENGINE_VERSION,
            "mode": "REAL_ONLY",
            "candidates": candidates,
        }
    finally:
        conn.close()


@router.post("/improve/{candidate_id}")
def run_strategy_auto_improvement(
    candidate_id: str,
    req: Optional[ImproveRequest] = None,
) -> Dict[str, Any]:
    """Run real closed-loop research; return proposals/results without certifying them."""
    request = req or ImproveRequest()

    conn = sqlite3.connect(str(STATE_DB_PATH), timeout=15.0)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute("SELECT candidate_id, status FROM candidates WHERE candidate_id = ?", (candidate_id,)).fetchone()
    finally:
        conn.close()

    if not row:
        raise HTTPException(status_code=404, detail=f"Candidato {candidate_id} no encontrado.")

    try:
        result = continuous_research_daemon.optimize_candidate_closed_loop(
            candidate_id=candidate_id,
            max_iterations=min(3, request.n_trials),
            generation_round=1,
        )
    except Exception as exc:
        logger.exception("Error en investigación cerrada para %s", candidate_id)
        raise HTTPException(status_code=500, detail=f"Research execution failed: {exc}") from exc

    return {
        "success": result.get("status") not in {"ERROR_NOT_FOUND", "ERROR_NO_DATASET", "ERROR_INSUFFICIENT_DATA"},
        "candidate_id": candidate_id,
        "engine_version": CURRENT_ENGINE_VERSION,
        "mode": "REAL_ONLY",
        "certification_owned_by": "canonical_validation_pipeline",
        "research_result": result,
    }
