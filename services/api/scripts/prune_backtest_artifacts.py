#!/usr/bin/env python3
"""Dry-run by default; delete only orphaned backtest artifact directories."""
from __future__ import annotations

import argparse
from datetime import timedelta
import json

from services.api.app.db.database import SessionLocal
from services.api.app.maintenance.artifact_retention import prune_orphan_backtests


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--min-age-hours", type=float, default=1.0)
    args = parser.parse_args()

    if args.min_age_hours < 0:
        parser.error("--min-age-hours must be non-negative")

    db = SessionLocal()
    try:
        report = prune_orphan_backtests(
            db,
            min_age=timedelta(hours=args.min_age_hours),
            apply=args.apply,
        )
    finally:
        db.close()
    print(json.dumps(report.to_dict(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
