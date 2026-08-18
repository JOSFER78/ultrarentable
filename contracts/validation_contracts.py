"""Validation & Gate Contracts for Ultrarentable V2.

Decoupled criteria and evidence gate result contracts for ULTRA convexity route
and FONDEO CME Prop Firm preservation route.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class RouteType(str, Enum):
    ULTRA = "ULTRA"
    FONDEO = "FONDEO"


class GateId(str, Enum):
    GATE_1_IN_SAMPLE = "GATE_1_IN_SAMPLE"
    GATE_2_OUT_OF_SAMPLE = "GATE_2_OUT_OF_SAMPLE"
    GATE_3_WALK_FORWARD = "GATE_3_WALK_FORWARD"
    GATE_4_MONTE_CARLO = "GATE_4_MONTE_CARLO"
    GATE_5_LIVE_READINESS = "GATE_5_LIVE_READINESS"


class EvidenceGateDecision(BaseModel):
    """Immutable record of an evaluation gate decision with verifiable metrics."""
    model_config = ConfigDict(frozen=True)

    gate_id: GateId
    passed: bool
    score: float = Field(..., ge=0.0, le=100.0, description="Normalized score 0..100")
    reason: str
    metrics: Dict[str, Any] = Field(default_factory=dict)
    evaluated_at_utc: str = Field("2026-08-18T00:00:00Z")


class FondeoValidationCriteria(BaseModel):
    """Strict capital preservation & CME Prop Firm passing criteria."""
    model_config = ConfigDict(frozen=True)

    account_size_usd: float = Field(50000.0)
    profit_target_usd: float = Field(3000.0)
    max_trailing_dd_pct: float = Field(4.0, description="Max 4.0% trailing drawdown ($2,000 / $50k)")
    max_daily_loss_pct: float = Field(2.0, description="Max 2.0% daily loss ($1,000 / $50k)")
    min_profit_factor: float = Field(1.35)
    min_win_rate_pct: float = Field(40.0)
    min_trades_oos: int = Field(25)
    max_single_day_profit_share_pct: float = Field(40.0, description="Consistency rule: no single day > 40% total profit")
    require_eod_flatten: bool = Field(True, description="Strictly no overnight / weekend holding")


class UltraValidationCriteria(BaseModel):
    """Convexity, fat-tails & hyperscaling criteria for BingX Crypto."""
    model_config = ConfigDict(frozen=True)

    initial_equity_usd: float = Field(10000.0)
    min_annualized_roi_pct: float = Field(100.0, description="Must show significant annualized compounding")
    min_win_rate_pct: float = Field(18.0, description="Low win rate accepted if payoff is asymmetric")
    min_asymmetric_payoff: float = Field(3.0, description="Average Win / Average Loss >= 3.0x")
    min_trades_oos: int = Field(20)
    allow_deep_drawdown: bool = Field(True, description="Permits drawdown up to 80% if not liquidating")
    disallow_account_bust: bool = Field(True, description="Total equity must strictly remain > 0 USD at all times")


class BalaExecutionRecord(BaseModel):
    """Immutable tracking record for an isolated capital bullet (Bala) in execution."""
    model_config = ConfigDict(frozen=True)

    bullet_id: str
    parent_vault_id: str
    seed_equity_usd: float
    current_equity_usd: float
    peak_equity_usd: float
    current_state: str = Field("ACTIVE", description="SEEDED, ACTIVE, RUNNER, HARVESTING, RECYCLE_PROFIT, STOPPED")
    harvested_profit_usd: float = Field(0.0)
    recycled_profit_usd: float = Field(0.0)
    open_positions_count: int = Field(0)
    total_trades_executed: int = Field(0)


class ValidationSummary(BaseModel):
    """Overall multi-gate validation summary for a candidate strategy."""
    model_config = ConfigDict(frozen=True)

    strategy_id: str
    route: RouteType
    overall_passed: bool
    final_score: float = Field(..., ge=0.0, le=100.0)
    gate_decisions: List[EvidenceGateDecision]
    verified_at_utc: str = Field("2026-08-18T00:00:00Z")
    rejection_reasons: List[str] = Field(default_factory=list)
