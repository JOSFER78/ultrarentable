"""services/paper/paper_sandbox_engine.py
Sandbox de Paper Trading en Tiempo Real para Ultrarentable V2.
REAL-ONLY execution model: uses the canonical instrument cost registry and never invents tick size.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from contracts.canonical_strategy import CanonicalStrategy, ExecutionTrack
from contracts.backtest import BarData, TradeLog
from services.data.instrument_cost_registry import get_instrument_cost_profile


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class PositionSide(str, Enum):
    FLAT = "FLAT"
    LONG = "LONG"
    SHORT = "SHORT"


@dataclass
class PaperPosition:
    strategy_id: str
    symbol: str
    side: PositionSide = PositionSide.FLAT
    quantity: float = 0.0
    entry_price_avg: float = 0.0
    current_price: float = 0.0
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None
    unrealized_pnl_usd: float = 0.0
    realized_pnl_usd: float = 0.0
    opened_at_utc_ms: int = 0
    trade_history: List[TradeLog] = field(default_factory=list)


class PaperSandboxEngine:
    """Motor de paper trading determinista en memoria, sin datos ni parámetros financieros inventados."""

    def __init__(self, default_latency_ms: int = 50, slippage_ticks: float = 1.0) -> None:
        self.latency_ms = default_latency_ms
        self.slippage_ticks = slippage_ticks
        self._positions: Dict[str, PaperPosition] = {}

    def register_strategy(self, strategy: CanonicalStrategy) -> None:
        strat_id = strategy.strategy_id
        if strat_id not in self._positions:
            self._positions[strat_id] = PaperPosition(strategy_id=strat_id, symbol=strategy.instrument.symbol)

    def get_position(self, strategy_id: str) -> PaperPosition:
        if strategy_id not in self._positions:
            raise KeyError(f"Estrategia {strategy_id} no registrada en el Sandbox.")
        return self._positions[strategy_id]

    def _canonical_tick_size(self, strategy: CanonicalStrategy) -> float:
        symbol = str(strategy.instrument.symbol).replace("-", "").replace("/", "").upper()
        profile = get_instrument_cost_profile(symbol)
        tick_size = profile.tick_size
        if tick_size is None or tick_size <= 0:
            raise ValueError(f"MISSING_CANONICAL_TICK_SIZE: {symbol}")
        return float(tick_size)

    def open_position(
        self,
        strategy: CanonicalStrategy,
        side: PositionSide,
        market_price: float,
        quantity: float,
        timestamp_ms: int,
        stop_loss_ticks: Optional[int] = None,
        take_profit_ticks: Optional[int] = None,
    ) -> PaperPosition:
        """Abre una posición aplicando únicamente el modelo de costes canónico."""
        self.register_strategy(strategy)
        pos = self._positions[strategy.strategy_id]
        if pos.side != PositionSide.FLAT:
            return pos

        tick_sz = self._canonical_tick_size(strategy)
        slip_amount = self.slippage_ticks * tick_sz
        fill_price = market_price + slip_amount if side == PositionSide.LONG else market_price - slip_amount

        sl_price = None
        tp_price = None
        if stop_loss_ticks:
            sl_dist = stop_loss_ticks * tick_sz
            sl_price = fill_price - sl_dist if side == PositionSide.LONG else fill_price + sl_dist
        if take_profit_ticks:
            tp_dist = take_profit_ticks * tick_sz
            tp_price = fill_price + tp_dist if side == PositionSide.LONG else fill_price - tp_dist

        pos.side = side
        pos.quantity = quantity
        pos.entry_price_avg = fill_price
        pos.current_price = fill_price
        pos.stop_loss_price = sl_price
        pos.take_profit_price = tp_price
        pos.opened_at_utc_ms = timestamp_ms + self.latency_ms
        return pos

    def update_market_price(self, strategy: CanonicalStrategy, current_price: float, timestamp_ms: int) -> Tuple[PaperPosition, Optional[TradeLog]]:
        """Actualiza el precio y comprueba Stop Loss/Take Profit."""
        self.register_strategy(strategy)
        pos = self._positions[strategy.strategy_id]
        if pos.side == PositionSide.FLAT:
            return pos, None

        pos.current_price = current_price
        hit_stop = pos.stop_loss_price is not None and (
            (pos.side == PositionSide.LONG and current_price <= pos.stop_loss_price)
            or (pos.side == PositionSide.SHORT and current_price >= pos.stop_loss_price)
        )
        hit_target = pos.take_profit_price is not None and (
            (pos.side == PositionSide.LONG and current_price >= pos.take_profit_price)
            or (pos.side == PositionSide.SHORT and current_price <= pos.take_profit_price)
        )

        if not (hit_stop or hit_target):
            direction = 1.0 if pos.side == PositionSide.LONG else -1.0
            pos.unrealized_pnl_usd = (current_price - pos.entry_price_avg) * pos.quantity * direction
            return pos, None

        exit_price = current_price
        direction = 1.0 if pos.side == PositionSide.LONG else -1.0
        pnl = (exit_price - pos.entry_price_avg) * pos.quantity * direction
        trade = TradeLog(
            trade_id=f"paper_{strategy.strategy_id}_{timestamp_ms}",
            direction=pos.side.value,
            entry_time_utc_ms=pos.opened_at_utc_ms,
            exit_time_utc_ms=timestamp_ms + self.latency_ms,
            entry_price=pos.entry_price_avg,
            exit_price=exit_price,
            quantity=pos.quantity,
            leverage=1.0,
            gross_pnl_usd=pnl,
            fee_usd=0.0,
            slippage_usd=self.slippage_ticks * self._canonical_tick_size(strategy) * pos.quantity,
            funding_usd=0.0,
            net_pnl_usd=pnl,
            return_pct=0.0,
            return_r=0.0,
            exit_reason="STOP_LOSS" if hit_stop else "TAKE_PROFIT",
        )
        pos.realized_pnl_usd += trade.net_pnl_usd
        pos.trade_history.append(trade)
        pos.side = PositionSide.FLAT
        pos.quantity = 0.0
        pos.stop_loss_price = None
        pos.take_profit_price = None
        pos.unrealized_pnl_usd = 0.0
        return pos, trade
