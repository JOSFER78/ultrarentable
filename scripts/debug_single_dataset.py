"""scripts/debug_single_dataset.py
Debug script to run gates on a single dataset and print detailed gate results.
"""

import json
import sys
import glob
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from contracts.snapshots.strategy_snapshot import StrategySnapshot
from services.validation.engine.event_backtest_engine import EventBacktestEngine
from services.api.app.validation.gates.gate_pipeline_orchestrator import GatePipelineOrchestrator
from services.discovery.ultra_discovery import UltraDiscoveryEngine

# Test ETH 1h dataset
data_file = ROOT_DIR / "data" / "normalized" / "ds_binance_ethusdt_1h_1695290400000_1787086800000.json"
with open(data_file) as f:
    candles = json.load(f)

total_bars = len(candles)
idx_is = int(total_bars * 0.60)
idx_val = int(total_bars * 0.80)

candles_is = candles[:idx_is]
candles_pre_oos = candles[:idx_val]
candles_blind_oos = candles[idx_val:]

engine = EventBacktestEngine()
orchestrator = GatePipelineOrchestrator()
ultra_discovery = UltraDiscoveryEngine()

grid = [
    ("TREND_FOLLOWING", 12, 36, 14, 52.0, 48.0, 1.5, 6.0, 0.015, 2, "ATR_REGIME", 0),
    ("MOMENTUM_BREAKOUT", 10, 30, 14, 52.0, 48.0, 1.8, 7.0, 0.015, 2, "ATR_REGIME", 20),
    ("EMA_CROSS", 10, 30, 14, 52.0, 48.0, 1.5, 6.0, 0.015, 2, None, 0),
    ("RSI_MOMENTUM", 8, 24, 14, 55.0, 45.0, 1.5, 6.0, 0.015, 2, None, 0),
]

for idx, (arch, ema_f, ema_s, rsi_p, rsi_l, rsi_s, sl_atr, tp_atr, risk_p, py_tiers, vol_filt, brk_lk) in enumerate(grid, 1):
    strat_id = f"DBG_ETH_1H_v{idx}"
    snapshot = ultra_discovery.generate_candidate_blueprint(
        strategy_id=strat_id,
        symbol="ETHUSDT",
        timeframe="1h",
        dataset_id=data_file.name,
        dataset_sha256="dbg_sha256",
        leverage=5.0,
        risk_pct=risk_p,
        sl_atr_mult=sl_atr,
        tp_atr_mult=tp_atr,
        ema_fast=ema_f,
        ema_slow=ema_s,
        rsi_period=rsi_p,
        rsi_threshold_long=rsi_l,
        rsi_threshold_short=rsi_s,
        pyramiding_tiers_count=py_tiers,
        archetype=arch,
        volatility_filter=vol_filt,
        breakout_confirmation=(brk_lk > 0),
        breakout_lookback=brk_lk,
        exit_family="RR_DYNAMIC",
        rr_multiple=tp_atr / max(0.1, sl_atr),
    )

    is_bt = engine.run_backtest(snapshot, candles_is, 1000.0)
    pre_oos_bt = engine.run_backtest(snapshot, candles_pre_oos, 1000.0)
    oos_bt = engine.run_backtest(snapshot, candles_blind_oos, 1000.0)

    print(f"\n========================================================", flush=True)
    print(f"Strategy {strat_id} ({arch}):", flush=True)
    print(f"  IS:  PF={is_bt.profit_factor:.2f}, DD={is_bt.max_drawdown_pct:.2f}%, Trades={is_bt.total_trades}, PnL=${is_bt.net_profit_usd:.2f}", flush=True)
    print(f"  OOS: PF={oos_bt.profit_factor:.2f}, DD={oos_bt.max_drawdown_pct:.2f}%, Trades={oos_bt.total_trades}, PnL=${oos_bt.net_profit_usd:.2f}", flush=True)

    is_pnls = [t.net_pnl_usd for t in is_bt.trades] if is_bt.trades else [0.0]
    pre_oos_pnls = [t.net_pnl_usd for t in pre_oos_bt.trades] if pre_oos_bt.trades else [0.0]
    oos_pnls = [t.net_pnl_usd for t in oos_bt.trades] if oos_bt.trades else [0.0]
    raw_trades_oos = [{'trade_id': t.trade_id, 'side': t.side, 'entry_price': t.entry_price, 'exit_price': t.exit_price, 'qty': t.qty, 'net_pnl_usd': t.net_pnl_usd, 'gross_pnl_usd': t.gross_pnl_usd, 'fees_usd': t.fees_usd, 'slippage_usd': t.slippage_usd, 'entry_bar': t.entry_bar, 'exit_bar': t.exit_bar, 'entry_time_ms': t.entry_time_ms, 'exit_time_ms': t.exit_time_ms} for t in oos_bt.trades]

    candidate_info = {
        "candidate_id": strat_id,
        "name": strat_id,
        "route": "ULTRA",
        "symbol": "ETHUSDT",
        "timeframe": "1h",
        "profit_factor_oos": oos_bt.profit_factor,
        "max_drawdown_pct": oos_bt.max_drawdown_pct,
        "dataset_id": data_file.name,
        "dataset_filepath": str(data_file),
        "dataset_sha256": "dbg_sha256",
        "trials_tested": len(grid),
        "parameters": {"ema_fast": ema_f, "ema_slow": ema_s, "rsi_period": rsi_p, "sl_atr_mult": sl_atr, "tp_atr_mult": tp_atr, "pyramiding_tiers": py_tiers, "archetype": arch},
    }

    res = orchestrator.run_all_gates(
        candidate_info=candidate_info,
        candles=candles_blind_oos,
        is_trades=is_pnls,
        oos_trades=oos_pnls,
        pre_oos_trades=pre_oos_pnls,
        trades_raw=raw_trades_oos,
        strategy_snapshot=snapshot,
    )

    print(f"  Gates Passed Count: {res.get('gates_passed_count')}/11, Overall Score: {res.get('overall_score')}", flush=True)
    for g in res.get("gates", []):
        p_str = "PASS" if g.get("passed") else "FAIL"
        print(f"    Gate {g.get('gate_id'):02d} ({g.get('name')}): [{p_str}] score={g.get('score')}, verdict={g.get('verdict')}", flush=True)
