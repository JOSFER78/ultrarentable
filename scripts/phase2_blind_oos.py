"""Execute Blind OOS exactly once for an immutable Phase-2 frozen champion.

This script is deliberately separate from discovery. It refuses to select, mutate,
or replace a champion and requires a matching physical dataset hash + strategy hash.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from scripts import phase2_research_adapter as research
from services.api.app.config import STATE_DB_PATH
from services.api.app.validation.gates.gate_pipeline_orchestrator import GatePipelineOrchestrator
from services.validation.engine.event_backtest_engine import EventBacktestEngine


def sha256_bytes(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", required=True)
    parser.add_argument("--data-dir", default=None)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    freeze_path = Path(args.freeze)
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    if freeze.get("schema") != "phase2-frozen-champion-v1":
        raise SystemExit("INVALID_FREEZE_SCHEMA")
    if freeze.get("status") != "FROZEN_VALIDATION_CHAMPION":
        raise SystemExit("CHAMPION_NOT_FROZEN")
    if freeze.get("blind_oos", {}).get("status") != "NOT_CONSUMED":
        raise SystemExit("BLIND_OOS_ALREADY_CONSUMED")

    data_dir = Path(args.data_dir or research.DATA_DIR)
    datasets = sorted(data_dir.glob("ds_bingx_*.json"))
    target_hash = str(freeze["dataset_sha256"])
    matches = [p for p in datasets if sha256_bytes(p) == target_hash]
    if len(matches) != 1:
        raise SystemExit(f"DATASET_HASH_MATCH_COUNT:{len(matches)}")
    path = matches[0]

    manifest, candles = research.load_custodied_dataset(path)
    if str(manifest["physicalFileSha256"]) != target_hash:
        raise SystemExit("PHYSICAL_HASH_MISMATCH")
    if str(manifest["datasetId"]) != str(freeze["dataset_id"]):
        raise SystemExit("DATASET_ID_MISMATCH")
    if str(manifest["symbol"]) != str(freeze["symbol"]) or str(manifest["interval"]) != str(freeze["timeframe"]):
        raise SystemExit("DATASET_SCOPE_MISMATCH")

    idx_val = int(freeze["partition"]["blind_oos_start_index"])
    if idx_val <= 0 or idx_val >= len(candles):
        raise SystemExit("INVALID_BLIND_OOS_BOUNDARY")
    blind = candles[idx_val:]
    is_candles = candles[: int(len(candles) * 0.60)]
    pre_oos_candles = candles[:idx_val]
    if not blind:
        raise SystemExit("EMPTY_BLIND_OOS")

    from services.discovery.ultra_discovery import UltraDiscoveryEngine
    from services.discovery.funding_discovery import FundingDiscoveryEngine

    ultra = UltraDiscoveryEngine()
    funding = FundingDiscoveryEngine()
    strategy = research.strategy_from_params(
        str(freeze["route"]), manifest, str(freeze["candidate_id"]),
        dict(freeze["parameters"]), ultra, funding
    )
    strategy_hash = getattr(strategy, "canonical_hash", "")
    if strategy_hash != str(freeze["strategy_snapshot_hash"]):
        raise SystemExit("STRATEGY_HASH_MISMATCH")

    initial_capital = 50_000.0 if str(freeze["route"]) == "FONDEO" else 1_000.0
    engine = EventBacktestEngine()
    is_bt = engine.run_backtest(strategy, is_candles, initial_capital_usd=initial_capital)
    pre_oos_bt = engine.run_backtest(strategy, pre_oos_candles, initial_capital_usd=initial_capital)
    oos_bt = engine.run_backtest(strategy, blind, initial_capital_usd=initial_capital)

    is_trades = [float(t.return_pct) / 100.0 for t in is_bt.trades]
    pre_oos_trades = [float(t.return_pct) / 100.0 for t in pre_oos_bt.trades]
    oos_trades = [float(t.return_pct) / 100.0 for t in oos_bt.trades]
    trades_raw = [{
        "entry_price": t.entry_price, "exit_price": t.exit_price, "qty": t.qty, "side": t.side,
        "net_pnl_usd": t.net_pnl_usd, "return_pct": t.return_pct, "r_multiple": t.r_multiple,
        "equity_before_usd": t.equity_before_usd, "equity_after_usd": t.equity_after_usd,
        "entry_bar_idx": t.entry_bar, "exit_bar_idx": t.exit_bar,
        "entry_time_ms": t.entry_time_ms, "exit_time_ms": t.exit_time_ms,
    } for t in oos_bt.trades]

    candidate_info = {
        "candidate_id": strategy.strategy_id,
        "name": strategy.strategy_id,
        "route": freeze["route"],
        "symbol": freeze["symbol"],
        "timeframe": freeze["timeframe"],
        "dataset_id": freeze["dataset_id"],
        "dataset_sha256": target_hash,
        "dataset_filepath": str(path),
        "strategy_snapshot_hash": strategy_hash,
        "roi_pct": round(((oos_bt.final_equity_usd - initial_capital) / initial_capital) * 100.0, 4),
        "profit_factor_oos": float(oos_bt.profit_factor),
        "max_drawdown_pct": float(oos_bt.max_drawdown_pct),
        "net_profit_oos_usd": float(oos_bt.net_profit_usd),
        "net_profit_usd": float(oos_bt.net_profit_usd),
        "trades_count": len(oos_bt.trades),
        "trials_tested": int(freeze["trial_budget"]),
        "parameters": freeze["parameters"],
        "rules": ["canonical_strategy_snapshot"],
        "indicators_count": 3,
        "run_id": str(freeze["run_id"]),
        "blind_oos_start_index": idx_val,
    }
    gates = GatePipelineOrchestrator(
        evidence_base_dir=str(research.EVIDENCE_DIR)
    ).run_all_gates(
        candidate_info=candidate_info,
        candles=candles,
        is_trades=is_trades,
        oos_trades=oos_trades,
        pre_oos_trades=pre_oos_trades,
        trades_raw=trades_raw,
        strategy_snapshot=strategy,
    )

    result = {
        "schema": "phase2-blind-oos-result-v1",
        "freeze": str(freeze_path),
        "run_id": freeze["run_id"],
        "candidate_id": strategy.strategy_id,
        "dataset_id": freeze["dataset_id"],
        "dataset_sha256": target_hash,
        "strategy_snapshot_hash": strategy_hash,
        "blind_oos_start_index": idx_val,
        "blind_oos": {
            "trades": len(oos_bt.trades),
            "pf": float(oos_bt.profit_factor),
            "dd_pct": float(oos_bt.max_drawdown_pct),
            "net_profit_usd": float(oos_bt.net_profit_usd),
            "roi_pct": candidate_info["roi_pct"],
        },
        "gates": gates,
        "status": "APPROVED" if gates.get("overall_certified") else gates.get("status_lifecycle", "REJECTED"),
    }
    out = Path(args.output) if args.output else research.EVIDENCE_DIR / f"{freeze['run_id']}_blind_oos.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"status": result["status"], "candidate_id": strategy.strategy_id}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
