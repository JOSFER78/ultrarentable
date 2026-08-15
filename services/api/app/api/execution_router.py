"""FastAPI Router for Paper/Live Execution Sessions and Kill-Switches."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from services.api.app.db.database import get_db, ExecutionSessionModel, AuditEventModel

execution_router = APIRouter(prefix="/execution", tags=["Execution Sessions & Kill-Switches"])


class CreateSessionSchema(BaseModel):
    route: str = Field("ULTRA", description="ULTRA or FONDEO")
    environment: str = Field("PAPER_BINGX", description="PAPER_BINGX, LIVE_BINGX, PAPER_PROP_FIRM, EVAL_PROP_FIRM")
    candidate_id: str
    provider_id: Optional[str] = None
    symbol: str = "BTC-USDT"
    initial_capital: float = 10000.0


class KillSwitchTriggerSchema(BaseModel):
    reason: str = Field(..., description="Reason for triggering kill-switch (e.g. DLL reached, 3 consecutive stops, manual emergency)")


@execution_router.get("/sessions")
def list_sessions(
    route: Optional[str] = Query(None, description="ULTRA, FONDEO"),
    environment: Optional[str] = Query(None, description="PAPER_BINGX, LIVE_BINGX, PAPER_PROP_FIRM, EVAL_PROP_FIRM"),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """List execution sessions with telemetry."""
    query = db.query(ExecutionSessionModel)
    if route:
        query = query.filter(ExecutionSessionModel.route == route.upper())
    if environment:
        query = query.filter(ExecutionSessionModel.environment == environment.upper())
        
    results = []
    for s in query.order_by(ExecutionSessionModel.created_at.desc()).all():
        positions = []
        if s.open_positions_json:
            try:
                positions = json.loads(s.open_positions_json)
            except Exception:
                positions = []
                
        results.append({
            "session_id": s.session_id,
            "route": s.route,
            "environment": s.environment,
            "candidate_id": s.candidate_id,
            "provider_id": s.provider_id,
            "symbol": s.symbol,
            "status": s.status,
            "current_pnl_usd": s.current_pnl_usd,
            "daily_pnl_usd": s.daily_pnl_usd,
            "current_drawdown_pct": s.current_drawdown_pct,
            "peak_equity_usd": s.peak_equity_usd,
            "heartbeat_last_at": s.heartbeat_last_at.isoformat() if s.heartbeat_last_at else None,
            "last_signal": s.last_signal,
            "last_order": s.last_order,
            "open_positions": positions,
            "kill_switch_active": s.kill_switch_active,
            "kill_switch_reason": s.kill_switch_reason,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        })
    return results


@execution_router.get("/sessions/{session_id}")
def get_session(session_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get single execution session telemetry."""
    s = db.query(ExecutionSessionModel).filter(ExecutionSessionModel.session_id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="SESSION_NOT_FOUND")
    positions = []
    if s.open_positions_json:
        try:
            positions = json.loads(s.open_positions_json)
        except Exception:
            positions = []
    return {
        "session_id": s.session_id,
        "route": s.route,
        "environment": s.environment,
        "candidate_id": s.candidate_id,
        "provider_id": s.provider_id,
        "symbol": s.symbol,
        "status": s.status,
        "current_pnl_usd": s.current_pnl_usd,
        "daily_pnl_usd": s.daily_pnl_usd,
        "current_drawdown_pct": s.current_drawdown_pct,
        "peak_equity_usd": s.peak_equity_usd,
        "heartbeat_last_at": s.heartbeat_last_at.isoformat() if s.heartbeat_last_at else None,
        "last_signal": s.last_signal,
        "last_order": s.last_order,
        "open_positions": positions,
        "kill_switch_active": s.kill_switch_active,
        "kill_switch_reason": s.kill_switch_reason,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


@execution_router.post("/sessions/{session_id}/kill-switch")
def trigger_kill_switch(
    session_id: str,
    payload: KillSwitchTriggerSchema,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Trigger immediate emergency kill-switch."""
    s = db.query(ExecutionSessionModel).filter(ExecutionSessionModel.session_id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="SESSION_NOT_FOUND")
    
    s.status = "KILL_SWITCH_TRIGGERED"
    s.kill_switch_active = True
    s.kill_switch_reason = payload.reason
    s.open_positions_json = "[]"  # Emergency flattened
    s.last_order = f"EMERGENCY FLATTEN @ {datetime.utcnow().isoformat()}: All open positions closed."
    
    # Audit log
    db.add(
        AuditEventModel(
            event_id=f"evt_kill_{session_id}_{int(datetime.utcnow().timestamp())}",
            category="KILL_SWITCH",
            route=s.route,
            title=f"🚨 KILL-SWITCH ACTIVADO: {s.session_id}",
            description=f"Se ha forzado el corte inmediato de la sesión {s.session_id} ({s.environment}). Motivo: {payload.reason}",
            severity="CRITICAL"
        )
    )
    db.commit()
    return {"status": "SUCCESS", "session_id": session_id, "kill_switch_active": True, "reason": s.kill_switch_reason}


@execution_router.post("/sessions/{session_id}/resume")
def resume_session(session_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Reset kill-switch and resume session."""
    s = db.query(ExecutionSessionModel).filter(ExecutionSessionModel.session_id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="SESSION_NOT_FOUND")
    
    s.status = "RUNNING"
    s.kill_switch_active = False
    s.kill_switch_reason = None
    s.heartbeat_last_at = datetime.utcnow()
    
    db.add(
        AuditEventModel(
            event_id=f"evt_resume_{session_id}_{int(datetime.utcnow().timestamp())}",
            category="KILL_SWITCH",
            route=s.route,
            title=f"🟢 SESIÓN REANUDADA: {s.session_id}",
            description=f"Se ha restablecido el Kill-Switch de la sesión {s.session_id} ({s.environment}).",
            severity="INFO"
        )
    )
    db.commit()
    return {"status": "SUCCESS", "session_id": session_id, "status": s.status}
