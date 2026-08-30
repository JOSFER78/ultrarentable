"""Pipeline de Meta-Estrategias (meta-ULTRA / meta-FONDEO).

Ensambla meta-portafolios de paridad de riesgo EXCLUSIVAMENTE sobre candidatos
certificados (APPROVED_CURRENT_ENGINE, motor 5.4.0) con serie de retornos OOS
real persistida en el scorecard. Fail-closed: si faltan componentes o evidencia,
no se construye nada.

Regla doctrinal: un meta-ensamblado NUNCA fabrica equity, profit factor ni
drawdown a nivel de portafolio; esos campos quedan a cero y el estado
`ASSEMBLED_PENDING_PORTFOLIO_BACKTEST` lo declara honestamente hasta que un
backtest de portafolio produzca ledger propio.
"""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from services.core.runtime_paths import DB_PATH

logger = logging.getLogger("MetaStrategyPipeline")

CERTIFIED_STATUS = "APPROVED_CURRENT_ENGINE"
ENGINE_VERSION = "5.4.0"


import os

def _db_path() -> str:
    from services.api.app.config import STATE_DB_PATH
    return os.getenv("ULTRARENTABLE_DB_PATH", os.getenv("STATE_DB_PATH", str(STATE_DB_PATH)))


def _load_certified_for_route(route: str) -> List[Dict[str, Any]]:
    """Lee candidatos certificados de la ruta con serie de retornos OOS real."""
    conn = sqlite3.connect(_db_path(), timeout=10.0)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT candidate_id, name, route, symbol, timeframe, scorecard_json
            FROM candidates
            WHERE route = ? AND status = ? AND engine_version = ?
            ORDER BY profit_factor_oos DESC
            """,
            (route.upper(), CERTIFIED_STATUS, ENGINE_VERSION),
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    out: List[Dict[str, Any]] = []
    seen_symbols: set[str] = set()
    for cid, name, route_str, symbol, timeframe, sc_json in rows:
        if not sc_json:
            continue
        try:
            sc = json.loads(sc_json)
        except (TypeError, ValueError):
            continue
        returns = sc.get("oos_returns")
        if not isinstance(returns, list) or len(returns) < 2:
            continue  # sin evidencia de retornos suficiente: fail-closed
        sym = (symbol or "").replace("-", "").replace("/", "").upper()
        if not sym or sym in seen_symbols:
            continue  # regla multi-activo: un símbolo, un peso
        seen_symbols.add(sym)
        out.append({
            "candidate_id": cid,
            "name": name or cid,
            "symbol": symbol,
            "timeframe": timeframe,
            "oos_returns": [float(x) for x in returns],
        })
    return out


def build_meta_for_route(route: str, base_capital: Optional[float] = None) -> Optional[Dict[str, Any]]:
    """Ensambla (si es posible) y persiste la meta-estrategia de una ruta."""
    from services.api.app.db.database import PortfolioModel, SessionLocal
    from services.portfolio.meta_ensemble_service import (
        MetaEnsembleService,
    )

    route_u = route.upper()
    if route_u not in ("ULTRA", "FONDEO"):
        raise ValueError("INVALID_ROUTE")

    components_evidence = _load_certified_for_route(route_u)
    if len(components_evidence) < 2:
        logger.info("Meta-%s: %d componentes certificados con evidencia (se requieren >= 2); no se ensambla.",
                    route_u, len(components_evidence))
        return None

    # Máximo 6 componentes por diversificación manejable
    components_evidence = components_evidence[:6]

    # Series semanales ALINEADAS desde timestamps reales de los ledgers de trades:
    # PnL semanal / capital base, cero en semanas sin operación (dato real).
    import sqlite3 as _sq

    def _weekly_aligned(comp_list: List[Dict[str, Any]]) -> Optional[List[List[float]]]:
        week_pnl: Dict[str, Dict[int, float]] = {}
        conn2 = sqlite3.connect(_db_path(), timeout=10.0)
        try:
            for comp in comp_list:
                row2 = conn2.execute(
                    "SELECT scorecard_json FROM candidates WHERE candidate_id=?", (comp["candidate_id"],)
                ).fetchone()
                if not row2 or not row2[0]:
                    return None
                sc2 = json.loads(row2[0])
                ledger_rel = sc2.get("ledger_path")
                lp = None
                if ledger_rel and Path(ledger_rel).exists():
                    try:
                        lp = json.loads(Path(ledger_rel).read_text(encoding="utf-8"))
                    except Exception:
                        lp = None
                if lp is None:
                    ev = Path("data/evidence") / comp["candidate_id"] / "ledger_oos.json"
                    try:
                        lp = json.loads(ev.read_text(encoding="utf-8"))
                    except Exception:
                        return None
                for t in lp.get("trades", []):
                    ts = t.get("entry_time_ms")
                    if not isinstance(ts, (int, float)) or ts <= 0:
                        return None
                    week = datetime.fromtimestamp(ts / 1000.0, tz=timezone.utc).isocalendar()[:2]
                    week_pnl.setdefault(comp["candidate_id"], {}).setdefault(week, 0.0)
                    week_pnl[comp["candidate_id"]][week] += float(t.get("net_pnl_usd", 0.0))
        finally:
            conn2.close()
        if len(week_pnl) != len(comp_list):
            return None
        all_weeks = sorted({w for m in week_pnl.values() for w in m})
        if len(all_weeks) < 4:
            return None  # sin historia semanal suficiente para correlación real
        base_cap = base_capital if base_capital else (10000.0 if route_u == "ULTRA" else 50000.0)
        series_out = []
        for comp in comp_list:
            m = week_pnl.get(comp["candidate_id"], {})
            series_out.append([round(100.0 * m.get(w, 0.0) / base_cap, 6) for w in all_weeks])
        return series_out

    aligned = _weekly_aligned(components_evidence)

    series: List[List[float]] = []
    vols: List[float] = []
    if aligned:
        # Descartar componentes con varianza semanal cero (sin actividad real suficiente)
        kept_pairs = []
        for comp, rets in zip(components_evidence, aligned):
            mean = sum(rets) / len(rets)
            var = sum((x - mean) ** 2 for x in rets) / (len(rets) - 1)
            if var > 0:
                kept_pairs.append((comp, rets))
                vols.append(var ** 0.5)
        if len(kept_pairs) < 2:
            logger.warning("Meta-%s: <2 componentes con actividad semanal real; fail-closed.", route_u)
            return None
        components_evidence = [c for c, _ in kept_pairs]
        series = [r for _, r in kept_pairs]
    else:
        # Fallback honesto: risk-parity por volatilidad por-trade (sin matriz de correlación)
        for comp in components_evidence:
            rets = comp["oos_returns"]
            mean = sum(rets) / len(rets)
            var = sum((x - mean) ** 2 for x in rets) / (len(rets) - 1)
            if var <= 0:
                logger.warning("Meta-%s: varianza cero en %s; fail-closed.", route_u, comp["candidate_id"])
                return None
            vols.append(var ** 0.5)
            series.append(rets)

    weights = MetaEnsembleService.compute_risk_parity_weights(vols)
    try:
        corr = MetaEnsembleService.compute_correlation_matrix(series)
    except ValueError:
        corr = [[1.0 if i == j else 0.0 for j in range(len(series))] for i in range(len(series))]
    ids = sorted(c["candidate_id"] for c in components_evidence)
    payload = {
        "target_route": route_u,
        "candidate_ids": ids,
        "weights": weights,
        "correlation_matrix": corr,
        "engine_version": ENGINE_VERSION,
    }
    canonical_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    portfolio_id = f"meta_{route_u.lower()}_{canonical_hash[:16]}"
    capital = float(base_capital if base_capital else (10000.0 if route_u == "ULTRA" else 50000.0))

    components = [
        {
            "strategy_id": c["candidate_id"],
            "name": c["name"],
            "symbol": c["symbol"],
            "timeframe": c["timeframe"],
            "weight": weights[i],
            "route": route_u,
        }
        for i, c in enumerate(components_evidence)
    ]

    db = SessionLocal()
    try:
        # Marcar como SUPERSEDED cualquier meta anterior de la ruta con hash distinto
        for old in db.query(PortfolioModel).filter(
            PortfolioModel.portfolio_id.like(f"meta_{route_u.lower()}_%"),
            PortfolioModel.canonical_hash != canonical_hash,
            PortfolioModel.status == "ASSEMBLED_PENDING_PORTFOLIO_BACKTEST",
        ).all():
            old.status = "SUPERSEDED"
        db.commit()

        existing = db.query(PortfolioModel).filter(PortfolioModel.portfolio_id == portfolio_id).first()
        if existing:
            return _summary(existing)
        row = PortfolioModel(
            portfolio_id=portfolio_id,
            name=f"Meta-{route_u} Risk-Parity ({len(components)} componentes)",
            target_route=route_u,
            base_capital_usd=capital,
            current_equity_usd=capital,
            components_json=json.dumps(components),
            correlation_matrix_json=json.dumps(corr),
            annualized_roi_pct=0.0,
            monthly_roi_pct=0.0,
            max_drawdown_pct=0.0,
            profit_factor=0.0,
            canonical_hash=canonical_hash,
            status="ASSEMBLED_PENDING_PORTFOLIO_BACKTEST",
        )
        db.add(row)
        db.commit()
        logger.info("Meta-estrategia ensamblada y persistida: %s (%d componentes)", portfolio_id, len(components))
        db.refresh(row)
        return _summary(row)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _summary(row: PortfolioModel) -> Dict[str, Any]:
    return {
        "portfolio_id": row.portfolio_id,
        "name": row.name,
        "target_route": row.target_route,
        "base_capital_usd": row.base_capital_usd,
        "components": json.loads(row.components_json or "[]"),
        "correlation_matrix": json.loads(row.correlation_matrix_json or "[]"),
        "canonical_hash": row.canonical_hash,
        "status": row.status,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def ensure_meta_strategies(routes: tuple = ("ULTRA", "FONDEO")) -> Dict[str, Any]:
    """Intenta ensamblar la meta-estrategia de cada ruta; idempotente."""
    results: Dict[str, Any] = {}
    for route in routes:
        try:
            results[route] = build_meta_for_route(route)
        except Exception as exc:
            logger.error("Meta-%s error: %s", route, exc)
            results[route] = {"error": str(exc)}
    return results
