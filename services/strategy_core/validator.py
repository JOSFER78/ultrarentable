"""Independent Strategy Validator for Ultra Rentable V2."""

from __future__ import annotations

from typing import Any, Dict, List
from pydantic import BaseModel, Field

from services.strategy_core.spec import StrategySpec


class ValidationCheckResult(BaseModel):
    check_name: str
    passed: bool
    score: float = Field(..., ge=0.0, le=100.0)
    details: str


class ValidationReport(BaseModel):
    strategy_id: str
    overall_passed: bool
    robustness_score: float = Field(..., ge=0.0, le=100.0)
    checks: List[ValidationCheckResult]
    recommendation: str


class IndependentStrategyValidator:
    """Validates candidate strategies produced by StrategyQuant X outside of SQX."""

    def __init__(self, min_trades: int = 30, min_profit_factor: float = 1.3, max_drawdown_pct: float = 20.0):
        self.min_trades = min_trades
        self.min_profit_factor = min_profit_factor
        self.max_drawdown_pct = max_drawdown_pct

    def validate_sqx_stats(self, spec: StrategySpec, sqx_stats: Dict[str, Any]) -> ValidationReport:
        """Validate SQX candidate metrics against independent robustness thresholds."""
        checks: List[ValidationCheckResult] = []
        
        # 1. Trade Count Check
        net_trades = int(sqx_stats.get("TradesCount", sqx_stats.get("NetTrades", 0)))
        passed_trades = net_trades >= self.min_trades
        checks.append(ValidationCheckResult(
            check_name="MINIMUM_TRADE_COUNT",
            passed=passed_trades,
            score=min(100.0, (net_trades / self.min_trades) * 100.0) if passed_trades else 20.0,
            details=f"Trades: {net_trades} (Threshold: >={self.min_trades})"
        ))

        # 2. Profit Factor Check
        profit_factor = float(sqx_stats.get("ProfitFactor", 0.0))
        passed_pf = profit_factor >= self.min_profit_factor
        checks.append(ValidationCheckResult(
            check_name="PROFIT_FACTOR_STABILITY",
            passed=passed_pf,
            score=min(100.0, (profit_factor / self.min_profit_factor) * 70.0) if passed_pf else 10.0,
            details=f"Profit Factor: {profit_factor:.2f} (Threshold: >={self.min_profit_factor})"
        ))

        # 3. Maximum Drawdown Check
        max_dd = float(sqx_stats.get("MaxDrawdownPct", sqx_stats.get("DrawdownPct", 0.0)))
        passed_dd = max_dd <= self.max_drawdown_pct
        checks.append(ValidationCheckResult(
            check_name="MAXIMUM_DRAWDOWN_LIMIT",
            passed=passed_dd,
            score=max(0.0, 100.0 - (max_dd / self.max_drawdown_pct) * 50.0) if passed_dd else 0.0,
            details=f"Max Drawdown: {max_dd:.2f}% (Threshold: <={self.max_drawdown_pct}%)"
        ))

        # 4. Anti-Lookahead / Session Rule Check
        has_session_exit = spec.close_at_session_end
        checks.append(ValidationCheckResult(
            check_name="SESSION_OVERNIGHT_RISK",
            passed=has_session_exit,
            score=100.0 if has_session_exit else 40.0,
            details="Mandatory session end exit configured" if has_session_exit else "Warning: Holds positions overnight"
        ))

        # Overall calculation
        passed_count = sum(1 for c in checks if c.passed)
        overall_passed = passed_count == len(checks)
        avg_score = sum(c.score for c in checks) / len(checks)

        if overall_passed and avg_score >= 80.0:
            recommendation = "APPROVED_FOR_EXPLOITATION_PROMOTION"
        elif overall_passed:
            recommendation = "APPROVED_WITH_MONITORING"
        else:
            recommendation = "REJECTED_ROBUSTNESS_CHECK_FAILED"

        return ValidationReport(
            strategy_id=spec.strategy_id,
            overall_passed=overall_passed,
            robustness_score=round(avg_score, 2),
            checks=checks,
            recommendation=recommendation
        )
