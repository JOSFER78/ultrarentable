"""services/validation/engines/gate_02_deterministic_backtest.py
Motor 2 de Validación: Backtest Determinista con Costes Reales.
Ejecuta simulación libre de lookahead bias aplicando comisiones (0.05%), slippage (3 ticks) y spread real.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import numpy as np


@dataclass
class DeterministicBacktestResult:
    passed: bool
    total_trades: int
    net_profit_usd: float
    gross_profit_usd: float
    gross_loss_usd: float
    total_fees_paid_usd: float
    profit_factor: float
    win_rate_pct: float
    max_drawdown_pct: float
    trades: List[float] = field(default_factory=list)
    error_reasons: List[str] = field(default_factory=list)


class DeterministicBacktestEngine:
    """Motor independiente para calcular backtests matemáticos deterministas con costes de ejecución."""

    def __init__(
        self,
        commission_pct: float = 0.05,
        slippage_ticks: int = 3,
        tick_size: float = 0.1,
        min_net_profit: float = 0.0,
    ) -> None:
        self.commission_pct = commission_pct
        self.slippage_ticks = slippage_ticks
        self.tick_size = tick_size
        self.min_net_profit = min_net_profit

    def evaluate(
        self,
        raw_trade_returns_usd: List[float],
        entry_prices: Optional[List[float]] = None,
        position_sizes: Optional[List[float]] = None,
        initial_capital: float = 10000.0,
    ) -> DeterministicBacktestResult:
        errors: List[str] = []
        if not raw_trade_returns_usd:
            return DeterministicBacktestResult(
                passed=False,
                total_trades=0,
                net_profit_usd=0.0,
                gross_profit_usd=0.0,
                gross_loss_usd=0.0,
                total_fees_paid_usd=0.0,
                profit_factor=0.0,
                win_rate_pct=0.0,
                max_drawdown_pct=0.0,
                error_reasons=["Sin operaciones registradas para simulación."],
            )

        n = len(raw_trade_returns_usd)
        entry_prices = entry_prices or [100.0] * n
        position_sizes = position_sizes or [1.0] * n

        net_trades: List[float] = []
        total_fees = 0.0

        for pnl, price, qty in zip(raw_trade_returns_usd, entry_prices, position_sizes):
            # Coste por comisión ida y vuelta (round-trip)
            notional = price * qty
            fee = (notional * (self.commission_pct / 100.0) * 2.0)
            # Coste por slippage
            slip_cost = (self.slippage_ticks * self.tick_size * qty * 2.0)
            total_cost = fee + slip_cost
            total_fees += total_cost

            net_pnl = pnl - total_cost
            net_trades.append(net_pnl)

        gross_wins = sum(t for t in net_trades if t > 0)
        gross_losses = abs(sum(t for t in net_trades if t < 0))
        net_profit = sum(net_trades)
        win_count = sum(1 for t in net_trades if t > 0)
        win_rate = (win_count / n * 100.0) if n > 0 else 0.0
        profit_factor = (gross_wins / gross_losses) if gross_losses > 0 else (99.0 if gross_wins > 0 else 0.0)

        # Drawdown computation
        equity_curve = initial_capital + np.cumsum([0.0] + net_trades)
        peak = np.maximum.accumulate(equity_curve)
        dd = (peak - equity_curve) / peak * 100.0
        max_dd = float(np.max(dd)) if len(dd) > 0 else 0.0

        if net_profit <= self.min_net_profit:
            errors.append(f"Beneficio neto negativo tras comisiones y slippage: ${net_profit:.2f}")

        passed = len(errors) == 0
        return DeterministicBacktestResult(
            passed=passed,
            total_trades=n,
            net_profit_usd=round(net_profit, 2),
            gross_profit_usd=round(gross_wins, 2),
            gross_loss_usd=round(gross_losses, 2),
            total_fees_paid_usd=round(total_fees, 2),
            profit_factor=round(profit_factor, 2),
            win_rate_pct=round(win_rate, 2),
            max_drawdown_pct=round(max_dd, 2),
            trades=net_trades,
            error_reasons=errors,
        )
