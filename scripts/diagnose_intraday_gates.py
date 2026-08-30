"""scripts/diagnose_intraday_gates.py
Diagnostic tool to inspect 11-gate results for intraday strategy candidates across symbols and timeframes.
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

data_dir = ROOT_DIR / "data" / "normalized"
manifests = sorted(glob.glob(str(data_dir / "*_manifest.json")))

intraday_datasets = []
for m_file in manifests:
    with open(m_file, "r") as f:
        mdata = json.load(f)
    sym = mdata.get("symbol", "").upper().replace("-", "").replace("_", "")
    tf = mdata.get("interval", "").lower()
    if tf in {"1m", "5m", "15m", "1h"}:
        df = m_file.replace("_manifest.json", ".json")
        if Path(df).exists():
            intraday_datasets.append((df, m_file, sym, tf, mdata))

print(f"Total intraday datasets: {len(intraday_datasets)}")

backtest_engine = EventBacktestEngine()
orchestrator = GatePipelineOrchestrator()
ultra_discovery = UltraDiscoveryEngine()

# Test sample candidate on first 5 intraday datasets
search_configs = [
    ("TREND_FOLLOWING", 12, 36, 14, 52.0, 48.0, 1.5, 5.0, 0.02, 2, "ATR_REGIME", 0),
    ("MOMENTUM_BREAKOUT", 10, 30, 14, 52.0, 48.0, 1.5, 6.0, 0.02, 2, "ATR_REGIME", 20),
    ("EMA_CROSS", 10, 30, 14, 50.0, 50.0, 1.5, 5.0, 0.02, 2, None, 0),
    ("RSI_MOMENTUM", 8, 24, 14, 55.0, 45.0, 1.5, 5.0, 0.02, 2, None, 0),
]

for ds_idx, (data_file, m_file, symbol, timeframe, mdata) in enumerate(intraday_datasets[:10], 1):
    with open(data_file, "r") as f:
        candles = json.load(f)

    if not isinstance(candles, list) or len(candles) < 300:
        continue

    total_bars = len(candles)
    idx_is = int(total_bars * 0.60)
    idx_val = int(total_bars * 0.80)

    candles_is = candles[:idx_is]
    candles_pre_oos = candles[:idx_val]
    candles_blind_oos = candles[idx_val:]

    print(f"\n--- Testing Dataset {symbol} {timeframe} ({total_bars} bars, {len(candles_blind_oos)} OOS) ---")

    for cfg_idx, (arch, ema_f, ema_s, rsi_p, rsi_l, rsi_s, sl_atr, tp_atr, risk_p, py_tiers, vol_filt, brk_lk) in enumerate(search_configs, 1):
        strat_id = f"DIAG_{symbol}_{timeframe}_v{cfg_idx}"

        snapshot = ultra_discovery.generate_candidate_blueprint(
            strategy_id=strat_id,
            symbol=symbol,
            timeframe=timeframe,
            dataset_id=Path(data_file).name,
            dataset_sha256="diag_hash",
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

        is_bt = backtest_engine.run_backtest(snapshot, candles_is, 1000.0)
        pre_oos_bt = backtest_engine.run_backtest(snapshot, candles_pre_oos, 1000.0)
        oos_bt = backtest_engine.run_backtest(snapshot, candles_blind_oos, 1000.0)

        print(f"  Cfg {cfg_idx} ({arch}): IS PF={is_bt.profit_factor:.2f}, OOS PF={oos_bt.profit_factor:.2f}, OOS DD={oos_bt.max_drawdown_pct:.2f}%, OOS Trades={oos_bt.total_trades}")

        if oos_bt.profit_factor >= 1.05 and oos_bt.total_trades >= 5:
            is_pnls = [t.net_pnl_usd for t in is_bt.trades] if is_bt.trades else [0.0]
            pre_oos_pnls = [t.net_pnl_usd for t in pre_oos_bt.trades] if pre_oos_bt.trades else [0.0]
            oos_pnls = [t.net_pnl_usd for t in oos_bt.trades] if oos_bt.trades else [0.0]
            raw_trades_oos = [{'trade_id': t.trade_id, 'side': t.side, 'entry_price': t.entry_price, 'exit_price': t.exit_price, 'qty': t.qty, 'net_pnl_usd': t.net_pnl_usd, 'gross_pnl_usd': t.gross_pnl_usd, 'fees_usd': t.fees_usd, 'slippage_usd': t.slippage_usd, 'entry_bar': t.entry_bar, 'exit_bar': t.exit_bar, 'entry_time_ms': t.entry_time_ms, 'exit_time_ms': t.exit_time_ms} for t in oos_bt.trades]

            candidate_info = {
                "candidate_id": strat_id,
                "name": strat_id,
                "route": "ULTRA",
                "symbol": symbol,
                "timeframe": timeframe,
                "profit_factor_oos": oos_bt.profit_factor,
                "max_drawdown_pct": oos_bt.max_drawdown_pct,
                "dataset_id": Path(data_file).name,
                "dataset_filepath": str(data_file),
                "dataset_sha256": "diag_hash",
                "trials_tested": 10,
                "parameters": {"ema_fast": ema_f, "ema_slow": ema_s, "rsi_period": rsi_p, "sl_atr_mult": sl_atr, "tp_atr_mult": tp_atr, "pyramiding_tiers": py_tiers, "archetype": arch},
            }

            eval_res = orchestrator.run_all_gates(
                candidate_info=candidate_info,
                candles=candles_blind_oos,
                is_trades=is_pnls,
                oos_trades=oos_pnls,
                pre_oos_trades=pre_oos_pnls,
                trades_raw=raw_trades_oos,
                strategy_snapshot=snapshot,
            )

            passed_count = eval_res.get("gates_passed_count", 0)
            print(f"    Passed Gates: {passed_count}/11")
            for g in eval_res.get("gates", []):
                if not g.get("passed"):
                    print(f"      ❌ Gate {g.get('gate_id')} ({g.get('name')}): score={g.get('score')}, verdict={g.get('verdict')}")
