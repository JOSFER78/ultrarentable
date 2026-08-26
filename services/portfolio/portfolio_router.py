"""services/portfolio/portfolio_router.py
FastAPI Router para la gestión, ensamblado y consulta de Meta-Estrategias y Portafolios.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from services.api.app.db.database import get_db, PortfolioModel, CandidateModel
from services.portfolio.autonomous_meta_daemon import autonomous_meta_daemon
from services.portfolio.meta_ensemble_service import MetaEnsembleService

router = APIRouter(tags=["Portfolio Studio & Meta-Strategies"])


@router.get("/status")
def get_portfolio_engine_status() -> Dict[str, Any]:
    """Retorna el estado de ejecución en vivo del motor de meta-estrategias 24/7."""
    return {
        "daemon_running": autonomous_meta_daemon.is_running,
        "interval_seconds": autonomous_meta_daemon.interval_seconds,
        "last_run_utc": autonomous_meta_daemon.last_run_timestamp,
        "portfolios_assembled_count": autonomous_meta_daemon.portfolios_assembled_count,
        "last_error": autonomous_meta_daemon.last_error,
    }


@router.get("/assembled")
def list_assembled_portfolios(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Lista todos los meta-portafolios ensamblados y registrados en SQLite WAL."""
    ports = db.query(PortfolioModel).order_by(PortfolioModel.created_at.desc()).all()
    results = []
    for p in ports:
        try:
            comps = json.loads(p.components_json) if p.components_json else []
        except Exception:
            comps = []
        try:
            corrs = json.loads(p.correlation_matrix_json) if p.correlation_matrix_json else []
        except Exception:
            corrs = []
        results.append({
            "portfolio_id": p.portfolio_id,
            "name": p.name,
            "target_route": p.target_route,
            "base_capital_usd": p.base_capital_usd,
            "current_equity_usd": p.current_equity_usd,
            "components": comps,
            "correlation_matrix": corrs,
            "annualized_roi_pct": p.annualized_roi_pct,
            "monthly_roi_pct": p.monthly_roi_pct,
            "max_drawdown_pct": p.max_drawdown_pct,
            "profit_factor": p.profit_factor,
            "canonical_hash": p.canonical_hash,
            "status": p.status,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        })
    return results


@router.post("/assemble")
def assemble_custom_portfolio(
        payload: Dict[str, Any],
        db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Ensambla un nuevo portafolio combinando IDs de estrategias seleccionadas."""
    candidate_ids = payload.get("candidate_ids", [])
    name = payload.get("name", "Custom Alpha Ensamble")
    target_route = payload.get("target_route", "ULTRA")
    base_capital = float(payload.get("base_capital", 10000.0))

    if len(candidate_ids) < 2:
        raise HTTPException(status_code=422, detail="SE_REQUIEREN_AL_MENOS_2_ESTRATEGIAS")

    meta = MetaEnsembleService.assemble_meta_portfolio(
        candidate_ids=candidate_ids,
        name=name,
        target_route=target_route,
        base_capital=base_capital,
        db_session=db,
    )
    if not meta:
        raise HTTPException(status_code=422, detail="NO_SE_PUDO_ENSAMBLAR_EL_PORTAFOLIO")

    return meta
