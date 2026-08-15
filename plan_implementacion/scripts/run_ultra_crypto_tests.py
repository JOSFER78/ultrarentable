"""Backtest and Stress-Testing of Ultra Strategies on BingX Crypto Perps."""

import json
import math
from typing import List, Dict, Any

# Load real normalized ETH-USDT 1h dataset (3839 bars)
DATA_PATH = "/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/normalized/ds_bingx_ETH_USDT_1h_1771750800000_1785567600000_b6299ab58d.json"

with open(DATA_PATH, "r") as f:
    bars = json.load(f)

# Sort by time
bars = sorted(bars, key=lambda x: x["time"])
TOTAL_BARS = len(bars)
IS_SPLIT = int(TOTAL_BARS * 0.70)
is_bars = bars[:IS_SPLIT]
oos_bars = bars[IS_SPLIT:]

print(f"Total Bars: {TOTAL_BARS} | In-Sample: {len(is_bars)} | Out-of-Sample: {len(oos_bars)}")

def run_backtest_strategy(bars_data: List[Dict[str, Any]], leverage: float = 3.0, r_mult: float = 2.0, atr_period: int = 14) -> Dict[str, Any]:
    initial_capital = 10000.0
    equity = initial_capital
    peak_equity = initial_capital
    max_drawdown_usd = 0.0
    max_drawdown_pct = 0.0
    
    trades = []
    position = None  # {'entry_price', 'side', 'size_usd', 'stop_loss', 'take_profit', 'entry_bar'}
    
    # Pre-calculate simple ATR
    atrs = [0.0] * len(bars_data)
    for i in range(1, len(bars_data)):
        high = bars_data[i]["high"]
        low = bars_data[i]["low"]
        prev_close = bars_data[i-1]["close"]
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        if i < atr_period:
            atrs[i] = tr
        else:
            atrs[i] = (atrs[i-1] * (atr_period - 1) + tr) / atr_period

    # BingX Friction
    TAKER_FEE_RATE = 0.0005  # 0.050%
    SPREAD_SLIPPAGE_PCT = 0.0004  # ~0.04%

    for i in range(20, len(bars_data)):
        bar = bars_data[i]
        prev_bars = bars_data[i-20:i]
        
        # Check open position exit
        if position is not None:
            exit_price = None
            exit_reason = None
            
            if position["side"] == "LONG":
                if bar["low"] <= position["stop_loss"]:
                    exit_price = position["stop_loss"]
                    exit_reason = "STOP_LOSS"
                elif bar["high"] >= position["take_profit"]:
                    exit_price = position["take_profit"]
                    exit_reason = "TAKE_PROFIT"
            elif position["side"] == "SHORT":
                if bar["high"] >= position["stop_loss"]:
                    exit_price = position["stop_loss"]
                    exit_reason = "STOP_LOSS"
                elif bar["low"] <= position["take_profit"]:
                    exit_price = position["take_profit"]
                    exit_reason = "TAKE_PROFIT"
                    
            if exit_price is not None:
                # Calculate PnL with fees and leverage
                entry_val = position["size_usd"]
                exit_val = position["size_usd"] * (exit_price / position["entry_price"] if position["side"] == "LONG" else (2.0 - exit_price / position["entry_price"]))
                gross_pnl = exit_val - entry_val
                
                # Fees (entry + exit) + slippage
                fees = (entry_val + exit_val) * (TAKER_FEE_RATE + SPREAD_SLIPPAGE_PCT)
                net_pnl = gross_pnl - fees
                
                equity += net_pnl
                trades.append({
                    "pnl": net_pnl,
                    "return_pct": (net_pnl / position["margin_usd"]) * 100,
                    "reason": exit_reason,
                    "bars_held": i - position["entry_bar"]
                })
                
                if equity > peak_equity:
                    peak_equity = equity
                dd_usd = peak_equity - equity
                dd_pct = (dd_usd / peak_equity) * 100
                if dd_pct > max_drawdown_pct:
                    max_drawdown_pct = dd_pct
                    max_drawdown_usd = dd_usd
                
                position = None
                
        # Signal Generation (Donchian 20 + ATR Filter)
        if position is None and atrs[i] > 0:
            highest_high = max(b["high"] for b in prev_bars)
            lowest_low = min(b["low"] for b in prev_bars)
            atr = atrs[i]
            
            # Sizing based on fixed 2% risk of equity
            risk_usd = equity * 0.02
            stop_dist = atr * 1.5
            
            if bar["close"] > highest_high:
                # LONG Signal
                entry_price = bar["close"] * (1.0 + SPREAD_SLIPPAGE_PCT)
                stop_loss = entry_price - stop_dist
                take_profit = entry_price + (stop_dist * r_mult)
                
                size_coins = risk_usd / stop_dist
                notional_usd = size_coins * entry_price
                margin_usd = notional_usd / leverage
                
                if margin_usd <= equity * 0.5:  # Max 50% equity margin usage
                    position = {
                        "side": "LONG",
                        "entry_price": entry_price,
                        "stop_loss": stop_loss,
                        "take_profit": take_profit,
                        "size_usd": notional_usd,
                        "margin_usd": margin_usd,
                        "entry_bar": i
                    }
                    
            elif bar["close"] < lowest_low:
                # SHORT Signal
                entry_price = bar["close"] * (1.0 - SPREAD_SLIPPAGE_PCT)
                stop_loss = entry_price + stop_dist
                take_profit = entry_price - (stop_dist * r_mult)
                
                size_coins = risk_usd / stop_dist
                notional_usd = size_coins * entry_price
                margin_usd = notional_usd / leverage
                
                if margin_usd <= equity * 0.5:
                    position = {
                        "side": "SHORT",
                        "entry_price": entry_price,
                        "stop_loss": stop_loss,
                        "take_profit": take_profit,
                        "size_usd": notional_usd,
                        "margin_usd": margin_usd,
                        "entry_bar": i
                    }

    # Summary metrics
    wins = [t for t in trades if t["pnl"] > 0]
    losses = [t for t in trades if t["pnl"] <= 0]
    total_gain = sum(t["pnl"] for t in wins)
    total_loss = abs(sum(t["pnl"] for t in losses)) if losses else 1.0
    pf = total_gain / total_loss if total_loss > 0 else 0.0
    win_rate = (len(wins) / len(trades) * 100) if trades else 0.0
    net_profit = equity - initial_capital
    net_return_pct = (net_profit / initial_capital) * 100

    return {
        "trades_count": len(trades),
        "wins_count": len(wins),
        "losses_count": len(losses),
        "win_rate_pct": round(win_rate, 2),
        "profit_factor": round(pf, 2),
        "net_profit_usd": round(net_profit, 2),
        "net_return_pct": round(net_return_pct, 2),
        "max_drawdown_pct": round(max_drawdown_pct, 2),
        "final_equity_usd": round(equity, 2)
    }

print("\n=== RUNNING BACKTESTS FOR ULTRA CRYPTO (BINGX PERPS) ===")
# Test across multiple leverage levels & R:R ratios
for lev in [1.0, 2.0, 3.0, 5.0]:
    for r_rr in [1.5, 2.0, 3.0]:
        is_res = run_backtest_strategy(is_bars, leverage=lev, r_mult=r_rr)
        oos_res = run_backtest_strategy(oos_bars, leverage=lev, r_mult=r_rr)
        print(f"\n--- Leverage: {lev}x | R:R Target: 1:{r_rr} ---")
        print(f"  IN-SAMPLE  (70%): Return: +{is_res['net_return_pct']}% | Trades: {is_res['trades_count']} | PF: {is_res['profit_factor']} | MaxDD: {is_res['max_drawdown_pct']}% | WinRate: {is_res['win_rate_pct']}%")
        print(f"  OUT-SAMPLE (30%): Return: +{oos_res['net_return_pct']}% | Trades: {oos_res['trades_count']} | PF: {oos_res['profit_factor']} | MaxDD: {oos_res['max_drawdown_pct']}% | WinRate: {oos_res['win_rate_pct']}%")
