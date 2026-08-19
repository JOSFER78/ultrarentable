from services.api.app.factory.intelligent_quant_miner import intelligent_quant_miner
import pandas as pd

symbols = [
    ('SOL-USDT', '1h', 'ULTRA', 3.5, 100, 14, 2.5, 30, 4.5),
    ('SOL-USDT', '4h', 'ULTRA', 4.0, 50, 14, 2.8, 20, 5.0),
    ('ETH-USDT', '4h', 'ULTRA', 3.5, 50, 14, 2.5, 20, 4.5),
    ('BTC-USDT', '4h', 'ULTRA', 3.5, 50, 14, 2.5, 20, 4.5),
    ('NQ', '4h', 'FONDEO', 1.0, 60, 14, 3.0, 30, 3.0),
    ('GC', '4h', 'FONDEO', 1.0, 60, 14, 2.8, 30, 3.0),
]

for s, tf, route, lev, ema, atr_p, trail, donch, tp in symbols:
    df = intelligent_quant_miner.load_dataset(s, tf)
    if df is not None:
        is_r, oos_r = intelligent_quant_miner.run_asymmetric_convex_backtest(
            df, s, tf, route=route, leverage=lev, ema_trend=ema, atr_period=atr_p,
            atr_trail_mult=trail, donchian_period=donch, take_profit_r=tp
        )
        if is_r and oos_r:
            print(f"{s:10s} {tf:3s} | IS: Net=${is_r.net_profit_usd:8.1f} (PF {is_r.profit_factor:4.2f}, DD {is_r.max_drawdown_pct:4.1f}%) | OOS: Net=${oos_r.net_profit_usd:8.1f} ({oos_r.monthly_roi_pct:5.1f}%/m, PF {oos_r.profit_factor:4.2f}, DD {oos_r.max_drawdown_pct:4.1f}%, MC {oos_r.monte_carlo_score:4.1f}%)")
