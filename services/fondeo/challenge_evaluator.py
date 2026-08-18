"""services/fondeo/challenge_evaluator.py
Evaluador y guardián de retos de empresas de fondeo (Prop Firms).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from contracts.portfolio import PropChallengeConfig


class PropChallengeEvaluator:
    """Verificador de reglas de fondeo de CME Prop Firms."""

    def evaluate_account_health(
        self,
        config: PropChallengeConfig,
        current_equity: float,
        peak_equity: float,
        daily_loss: float,
    ) -> Dict[str, Any]:
        trailing_dd = peak_equity - current_equity
        trailing_violation = trailing_dd > config.max_trailing_drawdown_usd
        
        daily_violation = False
        if config.daily_loss_limit_usd is not None:
            daily_violation = daily_loss > config.daily_loss_limit_usd

        profit_secured = current_equity - config.account_size_usd
        passed_challenge = profit_secured >= config.profit_target_usd and not trailing_violation

        return {
            "firm_name": config.firm_name,
            "passed": passed_challenge,
            "failed": trailing_violation or daily_violation,
            "trailing_drawdown_usd": trailing_dd,
            "daily_loss_usd": daily_loss,
            "trailing_violation": trailing_violation,
            "daily_violation": daily_violation,
            "profit_target_reached": profit_secured >= config.profit_target_usd,
        }
