"""Run Risk-Controlled Backtests on Real ETH Datasets."""

import json
from pathlib import Path
from services.api.app.factory.ultra_risk_controlled_engine import UltraRiskControlledEngine

norm_dir = Path("data/normalized")
datasets = [
    ("ETH-USDT", "1h", norm_dir / "ds_bingx_ETH_USDT_1h_1771718400000_1785535200000_6668069ea1.json"),
    ("ETH-USDT", "15m", norm_dir / "ds_bingx_ETH_USDT_15m_1771718400000_1785540600000_6fb02da608.json"),
]

for sym, tf, p in datasets:
    with open(p, "r") as f:
        data = json.load(f)
        bars = data if isinstance(data, list) else data.get("bars", data.get("data", []))
    print(f"\n=======================================================")
    print(f"📊 BACKTEST CON GESTIÓN DE RIESGO REAL: {sym} {tf} ({len(bars)} velas)")
    print(f"=======================================================")
    engine = UltraRiskControlledEngine(bars, symbol=sym, timeframe=tf)
    res = engine.run_strategy(
        name=f"TrendBreakout_R:R_1:4_{sym}_{tf}",
        risk_per_trade_pct=1.5,
        max_leverage=10.0,
        atr_stop_mult=1.4,
        atr_tp_mult=4.2,
        split_ratio=0.70
    )
    print(f"Capital Inicial: ${res.initial_equity:,.2f} -> Final: ${res.final_equity:,.2f} USD")
    print(f"Beneficio Neto: +${res.net_profit_usd:,.2f} USD ({res.roi_pct}% ROI)")
    print(f"Max Drawdown: {res.max_drawdown_pct}% (Límite Seguro < 15%)")
    print(f"Trades Totales: {res.total_trades} | Win Rate: {res.win_rate_pct}% | Profit Factor: {res.profit_factor} | Sharpe: {res.sharpe_ratio}")
    print(f" -> In-Sample (70%): Trades={res.is_metrics['trades']}, Net=+${res.is_metrics['net_profit']}, PF={res.is_metrics['profit_factor']}")
    print(f" -> Out-of-Sample (30%): Trades={res.oos_metrics['trades']}, Net=+${res.oos_metrics['net_profit']}, PF={res.oos_metrics['profit_factor']}")
