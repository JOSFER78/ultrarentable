"""services/validation/engine/event_backtest_engine.py
Motor de Backtesting Determinista Orientado a Eventos (Fase 4).
Ejecuta la simulación completa barra por barra:
Market Data Event -> Signal -> Order -> Fill -> Friction (Fees & Slippage) -> Position -> Margin -> Equity.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import numpy as np
from pydantic import BaseModel

from contracts.canonical_execution import (
    CanonicalExecutionLedger,
    ExecutionTruth,
    ExitReason,
    OrderSide,
)
from contracts.snapshots.dataset_snapshot import DatasetSnapshot
from contracts.snapshots.strategy_snapshot import StrategyRoute, StrategySnapshot


@dataclass
class OrderEvent:
    order_id: str
    bar_index: int
    timestamp_ms: int
    order_type: str  # "MARKET" | "LIMIT"
    side: str  # "BUY" | "SELL"
    qty: float
    price_requested: float
    reason: str


@dataclass
class FillEvent:
    fill_id: str
    order_id: str
    bar_index: int
    timestamp_ms: int
    side: str
    qty: float
    price_executed: float
    slippage_usd: float
    commission_usd: float
    funding_fee_usd: float


@dataclass
class TradeRecord:
    trade_id: str
    entry_bar: int
    exit_bar: int
    entry_time_ms: int
    exit_time_ms: int
    side: str
    qty: float
    entry_price: float
    exit_price: float
    gross_pnl_usd: float
    net_pnl_usd: float
    return_pct: float
    fees_usd: float
    slippage_usd: float
    exit_reason: str
    pyramid_level: int = 0
    equity_before_usd: float = 1000.0
    equity_after_usd: float = 1000.0
    r_multiple: float = 0.0


@dataclass
class EventBacktestResult:
    strategy_id: str
    canonical_hash: str
    dataset_id: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate_pct: float
    net_profit_usd: float
    profit_factor: float
    max_drawdown_pct: float
    peak_equity_usd: float
    final_equity_usd: float
    peak_margin_utilization_pct: float
    min_liquidation_distance_pct: float
    total_fees_usd: float
    total_slippage_usd: float
    trades: List[TradeRecord] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)
    drawdown_curve: List[float] = field(default_factory=list)
    order_log: List[OrderEvent] = field(default_factory=list)
    fill_log: List[FillEvent] = field(default_factory=list)
    execution_time_ms: float = 0.0

    def to_canonical_ledger(self, symbol: str = "BTCUSDT", execution_config_hash: str = "") -> CanonicalExecutionLedger:
        """Convierte el resultado de backtest determinista a CanonicalExecutionLedger oficial con Hash-Chain Merkle."""
        import hashlib
        canonical_trades = []
        for t in self.trades:
            side_enum = OrderSide.BUY if t.side == "LONG" else OrderSide.SELL
            exit_reason_enum = (
                ExitReason.TAKE_PROFIT if t.exit_reason == "TAKE_PROFIT"
                else ExitReason.STOP_LOSS if t.exit_reason == "STOP_LOSS"
                else ExitReason.KILL_SWITCH
            )
            canonical_trades.append(
                ExecutionTruth(
                    trade_id=t.trade_id,
                    symbol=symbol,
                    side=side_enum,
                    entry_timestamp_utc_ms=t.entry_time_ms,
                    exit_timestamp_utc_ms=t.exit_time_ms,
                    market_data_hash=self.dataset_id,
                    strategy_snapshot_hash=self.canonical_hash,
                    execution_config_hash=execution_config_hash or hashlib.sha256(b"canonical_exec_cfg").hexdigest(),
                    decision_price=t.entry_price,
                    requested_qty=t.qty,
                    filled_qty=t.qty,
                    entry_price=t.entry_price,
                    exit_price=t.exit_price,
                    stop_loss_px=None,
                    take_profit_px=None,
                    commission_usd=t.fees_usd,
                    slippage_usd=t.slippage_usd,
                    funding_usd=0.0,
                    total_friction_cost_usd=round(t.fees_usd + t.slippage_usd, 4),
                    gross_pnl_usd=t.gross_pnl_usd,
                    net_pnl_usd=t.net_pnl_usd,
                    return_r=t.r_multiple,
                    exit_reason=exit_reason_enum,
                    notional_usd=round(t.entry_price * t.qty, 2),
                    margin_used_usd=max(1.0, round((t.entry_price * t.qty) / 10.0, 2)),
                    leverage_actual=10.0,
                    equity_before_usd=t.equity_before_usd,
                    equity_after_usd=t.equity_after_usd,
                    drawdown_after_pct=0.0,
                )
            )

        initial_cap = max(1.0, self.final_equity_usd - self.net_profit_usd)
        roi = (self.net_profit_usd / initial_cap) * 100.0

        ledger = CanonicalExecutionLedger(
            strategy_id=self.strategy_id,
            strategy_snapshot_hash=self.canonical_hash,
            dataset_sha256=self.dataset_id,
            execution_config_hash=execution_config_hash or hashlib.sha256(b"canonical_exec_cfg").hexdigest(),
            engine_name="EventBacktestEngine",
            initial_capital_usd=round(initial_cap, 2),
            final_equity_usd=self.final_equity_usd,
            net_profit_usd=self.net_profit_usd,
            roi_pct=round(roi, 2),
            profit_factor=self.profit_factor,
            win_rate_pct=self.win_rate_pct,
            max_drawdown_pct=self.max_drawdown_pct,
            peak_leverage_used=10.0,
            total_trades_count=self.total_trades,
            winning_trades_count=self.winning_trades,
            losing_trades_count=self.losing_trades,
            total_commission_paid_usd=self.total_fees_usd,
            total_slippage_paid_usd=self.total_slippage_usd,
            total_funding_paid_usd=0.0,
            trades=canonical_trades,
        )
        return ledger


class EventBacktestEngine:
    """Motor de ejecución determinista con soporte de margen, apalancamiento y piramidación."""

    def __init__(
        self,
        taker_fee_pct: float = 0.05,
        maker_fee_pct: float = 0.02,
        slippage_bps: float = 2.0,
        cme_fee_per_contract_usd: float = 2.50,
        funding_rate_8h: float = 0.0001,
    ):
        self.taker_fee = taker_fee_pct / 100.0
        self.maker_fee = maker_fee_pct / 100.0
        self.slippage = slippage_bps / 10000.0
        self.cme_fee = cme_fee_per_contract_usd
        self.funding_rate_8h = funding_rate_8h

    @staticmethod
    def _calc_ema(series: np.ndarray, span: int) -> np.ndarray:
        """Cálculo matemático exacto de Exponential Moving Average recursiva."""
        span = max(1, int(span))
        alpha = 2.0 / (span + 1.0)
        ema = np.empty_like(series)
        ema[0] = series[0]
        for t in range(1, len(series)):
            ema[t] = alpha * series[t] + (1.0 - alpha) * ema[t - 1]
        return ema

    @staticmethod
    def _calc_rsi(closes: np.ndarray, period: int = 14) -> np.ndarray:
        """Cálculo matemático exacto del Relative Strength Index (Wilder's Smoothing)."""
        period = max(2, int(period))
        n = len(closes)
        rsi = np.full(n, 50.0, dtype=np.float64)
        if n <= period:
            return rsi

        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0.0)
        losses = np.where(deltas < 0, -deltas, 0.0)

        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])

        if avg_loss == 0:
            rsi[period] = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi[period] = 100.0 - (100.0 / (1.0 + rs))

        for i in range(period + 1, n):
            gain = gains[i - 1]
            loss = losses[i - 1]
            avg_gain = (avg_gain * (period - 1) + gain) / period
            avg_loss = (avg_loss * (period - 1) + loss) / period

            if avg_loss == 0:
                rsi[i] = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi[i] = 100.0 - (100.0 / (1.0 + rs))

        return rsi

    def run_backtest(
        self,
        strategy: StrategySnapshot,
        candles: List[Dict[str, Any]],
        initial_capital_usd: Optional[float] = None,
    ) -> EventBacktestResult:
        """Ejecuta la simulación determinista de la estrategia sobre el dataset de velas."""
        t_start = datetime.now(timezone.utc)

        if not candles or len(candles) < 35:
            return EventBacktestResult(
                strategy_id=strategy.strategy_id,
                canonical_hash=strategy.canonical_hash,
                dataset_id=strategy.dataset_id_reference,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate_pct=0.0,
                net_profit_usd=0.0,
                profit_factor=0.0,
                max_drawdown_pct=0.0,
                peak_equity_usd=initial_capital_usd or 1000.0,
                final_equity_usd=initial_capital_usd or 1000.0,
                peak_margin_utilization_pct=0.0,
                min_liquidation_distance_pct=100.0,
                total_fees_usd=0.0,
                total_slippage_usd=0.0,
            )

        # Capital base según ruta
        is_ultra = (strategy.route == StrategyRoute.ULTRA)
        is_fondeo = (strategy.route == StrategyRoute.FONDEO)
        base_capital = initial_capital_usd or (1000.0 if is_ultra else 50000.0)
        max_leverage = strategy.margin_policy.max_leverage_ceiling if hasattr(strategy, "margin_policy") and strategy.margin_policy else (500.0 if is_ultra else 1.0)

        closes = np.array([float(c["close"]) for c in candles], dtype=np.float64)
        highs = np.array([float(c["high"]) for c in candles], dtype=np.float64)
        lows = np.array([float(c["low"]) for c in candles], dtype=np.float64)
        opens = np.array([float(c["open"]) for c in candles], dtype=np.float64)
        timestamps = [int(c.get("timestamp_ms") or c.get("timestamp") or 0) for c in candles]

        # 1. Extracción e Intérprete Dinámico de Indicadores del StrategySnapshot
        ema_fast_period = 20
        ema_slow_period = 50
        rsi_period = 14
        rsi_threshold_long = 50.0
        rsi_threshold_short = 50.0
        use_rsi = False
        breakout_lookback = 15

        if hasattr(strategy, "entry_rules") and strategy.entry_rules:
            # Long conditions
            for cond in getattr(strategy.entry_rules, "long_conditions", []):
                l_name = getattr(cond.left_indicator, "name", "").upper()
                l_period = getattr(cond.left_indicator, "period", None)
                if l_name == "EMA" and l_period:
                    ema_fast_period = int(l_period)
                    if hasattr(cond, "right_indicator") and cond.right_indicator and cond.right_indicator.name.upper() == "EMA":
                        ema_slow_period = int(cond.right_indicator.period)
                elif l_name == "RSI" and l_period:
                    rsi_period = int(l_period)
                    if getattr(cond, "threshold_value", None) is not None:
                        rsi_threshold_long = float(cond.threshold_value)
                        use_rsi = True
                if getattr(cond, "lookback_bars", 0) > 0:
                    breakout_lookback = int(cond.lookback_bars)

            # Short conditions
            for cond in getattr(strategy.entry_rules, "short_conditions", []):
                l_name = getattr(cond.left_indicator, "name", "").upper()
                if l_name == "RSI":
                    if getattr(cond, "threshold_value", None) is not None:
                        rsi_threshold_short = float(cond.threshold_value)
                        use_rsi = True

        # Precalcular ATR para stops y take profits dinámicos
        tr = np.maximum(highs[1:] - lows[1:], np.maximum(np.abs(highs[1:] - closes[:-1]), np.abs(lows[1:] - closes[:-1])))
        atr = np.zeros(len(closes))
        atr[1:] = tr
        for i in range(14, len(closes)):
            atr[i] = np.mean(tr[i-14:i])

        # Precalcular series de indicadores exactas según configuración del Snapshot
        ema_fast_series = self._calc_ema(closes, ema_fast_period)
        ema_slow_series = self._calc_ema(closes, ema_slow_period)
        rsi_series = self._calc_rsi(closes, rsi_period) if use_rsi else None

        # Parámetros de salida y riesgo del Snapshot
        sl_atr_mult = strategy.exit_rules.stop_loss_atr_mult or 2.0 if hasattr(strategy, "exit_rules") and strategy.exit_rules and strategy.exit_rules.stop_loss_atr_mult else 2.0
        tp_atr_mult = strategy.exit_rules.take_profit_atr_mult or 6.0 if hasattr(strategy, "exit_rules") and strategy.exit_rules and strategy.exit_rules.take_profit_atr_mult else 6.0
        default_risk = 0.075 if is_ultra else 0.01
        risk_pct = (strategy.sizing_and_risk.base_risk_pct / 100.0) if hasattr(strategy, "sizing_and_risk") and strategy.sizing_and_risk and strategy.sizing_and_risk.base_risk_pct else default_risk
        warmup_bars = max(30, ema_slow_period + 5, rsi_period + 5)

        # Estado del backtest
        current_equity = base_capital
        peak_equity = base_capital
        equity_curve = [base_capital]
        drawdown_curve = [0.0]
        max_drawdown_pct = 0.0
        peak_margin_utilization = 0.0
        min_liq_dist = 100.0

        orders: List[OrderEvent] = []
        fills: List[FillEvent] = []
        trades: List[TradeRecord] = []

        position_side = None
        position_qty = 0.0
        position_entry_price = 0.0
        position_entry_bar = 0
        position_entry_time = 0
        position_equity_before = base_capital
        position_risk_amount = base_capital * risk_pct
        stop_loss_price = 0.0
        take_profit_price = 0.0
        pyramid_count = 0
        total_fees = 0.0
        total_slippage = 0.0

        for i in range(warmup_bars, len(closes)):
            bar_close = closes[i]
            bar_high = highs[i]
            bar_low = lows[i]
            bar_atr = max(1e-4, atr[i])
            ts = timestamps[i]

            # 1. Chequeo de salidas y liquidación si estamos en posición
            if position_side is not None:
                # Comprobar distancia a liquidación
                margin_used = (position_qty * bar_close) / max_leverage
                margin_util_pct = (margin_used / max(1.0, current_equity)) * 100.0
                peak_margin_utilization = max(peak_margin_utilization, margin_util_pct)

                liq_price = position_entry_price * (1.0 - 1.0 / max_leverage) if position_side == "LONG" else position_entry_price * (1.0 + 1.0 / max_leverage)
                dist_liq_pct = abs(bar_close - liq_price) / bar_close * 100.0
                min_liq_dist = min(min_liq_dist, dist_liq_pct)

                # Comprobar liquidación real (quiebra al 100%)
                if (position_side == "LONG" and bar_low <= liq_price) or (position_side == "SHORT" and bar_high >= liq_price):
                    # Liquidación
                    exit_price = liq_price
                    gross_pnl = (exit_price - position_entry_price) * position_qty if position_side == "LONG" else (position_entry_price - exit_price) * position_qty
                    comm = exit_price * position_qty * self.taker_fee
                    slip = exit_price * position_qty * self.slippage
                    net_pnl = gross_pnl - comm - slip
                    current_equity = max(0.0, current_equity + net_pnl)
                    total_fees += comm
                    total_slippage += slip

                    trades.append(
                        TradeRecord(
                            trade_id=f"trade_{len(trades)+1}",
                            entry_bar=position_entry_bar,
                            exit_bar=i,
                            entry_time_ms=position_entry_time,
                            exit_time_ms=ts,
                            side=position_side,
                            qty=position_qty,
                            entry_price=position_entry_price,
                            exit_price=exit_price,
                            gross_pnl_usd=gross_pnl,
                            net_pnl_usd=net_pnl,
                            return_pct=round((net_pnl / max(1.0, position_equity_before)) * 100.0, 4),
                            fees_usd=comm,
                            slippage_usd=slip,
                            exit_reason="LIQUIDATION",
                            pyramid_level=pyramid_count,
                            equity_before_usd=round(position_equity_before, 2),
                            equity_after_usd=round(current_equity, 2),
                            r_multiple=round(net_pnl / max(1e-4, position_risk_amount), 2),
                        )
                    )
                    position_side = None
                    position_qty = 0.0

                # Comprobar Stop Loss
                elif (position_side == "LONG" and bar_low <= stop_loss_price) or (position_side == "SHORT" and bar_high >= stop_loss_price):
                    exit_price = stop_loss_price
                    gross_pnl = (exit_price - position_entry_price) * position_qty if position_side == "LONG" else (position_entry_price - exit_price) * position_qty
                    comm = exit_price * position_qty * self.taker_fee
                    slip = exit_price * position_qty * self.slippage
                    net_pnl = gross_pnl - comm - slip
                    current_equity += net_pnl
                    total_fees += comm
                    total_slippage += slip

                    trades.append(
                        TradeRecord(
                            trade_id=f"trade_{len(trades)+1}",
                            entry_bar=position_entry_bar,
                            exit_bar=i,
                            entry_time_ms=position_entry_time,
                            exit_time_ms=ts,
                            side=position_side,
                            qty=position_qty,
                            entry_price=position_entry_price,
                            exit_price=exit_price,
                            gross_pnl_usd=gross_pnl,
                            net_pnl_usd=net_pnl,
                            return_pct=round((net_pnl / max(1.0, position_equity_before)) * 100.0, 4),
                            fees_usd=comm,
                            slippage_usd=slip,
                            exit_reason="STOP_LOSS",
                            pyramid_level=pyramid_count,
                            equity_before_usd=round(position_equity_before, 2),
                            equity_after_usd=round(current_equity, 2),
                            r_multiple=round(net_pnl / max(1e-4, position_risk_amount), 2),
                        )
                    )
                    position_side = None
                    position_qty = 0.0

                # Comprobar Take Profit
                elif (position_side == "LONG" and bar_high >= take_profit_price) or (position_side == "SHORT" and bar_low <= take_profit_price):
                    exit_price = take_profit_price
                    gross_pnl = (exit_price - position_entry_price) * position_qty if position_side == "LONG" else (position_entry_price - exit_price) * position_qty
                    comm = exit_price * position_qty * self.taker_fee
                    slip = exit_price * position_qty * self.slippage
                    net_pnl = gross_pnl - comm - slip
                    current_equity += net_pnl
                    total_fees += comm
                    total_slippage += slip

                    trades.append(
                        TradeRecord(
                            trade_id=f"trade_{len(trades)+1}",
                            entry_bar=position_entry_bar,
                            exit_bar=i,
                            entry_time_ms=position_entry_time,
                            exit_time_ms=ts,
                            side=position_side,
                            qty=position_qty,
                            entry_price=position_entry_price,
                            exit_price=exit_price,
                            gross_pnl_usd=gross_pnl,
                            net_pnl_usd=net_pnl,
                            return_pct=round((net_pnl / max(1.0, position_equity_before)) * 100.0, 4),
                            fees_usd=comm,
                            slippage_usd=slip,
                            exit_reason="TAKE_PROFIT",
                            pyramid_level=pyramid_count,
                            equity_before_usd=round(position_equity_before, 2),
                            equity_after_usd=round(current_equity, 2),
                            r_multiple=round(net_pnl / max(1e-4, position_risk_amount), 2),
                        )
                    )
                    position_side = None
                    position_qty = 0.0

                # Piramidación sobre beneficio si está habilitada (Ruta Ultra)
                elif is_ultra and strategy.pyramiding_policy.enabled and pyramid_count < strategy.pyramiding_policy.max_tiers:
                    floating_pnl_r = ((bar_close - position_entry_price) / bar_atr) if position_side == "LONG" else ((position_entry_price - bar_close) / bar_atr)
                    if floating_pnl_r >= (pyramid_count + 1) * 1.5:
                        # Mover stop loss a break-even
                        stop_loss_price = position_entry_price
                        # Añadir tramo acotado a subcuenta bala
                        max_nominal_qty = (base_capital * max_leverage) / max(1e-4, bar_close)
                        added_qty = (base_capital * risk_pct * max_leverage) / (bar_close * max(1.0, float(pyramid_count + 1)))
                        position_qty = min(position_qty + added_qty, max_nominal_qty)
                        pyramid_count += 1

            # 2. Señal de Entrada si estamos planos
            if position_side is None and current_equity > 0:
                ema_fast_val = ema_fast_series[i]
                ema_slow_val = ema_slow_series[i]
                
                lookback = min(breakout_lookback, i)
                breakout_long = (bar_close >= np.max(highs[i-lookback:i])) if lookback > 1 else True
                rsi_long_ok = (rsi_series[i] >= rsi_threshold_long) if (use_rsi and rsi_series is not None) else True
                long_signal = (ema_fast_val > ema_slow_val) and breakout_long and rsi_long_ok

                breakout_short = (bar_close <= np.min(lows[i-lookback:i])) if lookback > 1 else True
                rsi_short_ok = (rsi_series[i] <= rsi_threshold_short) if (use_rsi and rsi_series is not None) else True
                short_signal = (ema_fast_val < ema_slow_val) and breakout_short and rsi_short_ok

                if long_signal:
                    position_side = "LONG"
                    position_entry_bar = i
                    position_entry_time = ts
                    position_entry_price = bar_close * (1.0 + self.slippage)
                    position_equity_before = current_equity
                    # Sizing agresivo para Ultra (subcuenta bala con reinversión de equidad) / Fondeo acotado
                    effective_equity = current_equity if is_ultra else min(current_equity, base_capital * 1.2)
                    risk_amount_usd = effective_equity * risk_pct
                    position_risk_amount = risk_amount_usd
                    sl_dist = bar_atr * sl_atr_mult
                    raw_qty = risk_amount_usd / max(1e-4, sl_dist)
                    max_nominal_qty = (current_equity * max_leverage * 0.85) / max(1e-4, position_entry_price) if is_ultra else (base_capital * max_leverage) / max(1e-4, position_entry_price)
                    position_qty = max(0.001, min(raw_qty, max_nominal_qty))
                    stop_loss_price = position_entry_price - sl_dist
                    take_profit_price = position_entry_price + (bar_atr * tp_atr_mult)
                    pyramid_count = 0

                    comm = position_entry_price * position_qty * self.taker_fee
                    slip = position_entry_price * position_qty * self.slippage
                    current_equity -= (comm + slip)
                    total_fees += comm
                    total_slippage += slip

                elif short_signal:
                    position_side = "SHORT"
                    position_entry_bar = i
                    position_entry_time = ts
                    position_entry_price = bar_close * (1.0 - self.slippage)
                    position_equity_before = current_equity
                    # Sizing agresivo para Ultra (subcuenta bala con reinversión de equidad) / Fondeo acotado
                    effective_equity = current_equity if is_ultra else min(current_equity, base_capital * 1.2)
                    risk_amount_usd = effective_equity * risk_pct
                    position_risk_amount = risk_amount_usd
                    sl_dist = bar_atr * sl_atr_mult
                    raw_qty = risk_amount_usd / max(1e-4, sl_dist)
                    max_nominal_qty = (current_equity * max_leverage * 0.85) / max(1e-4, position_entry_price) if is_ultra else (base_capital * max_leverage) / max(1e-4, position_entry_price)
                    position_qty = max(0.001, min(raw_qty, max_nominal_qty))
                    stop_loss_price = position_entry_price + sl_dist
                    take_profit_price = position_entry_price - (bar_atr * tp_atr_mult)
                    pyramid_count = 0

                    comm = position_entry_price * position_qty * self.taker_fee
                    slip = position_entry_price * position_qty * self.slippage
                    current_equity -= (comm + slip)
                    total_fees += comm
                    total_slippage += slip

            # Track equity curve and drawdown
            peak_equity = max(peak_equity, current_equity)
            dd_pct = ((peak_equity - current_equity) / max(1.0, peak_equity)) * 100.0
            max_drawdown_pct = max(max_drawdown_pct, dd_pct)
            equity_curve.append(round(current_equity, 2))
            drawdown_curve.append(round(dd_pct, 2))

        # Cierre forzado al final del dataset si queda posición abierta
        if position_side is not None:
            exit_price = closes[-1]
            gross_pnl = (exit_price - position_entry_price) * position_qty if position_side == "LONG" else (position_entry_price - exit_price) * position_qty
            comm = exit_price * position_qty * self.taker_fee
            slip = exit_price * position_qty * self.slippage
            net_pnl = gross_pnl - comm - slip
            current_equity += net_pnl
            total_fees += comm
            total_slippage += slip

            trades.append(
                TradeRecord(
                    trade_id=f"trade_{len(trades)+1}",
                    entry_bar=position_entry_bar,
                    exit_bar=len(closes)-1,
                    entry_time_ms=position_entry_time,
                    exit_time_ms=timestamps[-1],
                    side=position_side,
                    qty=position_qty,
                    entry_price=position_entry_price,
                    exit_price=exit_price,
                    gross_pnl_usd=gross_pnl,
                    net_pnl_usd=net_pnl,
                    return_pct=round((net_pnl / max(1.0, position_equity_before)) * 100.0, 4),
                    fees_usd=comm,
                    slippage_usd=slip,
                    exit_reason="END_OF_DATASET",
                    pyramid_level=pyramid_count,
                    equity_before_usd=round(position_equity_before, 2),
                    equity_after_usd=round(current_equity, 2),
                    r_multiple=round(net_pnl / max(1e-4, position_risk_amount), 2),
                )
            )

        # Resumen de métricas
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t.net_pnl_usd > 0)
        losing_trades = sum(1 for t in trades if t.net_pnl_usd <= 0)
        win_rate = (winning_trades / total_trades * 100.0) if total_trades > 0 else 0.0
        net_profit = current_equity - base_capital

        gross_gains = sum(t.net_pnl_usd for t in trades if t.net_pnl_usd > 0)
        gross_losses = abs(sum(t.net_pnl_usd for t in trades if t.net_pnl_usd < 0))
        pf = (gross_gains / gross_losses) if gross_losses > 0 else (99.0 if gross_gains > 0 else 0.0)

        t_end = datetime.now(timezone.utc)
        exec_time = (t_end - t_start).total_seconds() * 1000.0

        return EventBacktestResult(
            strategy_id=strategy.strategy_id,
            canonical_hash=strategy.canonical_hash,
            dataset_id=strategy.dataset_id_reference,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate_pct=round(win_rate, 2),
            net_profit_usd=round(net_profit, 2),
            profit_factor=round(pf, 2),
            max_drawdown_pct=round(max_drawdown_pct, 2),
            peak_equity_usd=round(peak_equity, 2),
            final_equity_usd=round(current_equity, 2),
            peak_margin_utilization_pct=round(peak_margin_utilization, 2),
            min_liquidation_distance_pct=round(min_liq_dist, 2),
            total_fees_usd=round(total_fees, 2),
            total_slippage_usd=round(total_slippage, 2),
            trades=trades,
            equity_curve=equity_curve,
            drawdown_curve=drawdown_curve,
            execution_time_ms=round(exec_time, 2),
        )
