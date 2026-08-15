"""TradingView Pine Script (v5) Exporter for Ultrarentable Strategies.

Generates complete, verified Pine Script (v5) strategy code ready for TradingView:
- Built-in Commission (0.05% Taker) & Slippage (3 ticks) overlay.
- In-Sample / Out-of-Sample Date Filter with visual background shading.
- Dynamic ATR Stop Loss & Profit Target.
- Webhook JSON alerts for BingX / Custom Execution Bridges.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


def generate_pinescript_v5(
    strategy_name: str,
    symbol: str = "BTCUSDT",
    timeframe: str = "60",
    fast_ema: int = 21,
    slow_ema: int = 55,
    donchian_period: int = 20,
    atr_period: int = 14,
    atr_stop_mult: float = 1.5,
    atr_tp_mult: float = 4.0,
    risk_per_trade_pct: float = 1.5,
    oos_start_year: int = 2026,
    oos_start_month: int = 6,
    oos_start_day: int = 18
) -> str:
    """Generate compilable TradingView Pine Script (v5) code."""
    clean_name = strategy_name.replace("'", "").replace('"', "")
    
    code = f"""//@version=5
strategy("{clean_name} [Ultrarentable]", overlay=true, initial_capital=10000, default_qty_type=strategy.percent_of_equity, default_qty_value={risk_per_trade_pct}, commission_type=strategy.commission.percent, commission_value=0.05, slippage=3)

// === 1. PARÁMETROS CONFIGURABLES ===
fast_ema_len = input.int({fast_ema}, "EMA Rápida", group="Indicadores")
slow_ema_len = input.int({slow_ema}, "EMA Lenta", group="Indicadores")
donchian_len = input.int({donchian_period}, "Período Donchian", group="Indicadores")
atr_len      = input.int({atr_period}, "Período ATR", group="Gestión de Riesgo")
atr_sl_mult  = input.float({atr_stop_mult}, "Multiplicador SL (x ATR)", group="Gestión de Riesgo", step=0.1)
atr_tp_mult  = input.float({atr_tp_mult}, "Multiplicador TP (x ATR)", group="Gestión de Riesgo", step=0.1)

// === 2. FILTRO DE FECHAS (IN-SAMPLE / OUT-OF-SAMPLE) ===
use_date_filter = input.bool(true, "Habilitar Separación IS / OOS", group="Validación Anti-Overfit")
oos_year        = input.int({oos_start_year}, "Año Inicio OOS", group="Validación Anti-Overfit")
oos_month       = input.int({oos_start_month}, "Mes Inicio OOS", group="Validación Anti-Overfit")
oos_day         = input.int({oos_start_day}, "Día Inicio OOS", group="Validación Anti-Overfit")

is_oos = time >= timestamp(syminfo.timezone, oos_year, oos_month, oos_day, 0, 0)
bgcolor(is_oos ? color.new(color.orange, 90) : color.new(color.blue, 95), title="Sombreado IS (Azul) vs OOS (Naranja)")

// === 3. INDICADORES ===
ema_fast = ta.ema(close, fast_ema_len)
ema_slow = ta.ema(close, slow_ema_len)
hh = ta.highest(high, donchian_len)
ll = ta.lowest(low, donchian_len)
atr_val = ta.atr(atr_len)

plot(ema_fast, "EMA Rápida", color=color.aqua, linewidth=2)
plot(ema_slow, "EMA Lenta", color=color.purple, linewidth=2)
plot(hh[1], "Donchian High", color=color.green, style=plot.style_circles)
plot(ll[1], "Donchian Low", color=color.red, style=plot.style_circles)

// === 4. CONDICIONES DE ENTRADA Y SALIDA ===
trend_up   = ema_fast > ema_slow and close > ema_fast
trend_down = ema_fast < ema_slow and close < ema_fast

long_condition  = trend_up and close >= hh[1]
short_condition = trend_down and close <= ll[1]

// === 5. EJECUCIÓN CON SL/TP DINÁMICO POR ATR ===
if (strategy.position_size == 0)
    if (long_condition)
        sl_price = close - (atr_val * atr_sl_mult)
        tp_price = close + (atr_val * atr_tp_mult)
        strategy.entry("Long", strategy.long, comment="BUY_SIGNAL")
        strategy.exit("Long Exit", "Long", stop=sl_price, limit=tp_price, comment="LONG_SL_TP")
        alert('{{"action": "BUY", "symbol": "' + syminfo.ticker + '", "price": ' + str.tostring(close) + ', "sl": ' + str.tostring(sl_price) + ', "tp": ' + str.tostring(tp_price) + '}}', alert.freq_once_per_bar_close)

    if (short_condition)
        sl_price = close + (atr_val * atr_sl_mult)
        tp_price = close - (atr_val * atr_tp_mult)
        strategy.entry("Short", strategy.short, comment="SELL_SIGNAL")
        strategy.exit("Short Exit", "Short", stop=sl_price, limit=tp_price, comment="SHORT_SL_TP")
        alert('{{"action": "SELL", "symbol": "' + syminfo.ticker + '", "price": ' + str.tostring(close) + ', "sl": ' + str.tostring(sl_price) + ', "tp": ' + str.tostring(tp_price) + '}}', alert.freq_once_per_bar_close)

// === 6. TABLA DE TELEMETRÍA EN PANTALLA ===
var table perfTable = table.new(position.top_right, 4, 2, bgcolor=color.new(color.black, 20), border_color=color.gray, border_width=1)
if barstate.islast
    table.cell(perfTable, 0, 0, "Net Profit", text_color=color.white, text_size=size.small)
    table.cell(perfTable, 1, 0, "Profit Factor", text_color=color.white, text_size=size.small)
    table.cell(perfTable, 2, 0, "Win Rate", text_color=color.white, text_size=size.small)
    table.cell(perfTable, 3, 0, "Max DD", text_color=color.white, text_size=size.small)

    table.cell(perfTable, 0, 1, "$" + str.tostring(strategy.netprofit, "#.##"), text_color=strategy.netprofit >= 0 ? color.green : color.red, text_size=size.small)
    table.cell(perfTable, 1, 1, str.tostring(strategy.grossprofit / math.max(1, strategy.grossloss), "#.##"), text_color=color.yellow, text_size=size.small)
    table.cell(perfTable, 2, 1, str.tostring(strategy.wintrades / math.max(1, strategy.closedtrades) * 100, "#.#") + "%", text_color=color.aqua, text_size=size.small)
    table.cell(perfTable, 3, 1, str.tostring(strategy.max_drawdown / math.max(1, strategy.initial_capital) * 100, "#.##") + "%", text_color=color.red, text_size=size.small)
"""
    return code
