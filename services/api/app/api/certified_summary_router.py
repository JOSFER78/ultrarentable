"""Canonical certified-strategy summary.

REAL-ONLY / ZERO-INFERENCE:
- CandidateModel.status is NOT certification evidence.
- Missing metrics are returned as null; consumers must render N/D.
- 11/11 requires explicit evidence for every gate and every gate passed.
- No default duration, capital, drawdown, win rate, WFE or ROI is invented here.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from services.api.app.db.database import CandidateModel, get_db

certified_summary_router = APIRouter(prefix="/certified", tags=["Canonical Certification Summary"])


def _scorecard(candidate: CandidateModel) -> Dict[str, Any]:
    raw = candidate.scorecard_json
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    try:
        value = json.loads(raw)
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def _explicit_gate_state(sc: Dict[str, Any]) -> tuple[int, int, bool]:
    explicit: Dict[int, bool] = {}
    gates = sc.get("gates")
    if isinstance(gates, list):
        for gate in gates:
            if not isinstance(gate, dict):
                continue
            raw_id = gate.get("gate_id", gate.get("id"))
            try:
                gate_id = int(raw_id)
            except (TypeError, ValueError):
                continue
            if 1 <= gate_id <= 11:
                value = gate.get("passed")
                if value is None:
                    value = str(gate.get("status", "")).upper() == "PASSED"
                if isinstance(value, bool):
                    explicit[gate_id] = value

    ge = sc.get("gates_evaluation")
    if isinstance(ge, dict):
        for gate_id in range(1, 12):
            key = f"gate_{gate_id:02d}"
            if key not in ge:
                continue
            value = ge[key]
            if isinstance(value, bool):
                explicit[gate_id] = value
            elif isinstance(value, str) and value.upper() in {"PASSED", "FAILED"}:
                explicit[gate_id] = value.upper() == "PASSED"

    explicit_count = len(explicit)
    passed_count = sum(1 for value in explicit.values() if value)
    return explicit_count, passed_count, explicit_count == 11 and passed_count == 11


def _real_oos_months(sc: Dict[str, Any]) -> Optional[float]:
    duration = sc.get("duration_info")
    if not isinstance(duration, dict):
        return None
    raw = duration.get("oos_months")
    if isinstance(raw, (int, float)) and raw > 0:
        return float(raw)
    start = duration.get("oos_start")
    end = duration.get("oos_end")
    if start and end:
        try:
            s = datetime.fromisoformat(str(start).replace("Z", "+00:00"))
            e = datetime.fromisoformat(str(end).replace("Z", "+00:00"))
            days = (e - s).total_seconds() / 86400.0
            if days > 0:
                return days / 30.436875
        except (ValueError, TypeError):
            return None
    return None


def _metric(sc: Dict[str, Any], *keys: str) -> Optional[float]:
    containers = [sc, sc.get("oos_metrics") if isinstance(sc.get("oos_metrics"), dict) else {}]
    for container in containers:
        for key in keys:
            value = container.get(key)
            if isinstance(value, (int, float)) and value == value:
                return float(value)
    return None


def _certified_row(candidate: CandidateModel) -> Dict[str, Any]:
    sc = _scorecard(candidate)
    explicit_count, passed_count, all11 = _explicit_gate_state(sc)
    oos = sc.get("oos_metrics") if isinstance(sc.get("oos_metrics"), dict) else {}
    duration = _real_oos_months(sc)

    initial_capital = sc.get("initial_capital_usd")
    final_equity = sc.get("final_equity_usd")
    net_profit = candidate.net_profit_oos
    cumulative_roi = None
    annualized_roi = None
    monthly_roi = None
    if isinstance(initial_capital, (int, float)) and initial_capital > 0:
        if isinstance(final_equity, (int, float)):
            cumulative_roi = ((float(final_equity) / float(initial_capital)) - 1.0) * 100.0
        elif isinstance(net_profit, (int, float)):
            cumulative_roi = (float(net_profit) / float(initial_capital)) * 100.0
        if cumulative_roi is not None and duration and cumulative_roi > -100.0:
            growth = 1.0 + cumulative_roi / 100.0
            annualized_roi = (growth ** (12.0 / duration) - 1.0) * 100.0
            monthly_roi = (growth ** (1.0 / duration) - 1.0) * 100.0

    def optional_number(*names: str) -> Optional[float]:
        value = _metric(sc, *names)
        if value is not None:
            return value
        value = _metric(oos, *names)
        return value

    return {
        "candidate_id": candidate.candidate_id,
        "name": candidate.name,
        "route": candidate.route,
        "symbol": candidate.symbol,
        "timeframe": candidate.timeframe,
        "engine_version": candidate.engine_version,
        "status_source": candidate.status,
        "certification_status": "CERTIFIED_CURRENT" if all11 else "NO_EVIDENCE",
        "explicit_gates": explicit_count,
        "passed_gates": passed_count,
        "gates_verified_11": all11,
        "strategy_sha256": sc.get("strategy_sha256") or sc.get("canonical_hash"),
        "bundle_signature_sha256": sc.get("bundle_signature_sha256"),
        "dataset_id": candidate.dataset_id or sc.get("dataset_id"),
        "metrics": {
            "trades_oos": candidate.trades_oos if candidate.trades_oos is not None else optional_number("trades", "trades_oos"),
            "win_rate_pct": optional_number("win_rate_pct", "win_rate"),
            "profit_factor_is": candidate.profit_factor_is,
            "profit_factor_oos": candidate.profit_factor_oos,
            "roi_cumulative_pct": cumulative_roi,
            "roi_annualized_pct": annualized_roi,
            "roi_monthly_pct": monthly_roi,
            "max_dd_oos_pct": candidate.max_dd_oos_pct if candidate.max_dd_oos_pct is not None else optional_number("max_drawdown_pct", "max_dd_oos_pct"),
            "max_dd_realized_pct": optional_number("max_dd_realized_pct", "max_drawdown_realized_pct"),
            "wfe_pct": optional_number("wfe_pct", "wfo_pass_pct", "wfe_retention_pct"),
            "monte_carlo_score": optional_number("monte_carlo_score", "mc_robustness_score"),
            "ratio_oos_is": optional_number("ratio_oos_is"),
            "oos_months": duration,
        },
    }


@certified_summary_router.get("/summary")
def certified_summary(
    route: Optional[str] = Query(None, description="ULTRA, FONDEO"),
    verified_only: bool = Query(True, description="Return only explicit 11/11 evidence"),
    limit: int = Query(500, ge=1, le=5000),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    query = db.query(CandidateModel)
    if route and route.upper() != "ALL":
        query = query.filter(CandidateModel.route == route.upper())
    rows = query.order_by(CandidateModel.net_profit_oos.desc()).limit(limit).all()
    result = [_certified_row(candidate) for candidate in rows]
    if verified_only:
        result = [row for row in result if row["gates_verified_11"]]
    return result
