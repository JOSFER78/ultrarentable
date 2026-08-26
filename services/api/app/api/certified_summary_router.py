"""Canonical certified-strategy summary.

REAL-ONLY / ZERO-INFERENCE:
- CandidateModel.status is never certification evidence by itself.
- Every certified row requires explicit 11/11 gate evidence.
- Cryptographic identifiers must come from stored evidence; they are never generated here.
- Missing quantitative evidence remains missing.
- There are no candidate->certified fallbacks.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
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


def _explicit_gate_state(sc: Dict[str, Any]) -> tuple[int, int, bool, Dict[str, Any]]:
    explicit: Dict[int, bool] = {}
    gate_payload: Dict[str, Any] = {}

    gates = sc.get("gates")
    if isinstance(gates, list):
        gate_payload = {str(index + 1): gate for index, gate in enumerate(gates) if isinstance(gate, dict)}
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
    return explicit_count, passed_count, explicit_count == 11 and passed_count == 11, gate_payload


def _real_oos_months(sc: Dict[str, Any]) -> Optional[float]:
    """Derive OOS duration only from explicit real dates; never invent a default."""
    duration = sc.get("duration_info")
    if not isinstance(duration, dict):
        duration = {}

    explicit_months = duration.get("oos_months", sc.get("oos_months"))
    if isinstance(explicit_months, (int, float)) and explicit_months > 0:
        return float(explicit_months)

    start_raw = duration.get("oos_start") or sc.get("oos_start_timestamp_ms") or sc.get("oos_start_timestamp")
    end_raw = duration.get("oos_end") or sc.get("oos_end_timestamp_ms") or sc.get("oos_end_timestamp")

    def parse_datetime(value: Any) -> Optional[datetime]:
        if isinstance(value, (int, float)):
            # Millisecond timestamps are accepted only when clearly in ms range.
            if value < 1_000_000_000_000:
                return None
            return datetime.fromtimestamp(value / 1000.0, tz=timezone.utc)
        if isinstance(value, str) and value.strip():
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        return None

    start = parse_datetime(start_raw)
    end = parse_datetime(end_raw)
    if start is None or end is None or end <= start:
        return None
    return (end - start).total_seconds() / (30.436875 * 24 * 3600)


def _metric(sc: Dict[str, Any], *keys: str) -> Optional[float]:
    containers = [sc]
    oos = sc.get("oos_metrics")
    if isinstance(oos, dict):
        containers.append(oos)
    for container in containers:
        for key in keys:
            value = container.get(key)
            if isinstance(value, (int, float)) and value == value:
                return float(value)
    return None


def _required_string(value: Any) -> Optional[str]:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _certified_row(candidate: CandidateModel) -> Dict[str, Any]:
    sc = _scorecard(candidate)
    explicit_count, passed_count, all11, gate_payload = _explicit_gate_state(sc)

    dataset_id = _required_string(candidate.dataset_id or sc.get("dataset_id"))
    strategy_hash = _required_string(sc.get("strategy_sha256") or sc.get("canonical_hash"))
    ledger_hash = _required_string(sc.get("ledger_hash"))
    evidence_hash = _required_string(sc.get("bundle_signature_sha256") or sc.get("evidence_bundle_hash"))
    certified_at = _required_string(sc.get("certified_at_utc"))
    current_status = _required_string(candidate.status)

    if not all11:
        raise ValueError("INTERNAL_ONLY: _certified_row called without explicit 11/11 evidence")

    return {
        "candidate_id": candidate.candidate_id,
        "name": candidate.name,
        "route": candidate.route,
        "symbol": candidate.symbol,
        "timeframe": candidate.timeframe,
        "engine_version": candidate.engine_version,
        "status_source": current_status,
        "certification_status": "CERTIFIED_CURRENT" if current_status == "APPROVED_CURRENT_ENGINE" else "NO_EVIDENCE",
        "explicit_gates": explicit_count,
        "passed_gates": passed_count,
        "gates_verified_11": all11,
        "strategy_sha256": strategy_hash,
        "bundle_signature_sha256": evidence_hash,
        "dataset_id": dataset_id,
        "metrics": {
            "trades_oos": candidate.trades_oos,
            "win_rate_pct": _metric(sc, "win_rate_pct", "win_rate", "oos_win_rate_pct"),
            "profit_factor_is": candidate.profit_factor_is,
            "profit_factor_oos": candidate.profit_factor_oos,
            "roi_cumulative_pct": _metric(sc, "roi_cumulative_pct", "net_return_pct", "return_pct"),
            "roi_annualized_pct": _metric(sc, "roi_annualized_pct", "annual_return_pct", "annual_return"),
            "roi_monthly_pct": _metric(sc, "roi_monthly_pct", "monthly_return_pct", "monthly_return"),
            "max_dd_oos_pct": candidate.max_dd_oos_pct,
            "max_dd_realized_pct": _metric(sc, "max_dd_realized_pct", "max_drawdown_realized_pct"),
            "wfe_pct": _metric(sc, "wfe_pct", "wfo_pass_pct", "wfe_retention_pct"),
            "monte_carlo_score": _metric(sc, "monte_carlo_score", "mc_robustness_score"),
            "ratio_oos_is": _metric(sc, "ratio_oos_is"),
            "oos_months": _real_oos_months(sc),
        },
        "ledger_hash": ledger_hash,
        "ledger_verified": sc.get("ledger_verified") is True,
        "certified_at_utc": certified_at,
        "gates": gate_payload,
    }


@certified_summary_router.get("/summary")
def certified_summary(route: Optional[str] = Query(None, description="ULTRA, FONDEO"), verified_only: bool = Query(True, description="Return only explicit 11/11 evidence"), limit: int = Query(500, ge=1, le=5000), db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    query = db.query(CandidateModel)
    if route and route.upper() != "ALL":
        query = query.filter(CandidateModel.route == route.upper())

    rows = query.order_by(CandidateModel.net_profit_oos.desc()).limit(limit).all()
    result: List[Dict[str, Any]] = []
    for candidate in rows:
        sc = _scorecard(candidate)
        _, _, all11, _ = _explicit_gate_state(sc)
        if verified_only and not all11:
            continue
        try:
            row = _certified_row(candidate)
        except ValueError:
            continue
        if verified_only and row["certification_status"] != "CERTIFIED_CURRENT":
            continue
        result.append(row)
    return result


@certified_summary_router.get("/strategies")
def get_certified_strategies_endpoint(db: Session = Depends(get_db), limit: int = Query(500, ge=1, le=5000)) -> List[Dict[str, Any]]:
    query = db.query(CandidateModel).order_by(CandidateModel.net_profit_oos.desc()).limit(limit)
    rows = query.all()
    out: List[Dict[str, Any]] = []

    for candidate in rows:
        sc = _scorecard(candidate)
        _, _, all11, gates = _explicit_gate_state(sc)
        if not all11 or candidate.status != "APPROVED_CURRENT_ENGINE":
            continue

        strategy_hash = _required_string(sc.get("strategy_sha256") or sc.get("canonical_hash"))
        dataset_hash = _required_string(sc.get("dataset_hash") or sc.get("data_sha256"))
        ledger_hash = _required_string(sc.get("ledger_hash"))
        evidence_bundle_hash = _required_string(sc.get("bundle_signature_sha256") or sc.get("evidence_bundle_hash"))
        certified_at = _required_string(sc.get("certified_at_utc"))
        ledger_verified = sc.get("ledger_verified") is True

        if any(value is None for value in [strategy_hash, dataset_hash, ledger_hash, evidence_bundle_hash, certified_at]) or not ledger_verified:
            continue

        out.append({
            "strategy_id": str(candidate.candidate_id),
            "name": candidate.name,
            "symbol": candidate.symbol,
            "timeframe": candidate.timeframe,
            "family": candidate.route,
            "status": "APPROVED_CURRENT_ENGINE",
            "engine_version": candidate.engine_version,
            "strategy_hash": strategy_hash,
            "dataset_hash": dataset_hash,
            "ledger_hash": ledger_hash,
            "evidence_bundle_hash": evidence_bundle_hash,
            "all_gates_pass": True,
            "ledger_verified": True,
            "total_trades": candidate.trades_oos,
            "win_rate_pct": _metric(sc, "win_rate_pct", "win_rate", "oos_win_rate_pct"),
            "profit_factor": candidate.profit_factor_oos,
            "sharpe_ratio": _metric(sc, "sharpe_ratio", "oos_sharpe"),
            "max_drawdown_pct": candidate.max_dd_oos_pct,
            "oos_profit_factor": candidate.profit_factor_oos,
            "oos_start_timestamp_ms": sc.get("oos_start_timestamp_ms"),
            "oos_end_timestamp_ms": sc.get("oos_end_timestamp_ms"),
            "oos_months": _real_oos_months(sc),
            "monthly_return": _metric(sc, "monthly_return_pct", "monthly_return"),
            "annual_return": _metric(sc, "annual_return_pct", "annual_return"),
            "cagr": _metric(sc, "cagr"),
            "certified_at_utc": certified_at,
            "gates": gates,
            "equity_curve": sc.get("equity_curve") if isinstance(sc.get("equity_curve"), list) else [],
        })

    return out


@certified_summary_router.get("/meta-strategies")
def get_certified_meta_strategies_endpoint(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    return []
