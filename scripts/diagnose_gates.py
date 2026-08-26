"""scripts/diagnose_gates.py
Diagnóstico de 11 Gates sobre dataset 5m / 15m con alto número de trades.
"""
import glob
import json
import logging
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
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

DATA_DIR = ROOT_DIR / "data" / "normalized"
man_files = glob.glob(str(DATA_DIR / "*nq_5m*manifest.json")) or glob.glob(str(DATA_DIR / "*es_5m*manifest.json"))
if not man_files:
    print("No manifest found")
    sys.exit(1)

man_path = man_files[0]
with open(man_path, "r", encoding="utf-8") as f:
    manifest = json.load(f)

data_file = man_path.replace("_manifest.json", ".json")
with open(data_file, "r", encoding="utf-8") as f:
    candles = json.load(f)

symbol = manifest.get("symbol", "NQ")
timeframe = "5m"
dataset_id = manifest.get("dataset_id", "ds_nq_5m")
sha256 = manifest.get("checksum_sha256", "hash_nq_5m")

strat_id = f"UR_FONDEO_{symbol}_5m_v1"
ema_f, ema_s, rsi_p, sl_t, tp_t, risk_pct = 9, 21, 14, 15.0, 45.0, 0.25

entry_rules = RuleTree(
    logic=LogicalOp.AND,
    direction="BOTH",
    long_conditions=[
        ConditionNode(
            left=IndicatorSpec(name="EMA", params={"period": ema_f}, source_field="close", shift=0),
            op=ComparisonOp.CROSS_ABOVE,
            right=IndicatorSpec(name="EMA", params={"period": ema_s}, source_field="close", shift=0),
        ),
        ConditionNode(
            left=IndicatorSpec(name="RSI", params={"period": rsi_p}, source_field="close", shift=0),
            op=ComparisonOp.GT,
            right=50.0,
        ),
    ],
    short_conditions=[
        ConditionNode(
            left=IndicatorSpec(name="EMA", params={"period": ema_f}, source_field="close", shift=0),
            op=ComparisonOp.CROSS_BELOW,
            right=IndicatorSpec(name="EMA", params={"period": ema_s}, source_field="close", shift=0),
        ),
        ConditionNode(
            left=IndicatorSpec(name="RSI", params={"period": rsi_p}, source_field="close", shift=0),
            op=ComparisonOp.LT,
            right=50.0,
        ),
    ],
)

exit_rules = ExitModel(
    sl_type=StopLossType.FIXED_POINTS,
    sl_value=sl_t,
    tp_type=TakeProfitType.FIXED_POINTS,
    tp_value=tp_t,
    time_stop_bars=36,
)

sizing = SizingAndRisk(
    sizing_type=SizingType.RISK_PCT_EQUITY,
    risk_value=risk_pct,
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
    entry_rules=entry_rules,
    exit_rules=exit_rules,
    sizing_and_risk=sizing,
    dataset_id_reference=dataset_id,
    dataset_sha256_reference=sha256,
    pyramiding_policy=PyramidingPolicy(enabled=False),
    margin_policy=MarginPolicy(margin_mode="ISOLATED", max_leverage_ceiling=1.0),
    session_window=session_window,
)

backtest_engine = EventBacktestEngine()
bt_res = backtest_engine.run_backtest(
    strategy=snapshot,
    candles=candles,
    initial_capital_usd=50000.0,
)

print(f"Backtest Result: Trades={bt_res.total_trades}, PF={bt_res.profit_factor:.2f}, MaxDD={bt_res.max_drawdown_pct:.2f}%, NetPnL=${bt_res.net_profit_usd:.2f}")

trade_pnls = [t.net_pnl_usd for t in bt_res.trades]
split_idx = int(len(trade_pnls) * 0.7)
is_pnls = trade_pnls[:split_idx]
oos_pnls = trade_pnls[split_idx:] if trade_pnls[split_idx:] else trade_pnls

raw_trade_dicts = []
for tr in bt_res.trades:
    raw_trade_dicts.append({
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
    })

candidate_info = {
    "candidate_id": strat_id,
    "route": "FONDEO",
    "symbol": symbol,
    "timeframe": timeframe,
    "profit_factor_oos": bt_res.profit_factor,
    "max_drawdown_pct": bt_res.max_drawdown_pct,
    "dataset_id": dataset_id,
    "dataset_sha256": sha256,
    "trials_tested": 8,
    "parameters": {"ema_fast": ema_f, "ema_slow": ema_s, "rsi_period": rsi_p, "sl_ticks": sl_t, "tp_ticks": tp_t},
}

gates_orchestrator = GatePipelineOrchestrator()
gate_eval = gates_orchestrator.run_all_gates(
    candidate_info=candidate_info,
    candles=candles,
    is_trades=is_pnls,
    oos_trades=oos_pnls,
    trades_raw=raw_trade_dicts,
    strategy_snapshot=snapshot,
)

print("\n--- DESGLOSE DE LOS 11 GATES ---")
for g in gate_eval.get("gates", []):
    status_icon = "✅" if g.get("passed") else "❌"
    print(f"{status_icon} Gate {g.get('gate_id')} ({g.get('name')}): Score={g.get('score')} | Veredicto: {g.get('verdict')}")
