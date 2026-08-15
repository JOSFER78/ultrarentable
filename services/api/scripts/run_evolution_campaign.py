from __future__ import annotations

import argparse
import json
import traceback
from pathlib import Path

from services.api.app.db.database import InstrumentRuleSnapshotModel, SessionLocal
from services.api.app.factory.autopilot import UniverseScanner
from services.api.app.factory.fast_engine_campaign import FastEngineCampaignRunner


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one verified FastEngine campaign")
    parser.add_argument("--interval", choices=("1m", "5m", "15m"), required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resume-from", type=Path)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    status_path = args.output.with_suffix(".status")
    db = SessionLocal()
    try:
        scanner = UniverseScanner(intervals=[args.interval], require_complete_universe=True)
        opportunities = scanner.scan_opportunities(db)
        if not opportunities:
            raise RuntimeError(f"No verified opportunity: {scanner.rejections}")
        opportunity = opportunities[0]
        rules = (
            db.query(InstrumentRuleSnapshotModel)
            .filter(InstrumentRuleSnapshotModel.symbol == opportunity["symbol"])
            .first()
        )
        carried = None
        if args.resume_from:
            previous = json.loads(args.resume_from.read_text(encoding="utf-8"))
            carried = [
                item["strategy"]
                for item in previous.get("topAttempts", [])
                if isinstance(item, dict) and isinstance(item.get("strategy"), dict)
            ]
        outcome = FastEngineCampaignRunner(db, seed=args.seed).run(
            opportunity,
            max_leverage=int(rules.max_leverage if rules else 20),
            initial_population=carried,
        )
        payload = outcome.to_dict()
        temporary = args.output.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        temporary.replace(args.output)
        status_path.write_text("0\n", encoding="utf-8")
        print(json.dumps({
            "status": payload["status"],
            "evaluations": payload["evaluations"],
            "archiveSize": payload["archiveSize"],
            "topAttempts": len(payload["topAttempts"]),
            "topEquity": payload["topAttempts"][0]["finalEquity"] if payload["topAttempts"] else None,
            "topEvidence": payload["topAttempts"][0]["evidenceScore"] if payload["topAttempts"] else None,
        }))
        return 0
    except Exception:
        status_path.write_text("1\n", encoding="utf-8")
        traceback.print_exc()
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
