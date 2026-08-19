import pandas as pd
import numpy as np
from pathlib import Path

def test_regime_momentum(csv_path, symbol, route='ULTRA', leverage=3.0, ema_fast=30, ema_slow=120, adx_len=14, adx_thresh=22, atr_trail=2.8, tp_r=4.5):
    df = pd.read_csv(csv_path)
    df.columns = [c.strip().replace('<', '').replace('>', '').lower() for c in df.columns]
    rename_map = {'dtyyyymmdd': 'date', 'vol': 'volume', 'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close'}
    df = df.rename(columns=rename_map)
    df['close'] = pd.to_numeric(df['close'], errors='coerce')
    df['open'] = pd.to_numeric(df['open'], errors='coerce')
    df['high'] = pd.to_numeric(df['high'], errors='coerce')
    df['low'] = pd.to_numeric(df['low'], errors='coerce')
    df['volume'] = pd.to_numeric(df.get('volume', 1.0), errors='coerce').fillna(1.0)
    df = df.dropna().reset_index(drop=True)
    
    if len(df) < 200:
        return
        
    # EMAs
    df['ema_fast'] = df['close'].ewm(span=ema_fast).mean()
    df['ema_slow'] = df['close'].ewm(span=ema_slow).mean()
    
    # ATR & TR
    tr = np.maximum(df['high'] - df['low'], np.maximum(abs(df['high'] - df['close'].shift(1)), abs(df['low'] - df['close'].shift(1))))
    df['atr'] = tr.rolling(14).mean()
    
    # Directional Movement & ADX
    up_move = df['high'] - df['high'].shift(1)
    down_move = df['low'].shift(1) - df['low']
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    
    tr14 = tr.rolling(adx_len).sum()
    plus_di = 100 * (pd.Series(plus_dm).rolling(adx_len).sum() / (tr14 + 1e-9))
    minus_di = 100 * (pd.Series(minus_dm).rolling(adx_len).sum() / (tr14 + 1e-9))
    dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di + 1e-9))
    df['adx'] = dx.rolling(adx_len).mean()
    df['plus_di'] = plus_di
    df['minus_di'] = minus_di
    
    # Donchian
    df['upper'] = df['high'].rolling(20).max().shift(1)
    df['lower'] = df['low'].rolling(20).min().shift(1)
    df['vol_sma'] = df['volume'].rolling(20).mean()
    
    # 70% IS, 30% OOS
    split_idx = int(len(df) * 0.70)
    df_is = df.iloc[:split_idx].copy().reset_index(drop=True)
    df_oos = df.iloc[split_idx:].copy().reset_index(drop=True)
    
    def simulate(df_sub):
        capital = 10000.0 if route == 'ULTRA' else 50000.0
        init_cap = capital
        equity = [capital]
        position = 0
        entry_price = 0.0
        stop_price = 0.0
        tp_price = 0.0
        trades = []
        
        for i in range(2, len(df_sub)):
            row = df_sub.iloc[i]
            prev = df_sub.iloc[i-1]
            
            if position == 1:
                if row['low'] <= stop_price:
                    exit_p = stop_price
                    pnl = (exit_p - entry_price) / entry_price * capital * leverage - (capital * leverage * 0.0006)
                    capital += pnl
                    trades.append(pnl)
                    position = 0
                elif row['high'] >= tp_price:
                    exit_p = tp_price
                    pnl = (exit_p - entry_price) / entry_price * capital * leverage - (capital * leverage * 0.0006)
                    capital += pnl
                    trades.append(pnl)
                    position = 0
                else:
                    new_stop = row['close'] - row['atr'] * atr_trail
                    stop_price = max(stop_price, new_stop)
                    
            elif position == -1:
                if row['high'] >= stop_price:
                    exit_p = stop_price
                    pnl = (entry_price - exit_p) / entry_price * capital * leverage - (capital * leverage * 0.0006)
                    capital += pnl
                    trades.append(pnl)
                    position = 0
                elif row['low'] <= tp_price:
                    exit_p = tp_price
                    pnl = (entry_price - exit_p) / entry_price * capital * leverage - (capital * leverage * 0.0006)
                    capital += pnl
                    trades.append(pnl)
                    position = 0
                else:
                    new_stop = row['close'] + row['atr'] * atr_trail
                    stop_price = min(stop_price, new_stop)
                    
            if position == 0:
                # Strong Bull Regime: Fast EMA > Slow EMA + ADX > thresh + +DI > -DI + Close > 20-bar High
                if prev['ema_fast'] > prev['ema_slow'] and prev['adx'] > adx_thresh and prev['plus_di'] > prev['minus_di'] and prev['close'] > prev['upper']:
                    position = 1
                    entry_price = row['open'] * 1.0002
                    risk = max(row['atr'] * 2.0, entry_price * 0.015)
                    stop_price = entry_price - risk
                    tp_price = entry_price + risk * tp_r
                # Strong Bear Regime (Futures only)
                elif 'USDT' not in symbol and (prev['ema_fast'] < prev['ema_slow'] and prev['adx'] > adx_thresh and prev['minus_di'] > prev['plus_di'] and prev['close'] < prev['lower']):
                    position = -1
                    entry_price = row['open'] * 0.9998
                    risk = max(row['atr'] * 2.0, entry_price * 0.015)
                    stop_price = entry_price + risk
                    tp_price = entry_price - risk * tp_r
                    
            equity.append(max(0.0, capital))
            if capital <= 0:
                break
                
        net_ret = (capital - init_cap) / init_cap * 100.0
        b_day = 24 if '1H' in csv_path.upper() else (6 if '4H' in csv_path.upper() else 96)
        months = max(0.1, (len(df_sub) / b_day) / 30.5)
        monthly_ret = net_ret / months
        wins = [t for t in trades if t > 0]
        losses = [t for t in trades if t <= 0]
        pf = sum(wins) / abs(sum(losses)) if losses and sum(losses) != 0 else (99.0 if wins else 0.0)
        wr = len(wins) / max(1, len(trades)) * 100.0
        
        eq_arr = np.array(equity)
        peaks = np.maximum.accumulate(eq_arr)
        dds = (peaks - eq_arr) / np.maximum(1e-9, peaks) * 100.0
        max_dd = np.max(dds)
        return net_ret, monthly_ret, pf, wr, max_dd, len(trades), months

    is_net, is_m_roi, is_pf, is_wr, is_dd, is_tr, is_mo = simulate(df_is)
    oos_net, oos_m_roi, oos_pf, oos_wr, oos_dd, oos_tr, oos_mo = simulate(df_oos)
    
    print(f'{symbol:12s} | IS: Net={is_net:6.1f}% (PF {is_pf:4.2f}, DD {is_dd:4.1f}%, {is_tr:3d} tr) | OOS: Net={oos_net:6.1f}% ({oos_m_roi:5.1f}%/m, PF {oos_pf:4.2f}, WR {oos_wr:4.1f}%, DD {oos_dd:4.1f}%, {oos_tr:3d} tr, {oos_mo:.1f}m)')

csvs = [
    ('/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/sqx_imports/SOLUSDT_4H.csv', 'SOL-USDT 4h', 'ULTRA', 4.0, 20, 80, 14, 25, 2.5, 4.5),
    ('/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/sqx_imports/ETHUSDT_4H.csv', 'ETH-USDT 4h', 'ULTRA', 3.5, 20, 80, 14, 25, 2.5, 4.5),
    ('/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/sqx_imports/BTCUSDT_4H.csv', 'BTC-USDT 4h', 'ULTRA', 3.5, 20, 80, 14, 25, 2.5, 4.5),
    ('/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/sqx_imports/DOGEUSDT_4H.csv', 'DOGE-USDT 4h', 'ULTRA', 3.5, 20, 80, 14, 25, 2.5, 4.5),
    ('/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/sqx_imports/GC_4H.csv', 'Gold GC 4h', 'FONDEO', 1.0, 20, 80, 14, 20, 2.5, 3.5),
    ('/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/sqx_imports/NQ_4H.csv', 'NQ 4h', 'FONDEO', 1.0, 20, 80, 14, 20, 3.0, 3.0),
]
for c in csvs:
    test_regime_momentum(c[0], c[1], c[2], c[3], c[4], c[5], c[6], c[7], c[8], c[9])
