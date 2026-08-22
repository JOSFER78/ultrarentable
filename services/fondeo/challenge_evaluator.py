"""services/fondeo/challenge_evaluator.py
Evaluador y guardián de retos de empresas de fondeo (Prop Firms) y cuentas de prueba Sim101.
"""

from __future__ import annotations

from typing import Any
from contracts.portfolio import PropChallengeConfig


class PropChallengeEvaluator:
    """Verificador de reglas de fondeo de CME Prop Firms & Sim101 Demo."""

    def evaluate_account_health(
        self,
        config: PropChallengeConfig,
        current_equity: float,
        peak_equity: float,
        daily_loss: float,
        daily_profits_history: list[float] | None = None,
        days_traded: int = 1,
    ) -> dict[str, Any]:
        """Calcula exhaustivamente la salud de la cuenta frente a las reglas institucionales."""
        trailing_dd = max(0.0, peak_equity - current_equity)
        trailing_violation = trailing_dd > config.max_trailing_drawdown_usd
        
        daily_violation = False
        daily_loss_limit = config.daily_loss_limit_usd or 1000.0
        if config.daily_loss_limit_usd is not None:
            daily_violation = daily_loss > config.daily_loss_limit_usd

        profit_secured = current_equity - config.account_size_usd
        target_reached = profit_secured >= config.profit_target_usd

        # Cojines de seguridad (Cushions)
        daily_cushion = max(0.0, daily_loss_limit - daily_loss)
        trailing_cushion = max(0.0, config.max_trailing_drawdown_usd - trailing_dd)

        # Regla de consistencia (e.g. max 40% del profit en un solo día)
        consistency_violation = False
        max_daily_share_pct = 0.0
        if daily_profits_history and profit_secured > 0:
            max_day_profit = max(daily_profits_history)
            if max_day_profit > 0:
                max_daily_share_pct = (max_day_profit / profit_secured) * 100.0
                if max_daily_share_pct > config.consistency_max_profit_share_pct:
                    consistency_violation = True

        min_days_reached = days_traded >= config.min_trading_days
        passed_challenge = target_reached and not trailing_violation and not daily_violation and not consistency_violation and min_days_reached
        is_failed = trailing_violation or daily_violation

        progress_pct = max(0.0, min(100.0, (profit_secured / config.profit_target_usd) * 100.0)) if config.profit_target_usd > 0 else 0.0

        return {
            "firm_name": config.firm_name,
            "account_size_usd": config.account_size_usd,
            "current_equity_usd": current_equity,
            "peak_equity_usd": peak_equity,
            "profit_secured_usd": round(profit_secured, 2),
            "profit_target_usd": config.profit_target_usd,
            "progress_pct": round(progress_pct, 2),
            "passed": passed_challenge,
            "failed": is_failed,
            "trailing_drawdown_usd": round(trailing_dd, 2),
            "trailing_drawdown_cushion_usd": round(trailing_cushion, 2),
            "daily_loss_usd": round(daily_loss, 2),
            "daily_loss_cushion_usd": round(daily_cushion, 2),
            "trailing_violation": trailing_violation,
            "daily_violation": daily_violation,
            "consistency_violation": consistency_violation,
            "max_daily_share_pct": round(max_daily_share_pct, 2),
            "min_days_reached": min_days_reached,
            "days_traded": days_traded,
            "min_trading_days": config.min_trading_days,
        }

    def evaluate_live_fill(
        self,
        config: PropChallengeConfig,
        current_equity: float,
        peak_equity: float,
        fill_pnl: float,
        session_daily_pnl: float,
    ) -> dict[str, Any]:
        """Evalúa el impacto inmediato de un fill de orden en tiempo real."""
        new_daily_loss = max(0.0, -session_daily_pnl)
        new_equity = current_equity + fill_pnl
        new_peak = max(peak_equity, new_equity)
        
        return self.evaluate_account_health(
            config=config,
            current_equity=new_equity,
            peak_equity=new_peak,
            daily_loss=new_daily_loss,
        )
