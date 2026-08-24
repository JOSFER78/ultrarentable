"""services/engine/universal_backtest_engine.py
Universal Deterministic Backtest Engine (v3.0.0).

DOCTRINA ZERO-MOCKS & UNIVERSAL ARCHITECTURE:
- 100% Deterministic Event Loop over real historical bars.
- Zero hardcoded strategies, zero hardcoded assets, zero hardcoded indicator parameters.
- Accepts any valid StrategySpecification, InstrumentSpecification, DatasetSpecification, ExecutionModel and RiskModel.
- Produces a full bar-by-bar equity ledger and trade stream with cryptographic Merkle provenance hash.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import numpy as np

from contracts.dataset_specification import DatasetSpecification
from contracts.execution_model import ExecutionModel
from contracts.instrument_specification import AssetClass, CommissionType, InstrumentSpecification
from contracts.risk_model import RiskDoctrine, RiskModel
from contracts.universal_ledger import (
    BarEquityRecord,
    TradeRecord,
    UniversalBacktestResult,
)
from contracts.universal_strategy import IndicatorType, StrategySpecification
from services.engine.indicator_engine import DynamicIndicatorEngine
from services.engine.rule_evaluator import DynamicRuleEvaluator


class UniversalDeterministicBacktestEngine:
    """Motor universal de ejecución determinista y simulación cuantitativa."""

    ENGINE_VERSION = "3.0.0"

    def __init__(self) -> None:
        pass

    def run(
        self,
        strategy: StrategySpecification,
        instrument: InstrumentSpecification,
        dataset: DatasetSpecification,
        candles: List[Dict[str, Any]],
        execution_model: ExecutionModel,
        risk_model: RiskModel,
        initial_capital_override: Optional[float] = None,
    ) -> UniversalBacktestResult:
        """Ejecuta el backtest determinista universal."""
        t_start = time.perf_counter()

        if not candles or len(candles) < 20:
            raise ValueError(f"INSUFFICIENT_DATA: Se requieren al menos 20 barras para ejecutar el motor (recibidas: {len(candles)}).")

        n_bars = len(candles)
        opens = np.array([float(c["open"]) for c in candles], dtype=np.float64)
        highs = np.array([float(c["high"]) for c in candles], dtype=np.float64)
        lows = np.array([float(c["low"]) for c in candles], dtype=np.float64)
        closes = np.array([float(c["close"]) for c in candles], dtype=np.float64)
        volumes = np.array([float(c.get("volume", 1.0)) for c in candles], dtype=np.float64)
        def _parse_ts(c_val: Any) -> int:
            raw_v = c_val.get("timestamp_utc_ms") or c_val.get("timestamp_ms") or c_val.get("timestamp") or c_val.get("time") or 0
            if isinstance(raw_v, (int, float)):
                return int(raw_v)
            if isinstance(raw_v, str):
                try:
                    return int(float(raw_v))
                except ValueError:
                    try:
                        from datetime import datetime
                        clean_iso = raw_v.replace("Z", "+00:00")
                        return int(datetime.fromisoformat(clean_iso).timestamp() * 1000)
                    except Exception:
                        return 0
            return 0

        timestamps = [_parse_ts(c) for c in candles]

        # 1. Inicialización de Motores Dinámicos
        ind_engine = DynamicIndicatorEngine(opens, highs, lows, closes, volumes)
        rule_evaluator = DynamicRuleEvaluator(ind_engine)

        # 2. Pre-cálculo de ATR de salida
        sl_atr_period = strategy.exit_rules.stop_loss_atr_period
        atr_series = ind_engine.get_series(IndicatorType.ATR, sl_atr_period)

        # 3. Determinación Dinámica de Warmup
        warmup_bars = max(20, sl_atr_period + 5)
        for cond in strategy.entry_rules.long_rules.conditions + strategy.entry_rules.short_rules.conditions:
            if cond.left.period:
                warmup_bars = max(warmup_bars, cond.left.period + 5)
            if cond.right.period:
                warmup_bars = max(warmup_bars, cond.right.period + 5)
        warmup_bars = min(warmup_bars, n_bars - 5)

        # 4. Estado de Cuenta y Riesgo
        base_capital = initial_capital_override or risk_model.base_capital_usd
        current_equity = base_capital
        peak_equity = base_capital
        cash_balance = base_capital
        realized_pnl_cum = 0.0
        fees_cum = 0.0
        slippage_cum = 0.0
        funding_cum = 0.0

        max_leverage = min(risk_model.max_leverage, instrument.max_allowed_leverage)
        is_ultra = (risk_model.doctrine == RiskDoctrine.ULTRA)
        is_fondeo = (risk_model.doctrine == RiskDoctrine.FONDEO)
        
        # Posición activa
        position_side: Optional[str] = None  # "LONG" | "SHORT"
        position_qty = 0.0
        position_entry_price = 0.0
        position_entry_bar = 0
        position_entry_time = 0
        position_equity_before = base_capital
        position_initial_risk_usd = 0.0
        position_funding_cum = 0.0
        stop_loss_price = 0.0
        take_profit_price = 0.0
        highest_price_in_trade = 0.0
        lowest_price_in_trade = 0.0
        pyramid_level = 0
        bars_in_trade = 0

        # Registros
        trades: List[TradeRecord] = []
        bar_ledger: List[BarEquityRecord] = []
        equity_curve: List[float] = []
        drawdown_curve: List[float] = []
        max_drawdown_pct = 0.0
        peak_margin_utilization = 0.0
        liquidated = False

        # 5. Bucle de Simulación Barra a Barra
        for i in range(n_bars):
            bar_close = closes[i]
            bar_high = highs[i]
            bar_low = lows[i]
            bar_atr = max(instrument.tick_size, atr_series[i])
            ts = timestamps[i]

            # A. Actualizar PnL No Realizado, Funding y Margen si estamos en posición
            unrealized_pnl = 0.0
            margin_used = 0.0
            if position_side is not None:
                bars_in_trade += 1
                highest_price_in_trade = max(highest_price_in_trade, bar_high)
                lowest_price_in_trade = min(lowest_price_in_trade, bar_low)

                if position_side == "LONG":
                    unrealized_pnl = (bar_close - position_entry_price) * position_qty * instrument.point_value
                else:
                    unrealized_pnl = (position_entry_price - bar_close) * position_qty * instrument.point_value

                notional = position_entry_price * position_qty * instrument.point_value
                margin_used = notional / max(1.0, max_leverage)
                margin_util_pct = (margin_used / max(1.0, current_equity)) * 100.0
                peak_margin_utilization = max(peak_margin_utilization, margin_util_pct)

                # Cobro de Funding Rate real en perpetuos apalancados
                if instrument.is_perpetual or execution_model.funding_settlement_enabled:
                    bar_hours = (ts - timestamps[i - 1]) / (1000.0 * 3600.0) if i > 0 else 1.0
                    f_rate = execution_model.funding_rate_8h or instrument.default_funding_rate
                    bar_funding = notional * f_rate * (max(0.01, bar_hours) / 8.0)
                    cash_balance -= bar_funding
                    funding_cum += bar_funding
                    position_funding_cum += bar_funding

            current_equity = max(0.0, cash_balance + unrealized_pnl)
            peak_equity = max(peak_equity, current_equity)
            dd_pct = ((peak_equity - current_equity) / peak_equity) * 100.0 if peak_equity > 0 else 0.0
            max_drawdown_pct = max(max_drawdown_pct, dd_pct)

            # B. Evaluación de Salidas si estamos en posición
            if position_side is not None and i >= warmup_bars:
                exit_triggered = False
                exit_price = bar_close
                exit_reason = "NONE"

                # Check Liquidación (pérdida >= 100% del margen)
                liq_price = (
                    position_entry_price * (1.0 - (1.0 / max_leverage))
                    if position_side == "LONG"
                    else position_entry_price * (1.0 + (1.0 / max_leverage))
                )
                if (position_side == "LONG" and bar_low <= liq_price) or (position_side == "SHORT" and bar_high >= liq_price):
                    exit_triggered = True
                    exit_price = liq_price
                    exit_reason = "LIQUIDATION"
                    liquidated = True

                # Check Stop Loss
                elif (position_side == "LONG" and bar_low <= stop_loss_price) or (position_side == "SHORT" and bar_high >= stop_loss_price):
                    exit_triggered = True
                    exit_price = stop_loss_price
                    exit_reason = "STOP_LOSS"

                # Check Take Profit
                elif take_profit_price > 0 and ((position_side == "LONG" and bar_high >= take_profit_price) or (position_side == "SHORT" and bar_low <= take_profit_price)):
                    exit_triggered = True
                    exit_price = take_profit_price
                    exit_reason = "TAKE_PROFIT"

                # Check Max Bars in Trade
                elif strategy.exit_rules.max_bars_in_trade and bars_in_trade >= strategy.exit_rules.max_bars_in_trade:
                    exit_triggered = True
                    exit_price = bar_close
                    exit_reason = "TIME_EXIT"

                # Check Break-Even Trigger
                if not exit_triggered and strategy.exit_rules.break_even_enabled:
                    floating_r = (unrealized_pnl / max(1e-4, position_initial_risk_usd))
                    if floating_r >= strategy.exit_rules.break_even_trigger_r:
                        stop_loss_price = position_entry_price

                # Check Trailing Stop Trigger
                if not exit_triggered and strategy.exit_rules.trailing_stop_enabled:
                    floating_r = (unrealized_pnl / max(1e-4, position_initial_risk_usd))
                    if floating_r >= strategy.exit_rules.trailing_trigger_r:
                        trail_dist = bar_atr * strategy.exit_rules.trailing_step_atr_mult
                        if position_side == "LONG":
                            stop_loss_price = max(stop_loss_price, highest_price_in_trade - trail_dist)
                        else:
                            stop_loss_price = min(stop_loss_price, lowest_price_in_trade + trail_dist)

                # Check Pyramiding (Ultra Route)
                if not exit_triggered and is_ultra and risk_model.pyramiding_enabled and pyramid_level < risk_model.pyramiding_max_tiers:
                    floating_r = (unrealized_pnl / max(1e-4, position_initial_risk_usd))
                    tier_spec = risk_model.pyramiding_tiers[pyramid_level] if pyramid_level < len(risk_model.pyramiding_tiers) else None
                    trigger_r = tier_spec.trigger_r_multiple if tier_spec else (pyramid_level + 1) * 1.5
                    
                    if floating_r >= trigger_r:
                        # Mover SL a break-even
                        stop_loss_price = position_entry_price
                        # Añadir tramo proporcional
                        reinvest_fraction = (tier_spec.reinvest_fraction_pct / 100.0) if tier_spec else 0.50
                        added_risk_usd = unrealized_pnl * reinvest_fraction
                        added_qty = instrument.round_quantity_to_step(added_risk_usd / max(1e-4, bar_atr * strategy.exit_rules.stop_loss_value * instrument.point_value))
                        
                        max_pos_qty = (current_equity * max_leverage * 0.85) / max(1e-4, bar_close * instrument.point_value)
                        if position_qty + added_qty <= max_pos_qty:
                            position_qty += added_qty
                            pyramid_level += 1

                # Ejecutar Cierre si se disparó la salida
                if exit_triggered:
                    exit_price = instrument.round_price_to_tick(exit_price)
                    gross_pnl = (
                        (exit_price - position_entry_price) * position_qty * instrument.point_value
                        if position_side == "LONG"
                        else (position_entry_price - exit_price) * position_qty * instrument.point_value
                    )
                    
                    notional_exit = exit_price * position_qty * instrument.point_value
                    comm_exit = execution_model.calculate_commission(notional_exit, position_qty)
                    slip_exit = execution_model.calculate_slippage_cost(notional_exit, bar_atr)
                    net_pnl = gross_pnl - comm_exit - slip_exit - position_funding_cum

                    cash_balance += (gross_pnl - comm_exit - slip_exit)
                    current_equity = max(0.0, cash_balance)
                    realized_pnl_cum += net_pnl
                    fees_cum += comm_exit
                    slippage_cum += slip_exit

                    ret_pct = (net_pnl / max(1.0, position_equity_before)) * 100.0
                    ret_r = net_pnl / max(1e-4, position_initial_risk_usd)

                    trades.append(
                        TradeRecord(
                            trade_id=f"T_{len(trades)+1:04d}",
                            strategy_id=strategy.strategy_id,
                            dataset_id=dataset.dataset_id,
                            symbol=instrument.symbol,
                            direction=position_side,
                            entry_bar=position_entry_bar,
                            exit_bar=i,
                            entry_time_ms=position_entry_time,
                            exit_time_ms=ts,
                            entry_price=position_entry_price,
                            exit_price=exit_price,
                            quantity=position_qty,
                            notional_usd=round(position_entry_price * position_qty * instrument.point_value, 2),
                            leverage_used=round((position_entry_price * position_qty * instrument.point_value) / max(1.0, position_equity_before), 2),
                            initial_risk_usd=round(position_initial_risk_usd, 2),
                            gross_pnl_usd=round(gross_pnl, 2),
                            commission_usd=round(comm_exit, 4),
                            slippage_usd=round(slip_exit, 4),
                            funding_usd=round(position_funding_cum, 4),
                            net_pnl_usd=round(net_pnl, 2),
                            return_pct=round(ret_pct, 4),
                            return_r=round(ret_r, 4),
                            exit_reason=exit_reason,
                            pyramid_level=pyramid_level,
                            equity_before_usd=round(position_equity_before, 2),
                            equity_after_usd=round(current_equity, 2),
                        )
                    )

                    position_side = None
                    position_qty = 0.0
                    position_funding_cum = 0.0

            # C. Evaluación de Entradas si estamos planos
            if position_side is None and i >= warmup_bars and current_equity > 0:
                long_signal, short_signal = rule_evaluator.evaluate_signals_at_bar(strategy.entry_rules, i)

                if long_signal or short_signal:
                    side = "LONG" if long_signal else "SHORT"
                    
                    # Slippage de entrada
                    slip_entry_rate = (execution_model.base_slippage_bps / 10000.0)
                    entry_price = instrument.round_price_to_tick(
                        bar_close * (1.0 + slip_entry_rate) if side == "LONG" else bar_close * (1.0 - slip_entry_rate)
                    )

                    # Cálculo dinámico de distancia de Stop Loss
                    if strategy.exit_rules.stop_loss_type == "PERCENTAGE":
                        sl_dist = entry_price * (strategy.exit_rules.stop_loss_value / 100.0)
                    elif strategy.exit_rules.stop_loss_type == "FIXED_TICKS":
                        sl_dist = strategy.exit_rules.stop_loss_value * instrument.tick_size
                    else:  # ATR_MULTIPLE
                        sl_dist = bar_atr * strategy.exit_rules.stop_loss_value

                    # Cálculo dinámico de Sizing
                    if is_fondeo and risk_model.fixed_contracts_count:
                        qty = float(risk_model.fixed_contracts_count)
                        risk_usd = qty * sl_dist * instrument.point_value
                    else:
                        effective_cap = current_equity if is_ultra else base_capital
                        risk_usd = effective_cap * (risk_model.base_risk_pct / 100.0)
                        raw_qty = risk_usd / max(1e-4, sl_dist * instrument.point_value)
                        
                        max_notional_cap = (current_equity * max_leverage * 0.85)
                        max_qty_leverage = max_notional_cap / max(1e-4, entry_price * instrument.point_value)
                        qty = instrument.round_quantity_to_step(min(raw_qty, max_qty_leverage))

                    if qty >= instrument.min_quantity:
                        notional_entry = entry_price * qty * instrument.point_value
                        comm_entry = execution_model.calculate_commission(notional_entry, qty)
                        slip_entry_cost = execution_model.calculate_slippage_cost(notional_entry, bar_atr)

                        cash_balance -= (comm_entry + slip_entry_cost)
                        fees_cum += comm_entry
                        slippage_cum += slip_entry_cost

                        position_side = side
                        position_qty = qty
                        position_entry_price = entry_price
                        position_entry_bar = i
                        position_entry_time = ts
                        position_equity_before = current_equity
                        position_initial_risk_usd = risk_usd
                        highest_price_in_trade = entry_price
                        lowest_price_in_trade = entry_price
                        pyramid_level = 0
                        bars_in_trade = 0

                        # Precios de SL y TP
                        stop_loss_price = instrument.round_price_to_tick(
                            entry_price - sl_dist if side == "LONG" else entry_price + sl_dist
                        )
                        
                        if strategy.exit_rules.take_profit_type == "RISK_REWARD_MULTIPLE":
                            tp_dist = sl_dist * strategy.exit_rules.take_profit_value
                        elif strategy.exit_rules.take_profit_type == "PERCENTAGE":
                            tp_dist = entry_price * (strategy.exit_rules.take_profit_value / 100.0)
                        elif strategy.exit_rules.take_profit_type == "FIXED_TICKS":
                            tp_dist = strategy.exit_rules.take_profit_value * instrument.tick_size
                        else:  # ATR_MULTIPLE
                            tp_dist = bar_atr * strategy.exit_rules.take_profit_value

                        take_profit_price = instrument.round_price_to_tick(
                            entry_price + tp_dist if side == "LONG" else entry_price - tp_dist
                        )

            # D. Registrar Ledger de la Barra
            bar_ledger.append(
                BarEquityRecord(
                    bar_index=i,
                    timestamp_ms=ts,
                    close_price=bar_close,
                    equity_usd=round(current_equity, 2),
                    balance_usd=round(cash_balance, 2),
                    cash_usd=round(cash_balance, 2),
                    unrealized_pnl_usd=round(unrealized_pnl, 2),
                    realized_pnl_usd=round(realized_pnl_cum, 2),
                    fees_cumulative_usd=round(fees_cum, 4),
                    slippage_cumulative_usd=round(slippage_cum, 4),
                    funding_cumulative_usd=round(funding_cum, 4),
                    margin_used_usd=round(margin_used, 2),
                    drawdown_pct=round(dd_pct, 2),
                    peak_equity_usd=round(peak_equity, 2),
                    in_position=(position_side is not None),
                    position_qty=position_qty,
                    position_side=position_side,
                )
            )
            equity_curve.append(round(current_equity, 2))
            drawdown_curve.append(round(dd_pct, 2))

        # 6. Cálculo Forense de Métricas Globales
        total_trades_count = len(trades)
        winning_trades = [t for t in trades if t.net_pnl_usd > 0]
        losing_trades = [t for t in trades if t.net_pnl_usd <= 0]
        win_count = len(winning_trades)
        loss_count = len(losing_trades)
        win_rate = (win_count / total_trades_count * 100.0) if total_trades_count > 0 else 0.0

        gross_wins = sum(t.net_pnl_usd for t in winning_trades)
        gross_losses = abs(sum(t.net_pnl_usd for t in losing_trades))
        profit_factor = round(gross_wins / gross_losses, 2) if gross_losses > 0 else (99.0 if gross_wins > 0 else 0.0)

        net_profit = current_equity - base_capital
        total_roi = (net_profit / base_capital) * 100.0
        
        # Duración temporal para anualizar
        span_ms = max(1, timestamps[-1] - timestamps[0])
        span_days = span_ms / (1000.0 * 86400.0)
        span_years = max(0.01, span_days / 365.25)
        annual_roi = total_roi / span_years
        monthly_roi = annual_roi / 12.0

        expectancy_r = round(float(np.mean([t.return_r for t in trades])), 2) if trades else 0.0

        # 7. Huella Criptográfica Canónica de Procedencia Merkle
        prov_parts = [
            strategy.compute_hash(),
            dataset.sha256_hash,
            instrument.compute_hash(),
            execution_model.compute_hash(),
            risk_model.compute_hash(),
            self.ENGINE_VERSION,
        ]
        provenance_hash = hashlib.sha256(":".join(prov_parts).encode("utf-8")).hexdigest()

        duration_ms = (time.perf_counter() - t_start) * 1000.0

        return UniversalBacktestResult(
            provenance_hash=provenance_hash,
            strategy_id=strategy.strategy_id,
            strategy_hash=strategy.compute_hash(),
            dataset_id=dataset.dataset_id,
            dataset_sha256=dataset.sha256_hash,
            instrument_symbol=instrument.symbol,
            instrument_hash=instrument.compute_hash(),
            execution_model_hash=execution_model.compute_hash(),
            risk_model_hash=risk_model.compute_hash(),
            engine_version=self.ENGINE_VERSION,
            initial_capital_usd=round(base_capital, 2),
            final_equity_usd=round(current_equity, 2),
            peak_equity_usd=round(peak_equity, 2),
            net_profit_usd=round(net_profit, 2),
            total_roi_pct=round(total_roi, 2),
            monthly_roi_pct=round(monthly_roi, 2),
            annualized_roi_pct=round(annual_roi, 2),
            profit_factor=profit_factor,
            win_rate_pct=round(win_rate, 2),
            expectancy_r=expectancy_r,
            total_trades=total_trades_count,
            winning_trades=win_count,
            losing_trades=loss_count,
            max_drawdown_pct=round(max_drawdown_pct, 2),
            max_drawdown_duration_bars=0,
            peak_margin_utilization_pct=round(peak_margin_utilization, 2),
            liquidated=liquidated,
            total_commissions_usd=round(fees_cum, 2),
            total_slippage_usd=round(slippage_cum, 2),
            total_funding_usd=round(funding_cum, 2),
            trades=trades,
            equity_curve=equity_curve,
            drawdown_curve=drawdown_curve,
            bar_ledger=bar_ledger,
            execution_duration_ms=round(duration_ms, 2),
        )

    def run_isolated_is_oos(
        self,
        strategy: StrategySpecification,
        instrument: InstrumentSpecification,
        dataset: DatasetSpecification,
        candles: List[Dict[str, Any]],
        execution_model: ExecutionModel,
        risk_model: RiskModel,
        split_ratio: float = 0.70,
        initial_capital_override: Optional[float] = None,
    ) -> Tuple[UniversalBacktestResult, UniversalBacktestResult]:
        """Ejecuta dos backtests físicamente aislados e independientes: In-Sample (IS) y Out-of-Sample (OOS).
        
        Garantía Zero-Leakage:
        - IS se ejecuta estrictamente sobre las primeras split_idx barras.
        - La estrategia queda fijada e inmutable sin optimizaciones posteriores.
        - OOS se ejecuta sobre el bloque de holdout ciego restante sin contaminación.
        """
        n_bars = len(candles)
        split_idx = int(n_bars * split_ratio)
        
        if split_idx < 20 or (n_bars - split_idx) < 10:
            raise ValueError(f"INSUFFICIENT_DATA_FOR_SPLIT: Muestra total ({n_bars} barras) insuficiente para partición {split_ratio*100:.0f}% IS / {(1-split_ratio)*100:.0f}% OOS.")

        candles_is = candles[:split_idx]
        candles_oos = candles[split_idx:]

        start_is_ms = int(candles_is[0].get("timestamp_utc_ms") or candles_is[0].get("timestamp_ms") or candles_is[0].get("timestamp") or 0)
        end_is_ms = int(candles_is[-1].get("timestamp_utc_ms") or candles_is[-1].get("timestamp_ms") or candles_is[-1].get("timestamp") or 0)
        start_oos_ms = int(candles_oos[0].get("timestamp_utc_ms") or candles_oos[0].get("timestamp_ms") or candles_oos[0].get("timestamp") or 0)
        end_oos_ms = int(candles_oos[-1].get("timestamp_utc_ms") or candles_oos[-1].get("timestamp_ms") or candles_oos[-1].get("timestamp") or 0)

        is_ds = dataset.model_copy(update={
            "dataset_id": f"{dataset.dataset_id}_IS",
            "bar_count": len(candles_is),
            "start_time_ms": start_is_ms,
            "end_time_ms": end_is_ms,
            "sha256_hash": hashlib.sha256(json.dumps(candles_is, sort_keys=True, default=str).encode("utf-8")).hexdigest(),
        })

        oos_ds = dataset.model_copy(update={
            "dataset_id": f"{dataset.dataset_id}_OOS",
            "bar_count": len(candles_oos),
            "start_time_ms": start_oos_ms,
            "end_time_ms": end_oos_ms,
            "sha256_hash": hashlib.sha256(json.dumps(candles_oos, sort_keys=True, default=str).encode("utf-8")).hexdigest(),
        })

        result_is = self.run(
            strategy=strategy,
            instrument=instrument,
            dataset=is_ds,
            candles=candles_is,
            execution_model=execution_model,
            risk_model=risk_model,
            initial_capital_override=initial_capital_override,
        )

        result_oos = self.run(
            strategy=strategy,
            instrument=instrument,
            dataset=oos_ds,
            candles=candles_oos,
            execution_model=execution_model,
            risk_model=risk_model,
            initial_capital_override=initial_capital_override,
        )

        return result_is, result_oos

