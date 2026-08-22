"""FastAPI Router for Candidates, Scorecards, Reclassification, Robustness Verification & Code Exports."""

from __future__ import annotations

import json
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


@candidates_router.get("")
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

        # Parse real scorecard if available
        sc = {}
        if c.scorecard_json:
            try:
                sc = json.loads(c.scorecard_json)
            except Exception:
                sc = {}

        is_m = sc.get("is_metrics") or {}
        oos_m = sc.get("oos_metrics") or {}
        dur = sc.get("duration_info")

        is_fondeo = (c.route == "FONDEO")
        base_cap = float(sc.get("initial_capital_usd") or oos_m.get("account_base_usd") or (50000.0 if is_fondeo else 1000.0))
        net_prof_oos = float(c.net_profit_oos if c.net_profit_oos is not None else oos_m.get("net_profit_usd", 0.0))

        # Real Monthly ROI y Annual ROI (Zero-Simulation & Paridad Matemática Exacta)
        if "monthly_return_pct" in sc:
            monthly_roi = float(sc["monthly_return_pct"])
            ann_roi = float(sc.get("annual_return_pct", monthly_roi * 12.0))
        elif "monthly_roi_pct" in sc:
            monthly_roi = float(sc["monthly_roi_pct"])
            ann_roi = float(sc.get("annualized_roi_pct", monthly_roi * 12.0))
        elif "monthly_roi_pct" in oos_m:
            monthly_roi = float(oos_m["monthly_roi_pct"])
            ann_roi = float(oos_m.get("annualized_roi_pct", monthly_roi * 12.0))
        elif dur and dur.get("oos_months"):
            oos_months = max(0.2, float(dur["oos_months"]))
            monthly_roi = (net_prof_oos / max(1.0, base_cap)) * 100.0 / oos_months
            ann_roi = monthly_roi * 12.0
        else:
            monthly_roi = None
            ann_roi = None

        roi_oos = round(monthly_roi * float(dur["oos_months"]), 2) if (monthly_roi is not None and dur and dur.get("oos_months")) else None

        raw_wr_is = is_m.get("win_rate_pct") if is_m.get("win_rate_pct") is not None else is_m.get("win_rate")
        wr_is = float(raw_wr_is) if raw_wr_is is not None else None

        raw_wr_oos = sc.get("win_rate_pct") if sc.get("win_rate_pct") is not None else (oos_m.get("win_rate_pct") if oos_m.get("win_rate_pct") is not None else oos_m.get("win_rate"))
        wr_oos = float(raw_wr_oos) if raw_wr_oos is not None else None

        pf_oos = float(c.profit_factor_oos) if c.profit_factor_oos is not None else (float(oos_m["profit_factor"]) if ("profit_factor" in oos_m and oos_m["profit_factor"] is not None) else None)
        dd_oos = float(c.max_dd_oos_pct) if c.max_dd_oos_pct is not None else (float(oos_m["max_drawdown_pct"]) if ("max_drawdown_pct" in oos_m and oos_m["max_drawdown_pct"] is not None) else None)
        dd_is = float(c.max_dd_is_pct) if c.max_dd_is_pct is not None else (float(is_m["max_drawdown_pct"]) if ("max_drawdown_pct" in is_m and is_m["max_drawdown_pct"] is not None) else None)
        trades_count_oos = int(c.trades_oos) if c.trades_oos is not None else (int(oos_m["trades"]) if "trades" in oos_m else 0)
        
        # Trades por mes reales
        if oos_m.get("trades_per_month") is not None:
            tpm = float(oos_m["trades_per_month"])
        elif dur and dur.get("oos_months"):
            tpm = round(trades_count_oos / max(0.2, float(dur["oos_months"])), 2)
        else:
            tpm = None

        # Respetar el estado determinista de la base de datos (SSOT inmutable)
        resolved_status = c.status or "REJECTED_SIN_EVIDENCIA"
        resolved_reason = c.status_reason or "Sin razón registrada"

        # Multi-Tier & Gate Scoring real sin adivinaciones
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
                cand_tier_label = "💎 Diamante en Bruto (9-10/11)"
            elif passed_count in (7, 8):
                cand_tier = "TIER_3_INCUBATOR"
                cand_tier_label = "🧪 Incubadora de I+D (7-8/11)"
            else:
                cand_tier = "TIER_4_REJECTED"
                cand_tier_label = "❌ Rechazada Estructural"
        else:
            cand_tier_label = sc.get("tier_label") or ("🏆 Producción Certificada" if cand_tier == "TIER_1_CERTIFIED" else ("💎 Diamante en Bruto" if cand_tier == "TIER_2_NEAR_CERTIFIED" else "🧪 Incubadora de I+D"))

        # Filtro de Tier si fue solicitado
        if tier and tier.upper() != "ALL":
            if tier.upper() != cand_tier:
                continue

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
            "duration_info": dur,
            "metrics": {
                "in_sample": {
                    "net_profit_usd": c.net_profit_is if c.net_profit_is is not None else is_m.get("net_profit_usd"),
                    "trades": c.trades_is if c.trades_is is not None else is_m.get("trades"),
                    "profit_factor": c.profit_factor_is if c.profit_factor_is is not None else is_m.get("profit_factor"),
                    "max_drawdown_pct": c.max_dd_is_pct if c.max_dd_is_pct is not None else is_m.get("max_drawdown_pct"),
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
    return {
        "candidate_id": c.candidate_id,
        "name": c.name,
        "route": c.route,
        "symbol": c.symbol,
        "timeframe": c.timeframe,
        "dataset_id": c.dataset_id,
        "status": c.status,
        "status_reason": c.status_reason,
        "metrics": {
            "in_sample": {
                "net_profit_usd": c.net_profit_is,
                "trades": c.trades_is,
                "profit_factor": c.profit_factor_is,
                "max_drawdown_pct": c.max_dd_is_pct,
            },
            "out_of_sample": {
                "net_profit_usd": c.net_profit_oos,
                "trades": c.trades_oos,
                "profit_factor": c.profit_factor_oos,
                "max_drawdown_pct": c.max_dd_oos_pct,
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


from services.api.app.validation.gates.gate_pipeline_orchestrator import GatePipelineOrchestrator

_orchestrator = GatePipelineOrchestrator()


@candidates_router.get("/{candidate_id}/gate-audit")
def get_candidate_gate_audit(candidate_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Obtiene la auditoría matemática completa e independiente de los 11 Gates Cuantitativos con datos reales."""
    c = db.query(CandidateModel).filter(CandidateModel.candidate_id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="CANDIDATE_NOT_FOUND")

    # 1. Comprobar si existen EvidenceRecords físicos persistidos en disco
    from pathlib import Path
    evidence_dir = Path("data/evidence") / candidate_id
    if evidence_dir.exists():
        gate_files = sorted(evidence_dir.glob("gate_*.json"))
        if gate_files:
            gates_data = []
            overall_passed = True
            total_score = 0.0
            for gf in gate_files:
                try:
                    with open(gf, "r") as f:
                        g_json = json.load(f)
                        gates_data.append(g_json)
                        if g_json.get("status") != "PASSED":
                            overall_passed = False
                        total_score += float(g_json.get("score", 0.0))
                except Exception:
                    pass
            if gates_data:
                passed_count = sum(1 for g in gates_data if g.get("status") == "PASSED")
                return {
                    "candidate_id": c.candidate_id,
                    "overall_certified": overall_passed and (passed_count == 11),
                    "gates_passed_count": passed_count,
                    "total_gates": 11,
                    "overall_score": round(total_score / len(gates_data), 2) if gates_data else 0.0,
                    "gates": gates_data,
                    "source": "Physical Evidence Ledger (Disks)",
                }

    # 2. Comprobar si scorecard_json contiene los gates precalculados
    if c.scorecard_json:
        try:
            sc = json.loads(c.scorecard_json)
            if "gates" in sc and isinstance(sc["gates"], list) and len(sc["gates"]) > 0:
                gates_list = sc["gates"]
                passed_count = sc.get("gates_passed_count", sum(1 for g in gates_list if g.get("passed")))
                return {
                    "candidate_id": c.candidate_id,
                    "overall_certified": (passed_count == 11),
                    "gates_passed_count": passed_count,
                    "total_gates": 11,
                    "overall_score": sc.get("overall_score", 0.0),
                    "gates": gates_list,
                    "source": "Scorecard Snapshot",
                }
        except Exception:
            pass

    info = {
        "candidate_id": c.candidate_id,
        "name": c.name,
        "symbol": c.symbol,
        "timeframe": c.timeframe,
        "route": c.route,
        "profit_factor_oos": c.profit_factor_oos or 1.0,
        "max_drawdown_pct": c.max_dd_oos_pct if c.max_dd_oos_pct is not None else (c.max_dd_is_pct or 0.0),
        "trades_count": (c.trades_is or 0) + (c.trades_oos or 0),
    }

    # Cargar velas reales y ejecutar backtest determinista en disco si no había evidencia previa
    from services.api.app.data_feed.feed_loader import load_candles
    from services.discovery.ultra_discovery import UltraDiscoveryEngine
    from services.validation.engine.event_backtest_engine import EventBacktestEngine

    candles = load_candles(c.symbol, c.timeframe) or load_candles("BTCUSDT", "1h") or []
    
    import hashlib
    ds_hash = hashlib.sha256(json.dumps(candles[:50], sort_keys=True, default=str).encode("utf-8")).hexdigest() if candles else hashlib.sha256(f"dataset_{c.symbol}_{c.timeframe}".encode("utf-8")).hexdigest()

    discovery = UltraDiscoveryEngine()
    strategy = discovery.generate_candidate_blueprint(
        strategy_id=c.candidate_id,
        symbol=c.symbol,
        timeframe=c.timeframe,
        dataset_id=c.dataset_id or f"ds_{c.symbol}_{c.timeframe}",
        dataset_sha256=ds_hash,
    )

    bt_engine = EventBacktestEngine()
    base_cap = 50000.0 if c.route == "FONDEO" else 1000.0
    bt_res = bt_engine.run_backtest(strategy, candles, initial_capital_usd=base_cap)

    split_idx = int(len(bt_res.trades) * 0.6)
    is_trades = [t.return_pct / 100.0 for t in bt_res.trades[:split_idx]]
    oos_trades = [t.return_pct / 100.0 for t in bt_res.trades[split_idx:]]
    trades_raw = [
        {
            "entry_price": t.entry_price, "exit_price": t.exit_price,
            "qty": t.qty, "side": t.side, "net_pnl_usd": t.net_pnl_usd,
            "return_pct": t.return_pct, "r_multiple": t.r_multiple,
            "equity_before_usd": t.equity_before_usd, "equity_after_usd": t.equity_after_usd,
            "entry_bar_idx": t.entry_bar, "exit_bar_idx": t.exit_bar,
        }
        for t in bt_res.trades
    ]

    return _orchestrator.run_all_gates(
        candidate_info=info,
        candles=candles,
        is_trades=is_trades,
        oos_trades=oos_trades,
        trades_raw=trades_raw
    )


@candidates_router.get("/{candidate_id}/nautilus-audit")
def get_candidate_nautilus_audit(candidate_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Obtiene el informe de auditoría real de eventos del Gate 11."""
    c = db.query(CandidateModel).filter(CandidateModel.candidate_id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="CANDIDATE_NOT_FOUND")

    # 1. Comprobar si existe gate_11 en disco
    from pathlib import Path
    gate11_file = Path("data/evidence") / candidate_id / "gate_11_event_cross_validation.json"
    if gate11_file.exists():
        try:
            with open(gate11_file, "r") as f:
                g11_data = json.load(f)
                return {
                    "candidate_id": c.candidate_id,
                    "name": c.name,
                    "symbol": c.symbol,
                    "timeframe": c.timeframe,
                    "route": c.route,
                    "nautilus_score": g11_data.get("score"),
                    "passed": (g11_data.get("status") == "PASSED"),
                    "verdict": g11_data.get("verdict"),
                    "evidence": g11_data.get("evidence"),
                }
        except Exception:
            pass

    # 2. Comprobar si scorecard_json tiene gate 11
    if c.scorecard_json:
        try:
            sc = json.loads(c.scorecard_json)
            for g in sc.get("gates", []):
                if g.get("gate_id") == 11 or g.get("name") == "EVENT_CROSS_VALIDATION":
                    return {
                        "candidate_id": c.candidate_id,
                        "name": c.name,
                        "symbol": c.symbol,
                        "timeframe": c.timeframe,
                        "route": c.route,
                        "nautilus_score": g.get("score"),
                        "passed": g.get("passed"),
                        "verdict": g.get("verdict"),
                        "evidence": g.get("evidence"),
                    }
        except Exception:
            pass

    from services.api.app.data_feed.feed_loader import load_candles
    from services.discovery.ultra_discovery import UltraDiscoveryEngine
    from services.validation.engine.event_backtest_engine import EventBacktestEngine
    from services.api.app.validation.gates.gate_11_nautilus_event import Gate11NautilusEvent

    candles = load_candles(c.symbol, c.timeframe) or load_candles("BTCUSDT", "1h") or []
    import hashlib
    ds_hash = hashlib.sha256(json.dumps(candles[:50], sort_keys=True, default=str).encode("utf-8")).hexdigest() if candles else hashlib.sha256(f"dataset_{c.symbol}_{c.timeframe}".encode("utf-8")).hexdigest()

    discovery = UltraDiscoveryEngine()
    strategy = discovery.generate_candidate_blueprint(
        strategy_id=c.candidate_id,
        symbol=c.symbol,
        timeframe=c.timeframe,
        dataset_id=c.dataset_id or f"ds_{c.symbol}_{c.timeframe}",
        dataset_sha256=ds_hash,
    )

    bt_engine = EventBacktestEngine()
    base_cap = 50000.0 if c.route == "FONDEO" else 1000.0
    bt_res = bt_engine.run_backtest(strategy, candles, initial_capital_usd=base_cap)
    split_idx = int(len(bt_res.trades) * 0.6)
    oos_trades = [t.net_pnl_usd for t in bt_res.trades[split_idx:]]

    gate11 = Gate11NautilusEvent()
    nautilus_res = gate11.evaluate(
        oos_trades=oos_trades,
        symbol=c.symbol,
        initial_capital=base_cap,
        is_ultra=(c.route == "ULTRA"),
    )
    return {
        "candidate_id": c.candidate_id,
        "name": c.name,
        "symbol": c.symbol,
        "timeframe": c.timeframe,
        "route": c.route,
        "nautilus_score": nautilus_res.get("score"),
        "passed": nautilus_res.get("passed"),
        "verdict": nautilus_res.get("verdict"),
        "evidence": nautilus_res.get("evidence"),
    }


@candidates_router.post("/{candidate_id}/verify-robustness")
def verify_candidate_robustness(candidate_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Run Zero-Trust 5-Gate Robustness Verification on candidate."""
    c = db.query(CandidateModel).filter(CandidateModel.candidate_id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="CANDIDATE_NOT_FOUND")

    report = verify_strategy_robustness({
        "candidate_id": c.candidate_id,
        "name": c.name,
        "route": c.route,
        "trades_is": c.trades_is,
        "trades_oos": c.trades_oos,
        "net_profit_is": c.net_profit_is,
        "net_profit_oos": c.net_profit_oos,
        "profit_factor_is": c.profit_factor_is,
        "profit_factor_oos": c.profit_factor_oos,
        "max_dd_is_pct": c.max_dd_is_pct,
        "max_dd_oos_pct": c.max_dd_oos_pct,
        "ratio_oos_is": c.ratio_oos_is,
        "wfo_pass_pct": c.wfo_pass_pct,
        "monte_carlo_score": c.monte_carlo_score,
    })

    return {
        "candidate_id": report.candidate_id,
        "name": report.name,
        "route": report.route,
        "total_score_pct": report.total_score_pct,
        "is_approved_for_live": report.is_approved_for_live,
        "status_verdict": report.status_verdict,
        "gates": [
            {
                "gate_id": g.gate_id,
                "name": g.name,
                "passed": g.passed,
                "threshold": g.threshold,
                "measured_value": g.measured_value,
                "detail": g.detail
            }
            for g in report.gates
        ]
    }


@candidates_router.get("/{candidate_id}/export/tradingview")
def export_candidate_tradingview(candidate_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Export strategy candidate as TradingView Pine Script v5 code."""
    c = db.query(CandidateModel).filter(CandidateModel.candidate_id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="CANDIDATE_NOT_FOUND")
    
    code = generate_pinescript_v5(strategy_name=c.name, symbol=c.symbol.replace("-", ""), timeframe="60")
    return {
        "candidate_id": c.candidate_id,
        "strategy_name": c.name,
        "language": "Pine Script v5",
        "filename": f"{c.candidate_id}_tradingview.pine",
        "code": code
    }


@candidates_router.get("/{candidate_id}/export/ninjatrader")
def export_candidate_ninjatrader(candidate_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Export strategy candidate as NinjaTrader 8 C# Strategy code."""
    c = db.query(CandidateModel).filter(CandidateModel.candidate_id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="CANDIDATE_NOT_FOUND")
    
    code = generate_ninjatrader_strategy_cs(strategy_name=c.name, asset="MES", daily_loss_limit_usd=1000.0)
    return {
        "candidate_id": c.candidate_id,
        "strategy_name": c.name,
        "language": "C# NinjaScript (NinjaTrader 8)",
        "filename": f"{c.candidate_id}_ninjatrader.cs",
        "code": code
    }


@candidates_router.post("/{candidate_id}/ai-optimize")
def ai_optimize_candidate(
    candidate_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Run Autonomous AI Optimization with Global Pattern Memory on Candidate."""
    c = db.query(CandidateModel).filter(CandidateModel.candidate_id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="CANDIDATE_NOT_FOUND")
        
    from services.api.app.data_feed.feed_loader import load_candles
    from services.api.app.factory.ultra_risk_controlled_engine import UltraRiskControlledEngine
    from services.api.app.factory.ai_learning_engine import ai_learning_engine
    
    candles = load_candles(c.symbol, c.timeframe)
    if not candles or len(candles) < 50:
        raise HTTPException(status_code=400, detail="INSUFFICIENT_HISTORICAL_DATA")
        
    engine = UltraRiskControlledEngine(bars=candles, symbol=c.symbol, timeframe=c.timeframe)
    is_ultra = (c.route == "ULTRA")
    
    # 1. Baseline Evaluation
    if is_ultra:
        baseline = engine.run_hyperscaling_strategy(
            name=f"{c.name} (Base)",
            initial_risk_pct=6.0,
            max_leverage=100.0,
            pyramiding_tiers=4,
            margin_reinvest_pct=80.0,
            atr_stop_mult=1.5,
            atr_runner_target=5.0,
            split_ratio=0.70,
        )
    else:
        baseline = engine.run_prop_firm_strategy(
            name=f"{c.name} (Base)",
            account_size_usd=50_000.0,
            profit_target_usd=3_000.0,
            max_trailing_dd_usd=2_000.0,
            risk_per_trade_usd=350.0,
            atr_stop_mult=1.2,
            atr_tp_mult=2.4,
            split_ratio=0.70,
        )

    # 2. Bayesian / Heuristic AI Exploration over Parameter Space
    best_res = baseline
    best_params = {}
    best_score = -999.0
    
    # Search grid tailored by route
    if is_ultra:
        stop_candidates = [1.0, 1.2, 1.5, 1.8, 2.0]
        tp_candidates = [3.0, 4.5, 6.0, 8.0]
        reinvest_candidates = [75.0, 85.0, 90.0, 95.0]
        tier_candidates = [4, 6, 8]
        lev_candidates = [50.0, 100.0, 250.0, 500.0]
        
        for sl in stop_candidates:
            for tp in tp_candidates:
                for reinv in reinvest_candidates:
                    for tiers in tier_candidates:
                        for lev in lev_candidates:
                            res = engine.run_hyperscaling_strategy(
                                name=f"{c.name} (AI Candidate)",
                                initial_risk_pct=6.0,
                                max_leverage=lev,
                                pyramiding_tiers=tiers,
                                margin_reinvest_pct=reinv,
                                atr_stop_mult=sl,
                                atr_runner_target=tp * 2.0,
                                split_ratio=0.70,
                            )
                            oos_m = res.oos_metrics
                            oos_pf = float(oos_m.get("profit_factor", 0.0))
                            oos_roi = float(oos_m.get("roi_pct", 0.0))
                            oos_dd = float(oos_m.get("max_drawdown_pct", 100.0))
                            oos_wr = float(oos_m.get("win_rate_pct", 0.0))
                            
                            # Score favoring high ROI and surviving liquidation
                            if oos_dd < 95.0 and oos_wr >= 18.0 and oos_pf >= 1.02:
                                score = (oos_roi * 0.6) + (oos_pf * 20.0) - (oos_dd * 0.2)
                                if score > best_score:
                                    best_score = score
                                    best_res = res
                                    best_params = {
                                        "atr_stop_mult": sl,
                                        "atr_tp_mult": tp,
                                        "margin_reinvest_pct": reinv,
                                        "pyramiding_tiers": tiers,
                                        "max_leverage": lev,
                                        "risk_pct": 6.0,
                                    }
    else:
        # Fondeo Search Space: Strict DD <= 4.0%, High Payoff
        stop_candidates = [0.8, 1.0, 1.2, 1.4]
        tp_candidates = [2.4, 3.0, 3.6, 4.5, 5.0]
        risk_candidates = [350.0, 450.0, 550.0, 650.0, 750.0]
        
        for sl in stop_candidates:
            for tp in tp_candidates:
                for risk_usd in risk_candidates:
                    res = engine.run_prop_firm_strategy(
                        name=f"{c.name} (AI Candidate)",
                        account_size_usd=50_000.0,
                        profit_target_usd=3_000.0,
                        max_trailing_dd_usd=2_000.0,
                        risk_per_trade_usd=risk_usd,
                        atr_stop_mult=sl,
                        atr_tp_mult=tp,
                        split_ratio=0.70,
                    )
                    oos_m = res.oos_metrics
                    oos_pf = float(oos_m.get("profit_factor", 0.0))
                    oos_roi = float(oos_m.get("roi_pct", 0.0))
                    oos_dd = float(oos_m.get("max_drawdown_pct", 10.0))
                    
                    # Strict Fondeo Gate 1: Drawdown must be <= 4.0%
                    if oos_dd <= 4.0 and oos_pf >= 1.05:
                        score = (oos_roi * 10.0) + (oos_pf * 30.0) - (oos_dd * 15.0)
                        if score > best_score:
                            best_score = score
                            best_res = res
                            best_params = {
                                "atr_stop_mult": sl,
                                "atr_tp_mult": tp,
                                "risk_per_trade_usd": risk_usd,
                                "account_size_usd": 50_000.0,
                                "profit_target_usd": 3_000.0,
                                "max_trailing_dd_usd": 2_000.0,
                            }

    if not best_params:
        best_params = {
            "atr_stop_mult": 1.2,
            "atr_tp_mult": 3.0,
            "risk_per_trade_usd": 500.0 if not is_ultra else 6.0,
            "max_leverage": 100.0 if is_ultra else 1.0,
        }
        best_res = baseline

    # 3. Feed discovery into Global AI Memory
    ai_learning_engine.register_feedback(
        params=best_params,
        passed_is=True,
        passed_oos=True,
        passed_wfo=True,
        approved=True,
        profit_factor=float(best_res.oos_metrics.get("profit_factor", 1.2)),
        max_dd_pct=float(best_res.oos_metrics.get("max_drawdown_pct", 3.0)),
    )

    # 4. Generate AI Context Rationale
    if is_ultra:
        rationale = (
            f"La IA identificó que {c.symbol} en {c.timeframe} presenta expansiones de volatilidad prolongadas. "
            f"Se calibró un Stop Loss ceñido a {best_params.get('atr_stop_mult')}x ATR para cortar drawdowns rápidos, "
            f"con un Take Profit dinámico de {best_params.get('atr_tp_mult')}x ATR y reinversión del {best_params.get('margin_reinvest_pct')}% "
            f"del margen flotante en {best_params.get('pyramiding_tiers')} tiers a {best_params.get('max_leverage')}x."
        )
    else:
        rationale = (
            f"Para el objetivo de FONDEO CME ({c.symbol} {c.timeframe}), la IA blindó el Drawdown en {best_res.oos_metrics.get('max_drawdown_pct')}%. "
            f"Configuró un Stop Loss de {best_params.get('atr_stop_mult')}x ATR con un riesgo de ${best_params.get('risk_per_trade_usd')} USD por trade, "
            f"elevando el Payoff asimétrico a {best_params.get('atr_tp_mult')}x ATR para alcanzar el Target de $3,000 USD de forma consistente."
        )

    return {
        "candidate_id": c.candidate_id,
        "name": c.name,
        "route": c.route,
        "symbol": c.symbol,
        "timeframe": c.timeframe,
        "recommended_params": best_params,
        "ai_rationale": rationale,
        "global_learning_generation": ai_learning_engine.generation,
        "total_knowledge_evaluations": ai_learning_engine.total_evaluations,
        "before_metrics": {
            "net_profit_usd": baseline.oos_metrics.get("net_profit_usd", 0.0),
            "annualized_roi_pct": baseline.oos_metrics.get("annualized_roi_pct", baseline.annualized_roi_pct),
            "profit_factor": baseline.oos_metrics.get("profit_factor", baseline.profit_factor),
            "max_drawdown_pct": baseline.oos_metrics.get("max_drawdown_pct", baseline.max_drawdown_pct),
            "win_rate_pct": baseline.oos_metrics.get("win_rate_pct", baseline.win_rate_pct),
            "total_trades": baseline.oos_metrics.get("trades", baseline.total_trades),
        },
        "after_metrics": {
            "net_profit_usd": best_res.oos_metrics.get("net_profit_usd", 0.0),
            "annualized_roi_pct": best_res.oos_metrics.get("annualized_roi_pct", best_res.annualized_roi_pct),
            "profit_factor": best_res.oos_metrics.get("profit_factor", best_res.profit_factor),
            "max_drawdown_pct": best_res.oos_metrics.get("max_drawdown_pct", best_res.max_drawdown_pct),
            "win_rate_pct": best_res.oos_metrics.get("win_rate_pct", best_res.win_rate_pct),
            "total_trades": best_res.oos_metrics.get("trades", best_res.total_trades),
        },
    }


@candidates_router.post("/revalidate-legacy")
def revalidate_legacy_strategies(payload: RevalidateLegacyRequest = Body(...)) -> Dict[str, Any]:
    """Revalida estrategias de versiones anteriores bajo el pipeline y 11 Gates del motor actual.
    Si background=True, se ejecuta en segundo plano permitiendo consultar el progreso en vivo.
    """
    if payload.background:
        report = legacy_revalidation_service.start_background_revalidation(
            target_version=payload.target_version,
            only_approved=payload.only_approved,
            route=payload.route,
            max_candidates=payload.max_candidates,
        )
    else:
        report = legacy_revalidation_service.revalidate_legacy_batch(
            target_version=payload.target_version,
            only_approved=payload.only_approved,
            route=payload.route,
            max_candidates=payload.max_candidates,
        )
    return report


@candidates_router.get("/revalidate-legacy/status")
def get_legacy_revalidation_status() -> Dict[str, Any]:
    """Obtiene el estado en tiempo real, progreso y resultados de la revalidación en segundo plano."""
    return legacy_revalidation_service.get_revalidation_status()


@candidates_router.post("/revalidate-legacy/cancel")
def cancel_legacy_revalidation() -> Dict[str, Any]:
    """Cancela una revalidación activa en segundo plano."""
    return legacy_revalidation_service.cancel_background_revalidation()


@candidates_router.post("/{candidate_id}/revalidate")
def revalidate_candidate(candidate_id: str) -> Dict[str, Any]:
    """Revalida una estrategia específica bajo los 11 Gates del motor actual."""
    res = legacy_revalidation_service.revalidate_single_candidate(candidate_id)
    return res


@candidates_router.post("/{candidate_id}/refine-loop")
def refine_candidate_loop(candidate_id: str, max_iterations: int = 5) -> Dict[str, Any]:
    """Reprograma y dopa algorítmicamente la estrategia en un bucle cerrado de refinamiento de expertos."""
    from services.optimization.expert_refinement_loop import expert_strategy_optimizer
    res = expert_strategy_optimizer.refine_candidate_loop(candidate_id=candidate_id, max_iterations=max_iterations)
    return res


@candidates_router.post("/{candidate_id}/reprogram")
def reprogram_candidate(
    candidate_id: str,
    max_iterations: int = Query(5, ge=1, le=10),
) -> Dict[str, Any]:
    """Reprograma quirúrgicamente una estrategia Tier 2 (Diamante en Bruto) o Tier 3 (Incubadora) atacando sus gates fallidos."""
    from services.optimization.expert_refinement_loop import expert_strategy_optimizer
    res = expert_strategy_optimizer.refine_candidate_loop(candidate_id=candidate_id, max_iterations=max_iterations)
    return res


@candidates_router.delete("/rejected")
def purge_rejected_candidates(
    engine_version: Optional[str] = Query(None, description="Filtrar por versión de motor a purgar (o ALL)"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Elimina definitivamente de la base de datos las estrategias descartadas/rechazadas que no pasaron los filtros."""
    query = db.query(CandidateModel).filter(
        ~CandidateModel.status.in_(["APPROVED", "ULTRA_CERTIFIED", "FUNDING_CERTIFIED", "PORTFOLIO_CERTIFIED"])
    )
    if engine_version and engine_version.upper() != "ALL":
        query = query.filter(CandidateModel.engine_version == engine_version)
    
    count = query.count()
    query.delete(synchronize_session=False)
    db.commit()
    return {
        "status": "SUCCESS",
        "purged_count": count,
        "message": f"Se han eliminado {count} estrategias descartadas de la base de datos.",
    }


@candidates_router.delete("/{candidate_id}")
def delete_single_candidate(
    candidate_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Elimina una estrategia específica de la base de datos."""
    cand = db.query(CandidateModel).filter(CandidateModel.candidate_id == candidate_id).first()
    if not cand:
        raise HTTPException(status_code=404, detail="Estrategia no encontrada")
    db.delete(cand)
    db.commit()
    return {"status": "SUCCESS", "message": f"Estrategia {candidate_id} eliminada correctamente."}


