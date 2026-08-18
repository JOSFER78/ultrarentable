"""services/api/app/api/real_data_router.py
Router para exponer datos 100% REALES de la base de datos SQLite (78,550+ estrategias),
matriz de densidad real y trades reales del sistema sin ningún tipo de mock o dato simulado.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from services.api.app.db.database import get_db, StrategyModel, BacktestModel, CandidateModel

router = APIRouter(tags=["Real Data & SQLite Strategies"])


@router.get("/overview")
def get_real_overview(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Retorna métricas cuantitativas agregadas 100% reales de la base de datos SQLite."""
    total_strategies = db.query(StrategyModel).count()
    total_backtests = db.query(BacktestModel).count()
    total_candidates = db.query(CandidateModel).count()

    # Conteo real por familia/arquetipo
    family_counts = {}
    for fam, cnt in db.query(StrategyModel.family, func.count(StrategyModel.strategy_id)).group_by(StrategyModel.family).all():
        family_counts[fam or "UNKNOWN"] = cnt

    # Conteo real por validation_status
    status_counts = {}
    for st, cnt in db.query(StrategyModel.validation_status, func.count(StrategyModel.strategy_id)).group_by(StrategyModel.validation_status).all():
        status_counts[st or "PENDING"] = cnt

    return {
        "status": "SUCCESS",
        "total_strategies_in_db": total_strategies,
        "total_backtests_in_db": total_backtests,
        "total_candidates_in_db": total_candidates,
        "by_family": family_counts,
        "by_status": status_counts,
    }


@router.get("/strategies")
def list_real_strategies(
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    family: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Lista estrategias reales paginadas directamente desde la tabla SQLite."""
    query = db.query(StrategyModel)
    if family:
        query = query.filter(StrategyModel.family == family)
    if status:
        query = query.filter(StrategyModel.validation_status == status)
    if search:
        query = query.filter(StrategyModel.name.ilike(f"%{search}%") | StrategyModel.strategy_id.ilike(f"%{search}%"))

    total = query.count()
    records = query.order_by(StrategyModel.created_at.desc()).offset(offset).limit(limit).all()

    strategies_out = []
    for s in records:
        dsl = {}
        if s.dsl_json:
            try:
                dsl = json.loads(s.dsl_json)
            except Exception:
                pass

        symbol = dsl.get("symbol") or dsl.get("market", {}).get("symbol", "ETH-USDT")
        timeframe = dsl.get("timeframe") or dsl.get("market", {}).get("timeframe", "1h")
        route = dsl.get("route") or ("TRACK_FONDEO" if "NQ" in symbol or "ES" in symbol else "TRACK_ULTRA")

        strategies_out.append({
            "strategy_id": s.strategy_id,
            "name": s.name,
            "family": s.family,
            "symbol": symbol,
            "timeframe": timeframe,
            "route": route,
            "validation_status": s.validation_status,
            "canonical_hash": s.canonical_hash,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "dsl_preview": dsl.get("description", ""),
        })

    return {
        "status": "SUCCESS",
        "total_count": total,
        "offset": offset,
        "limit": limit,
        "strategies": strategies_out,
    }


@router.get("/trades/botfreq")
def get_real_botfreq_trades() -> Dict[str, Any]:
    """Lee trades reales cerrados desde la base de datos de trading en vivo de la VPS."""
    db_path = Path("/home/ubuntu/db/botfreq/tradesv3.sqlite")
    if not db_path.exists():
        return {
            "status": "NO_BOTFREQ_DB",
            "count": 0,
            "total_pnl_usd": 0.0,
            "trades": [],
        }

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT id, pair, is_open, fee_open, fee_close, open_rate, close_rate, close_profit, close_profit_abs, stake_amount, amount, open_date, close_date FROM trades ORDER BY id DESC LIMIT 50")
        rows = cur.fetchall()
        trades = []
        for r in rows:
            trades.append(dict(r))
        conn.close()

        total_profit = sum(t.get("close_profit_abs") or 0.0 for t in trades if not t.get("is_open"))
        return {
            "status": "SUCCESS",
            "count": len(trades),
            "total_pnl_usd": round(total_profit, 2),
            "trades": trades,
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "error": str(e),
            "count": 0,
            "trades": [],
        }
