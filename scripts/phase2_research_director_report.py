"""Generate a deterministic next-campaign agenda from real research history."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from services.discovery.research_director import ResearchDirector
from services.discovery.strategy_search_registry import StrategySearchRegistry

ROOT = Path(__file__).resolve().parents[1]
FREEZE_DIR = ROOT / "data" / "phase2-evidence"


def _load_frozen_validation_history(dataset_sha256: str) -> List[Dict[str, Any]]:
    history: List[Dict[str, Any]] = []
    for path in sorted(FREEZE_DIR.glob("*_frozen.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if str(payload.get("dataset_sha256")) != dataset_sha256:
            continue
        if payload.get("status") != "FROZEN_VALIDATION_CHAMPION":
            continue
        robust = payload.get("validation_robustness")
        if not isinstance(robust, dict):
            continue
        history.append(
            {
                "trial_id": payload.get("candidate_id"),
                "run_id": payload.get("run_id"),
                "generation": 1,
                "symbol": payload.get("symbol"),
                "timeframe": payload.get("timeframe"),
                "route": payload.get("route"),
                "archetype": payload.get("parameters", {}).get("archetype", payload.get("route", "UNKNOWN")),
                "dataset_id": payload.get("dataset_id"),
                "dataset_sha256": dataset_sha256,
                "discovery_engine": "Phase2FrozenValidation",
                "validation_score": float(robust.get("score", 0.0) or 0.0),
                "profit_factor_validation": float(robust.get("median_pf", 0.0) or 0.0),
                "max_drawdown_validation_pct": float(robust.get("worst_drawdown_pct", 100.0) or 100.0),
                "validation_blocks": robust.get("blocks", []),
                "blind_oos_access": "NOT_CONSUMED",
            }
        )
    return history


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=None)
    parser.add_argument("--dataset-sha256", required=True)
    parser.add_argument("--output", default="data/phase2-evidence/research_director_next.json")
    parser.add_argument("--campaign-budget", type=int, default=12)
    parser.add_argument("--trials-per-campaign", type=int, default=100000)
    args = parser.parse_args()

    registry = StrategySearchRegistry(db_path=args.db)
    registry_history = registry.get_all_trials(limit=100000)
    frozen_history = _load_frozen_validation_history(args.dataset_sha256)
    history = registry_history + frozen_history

    director = ResearchDirector()
    campaigns = director.next_campaigns(
        dataset_sha256=args.dataset_sha256,
        history=history,
        campaign_budget=args.campaign_budget,
        trials_per_campaign=args.trials_per_campaign,
    )
    director.validate_campaigns(campaigns)
    payload = {
        "schema": "phase2-research-director-v2",
        "dataset_sha256": args.dataset_sha256,
        "history_trials_seen": len(history),
        "registry_trials_seen": len(registry_history),
        "frozen_validation_records_seen": len(frozen_history),
        "campaigns": [c.__dict__ for c in campaigns],
        "blind_oos": "NOT_CONSUMED_BY_DIRECTOR",
        "certification": "NO_CERTIFICATION",
        "note": "This is a next-search agenda derived from IS registry plus frozen Validation evidence. It never consumes Blind OOS.",
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(
        json.dumps(
            {
                "campaigns": len(campaigns),
                "history_trials_seen": len(history),
                "frozen_validation_records_seen": len(frozen_history),
                "status": "READY_FOR_SQX",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
