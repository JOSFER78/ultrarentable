"""Ledger and Performance Metrics Generator for FAST Engine."""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class TradeRecord:
    trade_id: str
    symbol: str
    side: str  # LONG, SHORT
    entry_time: int
    entry_price: float
    exit_time: int
    exit_price: float
    quantity: float
    leverage: int
    gross_pnl: float
    fees: float
    funding: float
    net_pnl: float
    return_pct: float
    exit_reason: str  # SIGNAL, STOP_LOSS, TAKE_PROFIT, LIQUIDATION, END_OF_DATA


@dataclass
class EquityPoint:
    timestamp: int
    equity: float
    drawdown_pct: float


@dataclass
class BacktestMetrics:
    initial_capital: float
    final_equity: float
    net_return_pct: float
    max_drawdown_pct: float
    win_rate: float
    trades_count: int
    profit_factor: float
    gross_profit: float
    gross_loss: float
    total_fees: float
    total_funding: float
    sharpe_ratio: float = 0.0


class BacktestLedger:
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.trades: list[TradeRecord] = []
        self.equity_curve: list[EquityPoint] = []
        self.peak_equity = initial_capital

    def record_equity(self, timestamp: int, equity: float) -> None:
        if equity > self.peak_equity:
            self.peak_equity = equity
        drawdown_pct = ((self.peak_equity - equity) / self.peak_equity) * 100.0 if self.peak_equity > 0 else 0.0
        self.equity_curve.append(EquityPoint(timestamp=timestamp, equity=round(equity, 6), drawdown_pct=round(drawdown_pct, 4)))

    def record_trade(self, trade: TradeRecord) -> None:
        self.trades.append(trade)
        self.current_capital += trade.net_pnl

    def compute_metrics(self) -> BacktestMetrics:
        if not self.trades:
            final_eq = self.equity_curve[-1].equity if self.equity_curve else self.initial_capital
            return BacktestMetrics(
                initial_capital=self.initial_capital,
                final_equity=final_eq,
                net_return_pct=((final_eq - self.initial_capital) / self.initial_capital) * 100.0,
                max_drawdown_pct=0.0,
                win_rate=0.0,
                trades_count=0,
                profit_factor=0.0,
                gross_profit=0.0,
                gross_loss=0.0,
                total_fees=0.0,
                total_funding=0.0,
                sharpe_ratio=0.0,
            )

        # Closed-trade capital is authoritative. The equity curve contains
        # intrabar marks and must not override final fees or forced-close PnL.
        final_equity = self.current_capital
        net_return_pct = round(((final_equity - self.initial_capital) / self.initial_capital) * 100.0, 4)
        max_drawdown_pct = round(max((p.drawdown_pct for p in self.equity_curve), default=0.0), 4)

        winning_trades = [t for t in self.trades if t.net_pnl > 0]
        losing_trades = [t for t in self.trades if t.net_pnl < 0]

        win_rate = round((len(winning_trades) / len(self.trades)) * 100.0, 2)
        gross_profit = sum(t.net_pnl for t in winning_trades)
        gross_loss = abs(sum(t.net_pnl for t in losing_trades))

        if gross_loss > 0:
            profit_factor = round(gross_profit / gross_loss, 4)
        elif gross_profit > 0:
            profit_factor = 999.0
        else:
            profit_factor = 0.0

        total_fees = round(sum(t.fees for t in self.trades), 6)
        total_funding = round(sum(t.funding for t in self.trades), 6)

        # Calculate Sharpe Ratio from equity returns
        sharpe = 0.0
        if len(self.equity_curve) > 2:
            eq_vals = [p.equity for p in self.equity_curve]
            returns = [(eq_vals[i] - eq_vals[i - 1]) / eq_vals[i - 1] for i in range(1, len(eq_vals)) if eq_vals[i - 1] > 0]
            if len(returns) > 1:
                std_dev = math.nan
                try:
                    import numpy as np
                    std = np.std(returns, ddof=1)
                    mean = np.mean(returns)
                    if std > 0:
                        sharpe = round((mean / std) * math.sqrt(252 * 24), 2)
                except Exception:
                    pass

        return BacktestMetrics(
            initial_capital=self.initial_capital,
            final_equity=round(final_equity, 4),
            net_return_pct=net_return_pct,
            max_drawdown_pct=max_drawdown_pct,
            win_rate=win_rate,
            trades_count=len(self.trades),
            profit_factor=profit_factor,
            gross_profit=round(gross_profit, 4),
            gross_loss=round(gross_loss, 4),
            total_fees=total_fees,
            total_funding=total_funding,
            sharpe_ratio=sharpe,
        )

    def to_artifacts(self) -> dict[str, Any]:
        metrics = self.compute_metrics()
        trades_dump = [asdict(t) for t in self.trades]
        equity_dump = [asdict(e) for e in self.equity_curve]
        deterministic_payload = {
            "engineType": "FAST_APPROXIMATE",
            "metrics": asdict(metrics),
            "trades": trades_dump,
            "equityCurve": equity_dump,
        }
        json_bytes = json.dumps(deterministic_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        checksum = hashlib.sha256(json_bytes).hexdigest()

        payload = {
            **deterministic_payload,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "checksum": checksum,
        }
        return payload
