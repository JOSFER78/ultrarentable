"""Execution-session API.

REAL-ONLY / FAIL-CLOSED:
- Creating a DB session is not the same as starting a real execution.
- No route/environment/symbol/capital defaults are invented.
- A session stays PENDING_PROVIDER until an actual provider adapter confirms startup.
- Kill-switch/flatten actions operate only on existing sessions.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from services.api.app.db.database import AuditEventModel, ExecutionSessionModel, get_db

execution_router = APIRouter(prefix="/execution", tags=["Execution Sessions & Kill-Switches"])


class CreateSessionSchema(BaseModel):
    route: str = Field(..., min_length=1, description="ULTRA or FONDEO")
    environment: str = Field(..., min_length=1, description="Explicit runtime environment")
    candidate_id: str = Field(..., min_length=1)
    provider_id: str = Field(..., min_length=1)
    symbol: str = Field(..., min_length=1)
    initial_capital: float = Field(..., gt=0.0)


class KillSwitchTriggerSchema(BaseModel):
    reason: str = Field(..., min_length=1, description="Reason for triggering kill-switch")


@execution_router.post("/sessions")
def create_session(payload: CreateSessionSchema, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Create an execution-session record without falsely claiming provider execution."""
    route = payload.route.strip().upper()
    environment = payload.environment.strip().upper()
    provider_id = payload.provider_id.strip()
    symbol = payload.symbol.strip()
    candidate_id = payload.candidate_id.strip()

    if not all([route, environment, provider_id, symbol, candidate_id]):
        raise HTTPException(status_code=422, detail="EXPLICIT_EXECUTION_CONTEXT_REQUIRED")

    now = datetime.now(timezone.utc)
    session_id = f"sess_{route.lower()}_{symbol.lower().replace('-', '_')}_{int(now.timestamp() * 1000)}"
    new_sess = ExecutionSessionModel(
        session_id=session_id,
        route=route,
        environment=environment,
        candidate_id=candidate_id,
        provider_id=provider_id,
        symbol=symbol,
        status="PENDING_PROVIDER",
        current_pnl_usd=0.0,
        daily_pnl_usd=0.0,
        current_drawdown_pct=0.0,
        peak_equity_usd=payload.initial_capital,
        heartbeat_last_at=None,
        last_signal="PENDING_PROVIDER · Sin confirmación de ejecución real",
        last_order="NO_ORDER_SENT",
        open_positions_json="[]",
        kill_switch_active=False,
        created_at=now,
    )
    db.add(new_sess)
    db.add(
        AuditEventModel(
            event_id=f"evt_create_{session_id}",
            category="PAPER" if "PAPER" in environment else "LIVE",
            route=route,
            title=f"SESIÓN CREADA (PENDING_PROVIDER): {session_id}",
            description=(
                f"Session record created for {candidate_id} on {provider_id}/{symbol}. "
                "No provider execution has been claimed."
            ),
            severity="INFO",
        )
    )
    db.commit()
    db.refresh(new_sess)

    return {
        "status": "PENDING_PROVIDER",
        "session_id": session_id,
        "environment": environment,
        "provider_id": provider_id,
        "candidate_id": candidate_id,
        "symbol": symbol,
        "execution_confirmed": False,
    }


@execution_router.get("/sessions")
def list_sessions(
    route: Optional[str] = Query(None),
    environment: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    query = db.query(ExecutionSessionModel)
    if route:
        query = query.filter(ExecutionSessionModel.route == route.upper())
    if environment:
        query = query.filter(ExecutionSessionModel.environment == environment.upper())

    results: List[Dict[str, Any]] = []
    for session in query.order_by(ExecutionSessionModel.created_at.desc()).all():
        try:
            positions = json.loads(session.open_positions_json or "[]")
        except (TypeError, ValueError):
            positions = []
        results.append({
            "session_id": session.session_id,
            "route": session.route,
            "environment": session.environment,
            "candidate_id": session.candidate_id,
            "provider_id": session.provider_id,
            "symbol": session.symbol,
            "status": session.status,
            "execution_confirmed": session.status in {"RUNNING", "PAUSED", "KILL_SWITCH_TRIGGERED"},
            "current_equity_usd": session.current_equity_usd,
            "current_pnl_usd": session.current_pnl_usd,
            "daily_pnl_usd": session.daily_pnl_usd,
            "current_drawdown_pct": session.current_drawdown_pct,
            "peak_equity_usd": session.peak_equity_usd,
            "heartbeat_last_at": session.heartbeat_last_at.isoformat() if session.heartbeat_last_at else None,
            "last_signal": session.last_signal,
            "last_order": session.last_order,
            "open_positions": positions,
            "kill_switch_active": session.kill_switch_active,
            "kill_switch_reason": session.kill_switch_reason,
            "created_at": session.created_at.isoformat() if session.created_at else None,
        })
    return results


@execution_router.get("/sessions/{session_id}")
def get_session(session_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    session = db.query(ExecutionSessionModel).filter(ExecutionSessionModel.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="SESSION_NOT_FOUND")
    try:
        positions = json.loads(session.open_positions_json or "[]")
    except (TypeError, ValueError):
        positions = []
    return {
        "session_id": session.session_id,
        "route": session.route,
        "environment": session.environment,
        "candidate_id": session.candidate_id,
        "provider_id": session.provider_id,
        "symbol": session.symbol,
        "status": session.status,
        "execution_confirmed": session.status in {"RUNNING", "PAUSED", "KILL_SWITCH_TRIGGERED"},
        "current_pnl_usd": session.current_pnl_usd,
        "daily_pnl_usd": session.daily_pnl_usd,
        "current_drawdown_pct": session.current_drawdown_pct,
        "peak_equity_usd": session.peak_equity_usd,
        "heartbeat_last_at": session.heartbeat_last_at.isoformat() if session.heartbeat_last_at else None,
        "last_signal": session.last_signal,
        "last_order": session.last_order,
        "open_positions": positions,
        "kill_switch_active": session.kill_switch_active,
        "kill_switch_reason": session.kill_switch_reason,
        "created_at": session.created_at.isoformat() if session.created_at else None,
    }


@execution_router.post("/sessions/{session_id}/kill-switch")
def trigger_kill_switch(session_id: str, payload: KillSwitchTriggerSchema, db: Session = Depends(get_db)) -> Dict[str, Any]:
    session = db.query(ExecutionSessionModel).filter(ExecutionSessionModel.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="SESSION_NOT_FOUND")

    now = datetime.now(timezone.utc)
    session.status = "KILL_SWITCH_TRIGGERED"
    session.kill_switch_active = True
    session.kill_switch_reason = payload.reason
    session.open_positions_json = "[]"
    session.last_order = f"EMERGENCY_FLATTEN_REQUESTED @ {now.isoformat()}"
    db.add(
        AuditEventModel(
            event_id=f"evt_kill_{session_id}_{int(now.timestamp() * 1000)}",
            category="KILL_SWITCH",
            route=session.route,
            title=f"KILL-SWITCH ACTIVADO: {session.session_id}",
            description=f"Emergency action requested for {session.session_id}. Reason: {payload.reason}",
            severity="CRITICAL",
        )
    )
    db.commit()
    return {
        "status": "SUCCESS",
        "session_id": session_id,
        "kill_switch_active": True,
        "reason": session.kill_switch_reason,
        "provider_execution_confirmed": False,
    }


@execution_router.post("/sessions/{session_id}/flatten")
def flatten_session_positions(session_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    session = db.query(ExecutionSessionModel).filter(ExecutionSessionModel.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="SESSION_NOT_FOUND")

    now = datetime.now(timezone.utc)
    session.open_positions_json = "[]"
    session.last_order = f"FLATTEN_REQUESTED @ {now.isoformat()}"
    db.add(
        AuditEventModel(
            event_id=f"evt_flat_{session_id}_{int(now.timestamp() * 1000)}",
            category="MANUAL_ACTION",
            route=session.route,
            title=f"FLATTEN REQUESTED: {session.session_id}",
            description="A flatten request was recorded; broker/provider fill must be confirmed separately.",
            severity="WARNING",
        )
    )
    db.commit()
    return {"status": "REQUESTED", "session_id": session_id, "provider_execution_confirmed": False}


@execution_router.post("/sessions/{session_id}/pause")
def pause_session(session_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    session = db.query(ExecutionSessionModel).filter(ExecutionSessionModel.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="SESSION_NOT_FOUND")
    session.status = "PAUSED"
    session.last_signal = "PAUSED · No se abrirán nuevas posiciones"
    db.commit()
    return {"status": "SUCCESS", "session_id": session_id, "status_value": "PAUSED"}


@execution_router.post("/sessions/{session_id}/resume")
def resume_session(session_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    session = db.query(ExecutionSessionModel).filter(ExecutionSessionModel.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="SESSION_NOT_FOUND")
    if session.kill_switch_active:
        raise HTTPException(status_code=409, detail="KILL_SWITCH_ACTIVE_REQUIRES_PROVIDER_RECONCILIATION")
    session.status = "PENDING_PROVIDER"
    session.last_signal = "PENDING_PROVIDER · Awaiting provider confirmation"
    db.commit()
    return {"status": "SUCCESS", "session_id": session_id, "status_value": "PENDING_PROVIDER"}
