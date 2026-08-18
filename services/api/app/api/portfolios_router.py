"""Portfolios Router: Multi-Strategy Portfolio Sprints for Prop Firm Challenges."""

from typing import Any, Dict, List
from fastapi import APIRouter
from services.api.app.factory.portfolio_sprint_engine import build_fondeo_sprint_portfolios
from services.api.app.factory.ultra_portfolio_engine import build_ultra_hyperscale_portfolios

portfolios_router = APIRouter(prefix="/api/v1/portfolios", tags=["portfolios"])


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
    """Get backtested multi-crypto hyper-scaling portfolios with 6-tier pyramiding."""
    ports = build_ultra_hyperscale_portfolios()
    return [
        {
            "portfolio_id": p.portfolio_id,
            "name": p.name,
            "description": p.description,
            "target_route": p.target_route,
            "base_capital_usd": p.base_capital_usd,
            "target_multiplication": p.target_multiplication,
            "max_leverage": p.max_leverage,
            "pyramiding_tiers": p.pyramiding_tiers,
            "floating_reinvest_pct": p.floating_reinvest_pct,
            "components": p.components,
            "annualized_roi_pct": p.annualized_roi_pct,
            "monthly_roi_pct": p.monthly_roi_pct,
            "total_roi_oos_pct": p.total_roi_oos_pct,
            "net_profit_usd": p.net_profit_usd,
            "profit_factor": p.profit_factor,
            "win_rate_pct": p.win_rate_pct,
            "max_drawdown_pct": p.max_drawdown_pct,
            "trades_per_month": p.trades_per_month,
            "total_trades": p.total_trades,
            "duration_info": p.duration_info,
            "equity_growth_curve": p.equity_growth_curve,
            "tier_synergy_summary": p.tier_synergy_summary,
        }
        for p in ports
    ]
