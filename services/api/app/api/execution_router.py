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


@execution_router.post("/sessions")
def create_session(payload: CreateSessionSchema, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Deploy and create a new execution session for a strategy candidate."""
    import time
    session_id = f"sess_{payload.route.lower()}_{payload.symbol.lower().replace('-', '_')}_{int(time.time() * 1000) % 100000}"
    new_sess = ExecutionSessionModel(
        session_id=session_id,
        route=payload.route.upper(),
        environment=payload.environment.upper(),
        candidate_id=payload.candidate_id,
        provider_id=payload.provider_id,
        symbol=payload.symbol,
        status="RUNNING",
        current_pnl_usd=0.0,
        daily_pnl_usd=0.0,
        current_drawdown_pct=0.0,
        peak_equity_usd=payload.initial_capital,
        heartbeat_last_at=datetime.utcnow(),
        last_signal="CONECTADO · Esperando primera condición de entrada",
        last_order="LISTO · Telemetría activa",
        open_positions_json="[]",
        kill_switch_active=False,
        created_at=datetime.utcnow(),
    )
    db.add(new_sess)
    
    # Audit log
    db.add(
        AuditEventModel(
            event_id=f"evt_deploy_{session_id}",
            category="LIVE" if "LIVE" in payload.environment else "PAPER",
            route=payload.route.upper(),
            title=f"🚀 SESIÓN DESPLEGADA: {session_id}",
            description=f"Se ha iniciado la ejecución de la estrategia {payload.candidate_id} en {payload.environment} ({payload.symbol}).",
            severity="INFO",
        )
    )
    db.commit()
    db.refresh(new_sess)
    
    return {
        "status": "CREATED",
        "session_id": new_sess.session_id,
        "environment": new_sess.environment,
        "candidate_id": new_sess.candidate_id,
        "symbol": new_sess.symbol,
    }


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


@execution_router.post("/sessions/{session_id}/flatten")
def flatten_session_positions(session_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Force flatten all open positions for this session without killing the process."""
    s = db.query(ExecutionSessionModel).filter(ExecutionSessionModel.session_id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="SESSION_NOT_FOUND")
    
    s.open_positions_json = "[]"
    s.last_order = f"MANUAL FLATTEN @ {datetime.utcnow().strftime('%H:%M:%S')}: Posiciones cerradas a mercado."
    db.add(
        AuditEventModel(
            event_id=f"evt_flat_{session_id}_{int(datetime.utcnow().timestamp())}",
            category="MANUAL_ACTION",
            route=s.route,
            title=f"🛑 POSICIONES APLANADAS: {s.session_id}",
            description=f"Se han cerrado a mercado todas las posiciones de la sesión {s.session_id}.",
            severity="WARNING"
        )
    )
    db.commit()
    return {"status": "SUCCESS", "session_id": session_id, "message": "Todas las posiciones cerradas a mercado."}


@execution_router.post("/sessions/{session_id}/pause")
def pause_session(session_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Pause bot from placing new entries while managing existing positions."""
    s = db.query(ExecutionSessionModel).filter(ExecutionSessionModel.session_id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="SESSION_NOT_FOUND")
    
    s.status = "PAUSED"
    s.last_signal = "BOT PAUSADO · No se abrirán nuevas posiciones"
    db.commit()
    return {"status": "SUCCESS", "session_id": session_id, "status": "PAUSED"}


@execution_router.post("/sessions/{session_id}/resume")
def resume_session(session_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Reset kill-switch or unpause session."""
    s = db.query(ExecutionSessionModel).filter(ExecutionSessionModel.session_id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="SESSION_NOT_FOUND")
    
    s.status = "RUNNING"
    s.kill_switch_active = False
    s.kill_switch_reason = None
    s.heartbeat_last_at = datetime.utcnow()
    s.last_signal = "ACTIVO · Analizando mercado en tiempo real"
    
    db.add(
        AuditEventModel(
            event_id=f"evt_resume_{session_id}_{int(datetime.utcnow().timestamp())}",
            category="KILL_SWITCH",
            route=s.route,
            title=f"🟢 SESIÓN REANUDADA: {s.session_id}",
            description=f"Se ha restablecido la sesión {s.session_id} ({s.environment}).",
            severity="INFO"
        )
    )
    db.commit()
    return {"status": "SUCCESS", "session_id": session_id, "status": s.status}
