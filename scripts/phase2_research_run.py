"""Canonical Phase-2 research runner.

REAL-ONLY, evidence-gated and finite: acquire data in a separate workflow step,
verify physical custody, explore a deterministic trial budget on IS, select on
Validation, freeze, then consume Blind OOS exactly once for final evidence.
"""
from __future__ import annotations

import hashlib
import json
import os
from itertools import product
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from services.api.app.validation.gates.gate_pipeline_orchestrator import GatePipelineOrchestrator
from services.api.app.config import DATA_DIR as BASE_DATA_DIR, STATE_DB_PATH
from services.discovery.funding_discovery import FundingDiscoveryEngine
from services.discovery.strategy_search_registry import SearchTrialRecord, StrategySearchRegistry
from services.discovery.ultra_discovery import UltraDiscoveryEngine
from services.validation.engine.event_backtest_engine import EventBacktestEngine

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.getenv("PHASE2_DATA_DIR", str(BASE_DATA_DIR / "normalized")))
EVIDENCE_DIR = ROOT / "data" / "phase2-evidence"
MAX_TRIALS_ULTRA = int(os.getenv("PHASE2_MAX_TRIALS_ULTRA", "128"))
MAX_TRIALS_FONDEO = int(os.getenv("PHASE2_MAX_TRIALS_FONDEO", "96"))
TOP_VALIDATION = int(os.getenv("PHASE2_TOP_VALIDATION", "20"))
MAX_DATASETS = int(os.getenv("PHASE2_MAX_DATASETS", "3"))


def sha256_bytes(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def load_custodied_dataset(path: Path) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    manifest_path = path.with_name(path.stem + "_manifest.json")
    if not manifest_path.is_file():
        raise RuntimeError(f"MISSING_MANIFEST: {path.name}")
    manifest = read_json(manifest_path)
    if manifest.get("normalizedPath") and manifest["normalizedPath"].replace("\\", "/").split("/")[-1] != path.name:
        raise RuntimeError(f"MANIFEST_PATH_MISMATCH: {path.name}")
    physical = sha256_bytes(path)
    expected = str(manifest.get("physicalFileSha256", ""))
    if expected and physical != expected:
        raise RuntimeError(f"PHYSICAL_HASH_MISMATCH: {path.name}")
    if not manifest.get("closedRecordsOnly", False):
        raise RuntimeError(f"OPEN_CANDLES_NOT_ALLOWED: {path.name}")
    if not manifest.get("completeHistory", False):
        raise RuntimeError(f"INCOMPLETE_HISTORY: {path.name}")
    candles = read_json(path)
    if not isinstance(candles, list) or len(candles) < 200:
        raise RuntimeError(f"INSUFFICIENT_DATASET: {path.name}")
    if int(manifest.get("recordCount", -1)) != len(candles):
        raise RuntimeError(f"RECORD_COUNT_MISMATCH: {path.name}")
    return manifest, candles


def is_fondeo(symbol: str) -> bool:
    normalized = symbol.replace("-", "").upper()
    return normalized in {"NQ", "ES", "YM", "GC", "CL", "RTY", "SI", "EURUSD", "GBPUSD", "AUDUSD", "USDCAD", "USDCHF", "USDJPY"}


def deterministic_space(route: str) -> List[Dict[str, Any]]:
    ema_fast = [8, 12, 20]
    ema_slow = [30, 50, 80]
    rsi_period = [10, 14, 21]
    rsi_long = [52.0, 55.0, 60.0]
    rsi_short = [48.0, 45.0, 40.0]
    archetypes = ["MOMENTUM_BREAKOUT", "TREND_FOLLOWING", "RSI_MOMENTUM", "MEAN_REVERSION"]
    if route == "ULTRA":
        tuples = product(archetypes, ema_fast, ema_slow, [1.5, 2.0, 3.0], [4.0, 6.0, 8.0], range(3), [1, 2, 3])
        return [
            {
                "archetype": a, "ema_fast": f, "ema_slow": s, "sl_atr_mult": sl,
                "tp_atr_mult": tp, "rsi_period": rsi_period[i],
                "rsi_threshold_long": rsi_long[i], "rsi_threshold_short": rsi_short[i],
                "pyramiding_tiers_count": tiers,
            }
            for a, f, s, sl, tp, i, tiers in tuples if f < s
        ]
    tuples = product(ema_fast, ema_slow, rsi_period, rsi_long, rsi_short, [0.15, 0.25, 0.35], [20, 30, 45], [8, 12, 16])
    return [
        {
            "ema_fast": f, "ema_slow": s, "rsi_period": rp, "rsi_threshold_long": rl,
            "rsi_threshold_short": rs, "risk_per_trade_pct": risk,
            "target_profit_ticks": tp, "stop_loss_ticks": sl,
        }
        for f, s, rp, rl, rs, risk, tp, sl in tuples if f < s
    ]


def budget_space(space: List[Dict[str, Any]], limit: int, dataset_hash: str) -> List[Dict[str, Any]]:
    if len(space) <= limit:
        return space
    start = int(dataset_hash[:12], 16) % len(space)
    stride = 97
    selected: List[Dict[str, Any]] = []
    seen = set()
    idx = start
    while len(selected) < limit:
        if idx not in seen:
            selected.append(space[idx])
            seen.add(idx)
        idx = (idx + stride) % len(space)
    return selected


def strategy_from_params(route: str, manifest: Dict[str, Any], strategy_id: str, params: Dict[str, Any],
                        ultra: UltraDiscoveryEngine, funding: FundingDiscoveryEngine):
    symbol = str(manifest["symbol"])
    timeframe = str(manifest["interval"])
    if route == "ULTRA":
        return ultra.generate_candidate_blueprint(
            strategy_id=strategy_id,
            symbol=symbol,
            timeframe=timeframe,
            dataset_id=str(manifest["datasetId"]),
            dataset_sha256=str(manifest["physicalFileSha256"]),
            archetype=str(params["archetype"]),
            ema_fast=int(params["ema_fast"]),
            ema_slow=int(params["ema_slow"]),
            rsi_period=int(params["rsi_period"]),
            rsi_threshold_long=float(params["rsi_threshold_long"]),
            rsi_threshold_short=float(params["rsi_threshold_short"]),
            sl_atr_mult=float(params["sl_atr_mult"]),
            tp_atr_mult=float(params["tp_atr_mult"]),
            pyramiding_tiers_count=int(params["pyramiding_tiers_count"]),
        )
    return funding.generate_candidate_blueprint(
        strategy_id=strategy_id,
        symbol=symbol,
        timeframe=timeframe,
        dataset_id=str(manifest["datasetId"]),
        dataset_sha256=str(manifest["physicalFileSha256"]),
        ema_fast=int(params["ema_fast"]),
        ema_slow=int(params["ema_slow"]),
        rsi_period=int(params["rsi_period"]),
        rsi_threshold_long=float(params["rsi_threshold_long"]),
        rsi_threshold_short=float(params["rsi_threshold_short"]),
        risk_per_trade_pct=float(params["risk_per_trade_pct"]),
        target_profit_ticks=float(params["target_profit_ticks"]),
        stop_loss_ticks=float(params["stop_loss_ticks"]),
    )


def score_is(result: Any) -> float:
    dd_penalty = max(0.01, 1.0 - (float(result.max_drawdown_pct) / 100.0))
    trades_bonus = 1.0 + __import__("math").log(1.0 + max(0, int(result.total_trades)))
    wr_factor = max(0.2, float(result.win_rate_pct) / 50.0)
    return float(result.profit_factor) * dd_penalty * trades_bonus * wr_factor


def process_dataset(path: Path, cycle: int = 1) -> Dict[str, Any]:
    manifest, candles = load_custodied_dataset(path)
    symbol = str(manifest["symbol"])
    timeframe = str(manifest["interval"])
    route = "FONDEO" if is_fondeo(symbol) else "ULTRA"
    initial_capital = 50_000.0 if route == "FONDEO" else 1_000.0
    dataset_hash = str(manifest["physicalFileSha256"])
    idx_is = int(len(candles) * 0.60)
    idx_val = int(len(candles) * 0.80)
    candles_is = candles[:idx_is]
    candles_val = candles[idx_is:idx_val]
    candles_blind_oos = candles[idx_val:]
    if not candles_blind_oos:
        raise RuntimeError(f"EMPTY_BLIND_OOS: {path.name}")

    ultra = UltraDiscoveryEngine()
    funding = FundingDiscoveryEngine()
    registry = StrategySearchRegistry(db_path=str(STATE_DB_PATH))
    engine = EventBacktestEngine()
    run_id = f"phase2_{dataset_hash[:16]}_{route}_{cycle}"

    full_space = deterministic_space(route)
    trial_budget = MAX_TRIALS_ULTRA if route == "ULTRA" else MAX_TRIALS_FONDEO
    params_space = budget_space(full_space, trial_budget, dataset_hash)
    trials: List[Tuple[float, Dict[str, Any], Any, Any]] = []

    for index, params in enumerate(params_space):
        trial_id = f"{run_id}_t{index:04d}"
        strategy = strategy_from_params(route, manifest, trial_id, params, ultra, funding)
        result = engine.run_backtest(strategy, candles_is, initial_capital_usd=initial_capital)
        registry.record_trial(SearchTrialRecord(
            trial_id=trial_id,
            run_id=run_id,
            generation=1,
            parent_trial_id=None,
            symbol=symbol,
            timeframe=timeframe,
            route=route,
            archetype=strategy.archetype,
            parameters=params,
            rules_json=strategy.entry_rules.model_dump_json(),
            dataset_id=str(manifest["datasetId"]),
            dataset_sha256=dataset_hash,
            discovery_engine="Phase2CanonicalResearchRunner",
            in_sample_pf=float(result.profit_factor),
            in_sample_dd_pct=float(result.max_drawdown_pct),
        ))
        trials.append((score_is(result), params, strategy, result))

    if not trials:
        return {"run_id": run_id, "status": "BLOCKED_NO_REAL_TRIALS", "dataset": path.name}
    trials.sort(key=lambda item: item[0], reverse=True)

    best_params = None
    best_val = float("-inf")
    for _, params, _, _ in trials[: min(TOP_VALIDATION, len(trials))]:
        candidate = strategy_from_params(route, manifest, f"{run_id}_validation", params, ultra, funding)
        val = engine.run_backtest(candidate, candles_val, initial_capital_usd=initial_capital)
        quality = float(val.profit_factor) * 100.0 + (float(val.net_profit_usd) / initial_capital) * 100.0 - float(val.max_drawdown_pct) * 0.5
        if quality > best_val:
            best_val = quality
            best_params = params
    if best_params is None:
        return {"run_id": run_id, "status": "BLOCKED_NO_VALIDATED_CHAMPION", "dataset": path.name}

    frozen = strategy_from_params(route, manifest, f"{run_id}_champion", best_params, ultra, funding)
    pre_oos = engine.run_backtest(frozen, candles_is + candles_val, initial_capital_usd=initial_capital)
    is_bt = engine.run_backtest(frozen, candles_is, initial_capital_usd=initial_capital)
    oos_bt = engine.run_backtest(frozen, candles_blind_oos, initial_capital_usd=initial_capital)
    is_trades = [float(t.return_pct) / 100.0 for t in is_bt.trades]
    pre_oos_trades = [float(t.return_pct) / 100.0 for t in pre_oos.trades]
    oos_trades = [float(t.return_pct) / 100.0 for t in oos_bt.trades]
    trades_raw = [
        {
            "entry_price": t.entry_price, "exit_price": t.exit_price, "qty": t.qty, "side": t.side,
            "net_pnl_usd": t.net_pnl_usd, "return_pct": t.return_pct, "r_multiple": t.r_multiple,
            "equity_before_usd": t.equity_before_usd, "equity_after_usd": t.equity_after_usd,
            "entry_bar_idx": t.entry_bar, "exit_bar_idx": t.exit_bar,
            "entry_time_ms": t.entry_time_ms, "exit_time_ms": t.exit_time_ms,
        } for t in oos_bt.trades
    ]
    candidate_info = {
        "candidate_id": frozen.strategy_id,
        "name": frozen.strategy_id,
        "route": route,
        "symbol": symbol,
        "timeframe": timeframe,
        "dataset_id": str(manifest["datasetId"]),
        "dataset_sha256": dataset_hash,
        "dataset_filepath": str(path),
        "strategy_snapshot_hash": getattr(frozen, "canonical_hash", ""),
        "roi_pct": round(((oos_bt.final_equity_usd - initial_capital) / initial_capital) * 100.0, 4),
        "profit_factor_oos": float(oos_bt.profit_factor),
        "max_drawdown_pct": float(oos_bt.max_drawdown_pct),
        "net_profit_oos_usd": float(oos_bt.net_profit_usd),
        "net_profit_usd": float(oos_bt.net_profit_usd),
        "trades_count": len(oos_trades),
        "trials_tested": len(params_space),
        "parameters": best_params,
        "rules": ["canonical_strategy_snapshot"],
        "indicators_count": 3,
        "run_id": run_id,
        "blind_oos_start_index": idx_val,
    }
    orchestrator = GatePipelineOrchestrator(evidence_base_dir=str(EVIDENCE_DIR))
    gates = orchestrator.run_all_gates(
        candidate_info=candidate_info,
        candles=candles,
        is_trades=is_trades,
        oos_trades=oos_trades,
        pre_oos_trades=pre_oos_trades,
        trades_raw=trades_raw,
        strategy_snapshot=frozen,
    )

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "run_id": run_id,
        "dataset_id": manifest["datasetId"],
        "dataset_sha256": dataset_hash,
        "physical_file_sha256": sha256_bytes(path),
        "symbol": symbol,
        "interval": timeframe,
        "route": route,
        "partition": {"is_pct": 60, "validation_pct": 20, "blind_oos_pct": 20, "blind_oos_start_index": idx_val},
        "trial_budget": len(params_space),
        "candidate_search_space": len(full_space),
        "top_validation": min(TOP_VALIDATION, len(trials)),
        "champion_parameters": best_params,
        "champion_strategy_hash": getattr(frozen, "canonical_hash", ""),
        "is": {"trades": len(is_bt.trades), "pf": is_bt.profit_factor, "dd_pct": is_bt.max_drawdown_pct, "net_profit_usd": is_bt.net_profit_usd},
        "validation_selection_score": best_val,
        "blind_oos": {"trades": len(oos_bt.trades), "pf": oos_bt.profit_factor, "dd_pct": oos_bt.max_drawdown_pct, "net_profit_usd": oos_bt.net_profit_usd, "roi_pct": candidate_info["roi_pct"]},
        "gates": gates,
        "status": "APPROVED" if gates.get("overall_certified") else gates.get("status_lifecycle", "REJECTED"),
    }
    out = EVIDENCE_DIR / f"{run_id}.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def main() -> int:
    datasets = sorted(
        p for p in DATA_DIR.glob("ds_bingx_*.json")
        if not p.name.endswith("_manifest.json")
    )[:MAX_DATASETS]
    if not datasets:
        raise SystemExit("PHASE2: NO_REAL_DATASETS")
    results = []
    for index, path in enumerate(datasets, start=1):
        results.append(process_dataset(path, cycle=index))
    summary = {
        "runner": "Phase2CanonicalResearchRunner",
        "datasets_processed": len(results),
        "approved": sum(1 for r in results if r.get("status") == "APPROVED"),
        "results": results,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
