"""FastAPI Router for Candidates, Scorecards, Reclassification, Robustness Verification & Code Exports."""

from __future__ import annotations

import json
import math
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from services.api.app.db.database import get_db, CandidateModel, AuditEventModel
from services.api.app.export.sqx_to_tradingview import generate_pinescript_v5
from services.api.app.export.sqx_to_ninjatrader import generate_ninjatrader_strategy_cs
from services.api.app.factory.robustness_verifier import verify_strategy_robustness
from services.api.app.validation.market_specs import get_market_spec
from services.engine_version import CURRENT_ENGINE_VERSION
from services.validation.legacy_revalidation_service import legacy_revalidation_service
from services.api.app.core.fast_cache import in_memory_cached, fast_cache

candidates_router = APIRouter(prefix="/candidates", tags=["Strategy Candidates & Scorecards"])


class StatusUpdateSchema(BaseModel):
    status: str = Field(..., description="INVESTIGACION_BTC, RECHAZADA_FONDEO_DD, CANDIDATA_FONDEO, PAPER, LISTA_PARA_EVALUACION, EJECUTANDO, PAUSADA, RETIRADA")
    reason: str = Field(..., description="Mandatory audit trail reason for status change")


class RevalidateLegacyRequest(BaseModel):
    target_version: Optional[str] = Field(None, description="Versión específica a revalidar e.g. '1.02', '1.00' o 'ALL'")
    only_approved: bool = Field(True, description="Si es True, revalida solo estrategias que no estén rechazadas")
    route: Optional[str] = Field("ALL", description="Filtro de ruta: 'ALL', 'ULTRA', 'FONDEO'")
    max_candidates: int = Field(0, ge=0, le=1000000, description="Máximo número de estrategias a revalidar (0 = Todas sin límite)")
    background: bool = Field(True, description="Si es True, procesa en segundo plano y permite consultar el progreso en vivo")


def normalize_symbol_key(raw_sym: str) -> str:
    s = (raw_sym or "").upper().replace("/", "").replace("-", "").replace("_", "").strip()
    if s.endswith("USDT"):
        base = s[:-4]
        return f"{base}-USDT"
    elif s.endswith("USD") and len(s) > 6 and s not in ["EURUSD", "GBPUSD", "AUDUSD", "USDCAD", "USDCHF", "USDJPY"]:
        base = s[:-3]
        return f"{base}-USDT"
    return s


@candidates_router.get("/summary")
@in_memory_cached(key_prefix="candidates_summary", ttl=2.0)
def list_candidates_summary(
    route: Optional[str] = Query(None, description="ULTRA, FONDEO"),
    status: Optional[str] = Query(None, description="Filter by status"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    timeframe: Optional[str] = Query(None, description="Filter by timeframe"),
    engine_version: Optional[str] = Query(None, description="Filter by engine version"),
    limit: int = Query(250, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Ultra-fast summary endpoint returning compact strategy rows without heavy scorecard blobs."""
    query = db.query(
        CandidateModel.candidate_id,
        CandidateModel.name,
        CandidateModel.route,
        CandidateModel.symbol,
        CandidateModel.timeframe,
        CandidateModel.status,
        CandidateModel.status_reason,
        CandidateModel.profit_factor_is,
        CandidateModel.profit_factor_oos,
        CandidateModel.max_dd_is_pct,
        CandidateModel.max_dd_oos_pct,
        CandidateModel.trades_is,
        CandidateModel.trades_oos,
        CandidateModel.net_profit_oos,
        CandidateModel.engine_version,
    )
    if route and route.upper() != "ALL":
        query = query.filter(CandidateModel.route == route.upper())
    if status and status.upper() != "ALL":
        if status.upper() == "APPROVED":
            query = query.filter(CandidateModel.status.in_(["APPROVED", "ULTRA_CERTIFIED", "FUNDING_CERTIFIED", "CERTIFIED_PASS"]))
        elif status.upper() == "REJECTED":
            query = query.filter(~CandidateModel.status.in_(["APPROVED", "ULTRA_CERTIFIED", "FUNDING_CERTIFIED", "CERTIFIED_PASS"]))
        else:
            query = query.filter(CandidateModel.status == status)
    if symbol and symbol.upper() != "ALL":
        query = query.filter(CandidateModel.symbol.ilike(f"%{symbol}%"))
    if timeframe and timeframe.upper() != "ALL":
        query = query.filter(CandidateModel.timeframe == timeframe)
    if engine_version and engine_version.upper() != "ALL":
        query = query.filter(CandidateModel.engine_version == engine_version)

    rows = query.order_by(CandidateModel.net_profit_oos.desc()).offset(offset).limit(limit).all()

    summary_list = []
    for r in rows:
        cid, name, r_route, r_sym, r_tf, r_st, r_rs, pf_is, pf_oos, dd_is, dd_oos, tr_is, tr_oos, net_oos, eng_ver = r
        is_fondeo = (r_route == "FONDEO")
        base_cap = 50000.0 if is_fondeo else 1000.0
        net_val = float(net_oos or 0.0)
        
        m_roi = round(((net_val / base_cap) * 100.0) / 2.4, 2) if base_cap > 0 else 0.0
        a_roi = round(m_roi * 12.0, 2)
        
        summary_list.append({
            "candidate_id": cid,
            "name": name or cid,
            "route": r_route or "ULTRA",
            "symbol": r_sym or "BTC",
            "timeframe": r_tf or "15m",
            "status": r_st or "REJECTED",
            "status_reason": r_rs or "",
            "profit_factor_is": float(pf_is or 0.0),
            "profit_factor_oos": float(pf_oos or 0.0),
            "max_dd_is_pct": float(dd_is or 0.0),
            "max_dd_oos_pct": float(dd_oos or 0.0),
            "trades_is": int(tr_is or 0),
            "trades_oos": int(tr_oos or 0),
            "net_profit_oos": net_val,
            "monthly_return_pct": m_roi,
            "annual_return_pct": a_roi,
            "engine_version": eng_ver or "5.3.0",
        })

    return summary_list


@candidates_router.get("")
@in_memory_cached(key_prefix="candidates_full", ttl=2.0)
def list_candidates(
    route: Optional[str] = Query(None, description="ULTRA, FONDEO"),
    status: Optional[str] = Query(None, description="Filter by candidate status"),
    symbol: Optional[str] = Query(None, description="Filter by symbol (e.g. BTC-USDT, EURUSD, NQ)"),
    timeframe: Optional[str] = Query(None, description="Filter by timeframe (e.g. 1m, 5m, 15m, 1h, 4h)"),
    tier: Optional[str] = Query(None, description="Filter by tier (TIER_1_CERTIFIED, TIER_2_NEAR_CERTIFIED, TIER_3_INCUBATOR, TIER_4_REJECTED, ALL)"),
    engine_version: Optional[str] = Query(None, description="Filter by engine version (e.g. 1.02, 1.00)"),
    include_rejected: bool = Query(True, description="Incluir o no candidatos rechazados"),
    deduplicate_champions: bool = Query(False, description="Deduplicar sólo el mejor candidato por símbolo"),
    limit: int = Query(250, ge=1, le=1000, description="Max candidates to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """List strategy candidates with filters, pagination, multi-tier ranking and actionable prescriptions."""
    query = db.query(CandidateModel)
    if route and route.upper() != "ALL":
        query = query.filter(CandidateModel.route == route.upper())
    if status and status.upper() != "ALL":
        if status.upper() == "APPROVED":
            query = query.filter(
                CandidateModel.status.in_(["APPROVED", "ULTRA_CERTIFIED", "FUNDING_CERTIFIED"]),
                CandidateModel.scorecard_json.isnot(None)
            )
        elif status.upper() == "REJECTED":
            query = query.filter(~CandidateModel.status.in_(["APPROVED", "ULTRA_CERTIFIED", "FUNDING_CERTIFIED"]))
        else:
            query = query.filter(CandidateModel.status == status)
    elif not include_rejected and (not tier or tier.upper() in ("TIER_1_CERTIFIED", "APPROVED")):
        query = query.filter(
            CandidateModel.status.in_(["APPROVED", "ULTRA_CERTIFIED", "FUNDING_CERTIFIED"]),
            CandidateModel.scorecard_json.isnot(None)
        )

    if symbol and symbol.upper() != "ALL":
        query = query.filter(CandidateModel.symbol.ilike(f"%{symbol}%"))
    if timeframe and timeframe.upper() != "ALL":
        query = query.filter(CandidateModel.timeframe == timeframe)
    if engine_version and engine_version.upper() != "ALL":
        query = query.filter(CandidateModel.engine_version == engine_version)
        
    candidates = query.order_by(CandidateModel.net_profit_oos.desc()).offset(offset).limit(limit).all()
    
    if deduplicate_champions:
        seen_champion_keys = set()
        filtered_candidates = []
        for c in candidates:
            norm_sym = normalize_symbol_key(c.symbol)
            champ_key = f"{c.route.upper()}_{norm_sym}"
            if champ_key in seen_champion_keys:
                continue
            seen_champion_keys.add(champ_key)
            filtered_candidates.append(c)
    else:
        filtered_candidates = candidates

    results = []
    for c in filtered_candidates:
        sc = {}
        if c.scorecard_json:
            try:
                sc = json.loads(c.scorecard_json)
            except Exception:
                sc = {}

        is_m = sc.get("is_metrics") or {}
        oos_m = sc.get("oos_metrics") or {}
        dur = sc.get("duration_info") or {}

        is_fondeo = (c.route == "FONDEO")
        base_cap = float(sc.get("initial_capital_usd") or oos_m.get("account_base_usd") or (50000.0 if is_fondeo else 1000.0))
        net_prof_oos = float(c.net_profit_oos if c.net_profit_oos is not None else oos_m.get("net_profit_usd", 0.0))

        tf = (c.timeframe or "1h").lower()
        tf_bars_per_month = {"1m": 43200, "5m": 8640, "15m": 2880, "1h": 720, "4h": 180, "1d": 30}
        bars_per_m = tf_bars_per_month.get(tf, 720)
        total_bars = int(dur.get("total_bars") or 3840)
        calc_months = max(0.5, round(total_bars / bars_per_m, 1))
        oos_months = float(dur.get("oos_months") or oos_m.get("oos_months") or max(0.2, round(calc_months * 0.2, 1)))

        # Cálculo robusto y realista de ROI mensual y anual (Cero overflow / Cero desbordamiento)
        raw_monthly = sc.get("monthly_return_pct") or sc.get("monthly_roi_pct") or oos_m.get("monthly_roi_pct")
        raw_annual = sc.get("annual_return_pct") or sc.get("annualized_roi_pct") or oos_m.get("annualized_roi_pct")
        
        if raw_monthly is not None and abs(float(raw_monthly)) <= 5000.0:
            monthly_roi = float(raw_monthly)
            ann_roi = float(raw_annual) if (raw_annual is not None and abs(float(raw_annual)) <= 50000.0) else round(monthly_roi * 12.0, 2)
        else:
            monthly_roi = round(((net_prof_oos / max(1.0, base_cap)) * 100.0) / max(0.2, oos_months), 2)
            ann_roi = round(monthly_roi * 12.0, 2)

        # Clamping de seguridad para evitar números no representables
        if abs(ann_roi) > 50000.0 or math.isnan(ann_roi) or math.isinf(ann_roi):
            monthly_roi = round(((net_prof_oos / max(1.0, base_cap)) * 100.0) / max(0.2, oos_months), 2)
            ann_roi = round(monthly_roi * 12.0, 2)

        roi_oos = round(monthly_roi * oos_months, 2) if monthly_roi is not None else None

        raw_wr_is = is_m.get("win_rate_pct") if is_m.get("win_rate_pct") is not None else is_m.get("win_rate")
        wr_is = float(raw_wr_is) if raw_wr_is is not None else None

        raw_wr_oos = sc.get("win_rate_pct") if sc.get("win_rate_pct") is not None else (oos_m.get("win_rate_pct") if oos_m.get("win_rate_pct") is not None else oos_m.get("win_rate"))
        wr_oos = float(raw_wr_oos) if raw_wr_oos is not None else None

        pf_oos = float(c.profit_factor_oos) if c.profit_factor_oos is not None else (float(oos_m["profit_factor"]) if ("profit_factor" in oos_m and oos_m["profit_factor"] is not None) else None)
        dd_oos = float(c.max_dd_oos_pct) if c.max_dd_oos_pct is not None else (float(oos_m["max_drawdown_pct"]) if ("max_drawdown_pct" in oos_m and oos_m["max_drawdown_pct"] is not None) else 0.0)
        dd_is = float(c.max_dd_is_pct) if c.max_dd_is_pct is not None else (float(is_m["max_drawdown_pct"]) if ("max_drawdown_pct" in is_m and is_m["max_drawdown_pct"] is not None) else 0.0)
        trades_count_oos = int(c.trades_oos) if c.trades_oos is not None else (int(oos_m["trades"]) if "trades" in oos_m else 0)
        
        max_dd_floating_oos = float(sc.get("max_dd_floating_pct") or oos_m.get("max_dd_floating_pct") or sc.get("max_drawdown_floating_pct") or dd_oos)
        max_dd_realized_oos = float(sc.get("max_dd_realized_pct") or oos_m.get("max_dd_realized_pct") or sc.get("max_drawdown_realized_pct") or (dd_oos * 0.85 if dd_oos else 0.0))

        max_dd_floating_is = float(sc.get("max_dd_floating_is_pct") or is_m.get("max_dd_floating_pct") or is_m.get("max_drawdown_floating_pct") or dd_is)
        max_dd_realized_is = float(sc.get("max_dd_realized_is_pct") or is_m.get("max_dd_realized_pct") or is_m.get("max_drawdown_realized_pct") or (dd_is * 0.85 if dd_is else 0.0))

        if oos_m.get("trades_per_month") is not None:
            tpm = float(oos_m["trades_per_month"])
        elif oos_months > 0:
            tpm = round(trades_count_oos / oos_months, 2)
        else:
            tpm = None

        resolved_status = c.status or "REJECTED_SIN_EVIDENCIA"
        resolved_reason = c.status_reason or "Sin razón registrada"

        passed_count = sc.get("gates_passed_count")
        if passed_count is None:
            if "gates" in sc and isinstance(sc["gates"], list):
                passed_count = sum(1 for g in sc["gates"] if g.get("passed"))
            elif resolved_status in ("APPROVED", "ULTRA_CERTIFIED", "FUNDING_CERTIFIED"):
                passed_count = 11
            else:
                import re
                m = re.search(r"(\d+)/11", resolved_reason)
                passed_count = int(m.group(1)) if m else None

        cand_tier = sc.get("tier")
        if not cand_tier:
            if passed_count == 11 or resolved_status in ("APPROVED", "ULTRA_CERTIFIED", "FUNDING_CERTIFIED"):
                cand_tier = "TIER_1_CERTIFIED"
                cand_tier_label = "🏆 Producción Certificada (11/11)"
            elif passed_count in (9, 10):
                cand_tier = "TIER_2_NEAR_CERTIFIED"
                cand_tier_label = "💎 Diamante en I+D (9-10/11)"
            elif passed_count is not None and passed_count >= 5:
                cand_tier = "TIER_3_INCUBATOR"
                cand_tier_label = "🧪 Incubadora de I+D (5-8/11)"
            else:
                cand_tier = "TIER_4_REJECTED"
                cand_tier_label = "❌ Rechazada Estructural (<5/11)"
        else:
            cand_tier_label = sc.get("tier_label") or ("🏆 Producción Certificada" if cand_tier == "TIER_1_CERTIFIED" else ("💎 Diamante en I+D" if cand_tier == "TIER_2_NEAR_CERTIFIED" else ("🧪 Incubadora de I+D" if cand_tier == "TIER_3_INCUBATOR" else "❌ Rechazada Estructural")))

        if tier and tier.upper() != "ALL":
            if tier.upper() != cand_tier:
                continue

        duration_info_payload = dur if dur else {
            "total_bars": total_bars,
            "total_months": calc_months,
            "total_years": round(calc_months / 12.0, 1),
            "oos_months": oos_months,
            "oos_days": int(oos_months * 30),
        }

        spec = get_market_spec(c.symbol)
        results.append({
            "candidate_id": c.candidate_id,
            "name": c.name,
            "route": c.route,
            "symbol": c.symbol,
            "timeframe": c.timeframe,
            "market_category": spec.category,
            "icon": spec.icon,
            "prop_firm_eligible": spec.prop_firm_eligible,
            "prop_firm_venues": spec.prop_firm_venues,
            "dataset_id": c.dataset_id,
            "status": resolved_status,
            "status_reason": resolved_reason,
            "tier": cand_tier,
            "tier_label": cand_tier_label,
            "gates_passed_count": passed_count,
            "can_reprogram": (cand_tier in ("TIER_2_NEAR_CERTIFIED", "TIER_3_INCUBATOR")),
            "prescriptions": sc.get("prescriptions", []),
            "archetype": sc.get("archetype") or "QUANT_PATTERN",
            "scorecard_json": c.scorecard_json,
            "duration_info": duration_info_payload,
            "profit_factor_oos": pf_oos,
            "max_dd_oos_pct": dd_oos,
            "max_dd_floating_pct": max_dd_floating_oos,
            "max_dd_realized_pct": max_dd_realized_oos,
            "net_profit_oos": net_prof_oos,
            "win_rate_pct": wr_oos,
            "trades_oos": trades_count_oos,
            "metrics": {
                "in_sample": {
                    "net_profit_usd": c.net_profit_is if c.net_profit_is is not None else is_m.get("net_profit_usd"),
                    "trades": c.trades_is if c.trades_is is not None else is_m.get("trades"),
                    "profit_factor": c.profit_factor_is if c.profit_factor_is is not None else is_m.get("profit_factor"),
                    "max_drawdown_pct": dd_is,
                    "max_dd_floating_pct": max_dd_floating_is,
                    "max_dd_realized_pct": max_dd_realized_is,
                    "win_rate_pct": wr_is,
                },
                "out_of_sample": {
                    "net_profit_usd": net_prof_oos,
                    "roi_pct": roi_oos,
                    "annualized_roi_pct": ann_roi,
                    "monthly_roi_pct": monthly_roi,
                    "trades_per_month": tpm,
                    "base_capital_usd": base_cap,
                    "trades": trades_count_oos,
                    "profit_factor": pf_oos,
                    "win_rate_pct": wr_oos,
                    "max_drawdown_pct": dd_oos,
                    "max_dd_floating_pct": max_dd_floating_oos,
                    "max_dd_realized_pct": max_dd_realized_oos,
                    "oos_months": oos_months,
                },
                "anti_overfit": {
                    "ratio_oos_is": c.ratio_oos_is,
                    "wfo_pass_pct": c.wfo_pass_pct,
                    "monte_carlo_score": c.monte_carlo_score,
                }
            },
            "engine_version": getattr(c, "engine_version", None) or CURRENT_ENGINE_VERSION,
            "validation_pipeline_version": getattr(c, "validation_pipeline_version", None) or CURRENT_ENGINE_VERSION,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })
        
        if len(results) >= offset + limit:
            break

    return results[offset : offset + limit]


@candidates_router.get("/{candidate_id}")
def get_candidate(candidate_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get single strategy candidate scorecard and validation details."""
    c = db.query(CandidateModel).filter(CandidateModel.candidate_id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="CANDIDATE_NOT_FOUND")

    sc = {}
    if c.scorecard_json:
        try:
            sc = json.loads(c.scorecard_json)
        except Exception:
            sc = {}

    is_m = sc.get("is_metrics") or {}
    oos_m = sc.get("oos_metrics") or {}
    dur = sc.get("duration_info") or {}

    is_fondeo = (c.route == "FONDEO")
    base_cap = float(sc.get("initial_capital_usd") or oos_m.get("account_base_usd") or (50000.0 if is_fondeo else 1000.0))
    net_prof_oos = float(c.net_profit_oos if c.net_profit_oos is not None else oos_m.get("net_profit_usd", 0.0))

    tf = (c.timeframe or "1h").lower()
    tf_bars_per_month = {"1m": 43200, "5m": 8640, "15m": 2880, "1h": 720, "4h": 180, "1d": 30}
    bars_per_m = tf_bars_per_month.get(tf, 720)
    total_bars = int(dur.get("total_bars") or 3840)
    calc_months = max(0.5, round(total_bars / bars_per_m, 1))
    oos_months = float(dur.get("oos_months") or oos_m.get("oos_months") or max(0.2, round(calc_months * 0.2, 1)))

    if "monthly_return_pct" in sc:
        monthly_roi = float(sc["monthly_return_pct"])
        ann_roi = float(sc.get("annual_return_pct", monthly_roi * 12.0))
    elif "monthly_roi_pct" in sc:
        monthly_roi = float(sc["monthly_roi_pct"])
        ann_roi = float(sc.get("annualized_roi_pct", monthly_roi * 12.0))
    elif "monthly_roi_pct" in oos_m:
        monthly_roi = float(oos_m["monthly_roi_pct"])
        ann_roi = float(oos_m.get("annualized_roi_pct", monthly_roi * 12.0))
    else:
        monthly_roi = round(((net_prof_oos / max(1.0, base_cap)) * 100.0) / max(0.2, oos_months), 2)
        ann_roi = round(monthly_roi * 12.0, 2)

    dd_oos = float(c.max_dd_oos_pct if c.max_dd_oos_pct is not None else (oos_m.get("max_drawdown_pct") or 0.0))
    dd_is = float(c.max_dd_is_pct if c.max_dd_is_pct is not None else (is_m.get("max_drawdown_pct") or 0.0))

    max_dd_floating_oos = float(sc.get("max_dd_floating_pct") or oos_m.get("max_dd_floating_pct") or sc.get("max_drawdown_floating_pct") or dd_oos)
    max_dd_realized_oos = float(sc.get("max_dd_realized_pct") or oos_m.get("max_dd_realized_pct") or sc.get("max_drawdown_realized_pct") or (dd_oos * 0.85 if dd_oos else 0.0))
    max_dd_floating_is = float(sc.get("max_dd_floating_is_pct") or is_m.get("max_dd_floating_pct") or is_m.get("max_drawdown_floating_pct") or dd_is)
    max_dd_realized_is = float(sc.get("max_dd_realized_is_pct") or is_m.get("max_dd_realized_pct") or is_m.get("max_drawdown_realized_pct") or (dd_is * 0.85 if dd_is else 0.0))

    return {
        "candidate_id": c.candidate_id,
        "name": c.name,
        "route": c.route,
        "symbol": c.symbol,
        "timeframe": c.timeframe,
        "dataset_id": c.dataset_id,
        "status": c.status,
        "status_reason": c.status_reason,
        "base_capital_usd": base_cap,
        "max_dd_floating_pct": max_dd_floating_oos,
        "max_dd_realized_pct": max_dd_realized_oos,
        "metrics": {
            "in_sample": {
                "net_profit_usd": c.net_profit_is,
                "trades": c.trades_is,
                "profit_factor": c.profit_factor_is,
                "max_drawdown_pct": dd_is,
                "max_dd_floating_pct": max_dd_floating_is,
                "max_dd_realized_pct": max_dd_realized_is,
            },
            "out_of_sample": {
                "net_profit_usd": c.net_profit_oos,
                "trades": c.trades_oos,
                "profit_factor": c.profit_factor_oos,
                "max_drawdown_pct": dd_oos,
                "max_dd_floating_pct": max_dd_floating_oos,
                "max_dd_realized_pct": max_dd_realized_oos,
                "monthly_roi_pct": monthly_roi,
                "annualized_roi_pct": ann_roi,
                "base_capital_usd": base_cap,
                "oos_months": oos_months,
            },
            "anti_overfit": {
                "ratio_oos_is": c.ratio_oos_is,
                "wfo_pass_pct": c.wfo_pass_pct,
                "monte_carlo_score": c.monte_carlo_score,
            }
        },
        "scorecard_json": c.scorecard_json,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }
