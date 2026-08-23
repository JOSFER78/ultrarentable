"""services/portfolio/portfolio_router.py
Router FastAPI para PortfolioEngine, MetaStrategyEngine, AutonomousMetaDaemon y Tabla Canónica de Meta-Estrategias.

DOCTRINA ZERO-MOCKS & REAL-ONLY:
- Endpoints 100% conectados a SQLite WAL y matrices de covarianza reales.
- Motor Autónomo 24/7 de Exploración y Auto-Optimización de Meta-Estrategias.
- Tabla Canónica de Meta-Estrategias con todas las métricas de un backtest consolidado.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import uuid
from typing import Any, Dict, List, Literal, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field

from contracts.backtest import TradeLog
from contracts.portfolio import PortfolioAllocation, PortfolioRequest
from services.core.event_bus import PortfolioRebalancedEvent, event_bus
from services.portfolio.portfolio_engine import PortfolioEngine
from services.portfolio.meta_ensemble_service import MetaEnsembleService
from services.portfolio.autonomous_meta_daemon import autonomous_meta_daemon
from services.semantic_ai.portfolio_debate_engine import portfolio_debate_engine
from services.api.app.db.database import SessionLocal, CandidateModel, PortfolioModel, DB_PATH

logger = logging.getLogger("PortfolioRouter")
router = APIRouter(tags=["Portfolio & Meta-Strategies"])

portfolio_engine_instance = PortfolioEngine()
meta_ensemble_service_instance = MetaEnsembleService()


class AllocateCapitalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request: PortfolioRequest
    asset_trades: Dict[str, List[TradeLog]]
    asset_point_values: Optional[Dict[str, float]] = Field(default_factory=dict)


class SynthesizeMetaEnsembleRequest(BaseModel):
    candidate_ids: List[str] = Field(..., min_length=2, description="Lista de IDs de estrategias en activos distintos.")
    route: Literal["ULTRA", "FONDEO"] = "ULTRA"
    custom_name: Optional[str] = None
    total_capital_usd: Optional[float] = None


class DebateMetaEnsembleRequest(BaseModel):
    portfolio_id: str
    route: Literal["ULTRA", "FONDEO"] = "ULTRA"
    strategies: List[Dict[str, Any]]
    meta_metrics: Dict[str, Any]


# ----------------------------------------------------------------------------
# 1. CONTROL Y TELEMETRÍA DEL DEMONIO 24/7 DE META-ESTRATEGIAS
# ----------------------------------------------------------------------------
@router.get("/daemon/status")
def get_meta_daemon_status() -> Dict[str, Any]:
    """Retorna la telemetría viva del demonio autónomo 24/7 de Meta-Estrategias."""
    return autonomous_meta_daemon.get_status()


@router.post("/daemon/start")
def start_meta_daemon() -> Dict[str, Any]:
    """Inicia el demonio autónomo 24/7 de Meta-Estrategias."""
    autonomous_meta_daemon.start_autonomous()
    return {"status": "SUCCESS", "message": "AutonomousMetaDaemon iniciado 24/7.", "daemon": autonomous_meta_daemon.get_status()}


@router.post("/daemon/stop")
def stop_meta_daemon() -> Dict[str, Any]:
    """Detiene el demonio autónomo 24/7 de Meta-Estrategias."""
    autonomous_meta_daemon.stop_autonomous()
    return {"status": "SUCCESS", "message": "AutonomousMetaDaemon detenido.", "daemon": autonomous_meta_daemon.get_status()}


# ----------------------------------------------------------------------------
# 2. TABLA CANÓNICA Y LISTADO DE META-ESTRATEGIAS
# ----------------------------------------------------------------------------
@router.get("/meta-strategies/table")
def get_meta_strategies_table(
    route: Optional[str] = Query(None, description="Filtro de ruta: ULTRA, FONDEO o ALL"),
    status: Optional[str] = Query(None, description="Filtro de estado: ALL, CERTIFIED, INCUBATING"),
    search: Optional[str] = Query(None, description="Búsqueda por texto o símbolo"),
    sort_by: str = Query("sharpe", description="sharpe, roi, dd, consensus, trades, created_at"),
    sort_order: str = Query("desc", description="asc o desc"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> Dict[str, Any]:
    """Retorna la lista de Meta-Estrategias estructuradas con todas las métricas de backtest para la tabla canónica."""
    try:
        with SessionLocal() as db:
            query = db.query(PortfolioModel)

            if route and route.upper() != "ALL":
                target_route = route.upper()
                query = query.filter((PortfolioModel.target_route == target_route) | (PortfolioModel.target_route == f"TRACK_{target_route}"))

            portfolios = query.order_by(PortfolioModel.created_at.desc()).all()

            results = []
            for p in portfolios:
                data = {}
                if p.allocation_json:
                    try:
                        data = json.loads(p.allocation_json)
                    except Exception:
                        data = {}

                comps = data.get("components") or []
                symbols = [c.get("symbol") for c in comps if c.get("symbol")]
                if not symbols and p.components_json:
                    try:
                        raw_c = json.loads(p.components_json)
                        symbols = [c.get("symbol") for c in raw_c if c.get("symbol")]
                    except Exception:
                        symbols = []

                tot_trades = sum([int(c.get("trades_count", 0)) for c in comps])
                
                # Win rate ponderado
                w_list = [float(c.get("weight_pct", 0.0)) for c in comps]
                wr_list = [float(c.get("individual_win_rate_pct", 0.0)) for c in comps]
                sum_w = sum(w_list) or 1.0
                win_rate = round(sum([w_list[i] * wr_list[i] for i in range(len(w_list))]) / sum_w, 1) if w_list else 0.0

                score = float(data.get("consensus_score") or 0.0)
                verdict = data.get("consensus_verdict") or "PENDIENTE_EVALUACION"
                is_app = data.get("is_approved", score >= 75.0)
                tier = "TIER_1_CERTIFIED" if is_app else "TIER_2_INCUBATOR"

                ann_roi = float(p.annualized_roi_pct or data.get("combined_annualized_roi_pct") or 0.0)
                max_dd = float(p.max_drawdown_pct or data.get("combined_max_dd_pct") or 0.0)
                pf = float(p.profit_factor or data.get("combined_profit_factor") or 0.0)
                sharpe = float(data.get("combined_sharpe_ratio") or 0.0)
                div_ratio = float(data.get("diversification_ratio") or 1.0)
                avg_corr = float(data.get("avg_cross_correlation") or 0.0)

                # Búsqueda por texto
                if search:
                    term = search.lower()
                    name_match = term in (p.name or "").lower()
                    sym_match = any(term in (s or "").lower() for s in symbols)
                    id_match = term in (p.portfolio_id or "").lower()
                    if not (name_match or sym_match or id_match):
                        continue

                # Filtro de estado
                if status and status.upper() != "ALL":
                    if status.upper() == "CERTIFIED" and not is_app:
                        continue
                    if status.upper() == "INCUBATING" and is_app:
                        continue

                results.append({
                    "portfolio_id": p.portfolio_id,
                    "name": p.name,
                    "target_route": p.target_route,
                    "base_capital_usd": p.base_capital_usd,
                    "current_equity_usd": p.current_equity_usd,
                    "symbols": symbols,
                    "components_count": len(comps) or len(symbols) or 2,
                    "total_trades": tot_trades,
                    "win_rate_pct": win_rate,
                    "profit_factor": pf,
                    "annualized_roi_pct": ann_roi,
                    "max_drawdown_pct": max_dd,
                    "sharpe_ratio": sharpe,
                    "diversification_ratio": div_ratio,
                    "avg_cross_correlation": avg_corr,
                    "consensus_score": score,
                    "consensus_verdict": verdict,
                    "is_approved": is_app,
                    "tier": tier,
                    "canonical_hash": p.canonical_hash or data.get("canonical_hash", ""),
                    "status": p.status,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                    "details": data,
                })

            # Ordenación
            reverse = (sort_order.lower() == "desc")
            if sort_by == "roi":
                results.sort(key=lambda x: x["annualized_roi_pct"], reverse=reverse)
            elif sort_by == "dd":
                results.sort(key=lambda x: x["max_drawdown_pct"], reverse=reverse)
            elif sort_by == "consensus":
                results.sort(key=lambda x: x["consensus_score"], reverse=reverse)
            elif sort_by == "trades":
                results.sort(key=lambda x: x["total_trades"], reverse=reverse)
            elif sort_by == "created_at":
                results.sort(key=lambda x: x["created_at"] or "", reverse=reverse)
            else:  # sharpe
                results.sort(key=lambda x: x["sharpe_ratio"], reverse=reverse)

            total_count = len(results)
            paginated = results[offset : offset + limit]

            return {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "meta_strategies": paginated,
            }

    except Exception as e:
        logger.error(f"Error obteniendo tabla de meta-estrategias: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/meta-strategies/{portfolio_id}")
def get_meta_strategy_details(portfolio_id: str) -> Dict[str, Any]:
    """Retorna los detalles completos de una Meta-Estrategia individual."""
    try:
        with SessionLocal() as db:
            p = db.query(PortfolioModel).filter(PortfolioModel.portfolio_id == portfolio_id).first()
            if not p:
                raise HTTPException(status_code=404, detail=f"Meta-Estrategia {portfolio_id} no encontrada.")

            data = {}
            if p.allocation_json:
                try:
                    data = json.loads(p.allocation_json)
                except Exception:
                    data = {}

            return {
                "portfolio_id": p.portfolio_id,
                "name": p.name,
                "target_route": p.target_route,
                "base_capital_usd": p.base_capital_usd,
                "current_equity_usd": p.current_equity_usd,
                "status": p.status,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "details": data,
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo detalle de meta-estrategia {portfolio_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------------------------------------------------------
# 3. ENDPOINTS DE GENERACIÓN Y SÍNTESIS ASISTIDA
# ----------------------------------------------------------------------------
@router.get("/eligible-candidates")
def get_eligible_candidates_by_asset(
    route: Literal["ULTRA", "FONDEO"] = "ULTRA",
    min_gates: int = Query(7, ge=5, le=11)
) -> Dict[str, Any]:
    """Retorna candidatos de SQLite agrupados por activo único para facilitar la combinación multi-activo."""
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=15.0)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        target_route = route.upper()
        rows = cur.execute(
            """
            SELECT candidate_id, name, symbol, timeframe, route, status,
                   net_profit_oos, profit_factor_oos, max_dd_oos_pct, scorecard_json, created_at
            FROM candidates
            WHERE (route = ? OR route = ?) AND status != 'RETIRED'
            ORDER BY profit_factor_oos DESC
            """,
            (target_route, f"TRACK_{target_route}")
        ).fetchall()
        conn.close()

        grouped_by_asset: Dict[str, List[Dict[str, Any]]] = {}
        all_candidates: List[Dict[str, Any]] = []

        for r in rows:
            sc = {}
            if r["scorecard_json"]:
                try:
                    sc = json.loads(r["scorecard_json"])
                except Exception:
                    sc = {}

            g_count = sc.get("gates_passed_count")
            if g_count is None:
                gates_list = sc.get("gates") or []
                g_count = len([g for g in gates_list if g.get("passed")]) if gates_list else 0

            tier = sc.get("tier")
            if not tier:
                if g_count == 10 or g_count == 11:
                    tier = "TIER_1_CERTIFIED"
                elif g_count in (8, 9):
                    tier = "TIER_2_NEAR_CERTIFIED"
                elif g_count in (5, 6, 7):
                    tier = "TIER_3_INCUBATOR"
                else:
                    tier = "TIER_4_REJECTED"

            raw_sym = r["symbol"] or "BTC-USDT"
            clean_sym = raw_sym.upper().replace("-", "").replace("/", "")

            item = {
                "candidate_id": r["candidate_id"],
                "name": r["name"] or r["candidate_id"],
                "symbol": raw_sym,
                "clean_symbol": clean_sym,
                "timeframe": r["timeframe"] or "1h",
                "route": target_route,
                "status": r["status"],
                "tier": tier,
                "gates_passed_count": g_count,
                "profit_factor": float(r["profit_factor_oos"] or 1.1),
                "max_dd_pct": float(r["max_dd_oos_pct"] or 5.0),
                "net_profit_usd": float(r["net_profit_oos"] or 0.0),
            }

            all_candidates.append(item)
            if clean_sym not in grouped_by_asset:
                grouped_by_asset[clean_sym] = []
            grouped_by_asset[clean_sym].append(item)

        return {
            "route": target_route,
            "total_candidates": len(all_candidates),
            "unique_assets_count": len(grouped_by_asset),
            "assets_available": list(grouped_by_asset.keys()),
            "grouped_by_asset": grouped_by_asset,
            "candidates": all_candidates[:60],
        }

    except Exception as e:
        logger.error(f"Error obteniendo candidatos elegibles por activo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/synthesize")
def synthesize_meta_ensemble(req: SynthesizeMetaEnsembleRequest) -> Dict[str, Any]:
    """Sintetiza una Meta-Estrategia multi-activo, calcula covarianzas, ejecuta el debate de agentes y evalúa los 11 Gates."""
    try:
        result = meta_ensemble_service_instance.assemble_meta_strategy(
            candidate_ids=req.candidate_ids,
            ensemble_name=req.custom_name,
            target_route=req.route,
            total_capital_usd=req.total_capital_usd,
        )

        components_list = [
            {
                "strategy_id": c.strategy_id,
                "symbol": c.symbol,
                "timeframe": c.timeframe,
                "route": c.route,
                "weight_pct": c.weight_pct,
                "individual_annualized_roi_pct": c.individual_annualized_roi_pct,
                "individual_max_dd_pct": c.individual_max_dd_pct,
                "individual_win_rate_pct": c.individual_win_rate_pct,
                "individual_profit_factor": c.individual_profit_factor,
                "role_in_ensemble": c.role_in_ensemble,
                "trades_count": c.trades_count,
            }
            for c in result.components
        ]

        response_payload = {
            "ensemble_id": result.ensemble_id,
            "name": result.name,
            "route": result.route,
            "total_capital_usd": result.total_capital_usd,
            "components": components_list,
            "correlation_matrix": result.correlation_matrix,
            "drawdown_correlation_matrix": result.drawdown_correlation_matrix,
            "avg_cross_correlation": result.avg_cross_correlation,
            "max_cross_correlation": result.max_cross_correlation,
            "combined_annualized_roi_pct": result.combined_annualized_roi_pct,
            "combined_monthly_roi_pct": result.combined_monthly_roi_pct,
            "combined_max_dd_pct": result.combined_max_dd_pct,
            "combined_profit_factor": result.combined_profit_factor,
            "combined_sharpe_ratio": result.combined_sharpe_ratio,
            "diversification_ratio": result.diversification_ratio,
            "combined_equity_curve": result.combined_equity_curve,
            "agents_debate": result.agents_debate,
            "consensus_verdict": result.consensus_verdict,
            "consensus_score": result.consensus_score,
            "is_approved": result.is_approved,
            "canonical_hash": result.compute_canonical_hash(),
            "created_at_utc": result.created_at_utc,
            "scorecard": result.scorecard,
        }

        return response_payload

    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        logger.error(f"Error sintetizando meta-estrategia: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/debate")
def debate_meta_ensemble(req: DebateMetaEnsembleRequest) -> Dict[str, Any]:
    """Ejecuta el debate dinámico de los 5 agentes sobre una combinación de estrategias."""
    try:
        return portfolio_debate_engine.conduct_portfolio_debate(
            route=req.route,
            portfolio_id=req.portfolio_id,
            strategies=req.strategies,
            meta_metrics=req.meta_metrics,
        )
    except Exception as e:
        logger.error(f"Error en debate de portafolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/meta-ensembles")
@router.get("/ensembles")
def list_meta_ensembles(route: Optional[str] = Query(None)) -> Dict[str, Any]:
    """Lista todos los meta-portafolios sintetizados persistidos en SQLite WAL."""
    try:
        with SessionLocal() as db:
            query = db.query(PortfolioModel)
            if route:
                query = query.filter(PortfolioModel.target_route == route.upper())
            portfolios = query.order_by(PortfolioModel.created_at.desc()).all()

            results = []
            for p in portfolios:
                data = {}
                if p.allocation_json:
                    try:
                        data = json.loads(p.allocation_json)
                    except Exception:
                        data = {}
                results.append({
                    "portfolio_id": p.portfolio_id,
                    "name": p.name,
                    "target_route": p.target_route,
                    "base_capital_usd": p.base_capital_usd,
                    "current_equity_usd": p.current_equity_usd,
                    "status": p.status,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                    "details": data,
                })

            return {
                "total": len(results),
                "ensembles": results,
            }
    except Exception as e:
        logger.error(f"Error listando meta-ensembles: {e}")
        return {"total": 0, "ensembles": [], "error": str(e)}
