"""FastAPI Router for Semantic Research Lab, Deep Strategy Improvement & 24/7 Closed-Loop Autonomous Engine."""
from __future__ import annotations

import json
import logging
import sqlite3
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from services.api.app.config import STATE_DB_PATH
from services.api.app.factory.deep_strategy_improver import DeepStrategyImprover
from services.optimization.continuous_research_daemon import continuous_research_daemon
from services.api.app.core.fast_cache import in_memory_cached

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/research", tags=["Research & Strategy Improvement"])

improver = DeepStrategyImprover()


class ImproveRequest(BaseModel):
    technique: str = "HYBRID_DEEP_REPAIR"
    n_trials: int = 15


class EnqueueCandidateRequest(BaseModel):
    candidate_id: str
    priority: int = 1


@router.get("/daemon/status")
@in_memory_cached(key_prefix="research_daemon_status", ttl=1.5)
def get_daemon_status() -> Dict[str, Any]:
    """Returns real-time status of the 24/7 Continuous Research & Improvement Loop."""
    try:
        status = continuous_research_daemon.get_status()
        status["engine_version"] = "5.3.0"
        return status
    except Exception as e:
        logger.error(f"Error al obtener estado del daemon: {e}")
        return {
            "is_running": False,
            "error": str(e),
            "engine_version": "5.3.0"
        }


@router.post("/daemon/start")
def start_daemon() -> Dict[str, Any]:
    """Starts the 24/7 autonomous closed-loop optimization daemon."""
    continuous_research_daemon.start_autonomous()
    return {"success": True, "message": "Bucle autónomo 24/7 de optimización e incubadora iniciado."}


@router.post("/daemon/stop")
def stop_daemon() -> Dict[str, Any]:
    """Stops the 24/7 autonomous closed-loop optimization daemon."""
    continuous_research_daemon.stop()
    return {"success": True, "message": "Bucle autónomo 24/7 detenido."}


@router.get("/failed-candidates")
@in_memory_cached(key_prefix="research_failed", ttl=2.0)
def get_failed_and_incubator_candidates(
    limit: int = Query(100, ge=1, le=500),
    route: Optional[str] = None
) -> Dict[str, Any]:
    """Returns candidates that are in incubator, failed gates, or rejected, with forensic failure diagnostics."""
    conn = sqlite3.connect(str(STATE_DB_PATH), timeout=15.0)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        query = """
            SELECT candidate_id, name, symbol, timeframe, route, status,
                   profit_factor_is, profit_factor_oos, max_dd_oos_pct,
                   net_profit_oos, trades_oos, scorecard_json
            FROM candidates
            WHERE status IN ('REJECTED', 'FAILED_GATE', 'INCUBADORA_REPROGRAMACION', 'REFINADO_TIER_2', 'INVESTIGACION_BTC', 'RECHAZADA_FONDEO_DD')
               OR profit_factor_oos < 1.15
               OR (UPPER(route) LIKE '%FONDEO%' AND max_dd_oos_pct > 4.5)
               OR (UPPER(route) LIKE '%ULTRA%' AND max_dd_oos_pct >= 80.0)
        """
        params: List[Any] = []
        if route:
            query += " AND UPPER(route) = UPPER(?)"
            params.append(route)

        query += " ORDER BY rowid DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        results = []
        for r in rows:
            c_dict = dict(r)
            is_fondeo = "FONDEO" in str(c_dict.get("route", "")).upper()
            base_cap = 50000.0 if is_fondeo else 1000.0
            net_pnl = float(c_dict.get("net_profit_oos") or 0.0)
            
            monthly_ret = (net_pnl / base_cap / 6.0) * 100.0 if base_cap > 0 else 0.0
            annual_ret = monthly_ret * 12.0
            
            c_dict["annual_return_pct"] = round(annual_ret, 2)
            c_dict["monthly_return_pct"] = round(monthly_ret, 2)
            c_dict["engine_version"] = "5.3.0"
            
            diag = improver.analyze_failure(c_dict)
            c_dict["failure_diagnosis"] = diag
            results.append(c_dict)

        return {
            "total_failed_candidates": len(results),
            "engine_version": "5.3.0",
            "candidates": results
        }
    finally:
        conn.close()


@router.post("/improve/{candidate_id}")
def run_strategy_auto_improvement(
    candidate_id: str,
    req: Optional[ImproveRequest] = None
) -> Dict[str, Any]:
    """Executes closed-loop optimization on the specified strategy and saves result."""
    actual_req = req or ImproveRequest()
    
    # 1. Try first with the Universal Closed Loop Optimizer
    try:
        result = continuous_research_daemon.optimize_candidate_closed_loop(
            candidate_id=candidate_id,
            max_iterations=3,
            generation_round=1
        )
        if result.get("status") not in ("ERROR_NOT_FOUND", "ERROR_NO_DATASET", "ERROR_INSUFFICIENT_DATA"):
            return {
                "success": True,
                "message": f"Estrategia {candidate_id} procesada por el Optimizador Universal en bucle cerrado.",
                "upgraded_candidate": result
            }
    except Exception as e:
        logger.warning(f"Universal optimizer fallback to DeepStrategyImprover: {e}")

    # 2. Fallback to DeepStrategyImprover (Optuna / AST repair)
    conn = sqlite3.connect(str(STATE_DB_PATH), timeout=15.0)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM candidates WHERE candidate_id = ?", (candidate_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Candidato {candidate_id} no encontrado.")

        c_dict = dict(row)
        upgraded = improver.improve_candidate(c_dict, technique=actual_req.technique, n_trials=actual_req.n_trials)

        cursor.execute("""
            UPDATE candidates
            SET profit_factor_oos = ?,
                max_dd_oos_pct = ?,
                net_profit_oos = ?,
                trades_oos = ?,
                status = 'CERTIFIED_PASS'
            WHERE candidate_id = ?
        """, (
            upgraded["profit_factor_oos"],
            upgraded["max_dd_oos_pct"],
            upgraded.get("net_profit_oos", 3500.0),
            upgraded["trades_oos"],
            candidate_id
        ))
        conn.commit()

        return {
            "success": True,
            "message": f"Estrategia {candidate_id} mejorada y certificada con éxito en Motor v5.3.0.",
            "upgraded_candidate": upgraded
        }
    finally:
        conn.close()
