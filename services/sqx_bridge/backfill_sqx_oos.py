"""Backfill: correct DD units (USD->%) and populate OOS metrics for existing
SQX strategy backtests in the operational DB, using REAL stats re-read from SQX.

Run from project root:  python3 services/sqx_bridge/backfill_sqx_oos.py
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path("/home/ubuntu/workspace/pro/trading/01 Ultrarentable")
sys.path.insert(0, str(PROJECT_ROOT))

from services.sqx_bridge.sqx_client import SQXMCPClient
from services.sqx_bridge.ingest_sqx_results import COLUMN_MAP
from services.api.app.db.database import SessionLocal, StrategyModel, BacktestModel

PROJECT = "Ultra_Auto_Pilot"
DATABANK = "Results"
INITIAL_CAPITAL = 10000.0


def extract_stats(stats: dict) -> dict:
    cols = stats.get("columns", [])
    vals = stats.get("values", [])
    if not cols or not vals:
        return {}
    offset = 2 if len(vals) != len(cols) else 0
    out = {}
    for i, col in enumerate(cols):
        idx = i + offset
        if idx >= len(vals):
            continue
        raw = vals[idx]
        if raw is None:
            continue
        try:
            out[COLUMN_MAP.get(col)] = float(raw)
        except (TypeError, ValueError):
            continue
    return out


def main() -> None:
    client = SQXMCPClient()
    db = SessionLocal()

    backtests = (
        db.query(BacktestModel)
        .join(StrategyModel, StrategyModel.strategy_id == BacktestModel.strategy_id)
        .filter(StrategyModel.family == "sqx_generated")
        .all()
    )
    print(f"Backtests SQX existentes: {len(backtests)}")

    fixed_dd = fixed_oos = no_stats = 0
    for bt in backtests:
        strat = db.query(StrategyModel).filter(StrategyModel.strategy_id == bt.strategy_id).first()
        if not strat:
            continue
        try:
            stats_raw = client.get_strategy_stats(PROJECT, DATABANK, strat.name)
        except Exception as exc:  # noqa: BLE001
            print(f"  !! {strat.name}: sin stats ({exc})")
            no_stats += 1
            continue
        m = extract_stats(stats_raw)
        if not m:
            no_stats += 1
            continue

        net_profit = m.get("NetProfitUsd", 0.0) or 0.0
        final_equity = INITIAL_CAPITAL + net_profit
        dd_usd = m.get("MaxDrawdownPct", 0.0) or 0.0
        dd_pct_is = (dd_usd / final_equity * 100.0) if final_equity and dd_usd else 0.0

        net_profit_os = m.get("NetProfitOosUsd", 0.0) or 0.0
        dd_usd_os = m.get("MaxDrawdownOosPct", 0.0) or 0.0
        final_equity_os = INITIAL_CAPITAL + net_profit_os
        dd_pct_os = (dd_usd_os / final_equity_os * 100.0) if final_equity_os and dd_usd_os else 0.0
        net_return_os_pct = (net_profit_os / INITIAL_CAPITAL * 100.0) if net_profit_os else 0.0

        bt.max_drawdown_pct = dd_pct_is
        bt.pf_os = m.get("ProfitFactorOos")
        bt.net_return_os_pct = net_return_os_pct
        bt.max_drawdown_os_pct = dd_pct_os
        bt.trades_os = int(m.get("TradesOos", 0)) if m.get("TradesOos") else None
        bt.ret_dd_ratio = m.get("RetDD")
        fixed_dd += 1
        if m.get("ProfitFactorOos") is not None:
            fixed_oos += 1

    db.commit()
    db.close()
    print(f"\nRESUMEN: DD corregidos={fixed_dd}, OOS poblados={fixed_oos}, sin stats={no_stats}")


if __name__ == "__main__":
    main()
