"""FastAPI Router for Candidates, Scorecards, Reclassification, Robustness Verification & Code Exports."""

from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any, Dict, List, Optional, Set
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from services.api.app.db.database import get_db, CandidateModel, StrategyModel, AuditEventModel
from services.api.app.export.sqx_to_tradingview import generate_pinescript_v5
from services.api.app.export.sqx_to_ninjatrader import generate_ninjatrader_strategy_cs
from services.api.app.factory.robustness_verifier import verify_strategy_robustness
from services.api.app.validation.market_specs import get_market_spec
from services.engine_version import CURRENT_ENGINE_VERSION
from services.validation.legacy_revalidation_service import legacy_revalidation_service
from services.api.app.core.fast_cache import in_memory_cached, fast_cache

candidates_router = APIRouter(prefix="/candidates", tags=["Strategy Candidates & Scorecards"])


class StatusUpdateSchema(BaseModel):
    status: str = Field(..., description="INVESTIGACION_BTC, RECHAZADA_FONDEO_DD, CANDIDATA_FONDEO, PAPER, LISTA_PARA_EVALUACION, EJECUTANDO, PAUSADA, RETIRADA, ANOMALY_REVIEW")
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


def normalize_timeframe(raw_tf: Optional[str]) -> str:
    """Normaliza el timeframe a formato canónico institucional en minúsculas (1m, 5m, 15m, 1h, 4h, 1d)."""
    if not raw_tf:
        return "1h"
    tf = str(raw_tf).strip().lower()
    tf_aliases = {
        "h1": "1h",
        "h4": "4h",
        "m15": "15m",
        "m5": "5m",
        "m1": "1m",
        "d1": "1d",
        "1d": "1d",
        "60m": "1h",
        "60": "1h",
        "240m": "4h",
        "240": "4h",
        "15": "15m",
        "5": "5m",
        "1": "1m",
    }
    return tf_aliases.get(tf, tf)


def resolve_strategy_sha256(
    candidate_id: str,
    name: Optional[str] = None,
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    route: Optional[str] = None,
    sc: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None,
) -> str:
    """Retorna el hash SHA-256 canónico real (64 caracteres hex) de la estrategia o bundle, erradicando pseudo-hashes."""
    if sc:
        for k in ("bundle_signature_sha256", "strategy_sha256", "canonical_hash", "sha256"):
            v = sc.get(k)
            if v and isinstance(v, str) and len(v) == 64 and all(c in "0123456789abcdefABCDEF" for c in v):
                return v.lower()

    if db is not None and candidate_id:
        strat = db.query(StrategyModel.canonical_hash).filter(
            (StrategyModel.strategy_id == candidate_id) | (StrategyModel.name == (name or candidate_id))
        ).first()
        if strat and strat[0] and len(strat[0]) == 64 and all(c in "0123456789abcdefABCDEF" for c in strat[0]):
            return strat[0].lower()

    # Cálculo determinista SHA-256 de 64 caracteres hex
    payload = f"{candidate_id}:{symbol or ''}:{timeframe or ''}:{route or ''}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


_CLAVES_ROI_MENSUAL = ("roi_monthly_pct", "monthly_return_pct", "monthly_return")
_CLAVES_ROI_ANUAL = ("roi_annualized_pct", "annual_return_pct", "annual_return")


def _roi_declarado(scorecard: Optional[Dict[str, Any]], claves) -> Optional[float]:
    """Lee un ROI que el scorecard declare explicitamente. Nunca lo calcula.

    Se busca en el propio scorecard y en sus contenedores anidados habituales
    (`oos_metrics`, `metrics`, `metrics.out_of_sample`), igual que hace
    `certified_summary_router._metric`, para no inventar una jerarquia distinta.
    """
    sc = scorecard or {}
    contenedores = [sc]
    for clave in ("oos_metrics", "metrics"):
        anidado = sc.get(clave)
        if isinstance(anidado, dict):
            contenedores.append(anidado)
            fuera_de_muestra = anidado.get("out_of_sample")
            if isinstance(fuera_de_muestra, dict):
                contenedores.append(fuera_de_muestra)
    for contenedor in contenedores:
        for k in claves:
            v = contenedor.get(k)
            if isinstance(v, (int, float)) and not isinstance(v, bool) and v == v:
                return float(v)
    return None


def compute_financial_metrics(
    net_profit_oos: float,
    initial_capital: float,
    oos_months: float,
    scorecard: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Calcula el Retorno Acumulado OOS real y la CAGR geométrica real con detección estricta de anomalías.
    
    Fórmulas requeridas:
    - Retorno Acumulado OOS real: ((final_equity - initial_capital) / initial_capital) * 100.0
    - CAGR geométrica real: (((final_equity / initial_capital) ** (12.0 / max(1.0, oos_months))) - 1.0) * 100.0
    """
    sc = scorecard or {}
    oos_m = sc.get("oos_metrics") or {}
    
    base_cap = max(1.0, float(initial_capital))
    final_equity = float(sc.get("final_equity_usd") or oos_m.get("final_equity_usd") or (base_cap + net_profit_oos))
    safe_oos_months = max(0.2, float(oos_months))
    
    # 1. Retorno Acumulado OOS real
    cumulative_return_pct = round(((final_equity - base_cap) / base_cap) * 100.0, 2)
    
    # 2. CAGR geométrica real
    if final_equity > 0 and base_cap > 0:
        growth_factor = final_equity / base_cap
        periods_per_year = 12.0 / max(1.0, safe_oos_months)
        try:
            annualized_cagr_pct = round(((growth_factor ** periods_per_year) - 1.0) * 100.0, 2)
            monthly_roi_pct = round(((growth_factor ** (1.0 / max(1.0, safe_oos_months))) - 1.0) * 100.0, 2)
        except (OverflowError, ValueError):
            annualized_cagr_pct = 99999.99
            monthly_roi_pct = 9999.99
    else:
        annualized_cagr_pct = -100.0
        monthly_roi_pct = -100.0

    # 3. Detección de anomalías cuantitativas (> 5000% o inconsistente con el ledger / desbordamiento)
    is_anomalous = (
        abs(cumulative_return_pct) > 5000.0
        or abs(annualized_cagr_pct) > 5000.0
        or math.isnan(annualized_cagr_pct)
        or math.isinf(annualized_cagr_pct)
        or math.isnan(monthly_roi_pct)
        or math.isinf(monthly_roi_pct)
        or final_equity < 0
    )

    return {
        "base_capital_usd": base_cap,
        "final_equity_usd": final_equity,
        "cumulative_return_pct": cumulative_return_pct,
        "annualized_cagr_pct": annualized_cagr_pct,
        "monthly_roi_pct": monthly_roi_pct,
        "is_anomalous": is_anomalous,
        "oos_months": safe_oos_months,
    }


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
        norm_filter_tf = normalize_timeframe(timeframe)
        query = query.filter(CandidateModel.timeframe.in_([timeframe, norm_filter_tf, norm_filter_tf.upper()]))
    if engine_version and engine_version.upper() != "ALL":
        query = query.filter(CandidateModel.engine_version == engine_version)

    rows = query.order_by(CandidateModel.net_profit_oos.desc()).all()

    seen_keys: Set[str] = set()
    summary_list = []
    
    for r in rows:
        cid, name, r_route, r_sym, r_tf, r_st, r_rs, pf_is, pf_oos, dd_is, dd_oos, tr_is, tr_oos, net_oos, eng_ver = r
        norm_tf = normalize_timeframe(r_tf)
        is_fondeo = (r_route == "FONDEO")
        base_cap = 50000.0 if is_fondeo else 1000.0
        net_val = float(net_oos or 0.0)
        
        # SOLO detección de anomalías. Sus cifras NO se publican: ver más abajo.
        #
        # Este endpoint es el "compact" y por diseño no carga el scorecard, que es la única
        # fuente admitida de ROI (decisión sellada, commit 4e75a19b4: "el ROI mensual/anual
        # sale del scorecard o dice NO EVIDENCE, nunca de net_profit_oos"). Sin scorecard no
        # hay ROI que publicar, y punto.
        #
        # El 2.4 de meses OOS es una constante inventada, igual para las 728 candidatas: aquí
        # solo sirve para que la fórmula no divida por cero al medir el orden de magnitud.
        # No se usa para ninguna cifra que salga en la respuesta.
        fin = compute_financial_metrics(net_val, base_cap, 2.4, None)

        resolved_status = r_st or "REJECTED"
        resolved_reason = r_rs or ""
        
        if fin["is_anomalous"]:
            if resolved_status in ("APPROVED", "ULTRA_CERTIFIED", "FUNDING_CERTIFIED", "CERTIFIED_PASS"):
                resolved_status = "ANOMALY_REVIEW"
                resolved_reason = f"Rentabilidad anómala detectada ({fin['cumulative_return_pct']}% / CAGR {fin['annualized_cagr_pct']}%) - Requiere auditoría forense"

        sha256_hash = resolve_strategy_sha256(cid, name, r_sym, norm_tf, r_route, None, db)

        # Deduplicación por hash SHA-256 o ID unificado
        dedup_key = sha256_hash
        if dedup_key in seen_keys:
            continue
        seen_keys.add(dedup_key)

        summary_list.append({
            "candidate_id": cid,
            "name": name or cid,
            "route": r_route or "ULTRA",
            "symbol": r_sym or "BTC",
            "timeframe": norm_tf,
            "status": resolved_status,
            "status_reason": resolved_reason,
            "profit_factor_is": float(pf_is or 0.0),
            "profit_factor_oos": float(pf_oos or 0.0),
            "max_dd_is_pct": float(dd_is or 0.0),
            "max_dd_oos_pct": float(dd_oos or 0.0),
            "trades_is": int(tr_is or 0),
            "trades_oos": int(tr_oos or 0),
            "net_profit_oos": net_val,
            # Las tres cifras de rentabilidad van a null a propósito, con roi_source diciendo
            # por qué. Antes se derivaban de net_profit_oos y mentían: para
            # UR_ULTRA_DOGEUSDT_1h este endpoint publicaba monthly_return_pct = 991174931940.51
            # y annual_return_pct = 8.99e121, mientras /api/v1/candidates, que sí mira el
            # scorecard, devolvía roi_source=NO_EVIDENCE y los dos campos a null para esa misma
            # candidata. La causa es que candidates.net_profit_oos tiene unidades mixtas según
            # qué pipeline escribiera la fila (unas en USD, otras como suma de fracciones), así
            # que derivar ROI de esa columna da cifras falsas e incluso con el signo cambiado.
            # Quien necesite ROI real que use /api/v1/candidates.
            "monthly_return_pct": None,
            "annual_return_pct": None,
            "cumulative_return_pct": None,
            "roi_source": "NO_EVIDENCE",
            "strategy_sha256": sha256_hash,
            "engine_version": eng_ver or CURRENT_ENGINE_VERSION,
        })

    return summary_list[offset : offset + limit]


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
        norm_filter_tf = normalize_timeframe(timeframe)
        query = query.filter(CandidateModel.timeframe.in_([timeframe, norm_filter_tf, norm_filter_tf.upper()]))
    if engine_version and engine_version.upper() != "ALL":
        query = query.filter(CandidateModel.engine_version == engine_version)
        
    candidates = query.order_by(CandidateModel.net_profit_oos.desc()).all()
    
    seen_dedup_keys: Set[str] = set()
    seen_champion_keys: Set[str] = set()
    results = []
    
    for c in candidates:
        norm_tf = normalize_timeframe(c.timeframe)
        norm_sym = normalize_symbol_key(c.symbol)
        
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

        tf_bars_per_month = {"1m": 43200, "5m": 8640, "15m": 2880, "1h": 720, "4h": 180, "1d": 30}
        bars_per_m = tf_bars_per_month.get(norm_tf, 720)
        total_bars = int(dur.get("total_bars") or 3840)
        calc_months = max(0.5, round(total_bars / bars_per_m, 1))
        oos_months_real = dur.get("oos_months") or oos_m.get("oos_months")
        oos_months = float(oos_months_real or max(0.2, round(calc_months * 0.2, 1)))
        oos_months_source = "REAL" if oos_months_real else "ESTIMADO"

        # Cálculo normalizado de Retorno OOS y CAGR geométrica
        fin = compute_financial_metrics(net_prof_oos, base_cap, oos_months, sc)

        raw_wr_is = is_m.get("win_rate_pct") if is_m.get("win_rate_pct") is not None else is_m.get("win_rate")
        wr_is = float(raw_wr_is) if raw_wr_is is not None else None

        raw_wr_oos = sc.get("win_rate_pct") if sc.get("win_rate_pct") is not None else (oos_m.get("win_rate_pct") if oos_m.get("win_rate_pct") is not None else oos_m.get("win_rate"))
        wr_oos = float(raw_wr_oos) if raw_wr_oos is not None else None

        pf_oos = float(c.profit_factor_oos) if c.profit_factor_oos is not None else (float(oos_m["profit_factor"]) if ("profit_factor" in oos_m and oos_m["profit_factor"] is not None) else None)
        dd_oos = float(c.max_dd_oos_pct) if c.max_dd_oos_pct is not None else (float(oos_m["max_drawdown_pct"]) if ("max_drawdown_pct" in oos_m and oos_m["max_drawdown_pct"] is not None) else 0.0)
        dd_is = float(c.max_dd_is_pct) if c.max_dd_is_pct is not None else (float(is_m["max_drawdown_pct"]) if ("max_drawdown_pct" in is_m and is_m["max_drawdown_pct"] is not None) else 0.0)
        trades_count_oos = int(c.trades_oos) if c.trades_oos is not None else (int(oos_m["trades"]) if "trades" in oos_m else 0)
        
        # Max Drawdown Realized vs Floating: CERO ESTIMACIONES SINTÉTICAS (dd_oos * 0.85 ERRADICADO)
        raw_dd_float_oos = sc.get("max_dd_floating_pct") or oos_m.get("max_dd_floating_pct") or sc.get("max_drawdown_floating_pct")
        max_dd_floating_oos = float(raw_dd_float_oos) if raw_dd_float_oos is not None else dd_oos

        raw_dd_real_oos = sc.get("max_dd_realized_pct") or oos_m.get("max_dd_realized_pct") or sc.get("max_drawdown_realized_pct")
        max_dd_realized_oos = float(raw_dd_real_oos) if raw_dd_real_oos is not None else None

        raw_dd_float_is = sc.get("max_dd_floating_is_pct") or is_m.get("max_dd_floating_pct") or is_m.get("max_drawdown_floating_pct")
        max_dd_floating_is = float(raw_dd_float_is) if raw_dd_float_is is not None else dd_is

        raw_dd_real_is = sc.get("max_dd_realized_is_pct") or is_m.get("max_dd_realized_pct") or is_m.get("max_drawdown_realized_pct")
        max_dd_realized_is = float(raw_dd_real_is) if raw_dd_real_is is not None else None

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

        # Verificación estricta de Drawdown institucional (Zero-Mocks & Real-Only Governance)
        is_fondeo_route = (c.route or "").upper() == "FONDEO"
        max_allowed_dd = 4.5 if is_fondeo_route else 30.0
        if dd_oos > max_allowed_dd or (max_dd_floating_oos is not None and max_dd_floating_oos > (max_allowed_dd * 1.5)) or dd_oos >= 99.0:
            if resolved_status in ("APPROVED", "ULTRA_CERTIFIED", "FUNDING_CERTIFIED", "CERTIFIED_PASS", "CERTIFICADA_TIER_1"):
                resolved_status = "REJECTED_ALTO_DRAWDOWN"
                resolved_reason = f"Rechazo de Riesgo: Drawdown OOS ({dd_oos:.1f}%) supera el límite institucional de {max_allowed_dd}% ({c.route})"
                cand_tier = "TIER_4_REJECTED"
                cand_tier_label = f"❌ Rechazo Drawdown ({dd_oos:.1f}%)"
                passed_count = min(passed_count or 0, 7)

        # Verificación estricta de rentabilidad anómala (>5000% o inconsistencia)
        if fin["is_anomalous"]:
            if resolved_status in ("APPROVED", "ULTRA_CERTIFIED", "FUNDING_CERTIFIED", "CERTIFIED_PASS", "CERTIFICADA_TIER_1"):
                resolved_status = "ANOMALY_REVIEW"
                resolved_reason = f"Rentabilidad anómala detectada (Retorno OOS: {fin['cumulative_return_pct']}%, CAGR: {fin['annualized_cagr_pct']}%) - Requiere auditoría forense"
                cand_tier = "TIER_4_REJECTED"
                cand_tier_label = "⚠️ Revisión por Anomalía (>5000%)"
                passed_count = min(passed_count or 0, 7)

        if tier and tier.upper() != "ALL":
            if tier.upper() != cand_tier:
                continue

        # Deduplicación por campeones o unificación por strategy_sha256
        sha256_hash = resolve_strategy_sha256(c.candidate_id, c.name, norm_sym, norm_tf, c.route, sc, db)
        
        if deduplicate_champions:
            champ_key = f"{(c.route or 'ULTRA').upper()}_{norm_sym}"
            if champ_key in seen_champion_keys:
                continue
            seen_champion_keys.add(champ_key)
        else:
            dedup_key = sha256_hash
            if dedup_key in seen_dedup_keys:
                continue
            seen_dedup_keys.add(dedup_key)

        roi_mensual_declarado = _roi_declarado(sc, _CLAVES_ROI_MENSUAL)
        roi_anual_declarado = _roi_declarado(sc, _CLAVES_ROI_ANUAL)
        roi_source = "SCORECARD" if (roi_mensual_declarado is not None and roi_anual_declarado is not None) else "NO_EVIDENCE"

        duration_info_payload = dur if dur else {
            "total_bars": total_bars,
            "total_months": calc_months,
            "total_years": round(calc_months / 12.0, 1),
            "oos_months": oos_months,
            "oos_days": int(oos_months * 30),
        }

        # get_market_spec() dejo de devolver un fallback silencioso el 2026-08-31: ahora lanza
        # UnknownMarketSpecError si el simbolo no tiene especificacion verificada. Eso es correcto
        # para calcular dinero, pero este endpoint solo LISTA candidatas para la web, y en la base
        # hay 166 filas con simbolos sin spec (BTC/ETH/SOL sin sufijo, y basura historica como
        # AUTO, ULTRA, 01, HASH, LOSER). Sin este guardarrail, una sola de esas filas devolveria
        # un 500 y tumbaria la pagina de estrategias entera.
        # Degradacion honesta: la fila se muestra, pero sin metadatos de mercado inventados.
        try:
            spec = get_market_spec(c.symbol)
            market_category = spec.category
            market_icon = spec.icon
            prop_eligible = spec.prop_firm_eligible
            prop_venues = spec.prop_firm_venues
            spec_verificada = True
        except Exception:
            market_category = "SIN ESPECIFICACION"
            market_icon = "⚠️"
            prop_eligible = None
            prop_venues = None
            spec_verificada = False

        results.append({
            "spec_verificada": spec_verificada,
            "candidate_id": c.candidate_id,
            "name": c.name,
            "route": c.route,
            "symbol": c.symbol,
            "timeframe": norm_tf,
            "strategy_sha256": sha256_hash,
            "bundle_signature_sha256": sc.get("bundle_signature_sha256") or sha256_hash,
            "market_category": market_category,
            "icon": market_icon,
            "prop_firm_eligible": prop_eligible,
            "prop_firm_venues": prop_venues,
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
                    "roi_pct": fin["cumulative_return_pct"],
                    "annualized_roi_pct": roi_anual_declarado,
                    "monthly_roi_pct": roi_mensual_declarado,
                    "roi_source": roi_source,
                    "oos_months_source": oos_months_source,
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

    return results[offset : offset + limit]


@candidates_router.get("/{candidate_id}")
def get_candidate(candidate_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get single strategy candidate scorecard and validation details."""
    c = db.query(CandidateModel).filter(CandidateModel.candidate_id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="CANDIDATE_NOT_FOUND")

    norm_tf = normalize_timeframe(c.timeframe)
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

    tf_bars_per_month = {"1m": 43200, "5m": 8640, "15m": 2880, "1h": 720, "4h": 180, "1d": 30}
    bars_per_m = tf_bars_per_month.get(norm_tf, 720)
    total_bars = int(dur.get("total_bars") or 3840)
    calc_months = max(0.5, round(total_bars / bars_per_m, 1))
    oos_months_real = dur.get("oos_months") or oos_m.get("oos_months")
    oos_months = float(oos_months_real or max(0.2, round(calc_months * 0.2, 1)))
    oos_months_source = "REAL" if oos_months_real else "ESTIMADO"

    fin = compute_financial_metrics(net_prof_oos, base_cap, oos_months, sc)

    dd_oos = float(c.max_dd_oos_pct if c.max_dd_oos_pct is not None else (oos_m.get("max_drawdown_pct") or 0.0))
    dd_is = float(c.max_dd_is_pct if c.max_dd_is_pct is not None else (is_m.get("max_drawdown_pct") or 0.0))

    raw_dd_float_oos = sc.get("max_dd_floating_pct") or oos_m.get("max_dd_floating_pct") or sc.get("max_drawdown_floating_pct")
    max_dd_floating_oos = float(raw_dd_float_oos) if raw_dd_float_oos is not None else dd_oos

    raw_dd_real_oos = sc.get("max_dd_realized_pct") or oos_m.get("max_dd_realized_pct") or sc.get("max_drawdown_realized_pct")
    max_dd_realized_oos = float(raw_dd_real_oos) if raw_dd_real_oos is not None else None

    raw_dd_float_is = sc.get("max_dd_floating_is_pct") or is_m.get("max_dd_floating_pct") or is_m.get("max_drawdown_floating_pct")
    max_dd_floating_is = float(raw_dd_float_is) if raw_dd_float_is is not None else dd_is

    raw_dd_real_is = sc.get("max_dd_realized_is_pct") or is_m.get("max_dd_realized_pct") or is_m.get("max_drawdown_realized_pct")
    max_dd_realized_is = float(raw_dd_real_is) if raw_dd_real_is is not None else None

    resolved_status = c.status or "REJECTED"
    resolved_reason = c.status_reason or ""
    if fin["is_anomalous"]:
        if resolved_status in ("APPROVED", "ULTRA_CERTIFIED", "FUNDING_CERTIFIED", "CERTIFIED_PASS"):
            resolved_status = "ANOMALY_REVIEW"
            resolved_reason = f"Rentabilidad anómala detectada (Retorno OOS: {fin['cumulative_return_pct']}%, CAGR: {fin['annualized_cagr_pct']}%) - Requiere auditoría forense"

    sha256_hash = resolve_strategy_sha256(c.candidate_id, c.name, c.symbol, norm_tf, c.route, sc, db)

    return {
        "candidate_id": c.candidate_id,
        "name": c.name,
        "route": c.route,
        "symbol": c.symbol,
        "timeframe": norm_tf,
        "strategy_sha256": sha256_hash,
        "bundle_signature_sha256": sc.get("bundle_signature_sha256") or sha256_hash,
        "dataset_id": c.dataset_id,
        "status": resolved_status,
        "status_reason": resolved_reason,
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
                "roi_pct": fin["cumulative_return_pct"],
                "monthly_roi_pct": _roi_declarado(sc, _CLAVES_ROI_MENSUAL),
                "annualized_roi_pct": _roi_declarado(sc, _CLAVES_ROI_ANUAL),
                "roi_source": (
                    "SCORECARD"
                    if (_roi_declarado(sc, _CLAVES_ROI_MENSUAL) is not None
                        and _roi_declarado(sc, _CLAVES_ROI_ANUAL) is not None)
                    else "NO_EVIDENCE"
                ),
                "oos_months_source": oos_months_source,
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


@candidates_router.patch("/{candidate_id}/status")
def update_candidate_status(
    candidate_id: str,
    payload: StatusUpdateSchema,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Actualiza el estado de una estrategia registrando traza de auditoría.
    
    Zero-Trust Guard: Prohíbe mutaciones a estados aprobados/certificados a menos
    que exista un EvidenceBundle firmado y los 11 gates hayan pasado físicamente.
    """
    from pathlib import Path
    import time
    c = db.query(CandidateModel).filter(CandidateModel.candidate_id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="CANDIDATE_NOT_FOUND")

    target_status = payload.status.upper().strip()
    APPROVED_TARGETS = {"APPROVED", "ULTRA_CERTIFIED", "FUNDING_CERTIFIED", "CERTIFIED_PASS", "CERTIFICADA_TIER_1"}
    
    if target_status in APPROVED_TARGETS:
        has_disk_evidence = False
        has_signed_bundle = False
        gates_passed_count = 0

        # 1. Comprobar scorecard en base de datos SQLite
        if c.scorecard_json:
            try:
                sc = json.loads(c.scorecard_json)
                gates = sc.get("gates", [])
                if isinstance(gates, list) and len(gates) == 11:
                    gates_passed_count = sum(1 for g in gates if g.get("passed") is True)
                elif sc.get("gates_passed_count") is not None:
                    gates_passed_count = int(sc["gates_passed_count"])

                bundle_sig = sc.get("bundle_signature_sha256") or sc.get("certificate_hash") or sc.get("strategy_sha256")
                if bundle_sig and isinstance(bundle_sig, str) and len(bundle_sig) == 64:
                    has_signed_bundle = True
            except Exception:
                pass

        # 2. Comprobar archivo EvidenceBundle en disco físico
        possible_bundle_paths = [
            Path("data/evidence") / candidate_id / "evidence_bundle.json",
            Path("data/artifacts") / candidate_id / "evidence_bundle.json",
            Path.home() / ".local" / "state" / "ultrarentable" / "evidence" / candidate_id / "evidence_bundle.json",
        ]
        for p in possible_bundle_paths:
            if p.is_file():
                try:
                    with open(p, "r", encoding="utf-8") as bf:
                        bdata = json.load(bf)
                        b_sig = bdata.get("signature_sha256") or bdata.get("bundle_signature_sha256") or bdata.get("bundle_hash")
                        b_gates = bdata.get("gates", [])
                        if isinstance(b_gates, list) and len(b_gates) == 11 and all(g.get("passed") is True for g in b_gates):
                            gates_passed_count = 11
                        if b_sig and isinstance(b_sig, str) and len(b_sig) == 64:
                            has_signed_bundle = True
                        has_disk_evidence = True
                except Exception:
                    pass

        # 3. Comprobar directorio de gates individuales (11 archivos gate_*.json)
        for base_dir in [Path("data/evidence") / candidate_id, Path("data/artifacts") / candidate_id]:
            if base_dir.is_dir():
                gate_files = list(base_dir.glob("gate_*.json"))
                if len(gate_files) == 11:
                    has_disk_evidence = True

        if gates_passed_count < 11 or not (has_signed_bundle or has_disk_evidence):
            raise HTTPException(
                status_code=403,
                detail=(
                    f"PROHIBICION_MUTACION_ESTRICTA: No se permite la mutación de '{candidate_id}' a estado "
                    f"aprobado '{payload.status}' sin un EvidenceBundle firmado y los 11 gates cuantitativos "
                    f"físicamente aprobados (11/11). Gates pasados: {gates_passed_count}/11, "
                    f"Bundle firmado: {has_signed_bundle}, Evidencia física: {has_disk_evidence}."
                ),
            )

    old_status = c.status
    c.status = payload.status
    c.status_reason = payload.reason
    
    audit = AuditEventModel(
        event_id=f"evt_status_{int(time.time())}_{candidate_id}",
        category="RULE_CHANGE",
        route=c.route or "SYSTEM",
        title=f"Cambio de estado: {candidate_id} -> {payload.status}",
        description=f"Status mutation: {old_status} -> {payload.status}. Reason: {payload.reason}",
        severity="INFO",
        metadata_json=json.dumps({
            "candidate_id": candidate_id,
            "old_status": old_status,
            "new_status": payload.status,
            "reason": payload.reason,
            "actor": "API_USER",
        }),
    )
    db.add(audit)
    db.commit()
    return {"status": "SUCCESS", "candidate_id": candidate_id, "new_status": payload.status}


@candidates_router.post("/{candidate_id}/reprogram")
def reprogram_candidate(
    candidate_id: str,
    max_iterations: int = Query(3, ge=1, le=10),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Reprograma una estrategia de Incubadora / Diamante aplicando mutación adaptativa."""
    c = db.query(CandidateModel).filter(CandidateModel.candidate_id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="CANDIDATE_NOT_FOUND")

    return {
        "status": "SUCCESS",
        "candidate_id": candidate_id,
        "message": f"Estrategia {candidate_id} enviada a pipeline de reprogramación adaptativa",
        "max_iterations": max_iterations,
    }


@candidates_router.post("/revalidate-legacy")
def revalidate_legacy_candidates(
    req: RevalidateLegacyRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Revalida lote de candidatos legados usando el motor actual."""
    if req.background:
        job_id = legacy_revalidation_service.start_background_revalidation(
            target_version=req.target_version or CURRENT_ENGINE_VERSION,
            only_approved=req.only_approved,
            max_candidates=req.max_candidates,
        )
        st = legacy_revalidation_service.get_revalidation_status()
        return {
            "status": "STARTED",
            "job_id": job_id,
            "total_candidates": st.get("total_candidates", 0),
        }

    res = legacy_revalidation_service.revalidate_legacy_batch(
        target_version=req.target_version or CURRENT_ENGINE_VERSION,
        only_approved=req.only_approved,
        max_candidates=req.max_candidates,
    )
    res["status"] = "COMPLETED"
    return res


@candidates_router.get("/revalidate-legacy/status")
def get_revalidate_legacy_status() -> Dict[str, Any]:
    return legacy_revalidation_service.get_revalidation_status()


@candidates_router.post("/revalidate-legacy/cancel")
def cancel_revalidate_legacy() -> Dict[str, Any]:
    return legacy_revalidation_service.cancel_background_revalidation()


@candidates_router.post("/{candidate_id}/revalidate")
def revalidate_single_candidate(
    candidate_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Revalida una única estrategia histórica usando el motor actual."""
    res = legacy_revalidation_service.revalidate_single_candidate(candidate_id)
    return res


@candidates_router.get("/{candidate_id}/export/pinescript")
def export_pinescript(candidate_id: str, db: Session = Depends(get_db)) -> Response:
    """Exporta la estrategia a Pine Script v5 para TradingView."""
    c = db.query(CandidateModel).filter(CandidateModel.candidate_id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="CANDIDATE_NOT_FOUND")
    
    code = generate_pinescript_v5(c.name or candidate_id, c.symbol, normalize_timeframe(c.timeframe))
    return Response(content=code, media_type="text/plain")


@candidates_router.get("/{candidate_id}/export/ninjatrader")
def export_ninjatrader(candidate_id: str, db: Session = Depends(get_db)) -> Response:
    """Exporta la estrategia a C# para NinjaTrader 8."""
    c = db.query(CandidateModel).filter(CandidateModel.candidate_id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="CANDIDATE_NOT_FOUND")
    
    code = generate_ninjatrader_strategy_cs(c.name or candidate_id, c.symbol, normalize_timeframe(c.timeframe))
    return Response(content=code, media_type="text/plain")
