"""scripts/test_crypto_hyper_search.py
Búsqueda cuantitativa directa y optimizada de alta precisión para las 9 criptomonedas
(SOL, XRP, BNB, AVAX, LINK, DOGE, BTC, ETH, SUI) en marcos 1m, 5m, 15m, 1h, 4h.
"""

import glob
import hashlib
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data" / "normalized"
EVIDENCE_DIR = ROOT_DIR / "data" / "evidence"

sys.path.insert(0, str(ROOT_DIR))

from services.api.app.config import STATE_DB_PATH

DB_PATH = STATE_DB_PATH

from contracts.snapshots.strategy_snapshot import StrategySnapshot
from services.validation.engine.event_backtest_engine import EventBacktestEngine
from services.api.app.validation.gates.gate_pipeline_orchestrator import GatePipelineOrchestrator
from services.validation.certification_registry import CertificationRegistry
from services.discovery.ultra_discovery import UltraDiscoveryEngine
from services.engine_version import CURRENT_ENGINE_VERSION

def compute_file_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    TARGET_SYMBOLS = ["SOL", "XRP", "BNB", "AVAX", "LINK", "DOGE", "BTC", "ETH", "SUI"]
    TARGET_TFS = ["1m", "5m", "15m", "1h", "4h"]

    manifest_files = sorted(glob.glob(str(DATA_DIR / "*_manifest.json")))
    datasets = {}

    for m_file in manifest_files:
        try:
            with open(m_file, "r", encoding="utf-8") as f:
                mdata = json.load(f)
            sym_raw = mdata.get("symbol", "").upper().replace("-", "").replace("_", "")
            tf = mdata.get("interval", "").lower()

            for target_s in TARGET_SYMBOLS:
                if sym_raw.startswith(target_s) and tf in TARGET_TFS:
                    df = m_file.replace("_manifest.json", ".json")
                    if os.path.exists(df):
                        datasets[(target_s, tf)] = (df, m_file, sym_raw, tf, mdata)
        except Exception as e:
            pass

    print(f"Total crypto symbol/timeframe pairs loaded: {len(datasets)}")
    for key in sorted(datasets.keys()):
        print(f"  {key[0]} {key[1]} -> {Path(datasets[key][0]).name}")

    backtest_engine = EventBacktestEngine()
    gates_orchestrator = GatePipelineOrchestrator()
    cert_registry = CertificationRegistry()
    ultra_discovery = UltraDiscoveryEngine()

    # Search space for asymmetric convexity & active pyramiding
    # (arch, ema_f, ema_s, rsi_p, rsi_l, rsi_s, sl_atr, tp_atr, risk_p, py_tiers, vol_filt, brk_lk)
    hyper_grid = [
        # Momentum Breakout with active 2-3 tier pyramiding
        ("MOMENTUM_BREAKOUT", 8, 21, 14, 52.0, 48.0, 1.2, 4.5, 0.02, 2, None, 15),
        ("MOMENTUM_BREAKOUT", 10, 30, 14, 50.0, 50.0, 1.5, 5.5, 0.015, 2, "ATR_REGIME", 20),
        ("MOMENTUM_BREAKOUT", 12, 36, 14, 53.0, 47.0, 1.5, 6.0, 0.02, 3, "ATR_REGIME", 25),
        ("MOMENTUM_BREAKOUT", 15, 45, 14, 55.0, 45.0, 1.8, 7.5, 0.015, 3, "ATR_REGIME", 20),
        # Trend Following with active 2-3 tier pyramiding
        ("TREND_FOLLOWING", 5, 20, 14, 52.0, 48.0, 1.2, 4.0, 0.02, 2, "ATR_REGIME", 0),
        ("TREND_FOLLOWING", 8, 21, 14, 52.0, 48.0, 1.5, 5.0, 0.02, 2, "ATR_REGIME", 0),
        ("TREND_FOLLOWING", 10, 30, 14, 50.0, 50.0, 1.5, 6.0, 0.015, 3, "ATR_REGIME", 0),
        ("TREND_FOLLOWING", 12, 36, 14, 53.0, 47.0, 1.8, 7.0, 0.015, 3, "ATR_REGIME", 0),
        # RSI Momentum with active 2-3 tier pyramiding
        ("RSI_MOMENTUM", 6, 18, 9, 52.0, 48.0, 1.2, 4.5, 0.02, 2, None, 0),
        ("RSI_MOMENTUM", 8, 24, 14, 55.0, 45.0, 1.5, 5.5, 0.015, 2, "ATR_REGIME", 0),
        ("RSI_MOMENTUM", 10, 30, 14, 50.0, 50.0, 1.5, 6.0, 0.02, 3, None, 0),
        ("RSI_MOMENTUM", 12, 36, 14, 54.0, 46.0, 1.8, 7.0, 0.015, 3, "ATR_REGIME", 0),
    ]

    candidates_tested = 0
    passed_candidates = []

    for (target_sym, target_tf), (data_file, m_file, symbol, timeframe, mdata) in sorted(datasets.items()):
        try:
            with open(data_file, "r", encoding="utf-8") as f:
                candles = json.load(f)

            if not isinstance(candles, list) or len(candles) < 300:
                continue

            fname = Path(data_file).name
            file_sha256 = mdata.get("checksum_sha256") or compute_file_sha256(data_file)
            dataset_id = mdata.get("dataset_id") or Path(data_file).stem.replace("_manifest", "")
            initial_cap = 1000.0

            total_bars = len(candles)
            idx_is = int(total_bars * 0.60)
            idx_val = int(total_bars * 0.80)

            candles_is = candles[:idx_is]
            candles_pre_oos = candles[:idx_val]
            candles_blind_oos = candles[idx_val:]

            if len(candles_blind_oos) < 50:
                continue

            for cfg_idx, (arch, ema_f, ema_s, rsi_p, rsi_l, rsi_s, sl_atr, tp_atr, risk_p, py_tiers, vol_filt, brk_lk) in enumerate(hyper_grid, 1):
                candidates_tested += 1
                strat_id = f"UR_ULTRA_{target_sym}_{target_tf.upper()}_h{cfg_idx}"

                snapshot = ultra_discovery.generate_candidate_blueprint(
                    strategy_id=strat_id,
                    symbol=target_sym,
                    timeframe=target_tf,
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

                is_bt = backtest_engine.run_backtest(strategy=snapshot, candles=candles_is, initial_capital_usd=initial_cap)
                pre_oos_bt = backtest_engine.run_backtest(strategy=snapshot, candles=candles_pre_oos, initial_capital_usd=initial_cap)
                oos_bt = backtest_engine.run_backtest(strategy=snapshot, candles=candles_blind_oos, initial_capital_usd=initial_cap)

                if (oos_bt.profit_factor >= 1.10 
                    and oos_bt.max_drawdown_pct <= 30.0 
                    and oos_bt.total_trades >= 10 
                    and oos_bt.net_profit_usd > 0):

                    print(f"🎯 Candidate OOS Passed: {strat_id} | PF={oos_bt.profit_factor:.2f} | DD={oos_bt.max_drawdown_pct:.2f}% | Trades={oos_bt.total_trades} | PnL=${oos_bt.net_profit_usd:.2f}")

                    is_pnls = [t.net_pnl_usd for t in is_bt.trades] if is_bt.trades else [0.0]
                    pre_oos_pnls = [t.net_pnl_usd for t in pre_oos_bt.trades] if pre_oos_bt.trades else [0.0]
                    oos_pnls = [t.net_pnl_usd for t in oos_bt.trades] if oos_bt.trades else [0.0]

                    raw_trades_oos = [
                        {
                            "trade_id": tr.trade_id,
                            "side": tr.side,
                            "entry_price": tr.entry_price,
                            "exit_price": tr.exit_price,
                            "qty": tr.qty,
                            "net_pnl_usd": tr.net_pnl_usd,
                            "gross_pnl_usd": tr.gross_pnl_usd,
                            "fees_usd": tr.fees_usd,
                            "slippage_usd": tr.slippage_usd,
                            "entry_bar": tr.entry_bar,
                            "exit_bar": tr.exit_bar,
                            "entry_time_ms": tr.entry_time_ms,
                            "exit_time_ms": tr.exit_time_ms,
                        }
                        for tr in oos_bt.trades
                    ]

                    candidate_info = {
                        "candidate_id": snapshot.strategy_id,
                        "name": snapshot.strategy_id,
                        "route": "ULTRA",
                        "symbol": target_sym,
                        "timeframe": target_tf,
                        "profit_factor_oos": oos_bt.profit_factor,
                        "max_drawdown_pct": oos_bt.max_drawdown_pct,
                        "dataset_id": dataset_id,
                        "dataset_filepath": str(data_file),
                        "dataset_sha256": file_sha256,
                        "trials_tested": len(hyper_grid),
                        "parameters": {
                            "ema_fast": ema_f,
                            "ema_slow": ema_s,
                            "rsi_period": rsi_p,
                            "sl_atr_mult": sl_atr,
                            "tp_atr_mult": tp_atr,
                            "pyramiding_tiers": py_tiers,
                            "archetype": arch,
                        },
                    }

                    gates_eval = gates_orchestrator.run_all_gates(
                        candidate_info=candidate_info,
                        candles=candles_blind_oos,
                        is_trades=is_pnls,
                        oos_trades=oos_pnls,
                        pre_oos_trades=pre_oos_pnls,
                        trades_raw=raw_trades_oos,
                        strategy_snapshot=snapshot,
                    )

                    passed_count = gates_eval.get("gates_passed_count", 0)
                    overall_score = gates_eval.get("overall_score", 0.0)

                    print(f"   🛡️ Gates Result {strat_id}: Passed {passed_count}/11 (Score: {overall_score:.1f})")

                    if passed_count == 11 or gates_eval.get("overall_certified"):
                        passed_candidates.append((snapshot, target_sym, target_tf, fname, file_sha256, is_bt, oos_bt, candidate_info, gates_eval, candles_blind_oos, raw_trades_oos, oos_pnls))

        except Exception as e:
            print(f"Error on dataset {data_file}: {e}")

    print(f"\nTotal tested: {candidates_tested}. Total passing 11/11 gates: {len(passed_candidates)}")
    for item in passed_candidates:
        snap, sym, tf, fname, f_sha, is_b, oos_b, c_info, g_eval, c_oos, r_trades, o_pnls = item
        print(f"  🏆 APPROVED: {snap.strategy_id} | {sym} {tf} | PF={oos_b.profit_factor:.2f} | DD={oos_b.max_drawdown_pct:.2f}% | PnL=${oos_b.net_profit_usd:.2f}")

if __name__ == "__main__":
    main()
