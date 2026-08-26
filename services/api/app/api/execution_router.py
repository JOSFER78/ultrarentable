"""Execution-session API.

REAL-ONLY / FAIL-CLOSED:
- Creating a DB session never claims provider execution.
- Session creation requires an explicitly certified/current candidate and an enabled provider.
- Runtime state remains PENDING_PROVIDER until provider confirmation exists.
- Kill-switch/flatten actions record requests but never erase local positions before a real fill/reconciliation.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from services.api.app.db.database import (
    AuditEventModel,
    CandidateModel,
    ExecutionSessionModel,
    GatewayProviderModel,
    get_db,
)

execution_router = APIRouter(prefix="/execution", tags=["Execution Sessions & Kill-Switches"])
_HASH_RE = re.compile(r"^[0-9a-fA-F]{64}$")
_ALLOWED_ENVIRONMENTS = {"LIVE_BINGX", "PAPER_BINGX", "PAPER_PROP_FIRM", "EVAL_PROP_FIRM"}


class CreateSessionSchema(BaseModel):
    route: str = Field(..., min_length=1, description="ULTRA or FONDEO")
    environment: str = Field(..., min_length=1, description="Explicit runtime environment")
    candidate_id: str = Field(..., min_length=1)
    provider_id: str = Field(..., min_length=1)
    symbol: str = Field(..., min_length=1)
    initial_capital: float = Field(..., gt=0.0)


class KillSwitchTriggerSchema(BaseModel):
    reason: str = Field(..., min_length=1, description="Reason for triggering kill-switch")


def _hash(value: Any) -> bool:
    return isinstance(value, str) and bool(_HASH_RE.fullmatch(value))


def _candidate_has_execution_evidence(candidate: CandidateModel) -> bool:
    if candidate.status != "APPROVED_CURRENT_ENGINE":
        return False
    if not candidate.scorecard_json:
        return False
    try:
        scorecard = json.loads(candidate.scorecard_json)
    except (TypeError, ValueError):
        return False
    if not isinstance(scorecard, dict):
        return False
    hashes = (
        scorecard.get("strategy_sha256") or scorecard.get("canonical_hash"),
        scorecard.get("dataset_hash") or scorecard.get("data_sha256"),
        scorecard.get("ledger_hash"),
        scorecard.get("bundle_signature_sha256") or scorecard.get("evidence_bundle_hash"),
    )
    if not all(_hash(value) for value in hashes) or scorecard.get("ledger_verified") is not True:
        return False

    gates = scorecard.get("gates")
    state: dict[int, bool] = {}
    if isinstance(gates, list):
        for gate in gates:
            if not isinstance(gate, dict):
                continue
            try:
                gate_id = int(gate.get("gate_id", gate.get("id")))
            except (TypeError, ValueError):
                continue
            if 1 <= gate_id <= 11 and isinstance(gate.get("passed"), bool):
                state[gate_id] = gate["passed"]
    evaluation = scorecard.get("gates_evaluation")
    if isinstance(evaluation, dict):
        for gate_id in range(1, 12):
            value = evaluation.get(f"gate_{gate_id:02d}")
            if isinstance(value, bool):
                state[gate_id] = value
            elif isinstance(value, str) and value.upper() in {"PASSED", "FAILED"}:
                state[gate_id] = value.upper() == "PASSED"
    return len(state) == 11 and all(state.values())


@execution_router.post("/sessions")
def create_session(payload: CreateSessionSchema, db: Session = Depends(get_db)) -> Dict[str, Any]:
    route = payload.route.strip().upper()
    environment = payload.environment.strip().upper()
    provider_id = payload.provider_id.strip()
    symbol = payload.symbol.strip()
    candidate_id = payload.candidate_id.strip()

    if route not in {"ULTRA", "FONDEO"} or environment not in _ALLOWED_ENVIRONMENTS:
        raise HTTPException(status_code=422, detail="EXPLICIT_CANONICAL_EXECUTION_CONTEXT_REQUIRED")

    candidate = db.query(CandidateModel).filter(CandidateModel.candidate_id == candidate_id).first()
    if candidate is None:
        raise HTTPException(status_code=404, detail="CANDIDATE_NOT_FOUND")
    if candidate.route != route:
        raise HTTPException(status_code=409, detail="CANDIDATE_ROUTE_MISMATCH")
    if not _candidate_has_execution_evidence(candidate):
        raise HTTPException(status_code=409, detail="CANDIDATE_NOT_CERTIFIED_WITH_VERIFIED_EVIDENCE")
    if candidate.symbol.upper() != symbol.upper():
        raise HTTPException(status_code=409, detail="CANDIDATE_SYMBOL_MISMATCH")

    provider = db.query(GatewayProviderModel).filter(GatewayProviderModel.provider_id == provider_id).first()
    if provider is None:
        raise HTTPException(status_code=404, detail="PROVIDER_NOT_FOUND")
    if provider.is_enabled is not True:
        raise HTTPException(status_code=409, detail="PROVIDER_DISABLED")

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
        last_signal="PENDING_PROVIDER · Esperando confirmación explícita del proveedor",
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
            description=f"Session record created for {candidate_id} on {provider_id}/{symbol}. Provider execution is not claimed.",
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


def _session_payload(session: ExecutionSessionModel) -> Dict[str, Any]:
    try:
        positions = json.loads(session.open_positions_json or "[]")
    except (TypeError, ValueError):
        positions = []
    # A DB status is never sufficient evidence of external execution confirmation.
    return {
        "session_id": session.session_id,
        "route": session.route,
        "environment": session.environment,
        "candidate_id": session.candidate_id,
        "provider_id": session.provider_id,
        "symbol": session.symbol,
        "status": session.status,
        "execution_confirmed": False,
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
    }


@execution_router.get("/sessions")
def list_sessions(route: Optional[str] = Query(None), environment: Optional[str] = Query(None), db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    query = db.query(ExecutionSessionModel)
    if route:
        query = query.filter(ExecutionSessionModel.route == route.upper())
    if environment:
        query = query.filter(ExecutionSessionModel.environment == environment.upper())
    return [_session_payload(session) for session in query.order_by(ExecutionSessionModel.created_at.desc()).all()]


@execution_router.get("/sessions/{session_id}")
def get_session(session_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    session = db.query(ExecutionSessionModel).filter(ExecutionSessionModel.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="SESSION_NOT_FOUND")
    return _session_payload(session)


@execution_router.post("/sessions/{session_id}/kill-switch")
def trigger_kill_switch(session_id: str, payload: KillSwitchTriggerSchema, db: Session = Depends(get_db)) -> Dict[str, Any]:
    session = db.query(ExecutionSessionModel).filter(ExecutionSessionModel.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="SESSION_NOT_FOUND")

    now = datetime.now(timezone.utc)
    session.status = "KILL_SWITCH_TRIGGERED"
    session.kill_switch_active = True
    session.kill_switch_reason = payload.reason
    # Never claim or erase provider positions before real reconciliation/fill confirmation.
    session.last_order = f"EMERGENCY_FLATTEN_REQUESTED @ {now.isoformat()}"
    db.add(
        AuditEventModel(
            event_id=f"evt_kill_{session_id}_{int(now.timestamp() * 1000)}",
            category="KILL_SWITCH",
            route=session.route,
            title=f"KILL-SWITCH ACTIVADO: {session.session_id}",
            description=f"Emergency flatten requested for {session.session_id}. Local positions remain until provider reconciliation. Reason: {payload.reason}",
            severity="CRITICAL",
        )
    )
    db.commit()
    return {
        "status": "REQUESTED",
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
    # Flatten is a provider action request; local positions are preserved until an actual fill is reconciled.
    session.last_order = f"FLATTEN_REQUESTED @ {now.isoformat()}"
    db.add(
        AuditEventModel(
            event_id=f"evt_flat_{session_id}_{int(now.timestamp() * 1000)}",
            category="MANUAL_ACTION",
            route=session.route,
            title=f"FLATTEN REQUESTED: {session.session_id}",
            description="Flatten request recorded. Broker/provider fill must be confirmed before positions are changed locally.",
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
    return {"status": "SUCCESS", "session_id": session_id, "status_value": "PAUSED", "execution_confirmed": False}


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
    return {"status": "SUCCESS", "session_id": session_id, "status_value": "PENDING_PROVIDER", "execution_confirmed": False}
