import glob
import hashlib
import json
import logging
import math
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", stream=sys.stdout)
logger = logging.getLogger("FundingMinerTest")

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data" / "normalized"
DB_PATH = Path(os.environ.get("ULTRARENTABLE_DB_PATH", os.path.expanduser("~/.local/state/ultrarentable/ultrarentable.sqlite3")))

sys.path.insert(0, str(ROOT_DIR))

from contracts.snapshots.strategy_snapshot import StrategySnapshot, StrategyRoute, PyramidingPolicy, MarginPolicy
from contracts.canonical_strategy import (
    RuleTree,
    ExitModel,
    StopLossType,
    TakeProfitType,
    SizingAndRisk,
    SizingType,
    IndicatorSpec,
    ConditionNode,
    ComparisonOp,
    LogicalOp,
    SessionWindow,
)
from services.validation.engine.event_backtest_engine import EventBacktestEngine
from services.api.app.validation.gates.gate_pipeline_orchestrator import GatePipelineOrchestrator
from services.validation.certification_registry import CertificationRegistry
from services.engine_version import CURRENT_ENGINE_VERSION

def compute_file_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def test_dataset(symbol="NQ", timeframe="1h"):
    files = glob.glob(str(DATA_DIR / f"*_{symbol.lower()}_{timeframe.lower()}_*.json"))
    files = [f for f in files if not f.endswith("_manifest.json")]
    if not files:
        print(f"No dataset file found for {symbol} {timeframe}", flush=True)
        return
    data_file = files[0]
    fname = Path(data_file).name
    file_sha256 = compute_file_sha256(data_file)
    with open(data_file, "r", encoding="utf-8") as f:
        candles = json.load(f)

    print(f"Loaded {symbol} {timeframe}: {len(candles)} candles", flush=True)

    total_bars = len(candles)
    idx_is = int(total_bars * 0.60)
    idx_val = int(total_bars * 0.80)
    candles_is = candles[:idx_is]
    candles_val = candles[idx_is:idx_val]
    candles_blind_oos = candles[idx_val:]

    backtest_engine = EventBacktestEngine()
    gates_orchestrator = GatePipelineOrchestrator()
    cert_registry = CertificationRegistry()

    initial_cap = 50000.0

    configs = []
    for ema_f in [5, 8, 10, 12]:
        for ema_s in [15, 20, 30, 40]:
            if ema_f >= ema_s: continue
            for rsi_p in [9, 14]:
                for sl_m in [1.0, 1.2, 1.5, 2.0]:
                    for tp_m in [2.5, 3.0, 4.0, 5.0]:
                        for risk_p in [0.05, 0.10, 0.15]:
                            configs.append(("INSTITUTIONAL_SESSION_MOMENTUM", ema_f, ema_s, rsi_p, 50.0, 50.0, sl_m, tp_m, risk_p))

    print(f"Generated {len(configs)} trial configurations for {symbol} {timeframe}", flush=True)

    candidates_evaluated = 0
    passed_is_val = 0

    for arch, ema_f, ema_s, rsi_p, rsi_l, rsi_s, sl_m, tp_m, risk_p in configs:
        candidates_evaluated += 1
        strat_id = f"UR_FONDEO_{symbol.upper()}_{timeframe.upper()}"

        ema_fast_spec = IndicatorSpec(name="EMA", params={"period": ema_f}, source_field="close", shift=0)
        ema_slow_spec = IndicatorSpec(name="EMA", params={"period": ema_s}, source_field="close", shift=0)
        rsi_spec = IndicatorSpec(name="RSI", params={"period": rsi_p}, source_field="close", shift=0)

        long_conds = [
            ConditionNode(left=ema_fast_spec, op=ComparisonOp.CROSS_ABOVE, right=ema_slow_spec),
            ConditionNode(left=rsi_spec, op=ComparisonOp.GT, right=float(rsi_l)),
        ]
        short_conds = [
            ConditionNode(left=ema_fast_spec, op=ComparisonOp.CROSS_BELOW, right=ema_slow_spec),
            ConditionNode(left=rsi_spec, op=ComparisonOp.LT, right=float(rsi_s)),
        ]

        entry_rules = RuleTree(
            logic=LogicalOp.AND,
            direction="BOTH",
            long_conditions=long_conds,
            short_conditions=short_conds,
        )

        exit_rules = ExitModel(
            sl_type=StopLossType.ATR_MULTIPLE,
            sl_value=sl_m,
            tp_type=TakeProfitType.ATR_MULTIPLE,
            tp_value=tp_m,
            time_stop_bars=36,
        )

        sizing = SizingAndRisk(
            sizing_type=SizingType.RISK_PCT_EQUITY,
            risk_value=risk_p,
            max_open_positions=1,
            max_daily_loss_usd=1000.0,
        )

        session_window = SessionWindow(
            start_time_utc="13:30",
            end_time_utc="20:00",
            close_at_eod=True,
            allowed_days=[0, 1, 2, 3, 4],
        )

        snapshot = StrategySnapshot.create_and_hash(
            strategy_id=strat_id,
            route=StrategyRoute.FONDEO,
            symbol=symbol,
            timeframe=timeframe,
            archetype=arch,
            entry_rules=entry_rules,
            exit_rules=exit_rules,
            sizing_and_risk=sizing,
            dataset_id_reference=fname,
            dataset_sha256_reference=file_sha256,
            pyramiding_policy=PyramidingPolicy(enabled=False),
            margin_policy=MarginPolicy(margin_mode="ISOLATED", max_leverage_ceiling=1.0),
            session_window=session_window,
        )

        is_bt = backtest_engine.run_backtest(snapshot, candles_is, initial_capital_usd=initial_cap)
        if is_bt.total_trades < 30 or is_bt.profit_factor < 1.15 or is_bt.max_drawdown_pct > 3.5:
            continue

        val_bt = backtest_engine.run_backtest(snapshot, candles_val, initial_capital_usd=initial_cap)
        if val_bt.total_trades < 10 or val_bt.profit_factor < 1.10 or val_bt.max_drawdown_pct > 3.5:
            continue

        passed_is_val += 1
        candles_pre_oos = candles_is + candles_val
        pre_oos_bt = backtest_engine.run_backtest(snapshot, candles_pre_oos, initial_capital_usd=initial_cap)
        oos_bt = backtest_engine.run_backtest(snapshot, candles_blind_oos, initial_capital_usd=initial_cap)

        print(f"Candidate IS/Val PASS! OOS: PF={oos_bt.profit_factor:.2f}, DD={oos_bt.max_drawdown_pct:.2f}%, Trades={oos_bt.total_trades} (IS={is_bt.total_trades}), NetPnL=${oos_bt.net_profit_usd:.2f}", flush=True)

        if oos_bt.profit_factor >= 1.15 and oos_bt.max_drawdown_pct <= 4.0 and oos_bt.total_trades >= 20 and oos_bt.net_profit_usd > 0:
            is_trades = [t.return_pct / 100.0 for t in is_bt.trades]
            pre_oos_trades = [t.return_pct / 100.0 for t in pre_oos_bt.trades]
            oos_trades = [t.return_pct / 100.0 for t in oos_bt.trades]
            trades_raw = [
                {
                    "entry_price": t.entry_price,
                    "exit_price": t.exit_price,
                    "qty": t.qty,
                    "side": t.side,
                    "net_pnl_usd": t.net_pnl_usd,
                    "gross_pnl_usd": t.gross_pnl_usd,
                    "fees_usd": t.fees_usd,
                    "slippage_usd": t.slippage_usd,
                    "return_pct": t.return_pct,
                    "r_multiple": t.r_multiple,
                    "equity_before_usd": t.equity_before_usd,
                    "equity_after_usd": t.equity_after_usd,
                    "entry_bar_idx": t.entry_bar,
                    "exit_bar_idx": t.exit_bar,
                    "entry_time_ms": t.entry_time_ms,
                    "exit_time_ms": t.exit_time_ms,
                }
                for t in oos_bt.trades
            ]

            candidate_info = {
                "candidate_id": snapshot.strategy_id,
                "name": snapshot.strategy_id,
                "route": "FONDEO",
                "symbol": symbol,
                "timeframe": timeframe,
                "dataset_id": fname,
                "dataset_sha256": file_sha256,
                "dataset_filepath": data_file,
                "roi_pct": round(((oos_bt.final_equity_usd - initial_cap) / initial_cap) * 100.0, 2),
                "profit_factor_oos": oos_bt.profit_factor,
                "max_drawdown_pct": oos_bt.max_drawdown_pct,
                "net_profit_oos_usd": oos_bt.net_profit_usd,
                "net_profit_usd": oos_bt.net_profit_usd,
                "trades_count": len(oos_trades),
                "trials_tested": len(configs),
                "parameters": {"archetype": arch, "ema_fast": ema_f, "ema_slow": ema_s, "rsi_period": rsi_p, "sl_atr_mult": sl_m, "tp_atr_mult": tp_m, "risk_pct": risk_p},
                "rules": [f"archetype={arch}", f"entry={snapshot.entry_rules.model_dump_json()}"],
                "indicators_count": 3,
            }

            gates_eval = gates_orchestrator.run_all_gates(
                candidate_info=candidate_info,
                candles=candles_blind_oos,
                is_trades=is_trades,
                oos_trades=oos_trades,
                pre_oos_trades=pre_oos_trades,
                trades_raw=trades_raw,
                strategy_snapshot=snapshot,
            )

            verdict = cert_registry.certify_candidate(
                strategy=snapshot,
                backtest_result=oos_bt,
                gates_passed_count=gates_eval.get("gates_passed_count", 0),
                scorecard_average=gates_eval.get("overall_score", 0.0),
            )

            print(f"   🛡️ Veredicto: {verdict.certified_status} (Gates: {verdict.gates_passed_count}/11, Score: {verdict.scorecard_average:.1f})", flush=True)

            if verdict.is_certified:
                print(f"🎉 SUCCESS! Strategy Certified 11/11: {snapshot.strategy_id}", flush=True)
                break

    print(f"Test completed for {symbol} {timeframe}. Evaluated: {candidates_evaluated}, Passed IS/Val: {passed_is_val}", flush=True)

if __name__ == "__main__":
    test_dataset("NQ", "1h")
