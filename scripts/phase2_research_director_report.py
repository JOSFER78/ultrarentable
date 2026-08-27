"""Generate the deterministic next-campaign agenda from the research registry."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from services.discovery.research_director import ResearchDirector
from services.discovery.strategy_search_registry import StrategySearchRegistry


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=None)
    parser.add_argument("--dataset-sha256", required=True)
    parser.add_argument("--output", default="data/phase2-evidence/research_director_next.json")
    parser.add_argument("--campaign-budget", type=int, default=12)
    parser.add_argument("--trials-per-campaign", type=int, default=100000)
    args = parser.parse_args()

    registry = StrategySearchRegistry(db_path=args.db)
    history = registry.get_all_trials(limit=100000)
    director = ResearchDirector()
    campaigns = director.next_campaigns(
        dataset_sha256=args.dataset_sha256,
        history=history,
        campaign_budget=args.campaign_budget,
        trials_per_campaign=args.trials_per_campaign,
    )
    director.validate_campaigns(campaigns)
    payload = {
        "schema": "phase2-research-director-v1",
        "dataset_sha256": args.dataset_sha256,
        "history_trials_seen": len(history),
        "campaigns": [c.__dict__ for c in campaigns],
        "certification": "NO_CERTIFICATION",
        "note": "This is a next-search agenda for SQX. It is not strategy performance evidence.",
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"campaigns": len(campaigns), "history_trials_seen": len(history), "status": "READY_FOR_SQX"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
