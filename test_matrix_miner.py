import glob
import json
import os
import numpy as np

files = glob.glob('/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/normalized/ds_binance_*_1h_*.json')
print(f'Total Datasets: {len(files)}')

best_strategies = []

for fp in files:
    sym = os.path.basename(fp).split('_')[2].upper()
    with open(fp) as f:
        candles = json.load(f)
    if len(candles) < 1000:
        continue
    
    n = len(candles)
    closes = np.array([c['close'] for c in candles], dtype=np.float64)
    highs = np.array([c['high'] for c in candles], dtype=np.float64)
    lows = np.array([c['low'] for c in candles], dtype=np.float64)
    vols = np.array([c.get('volume', 0.0) for c in candles], dtype=np.float64)
    
    split_idx = int(n * 0.70)
    
    # Precalc ATR 14
    tr = np.maximum(highs[1:] - lows[1:], np.maximum(np.abs(highs[1:] - closes[:-1]), np.abs(lows[1:] - closes[:-1])))
    atr = np.zeros(n)
    atr[0] = highs[0] - lows[0]
    for i in range(1, n):
        atr[i] = (atr[i-1] * 13 + tr[i-1]) / 14.0
        
    # Precalc EMAs
    ema20 = np.zeros(n)
    ema50 = np.zeros(n)
    ema200 = np.zeros(n)
    ema20[0] = closes[0]
    ema50[0] = closes[0]
    ema200[0] = closes[0]
    for i in range(1, n):
        ema20[i] = (2/21) * closes[i] + (1 - 2/21) * ema20[i-1]
        ema50[i] = (2/51) * closes[i] + (1 - 2/51) * ema50[i-1]
        ema200[i] = (2/201) * closes[i] + (1 - 2/201) * ema200[i-1]
        
    # Precalc RSI 14
    deltas = np.diff(closes)
    seed = deltas[:14]
    up = seed[seed >= 0].sum() / 14
    down = -seed[seed < 0].sum() / 14
    rs = up / down if down != 0 else 0
    rsi = np.zeros(n)
    rsi[14] = 100.0 - (100.0 / (1.0 + rs)) if (1.0 + rs) != 0 else 50.0
    for i in range(15, n):
        d = deltas[i-1]
        u = d if d > 0 else 0.0
        dw = -d if d < 0 else 0.0
        up = (up * 13 + u) / 14
        down = (down * 13 + dw) / 14
        rs = up / down if down != 0 else 0
        rsi[i] = 100.0 - (100.0 / (1.0 + rs)) if (1.0 + rs) != 0 else 50.0
        
    # Precalc Donchian 20
    donch_hi = np.zeros(n)
    donch_lo = np.zeros(n)
    for i in range(20, n):
        donch_hi[i] = np.max(highs[i-20:i])
        donch_lo[i] = np.min(lows[i-20:i])
        
    # Test Archetypes with Pyramiding & Margin Recycling
    archetypes = ['MEAN_REVERSION_RSI', 'TREND_EMA_REGIME', 'DONCHIAN_EXPANSION']
    
    for arch in archetypes:
        for sl_mult in [1.0, 1.5, 2.0]:
            for tp_mult in [3.0, 5.0, 7.0]:
                for risk_pct in [3.0, 5.0]:
                    # Run Simulation
                    initial_cap = 10000.0
                    eq = initial_cap
                    pk = initial_cap
                    max_dd = 0.0
                    trades_is = []
                    trades_oos = []
                    
                    in_pos = False
                    pos_side = ''
                    entry_px = 0.0
                    sl_px = 0.0
                    tp_px = 0.0
                    tier_count = 0
                    max_tiers = 3
                    pos_qty = 0.0
                    
                    for i in range(200, n):
                        c = closes[i]
                        h = highs[i]
                        l = lows[i]
                        a = atr[i]
                        
                        if in_pos:
                            sl_hit = (pos_side == 'LONG' and l <= sl_px) or (pos_side == 'SHORT' and h >= sl_px)
                            tp_hit = (pos_side == 'LONG' and h >= tp_px) or (pos_side == 'SHORT' and l <= tp_px)
                            
                            # Pyramiding & Break-Even Trailing
                            if not sl_hit and not tp_hit and tier_count < max_tiers:
                                dist = (h - entry_px) if pos_side == 'LONG' else (entry_px - l)
                                if dist >= tier_count * (1.8 * a):
                                    # Move SL to lock in profit (Risk-Free)
                                    sl_px = entry_px + ((tier_count - 1) * 0.8 * a) if pos_side == 'LONG' else entry_px - ((tier_count - 1) * 0.8 * a)
                                    # Add tier
                                    tier_risk = eq * (risk_pct / 100.0)
                                    added_qty = tier_risk / max(0.001, sl_mult * a)
                                    pos_qty += added_qty
                                    tier_count += 1
                                    
                            if sl_hit or tp_hit:
                                exit_px = sl_px if sl_hit else tp_px
                                pnl = (exit_px - entry_px) * pos_qty if pos_side == 'LONG' else (entry_px - exit_px) * pos_qty
                                # Exact fee: 0.05% taker on notional entry + exit
                                fee = (pos_qty * entry_px + pos_qty * exit_px) * 0.0005
                                net_pnl = pnl - fee
                                eq += net_pnl
                                pk = max(pk, eq)
                                cur_dd = (pk - eq) / pk * 100.0 if pk > 0 else 0.0
                                max_dd = max(max_dd, cur_dd)
                                
                                if i <= split_idx:
                                    trades_is.append(net_pnl)
                                else:
                                    trades_oos.append(net_pnl)
                                in_pos = False
                                continue
                                
                        if not in_pos:
                            if arch == 'MEAN_REVERSION_RSI':
                                long_sig = (rsi[i] < 32.0) and (l <= donch_lo[i]) and (c > ema20[i])
                                short_sig = (rsi[i] > 68.0) and (h >= donch_hi[i]) and (c < ema20[i])
                            elif arch == 'TREND_EMA_REGIME':
                                long_sig = (c > ema200[i]) and (ema20[i] > ema50[i]) and (c >= donch_hi[i-1]) and (a > np.mean(atr[i-20:i]))
                                short_sig = (c < ema200[i]) and (ema20[i] < ema50[i]) and (c <= donch_lo[i-1]) and (a > np.mean(atr[i-20:i]))
                            else: # DONCHIAN_EXPANSION
                                long_sig = (c >= donch_hi[i-1]) and (a >= np.mean(atr[i-20:i]) * 1.1)
                                short_sig = (c <= donch_lo[i-1]) and (a >= np.mean(atr[i-20:i]) * 1.1)
                                
                            if long_sig:
                                in_pos = True
                                pos_side = 'LONG'
                                entry_px = c
                                sl_px = c - (sl_mult * a)
                                tp_px = c + (tp_mult * a)
                                risk_cash = eq * (risk_pct / 100.0)
                                pos_qty = risk_cash / max(0.001, sl_mult * a)
                                tier_count = 1
                            elif short_sig:
                                in_pos = True
                                pos_side = 'SHORT'
                                entry_px = c
                                sl_px = c + (sl_mult * a)
                                tp_px = c - (tp_mult * a)
                                risk_cash = eq * (risk_pct / 100.0)
                                pos_qty = risk_cash / max(0.001, sl_mult * a)
                                tier_count = 1

                    w_is = [t for t in trades_is if t > 0]
                    l_is = [t for t in trades_is if t <= 0]
                    pf_is = sum(w_is) / abs(sum(l_is)) if l_is else 0.0
                    
                    w_oos = [t for t in trades_oos if t > 0]
                    l_oos = [t for t in trades_oos if t <= 0]
                    pf_oos = sum(w_oos) / abs(sum(l_oos)) if l_oos else 0.0
                    
                    oos_net = sum(trades_oos)
                    
                    if len(trades_is) >= 20 and len(trades_oos) >= 15 and pf_is >= 1.20 and pf_oos >= 1.35 and oos_net > 0:
                        best_strategies.append({
                            'symbol': sym,
                            'archetype': arch,
                            'sl_mult': sl_mult,
                            'tp_mult': tp_mult,
                            'risk_pct': risk_pct,
                            'is_trades': len(trades_is),
                            'is_pf': round(pf_is, 2),
                            'oos_trades': len(trades_oos),
                            'oos_pf': round(pf_oos, 2),
                            'oos_net': round(oos_net, 2),
                            'final_equity': round(eq, 2),
                            'max_dd_pct': round(max_dd, 2),
                            'win_rate_oos': round(len(w_oos)/len(trades_oos)*100, 1),
                        })

print(f'\n=== ESTRATEGIAS CAMPEONAS APROBADAS (Walk-Forward OOS PF >= 1.35): {len(best_strategies)} ===')
best_strategies.sort(key=lambda x: x['oos_pf'], reverse=True)
for s in best_strategies[:15]:
    print(s)
