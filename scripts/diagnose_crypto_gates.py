"""scripts/diagnose_crypto_gates.py
Diagnóstico punto por punto de los 11 Gates en estrategias Cripto.
Muestra qué gates aprueban y cuáles fallan en cada configuración.
"""

import glob
import json
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data" / "normalized"

sys.path.insert(0, str(ROOT_DIR))

from contracts.snapshots.strategy_snapshot import StrategySnapshot
from services.validation.engine.event_backtest_engine import EventBacktestEngine
from services.api.app.validation.gates.gate_pipeline_orchestrator import GatePipelineOrchestrator
from services.discovery.ultra_discovery import UltraDiscoveryEngine

def diagnose():
    manifest_files = sorted(glob.glob(str(DATA_DIR / "*_manifest.json")))
    target_syms = ["SOLUSDT", "BTCUSDT", "ETHUSDT", "SUIUSDT", "XRPUSDT", "BNBUSDT", "AVAXUSDT", "LINKUSDT", "DOGEUSDT"]
    target_tfs = ["15m", "1h", "4h"]

    backtest_engine = EventBacktestEngine()
    gates_orchestrator = GatePipelineOrchestrator()
    ultra_discovery = UltraDiscoveryEngine()

    configs = [
        # (arch, ema_f, ema_s, rsi_p, rsi_l, rsi_s, sl_atr, tp_atr, risk_p, py_tiers, vol_filt, brk_lk)
        ("MOMENTUM_BREAKOUT", 8, 21, 14, 52.0, 48.0, 1.5, 5.0, 0.02, 2, None, 15),
        ("MOMENTUM_BREAKOUT", 10, 30, 14, 50.0, 50.0, 1.5, 6.0, 0.015, 2, "ATR_REGIME", 20),
        ("TREND_FOLLOWING", 8, 21, 14, 52.0, 48.0, 1.5, 5.0, 0.02, 2, "ATR_REGIME", 0),
        ("TREND_FOLLOWING", 10, 30, 14, 50.0, 50.0, 1.5, 6.0, 0.015, 3, "ATR_REGIME", 0),
        ("RSI_MOMENTUM", 8, 24, 14, 55.0, 45.0, 1.5, 5.5, 0.015, 2, "ATR_REGIME", 0),
    ]

    for m_file in manifest_files:
        try:
            with open(m_file) as f:
                mdata = json.load(f)
            sym = mdata.get("symbol", "").upper().replace("-", "").replace("_", "")
            tf = mdata.get("interval", "").lower()

            if sym in target_syms and tf in target_tfs:
                df = m_file.replace("_manifest.json", ".json")
                if not os.path.exists(df):
                    continue

                with open(df) as f:
                    candles = json.load(f)
                if len(candles) < 300:
                    continue

                print(f"\n==================================================")
                print(f"📊 Dataset: {sym} ({tf}) - {len(candles)} barras")
                print(f"==================================================")

                total_bars = len(candles)
                idx_is = int(total_bars * 0.60)
                idx_val = int(total_bars * 0.80)

                candles_is = candles[:idx_is]
                candles_pre_oos = candles[:idx_val]
                candles_blind_oos = candles[idx_val:]

                file_sha256 = "dummy_hash"
                dataset_id = Path(df).stem

                for cfg_idx, (arch, ema_f, ema_s, rsi_p, rsi_l, rsi_s, sl_atr, tp_atr, risk_p, py_tiers, vol_filt, brk_lk) in enumerate(configs, 1):
                    strat_id = f"UR_ULTRA_{sym}_{tf.upper()}_d{cfg_idx}"

                    snapshot = ultra_discovery.generate_candidate_blueprint(
                        strategy_id=strat_id,
                        symbol=sym,
                        timeframe=tf,
                        dataset_id=dataset_id,
                        dataset_sha256=file_sha256,
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

                    is_bt = backtest_engine.run_backtest(strategy=snapshot, candles=candles_is, initial_capital_usd=1000.0)
                    pre_oos_bt = backtest_engine.run_backtest(strategy=snapshot, candles=candles_pre_oos, initial_capital_usd=1000.0)
                    oos_bt = backtest_engine.run_backtest(strategy=snapshot, candles=candles_blind_oos, initial_capital_usd=1000.0)

                    print(f"\n  Config {cfg_idx} ({arch}): PF={oos_bt.profit_factor:.2f}, DD={oos_bt.max_drawdown_pct:.2f}%, Trades={oos_bt.total_trades}, PnL=${oos_bt.net_profit_usd:.2f}")

                    if oos_bt.total_trades >= 5:
                        is_pnls = [t.net_pnl_usd for t in is_bt.trades] if is_bt.trades else [0.0]
                        pre_oos_pnls = [t.net_pnl_usd for t in pre_oos_bt.trades] if pre_oos_bt.trades else [0.0]
                        oos_pnls = [t.net_pnl_usd for t in oos_bt.trades] if oos_bt.trades else [0.0]

                        raw_trades_oos = [
                            {
                                "trade_id": tr.trade_id, "side": tr.side, "entry_price": tr.entry_price, "exit_price": tr.exit_price,
                                "qty": tr.qty, "net_pnl_usd": tr.net_pnl_usd, "gross_pnl_usd": tr.gross_pnl_usd,
                                "fees_usd": tr.fees_usd, "slippage_usd": tr.slippage_usd, "entry_bar": tr.entry_bar,
                                "exit_bar": tr.exit_bar, "entry_time_ms": tr.entry_time_ms, "exit_time_ms": tr.exit_time_ms,
                            }
                            for tr in oos_bt.trades
                        ]

                        candidate_info = {
                            "candidate_id": snapshot.strategy_id, "name": snapshot.strategy_id, "route": "ULTRA",
                            "symbol": sym, "timeframe": tf, "profit_factor_oos": oos_bt.profit_factor,
                            "max_drawdown_pct": oos_bt.max_drawdown_pct, "dataset_id": dataset_id,
                            "dataset_filepath": str(df), "dataset_sha256": file_sha256, "trials_tested": 20,
                            "parameters": {"ema_fast": ema_f, "ema_slow": ema_s, "rsi_period": rsi_p, "sl_atr_mult": sl_atr, "tp_atr_mult": tp_atr, "pyramiding_tiers": py_tiers, "archetype": arch},
                        }

                        gates_eval = gates_orchestrator.run_all_gates(
                            candidate_info=candidate_info, candles=candles_blind_oos, is_trades=is_pnls,
                            oos_trades=oos_pnls, pre_oos_trades=pre_oos_pnls, trades_raw=raw_trades_oos, strategy_snapshot=snapshot,
                        )

                        passed_cnt = gates_eval.get("gates_passed_count", 0)
                        print(f"   -> Gates Passed: {passed_cnt}/11")
                        for g in gates_eval.get("gates", []):
                            p_mark = "✅" if g.get("passed") else "❌"
                            print(f"      {p_mark} Gate {g.get('gate_id')}: {g.get('name')} -> {g.get('verdict')}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    diagnose()
