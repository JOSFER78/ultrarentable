import pandas as pd
import numpy as np

def test_pyramiding_alpha(csv_path, symbol, leverage=4.0, atr_len=14, mult_expansion=1.8, trail_atr=2.2, tp_atr=6.0):
    df = pd.read_csv(csv_path)
    df.columns = [c.strip().replace('<', '').replace('>', '').lower() for c in df.columns]
    rename_map = {'dtyyyymmdd': 'date', 'vol': 'volume', 'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close'}
    df = df.rename(columns=rename_map)
    df['close'] = pd.to_numeric(df['close'], errors='coerce')
    df['open'] = pd.to_numeric(df['open'], errors='coerce')
    df['high'] = pd.to_numeric(df['high'], errors='coerce')
    df['low'] = pd.to_numeric(df['low'], errors='coerce')
    df = df.dropna().reset_index(drop=True)
    
    # 50 EMA + ATR + Candle Body
    df['ema'] = df['close'].ewm(span=50).mean()
    tr = np.maximum(df['high'] - df['low'], np.maximum(abs(df['high'] - df['close'].shift(1)), abs(df['low'] - df['close'].shift(1))))
    df['atr'] = tr.rolling(atr_len).mean()
    df['body'] = abs(df['close'] - df['open'])
    
    # Split IS / OOS (70% / 30%)
    split_idx = int(len(df) * 0.70)
    df_is = df.iloc[:split_idx].copy().reset_index(drop=True)
    df_oos = df.iloc[split_idx:].copy().reset_index(drop=True)
    
    def simulate(df_sub):
        capital = 10000.0
        init_cap = capital
        equity = [capital]
        position = 0
        entry_price = 0.0
        stop_price = 0.0
        tp_price = 0.0
        units = 1.0
        trades = []
        
        for i in range(2, len(df_sub)):
            row = df_sub.iloc[i]
            prev = df_sub.iloc[i-1]
            
            if position == 1:
                # Check pyramiding (at +2R profit, add 0.5 units and ratchet stop to breakeven + 0.5R)
                r_dist = row['atr'] * 2.0
                if units == 1.0 and row['high'] >= entry_price + r_dist:
                    units = 1.5
                    stop_price = entry_price + r_dist * 0.5
                    
                if row['low'] <= stop_price:
                    exit_p = stop_price
                    pnl = (exit_p - entry_price) / entry_price * capital * leverage * units - (capital * leverage * units * 0.0006)
                    capital += pnl
                    trades.append(pnl)
                    position = 0
                    units = 1.0
                elif row['high'] >= tp_price:
                    exit_p = tp_price
                    pnl = (exit_p - entry_price) / entry_price * capital * leverage * units - (capital * leverage * units * 0.0006)
                    capital += pnl
                    trades.append(pnl)
                    position = 0
                    units = 1.0
                else:
                    new_stop = row['close'] - row['atr'] * trail_atr
                    stop_price = max(stop_price, new_stop)
                    
            if position == 0:
                # Volatility Expansion: Large Bullish Body (> 1.8x ATR) & Close > 50 EMA & Close > Previous High
                if prev['close'] > prev['ema'] and prev['body'] > prev['atr'] * mult_expansion and prev['close'] > prev['open'] and prev['close'] > df_sub.iloc[i-2]['high']:
                    position = 1
                    units = 1.0
                    entry_price = row['open'] * 1.0002
                    risk = max(row['atr'] * 2.0, entry_price * 0.02)
                    stop_price = entry_price - risk
                    tp_price = entry_price + risk * tp_atr
                    
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

    is_net, is_m, is_pf, is_wr, is_dd, is_tr, is_mo = simulate(df_is)
    oos_net, oos_m, oos_pf, oos_wr, oos_dd, oos_tr, oos_mo = simulate(df_oos)
    print(f'{symbol:12s} | IS: Net={is_net:7.1f}% (PF {is_pf:4.2f}, DD {is_dd:4.1f}%, {is_tr:3d} tr) | OOS: Net={oos_net:7.1f}% ({oos_m:5.1f}%/m, PF {oos_pf:4.2f}, WR {oos_wr:4.1f}%, DD {oos_dd:4.1f}%, {oos_tr:3d} tr, {oos_mo:.1f}m)')

csvs = [
    ('/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/sqx_imports/SOLUSDT_1H.csv', 'SOL-USDT 1h', 4.0, 14, 1.6, 2.5, 5.0),
    ('/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/sqx_imports/ETHUSDT_1H.csv', 'ETH-USDT 1h', 4.0, 14, 1.6, 2.5, 5.0),
    ('/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/sqx_imports/BTCUSDT_1H.csv', 'BTC-USDT 1h', 4.0, 14, 1.6, 2.5, 5.0),
    ('/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/sqx_imports/DOGEUSDT_1H.csv', 'DOGE-USDT 1h', 4.0, 14, 1.6, 2.5, 5.0),
    ('/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/sqx_imports/AVAXUSDT_1H.csv', 'AVAX-USDT 1h', 4.0, 14, 1.6, 2.5, 5.0),
]
for c in csvs:
    test_pyramiding_alpha(c[0], c[1], c[2], c[3], c[4], c[5], c[6])
