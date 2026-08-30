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

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from services.api.app.db.database import CandidateModel, PortfolioModel, get_db
from services.export.excel_master_catalog import (
    build_master_catalog_csv,
    build_master_catalog_xlsx,
)

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
    """Return only the stable gate-state tuple used by API/tests.

    Gate payload rendering is deliberately separate so callers cannot accidentally
    treat arbitrary payload details as certification evidence.
    """
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


def _gate_payload(sc: Dict[str, Any]) -> Dict[str, Any]:
    gates = sc.get("gates")
    if isinstance(gates, list):
        return {
            str(index + 1): gate
            for index, gate in enumerate(gates)
            if isinstance(gate, dict)
        }
    ge = sc.get("gates_evaluation")
    if isinstance(ge, dict):
        return {str(key): value for key, value in ge.items() if str(key).startswith("gate_")}
    return {}


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
    metrics = sc.get("metrics")
    if isinstance(metrics, dict):
        containers.append(metrics)
        out_of_sample = metrics.get("out_of_sample")
        if isinstance(out_of_sample, dict):
            containers.append(out_of_sample)
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
    explicit_count, passed_count, all11 = _explicit_gate_state(sc)

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
        "gates": _gate_payload(sc),
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
        _, _, all11 = _explicit_gate_state(sc)
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
def get_certified_strategies_endpoint(
    route: Optional[str] = Query(None, description="ULTRA, FONDEO"),
    db: Session = Depends(get_db),
    limit: int = Query(500, ge=1, le=5000),
) -> List[Dict[str, Any]]:
    actual_limit = limit if isinstance(limit, int) else (getattr(limit, "default", 500) if hasattr(limit, "default") and isinstance(getattr(limit, "default"), int) else 500)
    query = db.query(CandidateModel)
    if route and route.upper() != "ALL":
        query = query.filter(CandidateModel.route == route.upper())
    rows = query.order_by(CandidateModel.net_profit_oos.desc()).limit(actual_limit).all()
    out: List[Dict[str, Any]] = []

    for candidate in rows:
        sc = _scorecard(candidate)
        _, _, all11 = _explicit_gate_state(sc)
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
            "route": candidate.route,
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
            "monthly_return": _metric(sc, "monthly_return_pct", "monthly_return", "roi_monthly_pct", "monthly_roi_pct"),
            "annual_return": _metric(sc, "annual_return_pct", "annual_return"),
            "cagr": _metric(sc, "cagr"),
            "certified_at_utc": certified_at,
            "gates": _gate_payload(sc),
            "equity_curve": sc.get("equity_curve") if isinstance(sc.get("equity_curve"), list) else [],
        })

    return out


@certified_summary_router.get("/meta-strategies")
def get_certified_meta_strategies_endpoint(
    route: Optional[str] = Query(None, description="ULTRA, FONDEO"),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Meta-estrategias reales persistidas en portfolios (meta-ULTRA / meta-FONDEO).

    Solo se exponen ensamblados construidos sobre componentes certificados con
    evidencia criptográfica; un meta-ensamblado nunca presenta métricas de
    portafolio hasta que exista backtest de portafolio con ledger propio.
    """
    try:
        from services.portfolio.meta_strategy_pipeline import ensure_meta_strategies

        ensure_meta_strategies(("ULTRA", "FONDEO"))
    except Exception:
        pass  # fail-closed: si el pipeline no puede correr, se sirve lo persistido
    all_rows = (
        db.query(PortfolioModel)
        .filter(PortfolioModel.portfolio_id.like("meta%"))
        .all()
    )
    # Solo mis IDs canónicos (meta_ultra_<hash16> / meta_fondeo_<hash16>, minúsculas exactas)
    rows = [r for r in all_rows if r.portfolio_id.startswith(("meta_ultra_", "meta_fondeo_"))]
    if route and route.upper() != "ALL":
        rows = [r for r in rows if r.target_route.upper() == route.upper()]
    out: List[Dict[str, Any]] = []
    for row in rows:
        out.append({
            "meta_strategy_id": row.portfolio_id,
            "portfolio_id": row.portfolio_id,
            "name": row.name,
            "route": row.target_route,
            "target_route": row.target_route,
            "portfolio_hash": row.canonical_hash,
            "combined_ledger_hash": row.canonical_hash,
            "status": row.status,
            "engine_version": "5.4.0",
            "base_capital_usd": row.base_capital_usd,
            "components": json.loads(row.components_json or "[]"),
            "correlation_matrix": json.loads(row.correlation_matrix_json or "[]"),
            "canonical_hash": row.canonical_hash,
            "combined_profit_factor": None if row.status == "ASSEMBLED_PENDING_PORTFOLIO_BACKTEST" else row.profit_factor,
            "combined_sharpe_ratio": None if row.status == "ASSEMBLED_PENDING_PORTFOLIO_BACKTEST" else None,
            "combined_max_drawdown_pct": None if row.status == "ASSEMBLED_PENDING_PORTFOLIO_BACKTEST" else row.max_drawdown_pct,
            "monthly_return": None if row.status == "ASSEMBLED_PENDING_PORTFOLIO_BACKTEST" else row.monthly_roi_pct,
            "max_drawdown_pct": None if row.status == "ASSEMBLED_PENDING_PORTFOLIO_BACKTEST" else row.max_drawdown_pct,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        })
    return out


@certified_summary_router.get("/export/csv")
def export_certified_csv(
    route: Optional[str] = Query(None, description="Filter by route: ULTRA, FONDEO, or ALL"),
    db: Session = Depends(get_db),
) -> Response:
    """Export canonical master catalog (certified strategies and meta-strategies) as CSV."""
    csv_content = build_master_catalog_csv(db, route=route)
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    route_suffix = f"_{route.lower()}" if route and route.upper() != "ALL" else ""
    filename = f"catalogo_master_certificadas{route_suffix}_{timestamp_str}.csv"

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache, no-store, must-revalidate",
        },
    )


@certified_summary_router.get("/export/xlsx")
def export_certified_xlsx(
    route: Optional[str] = Query(None, description="Filter by route: ULTRA, FONDEO, or ALL"),
    db: Session = Depends(get_db),
) -> Response:
    """Export canonical master catalog (certified strategies and meta-strategies) as structured Excel (.xlsx)."""
    xlsx_bytes = build_master_catalog_xlsx(db, route=route)
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    route_suffix = f"_{route.lower()}" if route and route.upper() != "ALL" else ""
    filename = f"catalogo_master_certificadas{route_suffix}_{timestamp_str}.xlsx"

    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache, no-store, must-revalidate",
        },
    )

