"""FastAPI Router for Candidates, Scorecards and Reclassification."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from services.api.app.db.database import get_db, CandidateModel

candidates_router = APIRouter(prefix="/candidates", tags=["Strategy Candidates & Scorecards"])


class StatusUpdateSchema(BaseModel):
    status: str = Field(..., description="INVESTIGACION_BTC, RECHAZADA_FONDEO_DD, CANDIDATA_FONDEO, PAPER, LISTA_PARA_EVALUACION, EJECUTANDO, PAUSADA, RETIRADA")
    reason: str = Field(..., description="Mandatory audit trail reason for status change")


@candidates_router.get("")
def list_candidates(
    route: Optional[str] = Query(None, description="ULTRA, FONDEO"),
    status: Optional[str] = Query(None, description="Filter by candidate status"),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """List strategy candidates with filters and scorecards."""
    query = db.query(CandidateModel)
    if route:
        query = query.filter(CandidateModel.route == route.upper())
    if status:
        query = query.filter(CandidateModel.status == status)
        
    results = []
    for c in query.order_by(CandidateModel.created_at.desc()).all():
        results.append({
            "candidate_id": c.candidate_id,
            "name": c.name,
            "route": c.route,
            "symbol": c.symbol,
            "timeframe": c.timeframe,
            "dataset_id": c.dataset_id,
            "status": c.status,
            "status_reason": c.status_reason,
            "metrics": {
                "in_sample": {
                    "net_profit_usd": c.net_profit_is,
                    "trades": c.trades_is,
                    "profit_factor": c.profit_factor_is,
                    "max_drawdown_pct": c.max_dd_is_pct,
                },
                "out_of_sample": {
                    "net_profit_usd": c.net_profit_oos,
                    "trades": c.trades_oos,
                    "profit_factor": c.profit_factor_oos,
                    "max_drawdown_pct": c.max_dd_oos_pct,
                },
                "anti_overfit": {
                    "ratio_oos_is": c.ratio_oos_is,
                    "wfo_pass_pct": c.wfo_pass_pct,
                    "monte_carlo_score": c.monte_carlo_score,
                }
            },
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })
    return results


@candidates_router.get("/{candidate_id}")
def get_candidate(candidate_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get single strategy candidate scorecard and validation details."""
    c = db.query(CandidateModel).filter(CandidateModel.candidate_id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="CANDIDATE_NOT_FOUND")
    return {
        "candidate_id": c.candidate_id,
        "name": c.name,
        "route": c.route,
        "symbol": c.symbol,
        "timeframe": c.timeframe,
        "dataset_id": c.dataset_id,
        "status": c.status,
        "status_reason": c.status_reason,
        "metrics": {
            "in_sample": {
                "net_profit_usd": c.net_profit_is,
                "trades": c.trades_is,
                "profit_factor": c.profit_factor_is,
                "max_drawdown_pct": c.max_dd_is_pct,
            },
            "out_of_sample": {
                "net_profit_usd": c.net_profit_oos,
                "trades": c.trades_oos,
                "profit_factor": c.profit_factor_oos,
                "max_drawdown_pct": c.max_dd_oos_pct,
            },
            "anti_overfit": {
                "ratio_oos_is": c.ratio_oos_is,
                "wfo_pass_pct": c.wfo_pass_pct,
                "monte_carlo_score": c.monte_carlo_score,
            }
        },
        "scorecard_json": c.scorecard_json,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


@candidates_router.patch("/{candidate_id}/status")
def update_candidate_status(
    candidate_id: str,
    payload: StatusUpdateSchema,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Update candidate status with mandatory reason."""
    c = db.query(CandidateModel).filter(CandidateModel.candidate_id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="CANDIDATE_NOT_FOUND")
    c.status = payload.status
    c.status_reason = payload.reason
    db.commit()
    return {"status": "SUCCESS", "candidate_id": candidate_id, "new_status": c.status, "reason": c.status_reason}
