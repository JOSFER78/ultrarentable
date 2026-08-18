"""contracts/portfolio.py
Contratos para asignación de capital, portfolio multi-activo, Balas Ultra y Reglas Prop.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AllocationMethod(str, Enum):
    EQUAL_WEIGHT = "EQUAL_WEIGHT"
    INVERSE_VOLATILITY = "INVERSE_VOLATILITY"
    RISK_PARITY_ERC = "RISK_PARITY_ERC"
    HIERARCHICAL_RISK_PARITY = "HIERARCHICAL_RISK_PARITY"


class AssetWeight(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    symbol: str
    weight: float = Field(..., ge=0.0, le=1.0)
    target_capital_usd: float = Field(..., ge=0.0)
    max_contracts_or_lots: float = Field(..., ge=0.01)


class PortfolioRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    portfolio_id: str
    total_capital_usd: float = Field(..., gt=0.0)
    method: AllocationMethod = AllocationMethod.HIERARCHICAL_RISK_PARITY
    candidate_strategy_ids: List[str] = Field(..., min_length=1)
    max_correlation_allowed: float = Field(0.70, ge=0.0, le=1.0)
    max_aggregate_drawdown_pct: float = Field(5.0, gt=0.0, le=100.0)


class PortfolioAllocation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    portfolio_id: str
    timestamp_utc_ms: int
    total_capital_usd: float
    weights: List[AssetWeight]
    expected_sharpe: float
    diversification_ratio: float
    max_historical_drawdown_pct: float
    provenance_hash_sha256: str


# ============================================================================
# CONTRATOS ESPECÍFICOS ULTRA (BALAS & BÓVEDA RATCHET)
# ============================================================================

class BulletTradeDirection(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class BulletLayer(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    layer_id: int = Field(..., ge=0)
    entry_price: float = Field(..., gt=0.0)
    quantity: float = Field(..., gt=0.0)
    margin_allocated_usd: float = Field(..., gt=0.0)
    leverage: float = Field(..., ge=1.0)
    timestamp_ms: int
    is_house_money: bool = False


class IsolatedBullet(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    bullet_id: str
    symbol: str
    direction: BulletTradeDirection
    initial_margin_r_usd: float = Field(..., gt=0.0)
    current_isolated_margin_usd: float = Field(..., ge=0.0)
    entry_price_avg: float = Field(..., gt=0.0)
    current_sl_price: float = Field(..., gt=0.0)
    liquidation_price: float = Field(..., gt=0.0)
    layers: List[BulletLayer] = Field(default_factory=list)
    pyramid_count: int = Field(0, ge=0)
    peak_unrealized_pnl_usd: float = 0.0
    total_fees_paid_usd: float = Field(0.0, ge=0.0)
    created_at_ms: int
    closed_at_ms: Optional[int] = None
    realized_net_pnl_usd: float = 0.0
    close_reason: Optional[str] = None


class VaultRatchetConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    milestone_2x_lock_pct: float = Field(0.50, ge=0.0, le=1.0)
    milestone_3x_lock_pct: float = Field(0.65, ge=0.0, le=1.0)
    milestone_5x_lock_pct: float = Field(0.75, ge=0.0, le=1.0)
    milestone_10x_lock_pct: float = Field(0.85, ge=0.0, le=1.0)


# ============================================================================
# CONTRATOS ESPECÍFICOS FONDEO (PROP FIRM RULES)
# ============================================================================

class PropChallengeConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    firm_name: str
    account_size_usd: float = Field(50000.0, gt=0.0)
    profit_target_usd: float = Field(3000.0, gt=0.0)
    max_trailing_drawdown_usd: float = Field(2000.0, gt=0.0)
    daily_loss_limit_usd: Optional[float] = Field(1000.0, gt=0.0)
    consistency_max_profit_share_pct: float = Field(40.0, ge=10.0, le=100.0)
    min_trading_days: int = Field(5, ge=1)
    max_contracts_micros: int = Field(10, ge=1)
