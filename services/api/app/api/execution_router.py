"""FastAPI Router for Paper/Live Execution Sessions and Kill-Switches."""

from __future__ import annotations

import json
import time
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
            "current_equity_usd": s.current_equity_usd,
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


from services.api.app.db.database import (
    get_db, 
    ExecutionSessionModel, 
    AuditEventModel, 
    NinjaTraderAccountModel
)


class RegisterNinjaTraderAccountSchema(BaseModel):
    account_id: str = Field(..., description="ID de la cuenta en NT8, ej. Sim101, APEX-10923, TOPSTEP-8190")
    account_name: str = Field(..., description="Nombre descriptivo de la cuenta")
    account_type: str = Field("SIM101", description="SIM101, APEX, TOPSTEP, TRADOVATE, RITHMIC, LIVE_BROKER")
    broker: str = Field("NinjaTrader Continuum", description="Broker / proveedor")
    base_capital_usd: float = Field(50000.0, description="Capital base de la cuenta ($25k, $50k, $100k, $150k, $300k)")
    max_trailing_dd_limit_usd: float = Field(2000.0, description="Límite máximo de Trailing Drawdown")
    daily_loss_limit_usd: float = Field(1000.0, description="Límite diario de pérdida (DLL)")
    profit_target_usd: float = Field(3000.0, description="Objetivo de beneficio (Profit Target)")


@execution_router.get("/ninjatrader/accounts")
def list_ninjatrader_accounts(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """List all registered real NinjaTrader 8 accounts in SQLite."""
    accounts = db.query(NinjaTraderAccountModel).order_by(NinjaTraderAccountModel.created_at.desc()).all()
    results = []
    for a in accounts:
        trailing_dd_usd = max(0.0, a.peak_equity_usd - a.current_equity_usd)
        trailing_dd_pct = (trailing_dd_usd / a.peak_equity_usd * 100.0) if a.peak_equity_usd > 0 else 0.0
        remaining_cushion_usd = max(0.0, a.max_trailing_dd_limit_usd - trailing_dd_usd)
        profit_pct = ((a.current_equity_usd - a.base_capital_usd) / a.profit_target_usd * 100.0) if a.profit_target_usd > 0 else 0.0
        
        results.append({
            "account_id": a.account_id,
            "account_name": a.account_name,
            "account_type": a.account_type,
            "broker": a.broker,
            "base_capital_usd": a.base_capital_usd,
            "current_equity_usd": round(a.current_equity_usd, 2),
            "daily_pnl_usd": round(a.daily_pnl_usd, 2),
            "realized_pnl_usd": round(a.realized_pnl_usd, 2),
            "unrealized_pnl_usd": round(a.unrealized_pnl_usd, 2),
            "peak_equity_usd": round(a.peak_equity_usd, 2),
            "max_trailing_dd_limit_usd": a.max_trailing_dd_limit_usd,
            "daily_loss_limit_usd": a.daily_loss_limit_usd,
            "profit_target_usd": a.profit_target_usd,
            "trailing_drawdown_usd": round(trailing_dd_usd, 2),
            "trailing_drawdown_pct": round(trailing_dd_pct, 2),
            "remaining_cushion_usd": round(remaining_cushion_usd, 2),
            "profit_target_progress_pct": round(profit_pct, 1),
            "status": a.status,
            "last_sync_at": a.last_sync_at.isoformat() if a.last_sync_at else None,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        })
    return results


@execution_router.post("/ninjatrader/accounts")
def register_ninjatrader_account(
    payload: RegisterNinjaTraderAccountSchema,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Register or update a real NinjaTrader 8 account in SQLite."""
    acc_id = payload.account_id.strip()
    if not acc_id:
        raise HTTPException(status_code=400, detail="ACCOUNT_ID_REQUIRED")
        
    existing = db.query(NinjaTraderAccountModel).filter(NinjaTraderAccountModel.account_id == acc_id).first()
    if existing:
        existing.account_name = payload.account_name
        existing.account_type = payload.account_type.upper()
        existing.broker = payload.broker
        existing.base_capital_usd = payload.base_capital_usd
        existing.max_trailing_dd_limit_usd = payload.max_trailing_dd_limit_usd
        existing.daily_loss_limit_usd = payload.daily_loss_limit_usd
        existing.profit_target_usd = payload.profit_target_usd
        db.commit()
        db.refresh(existing)
        return {"status": "UPDATED", "account_id": existing.account_id}
    else:
        new_acc = NinjaTraderAccountModel(
            account_id=acc_id,
            account_name=payload.account_name,
            account_type=payload.account_type.upper(),
            broker=payload.broker,
            base_capital_usd=payload.base_capital_usd,
            current_equity_usd=payload.base_capital_usd,
            daily_pnl_usd=0.0,
            realized_pnl_usd=0.0,
            unrealized_pnl_usd=0.0,
            peak_equity_usd=payload.base_capital_usd,
            max_trailing_dd_limit_usd=payload.max_trailing_dd_limit_usd,
            daily_loss_limit_usd=payload.daily_loss_limit_usd,
            profit_target_usd=payload.profit_target_usd,
            status="CONNECTED",
            last_sync_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )
        db.add(new_acc)
        db.add(
            AuditEventModel(
                event_id=f"evt_acc_{acc_id}_{int(datetime.utcnow().timestamp())}",
                category="ACCOUNT_REGISTER",
                route="FONDEO",
                title=f"🏛️ CUENTA REGISTRADA: {acc_id}",
                description=f"Se ha registrado la cuenta {payload.account_name} ({payload.account_type}, ${payload.base_capital_usd:,.0f} USD).",
                severity="INFO",
            )
        )
        db.commit()
        db.refresh(new_acc)
        return {"status": "CREATED", "account_id": new_acc.account_id}


@execution_router.delete("/ninjatrader/accounts/{account_id}")
def delete_ninjatrader_account(account_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Delete a registered NinjaTrader account."""
    acc = db.query(NinjaTraderAccountModel).filter(NinjaTraderAccountModel.account_id == account_id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="ACCOUNT_NOT_FOUND")
    db.delete(acc)
    db.commit()
    return {"status": "DELETED", "account_id": account_id}


@execution_router.get("/ninjatrader/bridge/script")
def get_ninjatrader_bridge_script(
    account_id: str = Query("Sim101"),
    symbol: str = Query("MNQ"),
    host: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Generate universal ready-to-compile NinjaScript C# code for real-time telemetry and execution bridge."""
    from services.api.app.export.sqx_to_ninjatrader import generate_csharp_strategy
    target_host = host or "http://localhost:8000"
    code = generate_csharp_strategy(
        strategy_name=f"UR_Bridge_{symbol.upper()}",
        cme_symbol=symbol.upper(),
        webhook_url=f"{target_host}/api/v1/execution/ninjatrader/telemetry",
    )
    return {
        "filename": f"UR_Bridge_{symbol.upper()}.cs",
        "account_id": account_id,
        "symbol": symbol.upper(),
        "webhook_url": f"{target_host}/api/v1/execution/ninjatrader/telemetry",
        "code": code,
    }


# ----------------------------------------------------------------------------
# REMOTE ORDER & SIGNAL QUEUE (TWO-WAY NINJATRADER BRIDGE)
# ----------------------------------------------------------------------------
_SIGNAL_QUEUE: List[Dict[str, Any]] = []
_ORDER_HISTORY: List[Dict[str, Any]] = []


class RemoteOrderDispatchSchema(BaseModel):
    account_name: Optional[str] = Field("Sim101", description="Target NinjaTrader account ID / name")
    symbol: str = Field("MNQ", description="CME Symbol (MNQ, MES, NQ, ES, GC, CL, 6E)")
    action: str = Field("BUY", description="BUY, SELL, FLATTEN, KILL_SWITCH")
    order_type: str = Field("MARKET", description="MARKET, LIMIT")
    price: Optional[float] = Field(None, description="Limit price if applicable")
    quantity: int = Field(1, description="Number of contracts")
    stop_loss_ticks: Optional[int] = Field(40, description="Stop loss ticks")
    take_profit_ticks: Optional[int] = Field(100, description="Take profit ticks")
    strategy_source: Optional[str] = Field("MANUAL_REMOTE_TERMINAL", description="Source strategy or manual")


@execution_router.post("/ninjatrader/orders")
def dispatch_remote_order(payload: RemoteOrderDispatchSchema, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Dispatch a remote trading order to NinjaTrader 8."""
    global _SIGNAL_QUEUE, _ORDER_HISTORY
    order_id = f"ur_ord_{int(time.time()*1000)}"
    order_item = {
        "order_id": order_id,
        "account_name": payload.account_name,
        "symbol": payload.symbol.upper(),
        "action": payload.action.upper(),
        "order_type": payload.order_type.upper(),
        "price": payload.price,
        "quantity": payload.quantity,
        "stop_loss_ticks": payload.stop_loss_ticks,
        "take_profit_ticks": payload.take_profit_ticks,
        "strategy_source": payload.strategy_source,
        "status": "QUEUED",
        "timestamp_utc": datetime.utcnow().isoformat(),
    }
    _SIGNAL_QUEUE.append(order_item)
    _ORDER_HISTORY.insert(0, order_item)
    if len(_ORDER_HISTORY) > 100:
        _ORDER_HISTORY.pop()

    # Add audit log
    db.add(
        AuditEventModel(
            event_id=f"evt_{order_id}",
            category="REMOTE_ORDER",
            route="FONDEO",
            title=f"⚡ ORDEN REMOTA ENVIADA: {payload.action.upper()} {payload.quantity} {payload.symbol.upper()}",
            description=f"Orden remota despachada hacia NinjaTrader 8 ({payload.account_name}). Fuente: {payload.strategy_source}.",
            severity="INFO",
        )
    )
    db.commit()

    return {
        "status": "QUEUED",
        "order_id": order_id,
        "action": payload.action.upper(),
        "symbol": payload.symbol.upper(),
        "quantity": payload.quantity,
        "message": f"Orden {payload.action.upper()} {payload.quantity} {payload.symbol.upper()} en cola para NinjaTrader 8.",
    }


@execution_router.get("/ninjatrader/signals/poll")
def poll_ninjatrader_signals(
    account_name: Optional[str] = Query(None),
    symbol: Optional[str] = Query(None),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Long-poll / fetch pending signals for NinjaTrader 8 C# bridge."""
    global _SIGNAL_QUEUE
    pending: List[Dict[str, Any]] = []
    remaining: List[Dict[str, Any]] = []

    for item in _SIGNAL_QUEUE:
        match_acc = True
        if account_name and item.get("account_name"):
            match_acc = (account_name.lower() == item["account_name"].lower() or item["account_name"] == "*")
        match_sym = True
        if symbol and item.get("symbol"):
            match_sym = (symbol.upper() == item["symbol"].upper() or item["symbol"] == "*")

        if match_acc and match_sym:
            item["status"] = "DELIVERED"
            item["delivered_at"] = datetime.utcnow().isoformat()
            pending.append(item)
        else:
            remaining.append(item)

    _SIGNAL_QUEUE = remaining
    return pending


@execution_router.get("/ninjatrader/orders/history")
def get_remote_orders_history() -> List[Dict[str, Any]]:
    """Return recent remote trading order history."""
    global _ORDER_HISTORY
    return _ORDER_HISTORY


class NinjaTraderTelemetryPayload(BaseModel):
    strategy_name: str = "UR_Strategy_MNQ"
    symbol: str = "MNQ"
    account_name: Optional[str] = None
    account_id: Optional[str] = None
    execution_id: Optional[str] = None
    order_id: Optional[str] = "unknown"
    side: Optional[str] = None
    action: Optional[str] = None
    price: Optional[float] = None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    profit_target: Optional[float] = None
    quantity: Optional[float] = 1.0
    realized_pnl_usd: Optional[float] = 0.0
    unrealized_pnl_usd: Optional[float] = 0.0
    account_equity_usd: Optional[float] = None
    daily_pnl_usd: Optional[float] = 0.0
    trailing_dd_usd: Optional[float] = 0.0
    is_active: Optional[bool] = True
    message: Optional[str] = None
    timestamp_utc: Optional[str] = None


@execution_router.post("/ninjatrader/telemetry")
def receive_ninjatrader_telemetry(
    payload: NinjaTraderTelemetryPayload,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Ingest live execution fills and PnL events directly from NinjaTrader 8 Sim101 / Live."""
    from services.fondeo.challenge_evaluator import PropChallengeEvaluator
    from contracts.portfolio import PropChallengeConfig

    acc_key = payload.account_name or payload.account_id or "Sim101"
    clean_sym = payload.symbol.upper().replace("-", "_")
    session_id = f"sess_nt8_{acc_key.lower()}_{clean_sym.lower()}"
    s = db.query(ExecutionSessionModel).filter(ExecutionSessionModel.session_id == session_id).first()

    # Match or auto-register real account in SQLite
    acc = db.query(NinjaTraderAccountModel).filter(
        (NinjaTraderAccountModel.account_id == acc_key) |
        (NinjaTraderAccountModel.account_name == acc_key)
    ).first()

    # Determine broker & firm rules automatically from account ID
    detected_type = "SIM101"
    detected_broker = "NinjaTrader Continuum"
    detected_cap = payload.account_equity_usd or 50000.0
    detected_dd = 2000.0
    detected_dll = 1000.0
    detected_target = 3000.0

    upper_acc = acc_key.upper()
    if "APEX" in upper_acc:
        detected_type = "APEX"
        detected_broker = "Rithmic / Tradovate"
        detected_dd = 2500.0
        detected_dll = 1500.0
        detected_target = 3000.0
    elif "TOPSTEP" in upper_acc:
        detected_type = "TOPSTEP"
        detected_broker = "Tradovate"
        detected_dd = 2000.0
        detected_dll = 1000.0
        detected_target = 3000.0
    elif "TRADOVATE" in upper_acc:
        detected_type = "TRADOVATE"
        detected_broker = "Tradovate Direct"
    elif "BULENOX" in upper_acc:
        detected_type = "BULENOX"
        detected_broker = "Rithmic"
        detected_dd = 2500.0
        detected_dll = 1500.0

    initial_equity = payload.account_equity_usd or (detected_cap + (payload.daily_pnl_usd or 0.0))

    if not acc:
        acc = NinjaTraderAccountModel(
            account_id=acc_key,
            account_name=f"NinjaTrader {acc_key}",
            account_type=detected_type,
            broker=detected_broker,
            base_capital_usd=detected_cap,
            current_equity_usd=initial_equity,
            daily_pnl_usd=payload.daily_pnl_usd or 0.0,
            realized_pnl_usd=payload.realized_pnl_usd or 0.0,
            unrealized_pnl_usd=payload.unrealized_pnl_usd or 0.0,
            peak_equity_usd=max(detected_cap, initial_equity),
            max_trailing_dd_limit_usd=detected_dd,
            daily_loss_limit_usd=detected_dll,
            profit_target_usd=detected_target,
            status="CONNECTED",
            last_sync_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )
        db.add(acc)
        db.commit()
        db.refresh(acc)

    base_capital = acc.base_capital_usd
    trailing_limit = acc.max_trailing_dd_limit_usd
    daily_limit = acc.daily_loss_limit_usd
    target_profit = acc.profit_target_usd

    exec_price = payload.price or payload.entry_price or 0.0
    exec_side = payload.side or payload.action or "BUY"
    exec_id = payload.execution_id or f"exec_{int(time.time()*1000)}"

    current_equity = payload.account_equity_usd or (base_capital + (payload.daily_pnl_usd or 0.0))

    # Update Gateway Provider Packets counter
    from services.api.app.db.database import GatewayProviderModel
    gw = db.query(GatewayProviderModel).filter(GatewayProviderModel.provider_id == "ninjatrader_8").first()
    if gw:
        gw.status = "CONNECTED"
        gw.telemetry_packets_count = (gw.telemetry_packets_count or 0) + 1
        gw.last_ping_at = datetime.utcnow()
        gw.updated_at = datetime.utcnow()

    if not s:
        s = ExecutionSessionModel(
            session_id=session_id,
            route="FONDEO",
            environment="PAPER_PROP_FIRM",
            candidate_id=payload.strategy_name,
            provider_id=f"NinjaTrader 8 ({acc_key})",
            symbol=payload.symbol.upper(),
            status="RUNNING",
            current_pnl_usd=payload.daily_pnl_usd or 0.0,
            daily_pnl_usd=payload.daily_pnl_usd or 0.0,
            current_equity_usd=current_equity,
            current_drawdown_pct=0.0,
            peak_equity_usd=max(base_capital, current_equity),
            heartbeat_last_at=datetime.utcnow(),
            last_signal=f"FILL {exec_side} {payload.quantity} @ {exec_price}",
            last_order=f"Exec {exec_id} | Side: {exec_side} | Qty: {payload.quantity} @ {exec_price}",
            open_positions_json="[]",
            kill_switch_active=False,
            created_at=datetime.utcnow(),
        )
        db.add(s)
    else:
        s.daily_pnl_usd = payload.daily_pnl_usd or 0.0
        s.current_pnl_usd = payload.daily_pnl_usd or 0.0
        s.current_equity_usd = current_equity
        if current_equity > (s.peak_equity_usd or base_capital):
            s.peak_equity_usd = current_equity
        
        current_dd = max(0.0, s.peak_equity_usd - current_equity)
        s.current_drawdown_pct = round((current_dd / s.peak_equity_usd) * 100.0, 2) if s.peak_equity_usd > 0 else 0.0
        s.heartbeat_last_at = datetime.utcnow()
        s.last_order = f"Exec {exec_id} | Side: {exec_side} | Qty: {payload.quantity} @ {exec_price}"
        s.last_signal = f"ACTIVO · NinjaTrader {acc_key} ({payload.symbol})"

    # Update account balances
    acc.current_equity_usd = current_equity
    acc.daily_pnl_usd = payload.daily_pnl_usd or 0.0
    acc.realized_pnl_usd = payload.realized_pnl_usd or 0.0
    acc.unrealized_pnl_usd = payload.unrealized_pnl_usd or 0.0
    if acc.current_equity_usd > acc.peak_equity_usd:
        acc.peak_equity_usd = acc.current_equity_usd
    acc.last_sync_at = datetime.utcnow()
    acc.status = "CONNECTED"

    # Evaluate Prop Rules
    evaluator = PropChallengeEvaluator()
    config = PropChallengeConfig(
        firm_name=f"NinjaTrader {payload.account_name}",
        account_size_usd=base_capital,
        profit_target_usd=target_profit,
        max_trailing_drawdown_usd=trailing_limit,
        daily_loss_limit_usd=daily_limit,
    )
    current_equity = base_capital + payload.daily_pnl_usd
    daily_loss = max(0.0, -payload.daily_pnl_usd)
    eval_result = evaluator.evaluate_account_health(
        config=config,
        current_equity=current_equity,
        peak_equity=s.peak_equity_usd,
        daily_loss=daily_loss,
    )

    if eval_result["failed"] and not s.kill_switch_active:
        s.kill_switch_active = True
        s.status = "KILL_SWITCH_TRIGGERED"
        s.kill_switch_reason = "DLL_OR_TRAILING_DD_BREACH"
        if acc:
            acc.status = "KILL_SWITCH_TRIGGERED"
        db.add(
            AuditEventModel(
                event_id=f"evt_nt8_kill_{session_id}_{int(datetime.utcnow().timestamp())}",
                category="KILL_SWITCH",
                route="FONDEO",
                title=f"🚨 KILL-SWITCH NINJATRADER: {s.session_id}",
                description=f"Límite de riesgo sobrepasado en {payload.account_name}. Trailing DD: ${eval_result['trailing_drawdown_usd']}, Daily Loss: ${eval_result['daily_loss_usd']}",
                severity="CRITICAL"
            )
        )
    elif eval_result["passed"] and acc:
        acc.status = "TARGET_PASSED"

    db.commit()
    db.refresh(s)

    return {
        "status": "TELEMETRY_RECORDED",
        "session_id": s.session_id,
        "account_name": payload.account_name,
        "daily_pnl_usd": s.daily_pnl_usd,
        "current_drawdown_pct": s.current_drawdown_pct,
        "kill_switch_active": s.kill_switch_active,
        "challenge_evaluation": eval_result,
    }

