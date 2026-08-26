#!/usr/bin/env python3
"""Run bounded real-only strategy research against a physical dataset.

Example:
  python scripts/run_strategy_research.py --dataset data/normalized/<file>.json --symbol AVAX-USDT --timeframe 1h

The command performs generation + IS backtests + semantic evolution only.
It does not certify or touch blind OOS; certification remains owned by the
canonical validation pipeline.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from services.discovery.strategy_research_loop import StrategyResearchLoop
from services.discovery.strategy_search_registry import StrategySearchRegistry


def main() -> int:
    parser = argparse.ArgumentParser(description="Ultrarentable real-only strategy research")
    parser.add_argument("--dataset", required=True, help="Physical JSON dataset")
    parser.add_argument("--symbol", required=True, help="Canonical symbol")
    parser.add_argument("--timeframe", required=True, help="Canonical timeframe")
    parser.add_argument("--generations", type=int, default=3)
    parser.add_argument("--seeds", type=int, default=24)
    parser.add_argument("--children", type=int, default=6)
    args = parser.parse_args()

    path = Path(args.dataset)
    if not path.is_file():
        raise SystemExit(f"DATASET_NOT_FOUND: {path}")

    registry = StrategySearchRegistry()
    loop = StrategyResearchLoop(registry=registry)
    result = loop.run(
        dataset_path=str(path),
        symbol=args.symbol,
        timeframe=args.timeframe,
        generations=args.generations,
        seeds=args.seeds,
        children_per_seed=args.children,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
