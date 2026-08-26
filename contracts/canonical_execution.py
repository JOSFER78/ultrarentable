"""contracts/canonical_execution.py
Contratos Can?nicos de Ejecuci?n, Microestructura y Ledger (Fase 02 / Fase 03).
ZERO-MOCKS ? REAL-ONLY ? DETERMINISTIC ? NO-LOOKAHEAD ? PROVENANCE-LOCKED ? FAIL-CLOSED
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
    FOREX_SPOT = "FOREX_SPOT"
    CME_FUTURES = "CME_FUTURES"
    COMMODITIES = "COMMODITIES"
    COMMODITY_FUTURES = "COMMODITIES"
    EQUITY_STOCK = "EQUITY_STOCK"
    INDEX_CFD = "INDEX_CFD"


class InstrumentCostProfile(BaseModel):
    """Perfil can?nico inmutable de costes y microestructura de un activo."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    symbol: str = Field(..., description="S?mbolo can?nico del activo (ej. BTCUSDT, NQ, EURUSD)")
    asset_class: AssetClass = Field(..., description="Clase de activo can?nico")
    point_value: float = Field(..., gt=0.0, description="Valor monetario en USD por punto completo de movimiento")
    tick_size: float = Field(..., gt=0.0, description="Tama?o m?nimo de variaci?n de precio (tick)")
    contract_multiplier: float = Field(default=1.0, gt=0.0, description="Multiplicador de contrato o tama?o de lote")
    taker_fee_pct: float = Field(default=0.0, ge=0.0, description="Comisi?n taker porcentual (ej. 0.050 para 0.050%)")
    maker_fee_pct: float = Field(default=0.0, ge=0.0, description="Comisi?n maker porcentual (ej. 0.020 para 0.020%)")
    typical_spread_ticks: float = Field(default=1.0, ge=0.0, description="Spread t?pico en ticks")
    slippage_ticks_baseline: float = Field(default=1.0, ge=0.0, description="Deslizamiento esperado baseline en ticks")
    funding_rate_8h_pct: float = Field(default=0.0, ge=0.0, description="Tasa de financiaci?n estimada cada 8h en %")


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class ExitReason(str, Enum):
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"
    TRAILING_STOP = "TRAILING_STOP"
    TIME_STOP = "TIME_STOP"
    SESSION_EOD = "SESSION_EOD"
    KILL_SWITCH = "KILL_SWITCH"
    LIQUIDATION = "LIQUIDATION"
    MANUAL = "MANUAL"


class ExecutionTruth(BaseModel):
    """Registro inmutable de la verdad f?sica de una orden ejecutada."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    trade_id: str
    symbol: str
    side: OrderSide
    entry_timestamp_utc_ms: int
    exit_timestamp_utc_ms: int
    market_data_hash: str
    strategy_snapshot_hash: str
    execution_config_hash: str
    decision_price: float
    requested_qty: float
    filled_qty: float
    entry_price: float
    exit_price: float
    stop_loss_px: Optional[float] = None
    take_profit_px: Optional[float] = None
    commission_usd: float
    slippage_usd: float
    funding_usd: float = 0.0
    total_friction_cost_usd: float
    gross_pnl_usd: float
    net_pnl_usd: float
    return_r: float
    exit_reason: ExitReason
    notional_usd: float
    margin_used_usd: float
    leverage_actual: float
    equity_before_usd: float
    equity_after_usd: float
    drawdown_after_pct: float = 0.0


class CanonicalExecutionLedger(BaseModel):
    """Ledger can?nico inmutable de ejecuci?n determinista con sellado criptogr?fico."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    strategy_id: str
    strategy_snapshot_hash: str
    dataset_sha256: str
    execution_config_hash: str
    engine_name: str = "EventBacktestEngine"
    initial_capital_usd: float
    final_equity_usd: float
    net_profit_usd: float
    roi_pct: float
    profit_factor: float
    win_rate_pct: float
    max_drawdown_pct: float
    peak_leverage_used: float
    total_trades_count: int
    winning_trades_count: int
    losing_trades_count: int
    total_commission_paid_usd: float
    total_slippage_paid_usd: float
    total_funding_paid_usd: float = Field(default=0.0)
    trades: List[ExecutionTruth]
    ledger_hash: Optional[str] = None

    def compute_ledger_hash(self) -> str:
        payload = self.model_dump(exclude={"ledger_hash"})
        raw_json = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(raw_json.encode("utf-8")).hexdigest()

    def calculate_ledger_hash(self) -> str:
        return self.compute_ledger_hash()

    def model_post_init(self, __context: Any) -> None:
        if self.ledger_hash is None:
            computed = self.compute_ledger_hash()
            object.__setattr__(self, "ledger_hash", computed)

    def verify_ledger_integrity(self) -> bool:
        expected = self.compute_ledger_hash()
        return self.ledger_hash == expected

