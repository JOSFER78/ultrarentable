"""contracts/canonical_execution.py
Capa Canónica de Ejecución y Registro de Verdad (ExecutionTruth & CanonicalExecutionLedger).
Garantiza que FastEngine, NautilusGateEngine y SQX operen bajo el mismo modelo de microestructura y costes.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AssetClass(str, Enum):
    CRYPTO_PERPETUAL = "CRYPTO_PERPETUAL"
    FOREX_SPOT = "FOREX_SPOT"
    CME_FUTURES = "CME_FUTURES"
    COMMODITIES = "COMMODITIES"


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_MARKET = "STOP_MARKET"


class ExitReason(str, Enum):
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"
    TRAILING_STOP = "TRAILING_STOP"
    SESSION_END = "SESSION_END"
    SIGNAL_REVERSAL = "SIGNAL_REVERSAL"
    LIQUIDATION = "LIQUIDATION"
    KILL_SWITCH = "KILL_SWITCH"


class InstrumentCostProfile(BaseModel):
    """Perfil estricto de costes y microestructura. Prohibido omitir parámetros."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    symbol: str = Field(..., description="Símbolo normalizado e.g. SUIUSDT, EURUSD, NQ, BTCUSDT")
    asset_class: AssetClass
    point_value: float = Field(..., gt=0.0, description="Valor en USD de 1 punto de precio")
    tick_size: float = Field(..., gt=0.0, description="Variación mínima de precio")
    contract_multiplier: float = Field(1.0, gt=0.0, description="Multiplicador de contrato (e.g. 100,000 para Forex)")
    
    # Comisiones y fricción obligatorias (prohibido default 0 silencioso en producción)
    taker_fee_pct: float = Field(..., ge=0.0, description="Comisión taker % (e.g. 0.05% cripto, $2.50/lote forex)")
    maker_fee_pct: float = Field(..., ge=0.0, description="Comisión maker %")
    typical_spread_ticks: float = Field(..., ge=0.0, description="Spread medio en ticks")
    slippage_ticks_baseline: float = Field(..., ge=0.0, description="Slippage base en ticks")
    funding_rate_8h_pct: Optional[float] = Field(None, description="Tasa de financiación 8h para perps cripto")


class ExecutionTruth(BaseModel):
    """Registro inmutable trade-by-trade con trazabilidad de hashes y microestructura física."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    trade_id: str
    symbol: str
    side: OrderSide
    
    # Timestamps y Hashes de Provenance
    entry_timestamp_utc_ms: int
    exit_timestamp_utc_ms: int
    market_data_hash: str
    strategy_snapshot_hash: str
    execution_config_hash: str

    # Precios y Cantidad
    decision_price: float = Field(..., gt=0.0)
    requested_qty: float = Field(..., gt=0.0)
    filled_qty: float = Field(..., gt=0.0)
    entry_price: float = Field(..., gt=0.0)
    exit_price: float = Field(..., gt=0.0)
    stop_loss_px: Optional[float] = None
    take_profit_px: Optional[float] = None

    # Costes Reales Desglosados
    commission_usd: float = Field(..., ge=0.0)
    slippage_usd: float = Field(..., ge=0.0)
    funding_usd: float = Field(0.0)
    total_friction_cost_usd: float = Field(..., ge=0.0)

    # Resultados Financieros
    gross_pnl_usd: float
    net_pnl_usd: float
    return_r: float
    exit_reason: ExitReason

    # Riesgo y Margen
    notional_usd: float = Field(..., gt=0.0)
    margin_used_usd: float = Field(..., gt=0.0)
    leverage_actual: float = Field(..., ge=0.0)

    # Balance y Curva
    equity_before_usd: float = Field(..., gt=0.0)
    equity_after_usd: float = Field(..., ge=0.0)
    drawdown_after_pct: float = Field(..., ge=0.0, le=100.0)


class CanonicalExecutionLedger(BaseModel):
    """Ledger canónico de ejecución: la única fuente autorizada de trades y balance."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    strategy_id: str
    strategy_snapshot_hash: str
    dataset_sha256: str
    execution_config_hash: str
    engine_name: str
    
    initial_capital_usd: float = Field(..., gt=0.0)
    final_equity_usd: float = Field(..., ge=0.0)
    net_profit_usd: float
    roi_pct: float
    profit_factor: float = Field(..., ge=0.0)
    win_rate_pct: float = Field(..., ge=0.0, le=100.0)
    max_drawdown_pct: float = Field(..., ge=0.0, le=100.0)
    peak_leverage_used: float = Field(..., ge=0.0)
    
    total_trades_count: int = Field(..., ge=0)
    winning_trades_count: int = Field(..., ge=0)
    losing_trades_count: int = Field(..., ge=0)
    
    total_commission_paid_usd: float = Field(..., ge=0.0)
    total_slippage_paid_usd: float = Field(..., ge=0.0)
    total_funding_paid_usd: float = 0.0
    
    trades: List[ExecutionTruth] = Field(default_factory=list)
    ledger_hash: str = ""

    def model_post_init(self, __context: Any) -> None:
        """Auto-calcula y sella criptográficamente el hash del ledger en la inicialización."""
        if not self.ledger_hash:
            calculated = self.calculate_ledger_hash()
            object.__setattr__(self, "ledger_hash", calculated)

    def calculate_ledger_hash(self) -> str:
        """Calcula el hash criptográfico determinista mediante Hash-Chain secuencial sobre toda la serie ordenada de trades.
        Garantiza sensibilidad absoluta al orden de operaciones, microestructura, comisiones, slippage y equity.
        """
        genesis_payload = (
            f"{self.strategy_id}:{self.strategy_snapshot_hash}:{self.dataset_sha256}:"
            f"{self.execution_config_hash}:{self.engine_name}:{self.initial_capital_usd:.4f}"
        )
        current_hash = hashlib.sha256(genesis_payload.encode("utf-8")).hexdigest()

        for trade in self.trades:
            trade_dict = trade.model_dump()
            trade_str = json.dumps(trade_dict, sort_keys=True, separators=(",", ":"))
            chain_payload = f"{current_hash}:{trade_str}"
            current_hash = hashlib.sha256(chain_payload.encode("utf-8")).hexdigest()

        summary_payload = (
            f"{current_hash}:{self.final_equity_usd:.4f}:{self.total_trades_count}:"
            f"{self.net_profit_usd:.4f}:{self.total_commission_paid_usd:.4f}:{self.total_slippage_paid_usd:.4f}"
        )
        return hashlib.sha256(summary_payload.encode("utf-8")).hexdigest()
