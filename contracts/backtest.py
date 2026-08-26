"""contracts/backtest.py
Contratos tipados para solicitudes, resultados y logs del Backtest Fabric.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class EngineType(str, Enum):
    FAST_APPROXIMATE = "FAST_APPROXIMATE"
    SQX_PRECISION = "SQX_PRECISION"
    NAUTILUS_EVENT_DRIVEN = "NAUTILUS_EVENT_DRIVEN"


class BarData(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    timestamp_utc_ms: int
    open: float = Field(..., gt=0.0)
    high: float = Field(..., gt=0.0)
    low: float = Field(..., gt=0.0)
    close: float = Field(..., gt=0.0)
    volume: float = Field(1.0, ge=0.0)


class DatasetSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    dataset_id: str = Field(..., min_length=1)
    symbol: str = Field(..., min_length=1)
    timeframe: str = Field(..., min_length=1)
    start_timestamp_utc_ms: int = Field(..., ge=0)
    end_timestamp_utc_ms: int = Field(..., ge=0)
    total_bars: int = Field(..., ge=1)
    sha256_hash: str = Field(..., min_length=64, max_length=64)
    is_in_sample: bool = True

    @model_validator(mode="after")
    def validate_provenance(self) -> "DatasetSnapshot":
        if self.start_timestamp_utc_ms > self.end_timestamp_utc_ms:
            raise ValueError("DatasetSnapshot start_timestamp_utc_ms must be <= end_timestamp_utc_ms")
        if not re.fullmatch(r"[0-9a-fA-F]{64}", self.sha256_hash):
            raise ValueError("DatasetSnapshot sha256_hash must be exactly 64 hexadecimal characters")
        return self


class TradeLog(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    trade_id: str
    direction: str = Field(..., description="LONG / SHORT")
    entry_time_utc_ms: int
    exit_time_utc_ms: int
    entry_price: float = Field(..., gt=0.0)
    exit_price: float = Field(..., gt=0.0)
    quantity: float = Field(..., gt=0.0)
    leverage: float = Field(1.0, ge=0.0)
    gross_pnl_usd: float
    fee_usd: float = Field(..., ge=0.0, description="Comisión real pagada (requerida)")
    slippage_usd: float = Field(..., ge=0.0, description="Slippage real incurrido (requerido)")
    net_pnl_usd: float
    return_pct: float
    return_r: float
    exit_reason: str = Field(..., description="STOP_LOSS, TAKE_PROFIT, TRAILING_STOP, SESSION_END, LIQUIDATION")


class EquityPoint(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    timestamp_utc_ms: int
    equity_usd: float
    drawdown_pct: float = Field(0.0, ge=0.0)


class BacktestRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    request_id: str
    strategy_id: str
    strategy: Optional[Any] = Field(None, description="Instancia opcional de CanonicalStrategy para ejecución de AST dinámico")
    engine_type: EngineType = EngineType.FAST_APPROXIMATE
    dataset: DatasetSnapshot
    execution_config_hash: Optional[str] = Field(None, description="Hash SHA256 de la configuración canónica de ejecución")
    initial_capital_usd: float = Field(10000.0, gt=0.0)
    leverage: int = Field(1, ge=1, le=500)
    fee_multiplier: float = Field(1.0, ge=0.0)
    slippage_bps: float = Field(0.0, ge=0.0)
    split_ratio: float = Field(0.70, ge=0.1, le=1.0)


class BacktestResult(BaseModel):
    """Proyección de lectura (Read Model) derivada obligatoriamente del CanonicalExecutionLedger."""
    model_config = ConfigDict(frozen=True, extra="forbid")
    request_id: str
    strategy_id: str
    engine_type: EngineType
    dataset_id: str
    ledger_hash: str = Field(..., description="Hash SHA-256 del CanonicalExecutionLedger de origen")
    
    # Métricas Principales
    initial_capital_usd: float
    final_equity_usd: float
    net_profit_usd: float
    net_return_pct: float
    
    total_trades: int = Field(..., ge=0)
    winning_trades: int = Field(default=0, ge=0)
    losing_trades: int = Field(default=0, ge=0)
    win_rate_pct: float = Field(0.0, ge=0.0, le=100.0)
    
    profit_factor: float = Field(0.0, ge=0.0)
    max_drawdown_pct: float = Field(0.0, ge=0.0)
    max_drawdown_usd: float = Field(0.0, ge=0.0)
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    
    # Telemetría de Trades y Curva
    trades: List[TradeLog] = Field(default_factory=list)
    equity_curve: List[EquityPoint] = Field(default_factory=list)
    execution_time_ms: float = Field(0.0, ge=0.0)
    provenance_hash_sha256: str
