import json
import numpy as np

with open('/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/normalized/ds_binance_btcusdt_1h_1695290400000_1787086800000.json') as f:
    candles = json.load(f)

closes = np.array([c['close'] for c in candles])
highs = np.array([c['high'] for c in candles])
lows = np.array([c['low'] for c in candles])

n = len(candles)
split_idx = int(n * 0.70)

# ATR 14
tr = np.maximum(highs[1:] - lows[1:], np.maximum(np.abs(highs[1:] - closes[:-1]), np.abs(lows[1:] - closes[:-1])))
atr = np.zeros(n)
atr[0] = highs[0] - lows[0]
for i in range(1, n):
    atr[i] = (atr[i-1] * 13 + tr[i-1]) / 14.0

# EMA 20 & EMA 100
ema20 = np.zeros(n)
ema100 = np.zeros(n)
ema20[0] = closes[0]
ema100[0] = closes[0]
a20 = 2.0 / 21.0
a100 = 2.0 / 101.0
for i in range(1, n):
    ema20[i] = a20 * closes[i] + (1 - a20) * ema20[i-1]
    ema100[i] = a100 * closes[i] + (1 - a100) * ema100[i-1]

# Dynamic Risk & Compounding
capital = 10000.0
eq = capital
trades_is = []
trades_oos = []

in_pos = False
pos_side = ''
entry_px = 0.0
sl_px = 0.0
tp_px = 0.0
be_hit = False

for i in range(100, n):
    c = closes[i]
    h = highs[i]
    l = lows[i]
    a = atr[i]
    
    if in_pos:
        sl_hit = (pos_side == 'LONG' and l <= sl_px) or (pos_side == 'SHORT' and h >= sl_px)
        tp_hit = (pos_side == 'LONG' and h >= tp_px) or (pos_side == 'SHORT' and l <= tp_px)
        
        if not be_hit:
            gain = (c - entry_px) if pos_side == 'LONG' else (entry_px - c)
            if gain >= 1.5 * a:
                sl_px = entry_px + (0.05 * a) if pos_side == 'LONG' else entry_px - (0.05 * a)
                be_hit = True
                
        if sl_hit or tp_hit:
            exit_px = sl_px if sl_hit else tp_px
            ret = (exit_px - entry_px) / entry_px if pos_side == 'LONG' else (entry_px - exit_px) / entry_px
            pnl = (eq * 0.03 / max(0.005, 1.5 * a / entry_px)) * ret - (0.0005 * 2 * (eq * 0.03 / max(0.005, 1.5 * a / entry_px)))
            eq += pnl
            if i <= split_idx:
                trades_is.append(pnl)
            else:
                trades_oos.append(pnl)
            in_pos = False
            continue
            
    if not in_pos:
        long_sig = (c > ema100[i]) and (closes[i-1] <= ema20[i-1]) and (c > ema20[i]) and (a > np.mean(atr[i-20:i]))
        short_sig = (c < ema100[i]) and (closes[i-1] >= ema20[i-1]) and (c < ema20[i]) and (a > np.mean(atr[i-20:i]))
        
        if long_sig:
            in_pos = True
            pos_side = 'LONG'
            entry_px = c
            sl_px = c - (1.5 * a)
            tp_px = c + (5.0 * a)
            be_hit = False
        elif short_sig:
            in_pos = True
            pos_side = 'SHORT'
            entry_px = c
            sl_px = c + (1.5 * a)
            tp_px = c - (5.0 * a)
            be_hit = False

w_oos = [t for t in trades_oos if t > 0]
l_oos = [t for t in trades_oos if t <= 0]
pf_oos = sum(w_oos) / abs(sum(l_oos)) if l_oos else 0
print(f'BTC Pullback EMA Expansion: IS Trades={len(trades_is)} | OOS Trades={len(trades_oos)} | OOS Net=${sum(trades_oos):.2f} | OOS PF={pf_oos:.2f} | WinRate={len(w_oos)/len(trades_oos)*100:.1f}%')
