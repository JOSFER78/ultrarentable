"""FastAPI Router for Candidates, Scorecards, Reclassification, Robustness Verification & Code Exports."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from services.api.app.db.database import get_db, CandidateModel, AuditEventModel
from services.api.app.export.sqx_to_tradingview import generate_pinescript_v5
from services.api.app.export.sqx_to_ninjatrader import generate_ninjatrader_strategy_cs
from services.api.app.factory.robustness_verifier import verify_strategy_robustness

candidates_router = APIRouter(prefix="/candidates", tags=["Strategy Candidates & Scorecards"])


class StatusUpdateSchema(BaseModel):
    status: str = Field(..., description="INVESTIGACION_BTC, RECHAZADA_FONDEO_DD, CANDIDATA_FONDEO, PAPER, LISTA_PARA_EVALUACION, EJECUTANDO, PAUSADA, RETIRADA")
    reason: str = Field(..., description="Mandatory audit trail reason for status change")


@candidates_router.get("")
def list_candidates(
    route: Optional[str] = Query(None, description="ULTRA, FONDEO"),
    status: Optional[str] = Query(None, description="Filter by candidate status"),
    symbol: Optional[str] = Query(None, description="Filter by symbol (e.g. BTC-USDT, EURUSD, NQ)"),
    timeframe: Optional[str] = Query(None, description="Filter by timeframe (e.g. 1m, 5m, 15m, 1h, 4h)"),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """List strategy candidates with filters and scorecards."""
    query = db.query(CandidateModel)
    if route:
        query = query.filter(CandidateModel.route == route.upper())
    if status:
        query = query.filter(CandidateModel.status == status)
    if symbol:
        query = query.filter(CandidateModel.symbol.ilike(f"%{symbol}%"))
    if timeframe:
        query = query.filter(CandidateModel.timeframe == timeframe)
        
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


@candidates_router.post("/{candidate_id}/verify-robustness")
def verify_candidate_robustness(candidate_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Run Zero-Trust 5-Gate Robustness Verification on candidate."""
    c = db.query(CandidateModel).filter(CandidateModel.candidate_id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="CANDIDATE_NOT_FOUND")

    report = verify_strategy_robustness({
        "candidate_id": c.candidate_id,
        "name": c.name,
        "route": c.route,
        "trades_is": c.trades_is,
        "trades_oos": c.trades_oos,
        "net_profit_is": c.net_profit_is,
        "net_profit_oos": c.net_profit_oos,
        "profit_factor_is": c.profit_factor_is,
        "profit_factor_oos": c.profit_factor_oos,
        "max_dd_is_pct": c.max_dd_is_pct,
        "max_dd_oos_pct": c.max_dd_oos_pct,
        "ratio_oos_is": c.ratio_oos_is,
        "wfo_pass_pct": c.wfo_pass_pct,
        "monte_carlo_score": c.monte_carlo_score,
    })

    return {
        "candidate_id": report.candidate_id,
        "name": report.name,
        "route": report.route,
        "total_score_pct": report.total_score_pct,
        "is_approved_for_live": report.is_approved_for_live,
        "status_verdict": report.status_verdict,
        "gates": [
            {
                "gate_id": g.gate_id,
                "name": g.name,
                "passed": g.passed,
                "threshold": g.threshold,
                "measured_value": g.measured_value,
                "detail": g.detail
            }
            for g in report.gates
        ]
    }


@candidates_router.get("/{candidate_id}/export/tradingview")
def export_candidate_tradingview(candidate_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Export strategy candidate as TradingView Pine Script v5 code."""
    c = db.query(CandidateModel).filter(CandidateModel.candidate_id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="CANDIDATE_NOT_FOUND")
    
    code = generate_pinescript_v5(strategy_name=c.name, symbol=c.symbol.replace("-", ""), timeframe="60")
    return {
        "candidate_id": c.candidate_id,
        "strategy_name": c.name,
        "language": "Pine Script v5",
        "filename": f"{c.candidate_id}_tradingview.pine",
        "code": code
    }


@candidates_router.get("/{candidate_id}/export/ninjatrader")
def export_candidate_ninjatrader(candidate_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Export strategy candidate as NinjaTrader 8 C# Strategy code."""
    c = db.query(CandidateModel).filter(CandidateModel.candidate_id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="CANDIDATE_NOT_FOUND")
    
    code = generate_ninjatrader_strategy_cs(strategy_name=c.name, asset="MES", daily_loss_limit_usd=1000.0)
    return {
        "candidate_id": c.candidate_id,
        "strategy_name": c.name,
        "language": "C# NinjaScript (NinjaTrader 8)",
        "filename": f"{c.candidate_id}_ninjatrader.cs",
        "code": code
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
