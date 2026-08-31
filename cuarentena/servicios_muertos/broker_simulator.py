"""services/paper/broker_simulator.py
Simulador de broker en tiempo real con modelado de slippage y latencia para Paper Trading.
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class PaperOrder(BaseModel):
    model_config = ConfigDict(frozen=True)
    order_id: str
    symbol: str
    side: str
    quantity: float
    order_type: str = "MARKET"
    limit_price: Optional[float] = None
    created_at_ms: int = Field(default_factory=lambda: int(time.time() * 1000))


class PaperExecutionFill(BaseModel):
    model_config = ConfigDict(frozen=True)
    fill_id: str
    order_id: str
    fill_price: float
    filled_quantity: float
    fee_usd: float
    slippage_usd: float
    timestamp_ms: int = Field(default_factory=lambda: int(time.time() * 1000))


class PaperBrokerSimulator:
    """Broker simulado en memoria."""

    def __init__(self, slippage_bps: float = 0.5, fee_bps: float = 2.0) -> None:
        self.slippage_bps = slippage_bps
        self.fee_bps = fee_bps

    def execute_order(self, order: PaperOrder, mark_price: float) -> PaperExecutionFill:
        slippage_price = mark_price * (1.0 + (self.slippage_bps / 10000.0) if order.side == "BUY" else 1.0 - (self.slippage_bps / 10000.0))
        notional = slippage_price * order.quantity
        fee = notional * (self.fee_bps / 10000.0)

        return PaperExecutionFill(
            fill_id=f"fill_{order.order_id}",
            order_id=order.order_id,
            fill_price=round(slippage_price, 4),
            filled_quantity=order.quantity,
            fee_usd=round(fee, 4),
            slippage_usd=round(abs(slippage_price - mark_price) * order.quantity, 4),
        )
