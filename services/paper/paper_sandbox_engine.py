"""services/paper/paper_sandbox_engine.py
Sandbox de Paper Trading en Tiempo Real para Ultrarentable V2.
Simula la ejecución de estrategias en vivo con latencia de red, slippage realista y contabilidad de PnL tick a tick.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from contracts.canonical_strategy import CanonicalStrategy, ExecutionTrack
from contracts.backtest import BarData, TradeLog


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
    """Motor de simulación y ejecución paper trading en memoria."""

    def __init__(
        self,
        default_latency_ms: int = 50,
        slippage_ticks: float = 1.0,
    ) -> None:
        self.latency_ms = default_latency_ms
        self.slippage_ticks = slippage_ticks
        self._positions: Dict[str, PaperPosition] = {}

    def register_strategy(self, strategy: CanonicalStrategy) -> None:
        strat_id = strategy.strategy_id
        if strat_id not in self._positions:
            self._positions[strat_id] = PaperPosition(
                strategy_id=strat_id,
                symbol=strategy.instrument.symbol,
            )

    def get_position(self, strategy_id: str) -> PaperPosition:
        if strategy_id not in self._positions:
            raise KeyError(f"Estrategia {strategy_id} no registrada en el Sandbox.")
        return self._positions[strategy_id]

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
        """Abre una posición aplicando modelo de slippage y latencia."""
        self.register_strategy(strategy)
        pos = self._positions[strategy.strategy_id]
        if pos.side != PositionSide.FLAT:
            return pos  # Ya tiene posición abierta

        # Aplicar slippage adverso
        tick_sz = strategy.instrument.tick_size
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

    def update_market_price(
        self,
        strategy: CanonicalStrategy,
        current_price: float,
        timestamp_ms: int,
    ) -> Tuple[PaperPosition, Optional[TradeLog]]:
        """Actualiza el precio en vivo y comprueba si salta Stop Loss o Take Profit."""
        self.register_strategy(strategy)
        pos = self._positions[strategy.strategy_id]
        if pos.side == PositionSide.FLAT:
            return pos, None

        pos.current_price = current_price
        mult = 1.0 if pos.side == PositionSide.LONG else -1.0
        pt_val = strategy.instrument.point_value
        price_diff = (current_price - pos.entry_price_avg) * mult
        pos.unrealized_pnl_usd = price_diff * pos.quantity * pt_val

        # Comprobar SL
        is_sl_hit = False
        if pos.stop_loss_price:
            if pos.side == PositionSide.LONG and current_price <= pos.stop_loss_price:
                is_sl_hit = True
            elif pos.side == PositionSide.SHORT and current_price >= pos.stop_loss_price:
                is_sl_hit = True

        # Comprobar TP
        is_tp_hit = False
        if pos.take_profit_price:
            if pos.side == PositionSide.LONG and current_price >= pos.take_profit_price:
                is_tp_hit = True
            elif pos.side == PositionSide.SHORT and current_price <= pos.take_profit_price:
                is_tp_hit = True

        if is_sl_hit or is_tp_hit:
            exit_reason = "STOP_LOSS" if is_sl_hit else "TAKE_PROFIT"
            exit_price = pos.stop_loss_price if is_sl_hit else pos.take_profit_price
            closed_log = self._close_position(strategy, pos, exit_price or current_price, timestamp_ms, exit_reason)
            return pos, closed_log

        return pos, None

    def close_all_session_end(
        self,
        strategy: CanonicalStrategy,
        current_price: float,
        timestamp_ms: int,
    ) -> Optional[TradeLog]:
        """Cierre forzado al fin de sesión para cumplimiento de reglas prop."""
        pos = self._positions.get(strategy.strategy_id)
        if not pos or pos.side == PositionSide.FLAT:
            return None
        return self._close_position(strategy, pos, current_price, timestamp_ms, "SESSION_END")

    def _close_position(
        self,
        strategy: CanonicalStrategy,
        pos: PaperPosition,
        exit_price: float,
        timestamp_ms: int,
        reason: str,
    ) -> TradeLog:
        mult = 1.0 if pos.side == PositionSide.LONG else -1.0
        pt_val = strategy.instrument.point_value
        gross_pnl = (exit_price - pos.entry_price_avg) * mult * pos.quantity * pt_val
        fee = 2.50 * pos.quantity
        net_pnl = gross_pnl - fee

        log = TradeLog(
            trade_id=f"paper_trade_{strategy.strategy_id}_{len(pos.trade_history) + 1}",
            direction=pos.side.value,
            entry_time_utc_ms=pos.opened_at_utc_ms,
            exit_time_utc_ms=timestamp_ms,
            entry_price=pos.entry_price_avg,
            exit_price=exit_price,
            quantity=pos.quantity,
            leverage=strategy.sizing_and_risk.base_leverage,
            gross_pnl_usd=round(gross_pnl, 2),
            fee_usd=fee,
            slippage_usd=round(self.slippage_ticks * strategy.instrument.tick_size * pt_val, 2),
            net_pnl_usd=round(net_pnl, 2),
            return_pct=round((exit_price - pos.entry_price_avg) / pos.entry_price_avg * 100.0 * mult, 2),
            return_r=round(net_pnl / 100.0, 2),
            exit_reason=reason,
        )

        pos.realized_pnl_usd += net_pnl
        pos.unrealized_pnl_usd = 0.0
        pos.side = PositionSide.FLAT
        pos.quantity = 0.0
        pos.trade_history.append(log)

        return log
