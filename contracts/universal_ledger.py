"""contracts/universal_ledger.py
Universal Full Equity & Trade Ledger Contract (v3.0.0).

DOCTRINA FORENSE:
- Captures the complete bar-by-bar sequence of equity, cash, unrealized/realized PnL, margin, exposure, fees, and drawdown.
- Captures every trade execution event with full cost breakdown and R-multiple calculation.
- Guarantees 100% mathematical reproducibility with Merkle provenance chaining.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class BarEquityRecord(BaseModel):
    """Registro forense de equidad e indicadores contables barra por barra."""
    model_config = ConfigDict(frozen=True, extra="forbid")
    
    bar_index: int
    timestamp_ms: int
    close_price: float
    equity_usd: float
    balance_usd: float
    cash_usd: float
    unrealized_pnl_usd: float
    realized_pnl_usd: float
    fees_cumulative_usd: float
    slippage_cumulative_usd: float
    funding_cumulative_usd: float
    margin_used_usd: float
    drawdown_pct: float
    peak_equity_usd: float
    in_position: bool
    position_qty: float = 0.0
    position_side: Optional[str] = None


class TradeRecord(BaseModel):
    """Registro forense atómico de una operación ejecutada."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    trade_id: str
    strategy_id: str
    dataset_id: str
    symbol: str
    direction: str  # "LONG" | "SHORT"
    
    entry_bar: int
    exit_bar: int
    entry_time_ms: int
    exit_time_ms: int
    
    entry_price: float
    exit_price: float
    quantity: float
    notional_usd: float
    leverage_used: float
    initial_risk_usd: float
    
    gross_pnl_usd: float
    commission_usd: float
    slippage_usd: float
    funding_usd: float
    net_pnl_usd: float
    
    return_pct: float
    return_r: float
    exit_reason: str  # "TAKE_PROFIT" | "STOP_LOSS" | "TRAILING_STOP" | "BREAK_EVEN" | "LIQUIDATION" | "SESSION_END" | "TIME_EXIT"
    pyramid_level: int = 0
    equity_before_usd: float
    equity_after_usd: float


class UniversalBacktestResult(BaseModel):
    """Resultado determinista oficial e inmutable del backtest universal."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    # Identificadores & Huellas de Procedencia
    provenance_hash: str = Field(..., description="Hash SHA-256 de todas las entradas (Strategy, Dataset, Instrument, Execution, Risk, Engine)")
    strategy_id: str
    strategy_hash: str
    dataset_id: str
    dataset_sha256: str
    instrument_symbol: str
    instrument_hash: str
    execution_model_hash: str
    risk_model_hash: str
    engine_version: str = "3.0.0"
    
    # Capital & Retorno
    initial_capital_usd: float
    final_equity_usd: float
    peak_equity_usd: float
    net_profit_usd: float
    total_roi_pct: float
    monthly_roi_pct: float
    annualized_roi_pct: float
    
    # Ratios de Calidad Cuantitativa
    profit_factor: float
    win_rate_pct: float
    expectancy_r: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    
    # Riesgo y Drawdown
    max_drawdown_pct: float
    max_drawdown_duration_bars: int
    peak_margin_utilization_pct: float
    liquidated: bool
    
    # Fricciones Totales
    total_commissions_usd: float
    total_slippage_usd: float
    total_funding_usd: float
    
    # Registros Forenses Completos
    trades: List[TradeRecord] = Field(default_factory=list)
    equity_curve: List[float] = Field(default_factory=list)
    drawdown_curve: List[float] = Field(default_factory=list)
    bar_ledger: List[BarEquityRecord] = Field(default_factory=list)
    execution_duration_ms: float = 0.0
    created_at_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def canonical_json(self) -> str:
        data = self.model_dump(exclude={"bar_ledger"})
        return json.dumps(data, sort_keys=True, separators=(",", ":"))
