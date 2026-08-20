from dataclasses import asdict
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.api.app.db.database import SessionLocal, CandidateModel, PortfolioModel
from services.api.app.factory.portfolio_sprint_engine import build_fondeo_sprint_portfolios
from services.api.app.factory.ultra_portfolio_engine import build_ultra_hyperscale_portfolios
from services.portfolio.meta_ensemble_service import MetaEnsembleService

portfolios_router = APIRouter(prefix="/api/v1/portfolios", tags=["portfolios"])


class AssemblePortfolioRequest(BaseModel):
    candidate_ids: List[str] = Field(..., min_items=2, description="Lista de IDs de estrategias en activos distintos.")
    ensemble_name: Optional[str] = Field(None, description="Nombre personalizado del Meta-Portafolio.")
    target_route: Optional[str] = Field(None, description="Ruta cuantitativa: ULTRA o FONDEO.")
    total_capital_usd: Optional[float] = Field(None, description="Capital base total en USD.")


@portfolios_router.get("/available-candidates")
def get_available_candidates_for_meta(route: Optional[str] = Query(None)) -> List[Dict[str, Any]]:
    """Retorna candidatos certificados disponibles agrupados por activo para ensamblar Meta-Portafolios."""
    db = SessionLocal()
    try:
        q = db.query(CandidateModel)
        if route:
            q = q.filter(CandidateModel.route == route.upper())
        candidates = q.order_by(CandidateModel.profit_factor.desc()).all()

        return [
            {
                "candidate_id": c.candidate_id,
                "name": c.name,
                "route": c.route,
                "symbol": c.symbol,
                "timeframe": c.timeframe,
                "annualized_roi": c.annualized_roi,
                "max_drawdown": c.max_drawdown,
                "profit_factor": c.profit_factor,
                "win_rate": c.win_rate,
                "total_trades": c.total_trades,
                "gates_passed_count": c.gates_passed_count or 11,
                "is_certified": (c.gates_passed_count == 11),
            }
            for c in candidates
        ]
    finally:
        db.close()


@portfolios_router.post("/assemble-debate")
def assemble_and_debate_meta_portfolio(req: AssemblePortfolioRequest) -> Dict[str, Any]:
    """Ensambla un Meta-Portafolio multi-activo sobre datos reales y ejecuta el debate de los 5 agentes."""
    service = MetaEnsembleService()
    try:
        res = service.assemble_meta_strategy(
            candidate_ids=req.candidate_ids,
            ensemble_name=req.ensemble_name,
            target_route=req.target_route,
            total_capital_usd=req.total_capital_usd,
        )
        return {
            "status": "SUCCESS",
            "meta_ensemble": {
                "ensemble_id": res.ensemble_id,
                "name": res.name,
                "route": res.route,
                "total_capital_usd": res.total_capital_usd,
                "components": [asdict(c) for c in res.components],
                "correlation_matrix": res.correlation_matrix,
                "drawdown_correlation_matrix": res.drawdown_correlation_matrix,
                "avg_cross_correlation": res.avg_cross_correlation,
                "max_cross_correlation": res.max_cross_correlation,
                "combined_annualized_roi_pct": res.combined_annualized_roi_pct,
                "combined_monthly_roi_pct": res.combined_monthly_roi_pct,
                "combined_max_dd_pct": res.combined_max_dd_pct,
                "combined_profit_factor": res.combined_profit_factor,
                "combined_sharpe_ratio": res.combined_sharpe_ratio,
                "diversification_ratio": res.diversification_ratio,
                "combined_equity_curve": res.combined_equity_curve,
                "agents_debate": res.agents_debate,
                "consensus_verdict": res.consensus_verdict,
                "consensus_score": res.consensus_score,
                "created_at_utc": res.created_at_utc,
                "canonical_hash": res.canonical_hash,
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error durante el ensamblaje: {str(e)}")


@portfolios_router.get("/assembled")
def list_assembled_portfolios() -> List[Dict[str, Any]]:
    """Lista todos los Meta-Portafolios ensamblados y persistidos en SQLite."""
    db = SessionLocal()
    try:
        ports = db.query(PortfolioModel).order_by(PortfolioModel.created_at.desc()).all()
        return [
            {
                "portfolio_id": p.portfolio_id,
                "name": p.name,
                "target_route": p.target_route,
                "base_capital_usd": p.base_capital_usd,
                "annualized_roi_pct": p.annualized_roi_pct,
                "monthly_roi_pct": p.monthly_roi_pct,
                "max_drawdown_pct": p.max_drawdown_pct,
                "profit_factor": p.profit_factor,
                "canonical_hash": p.canonical_hash,
                "created_at": str(p.created_at),
            }
            for p in ports
        ]
    finally:
        db.close()


@portfolios_router.get("/fondeo-sprints")
def get_fondeo_sprint_portfolios() -> List[Dict[str, Any]]:
    """Get backtested multi-asset portfolios designed to pass prop firm challenges in <= 5 days."""
    ports = build_fondeo_sprint_portfolios()
    return [
        {
            "portfolio_id": p.portfolio_id,
            "name": p.name,
            "description": p.description,
            "target_route": p.target_route,
            "account_size_usd": p.account_size_usd,
            "profit_target_pct": p.profit_target_pct,
            "trailing_dd_limit_pct": p.trailing_dd_limit_pct,
            "components": p.components,
            "pass_rate_pct": p.pass_rate_pct,
            "avg_days_to_pass": p.avg_days_to_pass,
            "fastest_pass_days": p.fastest_pass_days,
            "avg_5d_roi_pct": p.avg_5d_roi_pct,
            "annualized_roi_pct": p.annualized_roi_pct,
            "monthly_roi_pct": p.monthly_roi_pct,
            "max_5d_drawdown_pct": p.max_5d_drawdown_pct,
            "max_daily_loss_pct": p.max_daily_loss_pct,
            "daily_trades_avg": p.daily_trades_avg,
            "correlation_score": p.correlation_score,
            "funded_phase_dd_pct": p.funded_phase_dd_pct,
            "funded_monthly_payout_usd": p.funded_monthly_payout_usd,
            "equity_curve_5d": p.equity_curve_5d,
            "day_by_day_progress": p.day_by_day_progress,
        }
        for p in ports
    ]


@portfolios_router.get("/ultra-hyperscale")
def get_ultra_hyperscale_portfolios() -> List[Dict[str, Any]]:
    """Get backtested multi-crypto hyper-scaling portfolios with adaptive leverage and cross-margin synergy."""
    ports = build_ultra_hyperscale_portfolios()
    return [
        {
            "portfolio_id": p.portfolio_id,
            "name": p.name,
            "description": p.description,
            "target_route": p.target_route,
            "base_capital_usd": p.base_capital_usd,
            "target_multiplication": p.target_multiplication,
            "leverage_system": p.leverage_system,
            "pyramiding_tiers": p.pyramiding_tiers,
            "floating_reinvest_pct": p.floating_reinvest_pct,
            "components": p.components,
            "combined_win_rate_pct": p.combined_win_rate_pct,
            "individual_win_rates": p.individual_win_rates,
            "annualized_roi_pct": p.annualized_roi_pct,
            "monthly_roi_pct": p.monthly_roi_pct,
            "total_roi_oos_pct": p.total_roi_oos_pct,
            "net_profit_usd": p.net_profit_usd,
            "profit_factor": p.profit_factor,
            "max_drawdown_pct": p.max_drawdown_pct,
            "individual_max_dd_avg": p.individual_max_dd_avg,
            "trades_per_month": p.trades_per_month,
            "total_trades": p.total_trades,
            "duration_info": p.duration_info,
            "hyper_resources": p.hyper_resources,
            "leverage_stages": p.leverage_stages,
            "equity_growth_curve": p.equity_growth_curve,
            "synergy_rules": p.synergy_rules,
            "real_synergy_events": p.real_synergy_events,
        }
        for p in ports
    ]
