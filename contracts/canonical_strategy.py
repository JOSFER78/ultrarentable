"""Canonical Strategy Contract v2.0.0 for Ultrarentable.

Immutable, typed definition of trading strategies with full AST rule representation,
instrument specification, risk sizing, costs, and deterministic SHA-256 provenance hashing.
"""

from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AssetClass(str, Enum):
    CRYPTO_PERPETUAL = "CRYPTO_PERPETUAL"
    CRYPTO_SPOT = "CRYPTO_SPOT"
    CME_FUTURES = "CME_FUTURES"
    FOREX = "FOREX"
    EQUITY_INDEX = "EQUITY_INDEX"


class ContractType(str, Enum):
    PERPETUAL = "PERPETUAL"
    FUTURES = "FUTURES"
    SPOT = "SPOT"
    FOREX = "FOREX"


class StrategyArchetype(str, Enum):
    VOLATILITY_EXPANSION = "VOLATILITY_EXPANSION"
    TREND_FOLLOWING_EMA = "TREND_FOLLOWING_EMA"
    MOMENTUM_BREAKOUT = "MOMENTUM_BREAKOUT"
    MEAN_REVERSION = "MEAN_REVERSION"
    RSI_DIVERGENCE = "RSI_DIVERGENCE"
    DONCHIAN_CHANNEL = "DONCHIAN_CHANNEL"


class StrategyStatus(str, Enum):
    DRAFT = "DRAFT"
    CANDIDATE = "CANDIDATE"
    VALIDATED = "VALIDATED"
    EXPLOITATION_ULTRA = "EXPLOITATION_ULTRA"
    EXPLOITATION_FONDEO = "EXPLOITATION_FONDEO"
    REJECTED = "REJECTED"
    RETIRED = "RETIRED"


class ComparisonOperator(str, Enum):
    GREATER_THAN = "GREATER_THAN"
    LESS_THAN = "LESS_THAN"
    GREATER_EQUAL = "GREATER_EQUAL"
    LESS_EQUAL = "LESS_EQUAL"
    CROSSES_ABOVE = "CROSSES_ABOVE"
    CROSSES_BELOW = "CROSSES_BELOW"
    EQUALS = "EQUALS"


class ActionType(str, Enum):
    ENTER_LONG = "ENTER_LONG"
    ENTER_SHORT = "ENTER_SHORT"
    EXIT_LONG = "EXIT_LONG"
    EXIT_SHORT = "EXIT_SHORT"
    TRAIL_STOP = "TRAIL_STOP"
    PYRAMID_ADD = "PYRAMID_ADD"


class ASTActionNode(BaseModel):
    model_config = ConfigDict(frozen=True)

    action_type: ActionType
    order_type: str = Field("MARKET", description="MARKET, LIMIT, STOP")
    quantity_pct: Optional[float] = None
    target_price: Optional[float] = None
    params: Dict[str, Any] = Field(default_factory=dict)


class InstrumentConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    symbol: str = Field(..., description="Canonical asset symbol (e.g. BTC-USDT, NQ, EURUSD)")
    exchange: str = Field("BINGX", description="Venue or Exchange name (e.g. BINGX, CME, CBOT, FOREX)")
    asset_class: AssetClass = Field(AssetClass.CRYPTO_PERPETUAL)
    contract_type: ContractType = Field(ContractType.PERPETUAL)
    point_value: float = Field(1.0, description="USD value per 1.0 unit move")
    tick_size: float = Field(0.01, description="Minimum price fluctuation")


class SessionConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    timezone: str = Field("UTC", description="Session timezone (e.g. UTC, America/New_York)")
    start_time: str = Field("00:00", description="Session start HH:MM")
    end_time: str = Field("23:59", description="Session end HH:MM")
    close_at_end: bool = Field(False, description="Whether positions must be flattened at session close")


class ASTIndicatorNode(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str = Field(..., description="Indicator name e.g. RSI, EMA, ATR, BollingerBands, Donchian")
    timeframe: str = Field("5m", description="Indicator timeframe")
    period: int = Field(14, description="Main calculation period")
    params: Dict[str, Any] = Field(default_factory=dict, description="Additional params e.g. std_dev, fast_period")


class ASTRuleCondition(BaseModel):
    model_config = ConfigDict(frozen=True)

    left_indicator: ASTIndicatorNode
    operator: ComparisonOperator
    right_indicator: Optional[ASTIndicatorNode] = None
    threshold_value: Optional[float] = None


class ASTEntryExitLogic(BaseModel):
    model_config = ConfigDict(frozen=True)

    archetype: StrategyArchetype
    long_entry_conditions: List[ASTRuleCondition] = Field(default_factory=list)
    short_entry_conditions: List[ASTRuleCondition] = Field(default_factory=list)
    stop_loss_atr_mult: Optional[float] = Field(1.5)
    take_profit_atr_mult: Optional[float] = Field(3.0)
    trailing_stop_atr_mult: Optional[float] = None
    time_exit_bars: Optional[int] = None
    pyramiding_tiers: int = Field(1, ge=1, le=5)


class RiskSizingConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    method: str = Field("FIXED_RISK_PCT", description="FIXED_RISK_PCT, FIXED_CONTRACTS, CAPITAL_COMPOUND")
    risk_per_trade_pct: float = Field(2.0, ge=0.1, le=50.0)
    fixed_contracts: Optional[float] = None
    max_leverage: float = Field(1.0, ge=1.0, le=125.0)
    margin_reinvest_pct: float = Field(0.0, ge=0.0, le=100.0)


class CostsConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    maker_fee_bps: float = Field(0.00020, description="Maker fee in bps (e.g. 0.02%)")
    taker_fee_bps: float = Field(0.00050, description="Taker fee in bps (e.g. 0.05%)")
    spread_ticks: float = Field(1.0, description="Estimated spread in ticks")
    slippage_ticks: float = Field(0.5, description="Estimated slippage in ticks")


class StrategyMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)

    author: str = Field("Ultrarentable Engine")
    generation_method: str = Field("AI_QUANT_SEARCH", description="AI_QUANT_SEARCH, SQX_GENETIC, MANUAL_RULE")
    source_project: Optional[str] = None
    source_databank: Optional[str] = None
    created_at_utc: str = Field("2026-08-18T00:00:00Z")
    tags: List[str] = Field(default_factory=list)


class CanonicalStrategy(BaseModel):
    """Canonical Strategy Representation v2.0.0.
    
    Fully immutable, verifiable representation of any trading strategy across the ecosystem.
    """
    model_config = ConfigDict(frozen=True)

    strategy_id: str = Field(..., description="Unique strategy identifier e.g. CS-SOL-5M-VOL-001")
    version: str = Field("2.0.0", description="Contract specification version")
    name: str = Field(..., description="Descriptive strategy name")
    target_route: str = Field("ULTRA", description="Target route: ULTRA or FONDEO")
    status: StrategyStatus = Field(StrategyStatus.DRAFT)

    instrument: InstrumentConfig
    timeframe: str = Field("5m")
    session: SessionConfig = Field(default_factory=SessionConfig)
    logic: ASTEntryExitLogic
    risk_sizing: RiskSizingConfig = Field(default_factory=RiskSizingConfig)
    costs: CostsConfig = Field(default_factory=CostsConfig)
    metadata: StrategyMetadata = Field(default_factory=StrategyMetadata)

    provenance_hash: Optional[str] = Field(None, description="Deterministic SHA-256 of canonical structure")

    def compute_provenance_hash(self) -> str:
        """Compute deterministic SHA-256 hash over canonical fields, ignoring volatile metadata."""
        canonical_dict = {
            "version": self.version,
            "target_route": self.target_route,
            "instrument": self.instrument.model_dump(),
            "timeframe": self.timeframe,
            "session": self.session.model_dump(),
            "logic": self.logic.model_dump(),
            "risk_sizing": self.risk_sizing.model_dump(),
            "costs": self.costs.model_dump(),
        }
        encoded = json.dumps(canonical_dict, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def with_provenance_hash(self) -> CanonicalStrategy:
        """Return a copy with computed provenance_hash populated."""
        computed = self.compute_provenance_hash()
        data = self.model_dump()
        data["provenance_hash"] = computed
        return CanonicalStrategy.model_validate(data)
