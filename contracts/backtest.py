"""Backtest Request & Result Contracts for Ultrarentable V2.

Typed, immutable data structures for deterministic backtesting, intrabar policy,
trade logs, and verifiable equity results.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from contracts.canonical_strategy import CanonicalStrategy


class IntrabarPolicy(str, Enum):
    PESSIMISTIC = "PESSIMISTIC"
    OPTIMISTIC = "OPTIMISTIC"
    LOWER_TF_REPLAY = "LOWER_TF_REPLAY"


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class PositionSide(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class BarData(BaseModel):
    """Single OHLCV price bar."""
    model_config = ConfigDict(frozen=True)

    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


class DatasetSnapshot(BaseModel):
    """Verifiable historical dataset snapshot."""
    model_config = ConfigDict(frozen=True)

    dataset_id: str
    symbol: str
    timeframe: str
    start_time: str
    end_time: str
    total_bars: int
    sha256_checksum: str


class TradeRecord(BaseModel):
    """Detailed record of an individual completed trade."""
    model_config = ConfigDict(frozen=True)

    trade_id: str
    entry_time: str
    exit_time: str
    side: PositionSide
    entry_price: float
    exit_price: float
    size_usd: float
    leverage: float = 1.0
    gross_pnl_usd: float
    fee_usd: float
    net_pnl_usd: float
    return_pct: float
    exit_reason: str = Field("TAKE_PROFIT", description="TAKE_PROFIT, STOP_LOSS, TRAILING_STOP, TIME_EXIT, EOD_FLATTEN")


class BacktestRequest(BaseModel):
    """Standardized deterministic backtest invocation request."""
    model_config = ConfigDict(frozen=True)

    strategy: CanonicalStrategy
    dataset: DatasetSnapshot
    initial_equity: float = Field(10000.0)
    intrabar_policy: IntrabarPolicy = Field(IntrabarPolicy.PESSIMISTIC)
    split_ratio: float = Field(0.70, ge=0.50, le=0.90)
    seed: int = Field(42)


class BacktestResult(BaseModel):
    """Complete, reproducible backtest result."""
    model_config = ConfigDict(frozen=True)

    backtest_id: str
    strategy_id: str
    dataset_id: str
    initial_equity: float
    final_equity: float
    net_profit_usd: float
    roi_pct: float
    annualized_roi_pct: float
    monthly_roi_pct: float
    profit_factor: float
    win_rate_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float
    trades_count: int
    
    is_metrics: Dict[str, Any] = Field(default_factory=dict)
    oos_metrics: Dict[str, Any] = Field(default_factory=dict)
    trades: List[TradeRecord] = Field(default_factory=list)
    
    provenance_hash: str = Field(..., description="SHA-256 hash connecting strategy + dataset + result")
    executed_at_utc: str = Field("2026-08-18T00:00:00Z")
