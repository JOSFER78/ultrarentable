#!/usr/bin/env python3
"""Build an isolated, bounded StrategyQuant X strategy-improvement project.

The source project supplies the already-audited market, cost, risk and OOS
settings. The generated CFX is an import artifact: StrategyQuant X remains the
owner of its market history and performs the actual improvement run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from datetime import UTC, datetime
from pathlib import Path


DEFAULT_SOURCE = Path("/home/ubuntu/StrategyQuantX/user/projects/Ultra_Auto_Pilot/project.cfx")
DEFAULT_TARGET = Path("artifacts/sqx/import/Ultra_Improve_Pilot.cfx")
DEFAULT_MANIFEST = Path("artifacts/sqx/improvement-project.json")


def require(root: ET.Element, path: str) -> ET.Element:
    node = root.find(path)
    if node is None:
        raise RuntimeError(f"Missing expected SQX setting: {path}")
    return node


def set_text(root: ET.Element, path: str, value: str) -> None:
    require(root, path).text = value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def configure_task(root: ET.Element, *, input_databank: str) -> None:
    strategy_type = require(root, "./WhatToBuild/StrategyType")
    strategy_type.attrib.clear()
    strategy_type.set("type", "improve")
    strategy_type.set("additionalCharts", "0")
    strategy_type.set("templateFile", "")
    strategy_type.set("improveType", "databank")
    strategy_type.set("strategyFile", "")
    strategy_type.set("improveDatabank", input_databank)

    build = require(root, "./WhatToBuild/BuildMode")
    set_text(build, "./PopulationSize", "16")
    set_text(build, "./MaxGenerations", "2")
    set_text(build, "./Islands", "1")
    require(build, "./EvoRestartOnFinish").set("status", "false")
    require(build, "./EvoRestartOnStagnation").set("status", "false")

    rankings = require(root, "./Rankings")
    set_text(rankings, "./MaxStrategies", "12")
    stop = require(rankings, "./StopCondition")
    stop.set("type", "databank-full")
    stop.set("passedStrategies", "12")
    stop.set("restartCount", "0")
    stop.set("days", "0")
    stop.set("hours", "0")
    stop.set("minutes", "15")

    parts = require(root, "./PartsToImprove")
    parts.set("improveATM", "false")
    entry = require(parts, "./EntryRules")
    entry.set("symmetry", "true")
    require(entry, "./LongImprovement").set("use", "true")
    require(entry, "./LongImprovement").set("action", "add-or-replace")
    require(entry, "./ShortImprovement").set("use", "true")
    require(entry, "./ShortImprovement").set("action", "add-or-replace")

    order_types = require(parts, "./OrderTypes")
    require(order_types, "./LongImprovement").set("use", "false")
    require(order_types, "./ShortImprovement").set("use", "false")

    exits = require(parts, "./ExitRules")
    exits.set("symmetry", "true")
    require(exits, "./LongImprovement").set("use", "true")
    require(exits, "./LongImprovement").set("action", "add-or-replace")
    require(exits, "./ShortImprovement").set("use", "true")
    require(exits, "./ShortImprovement").set("action", "add-or-replace")

    notes = require(root, "./Notes")
    notes.text = (
        "Ultrarentable bounded improvement pilot. Uses the candidate placed in "
        "Strategies to improve and SQX-managed history. Output remains unverified "
        "until separate OOS and robustness validation is completed."
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--project", default="Ultra_Improve_Pilot")
    parser.add_argument("--candidate", default="Strategy 1.2.22")
    parser.add_argument("--input-databank", default="Strategies to improve")
    args = parser.parse_args()

    if not args.source.is_file():
        raise SystemExit(f"Source project not found: {args.source}")
    if args.target.exists():
        raise SystemExit(f"Refusing to overwrite existing import artifact: {args.target}")

    with tempfile.TemporaryDirectory(prefix="ultrarentable-sqx-improve-") as temp_name:
        temp_dir = Path(temp_name)
        with zipfile.ZipFile(args.source) as archive:
            archive.extractall(temp_dir)

        config_path = temp_dir / "config.xml"
        task_paths = sorted(temp_dir.glob("*-Task*.xml"))
        if len(task_paths) != 1:
            raise RuntimeError(f"Expected exactly one Builder task, found {len(task_paths)}")

        config_tree = ET.parse(config_path)
        config_root = config_tree.getroot()
        config_root.set("name", args.project)
        task_ref = require(config_root, "./Tasks/Task")
        task_ref.set("name", f"Improve {args.candidate}")
        task_ref.set("active", "true")
        config_tree.write(config_path, encoding="utf-8", xml_declaration=False)

        task_tree = ET.parse(task_paths[0])
        configure_task(task_tree.getroot(), input_databank=args.input_databank)
        task_tree.write(task_paths[0], encoding="utf-8", xml_declaration=False)

        args.target.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(args.target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(temp_dir.iterdir()):
                archive.write(path, path.name)

    manifest = {
        "schema": "ultrarentable.sqx.improvement.v1",
        "createdAt": datetime.now(UTC).isoformat(),
        "project": args.project,
        "candidate": args.candidate,
        "sourceProjectFile": str(args.source),
        "sourceProjectSha256": sha256(args.source),
        "importArtifact": str(args.target.resolve()),
        "importArtifactSha256": sha256(args.target),
        "historyOwner": "StrategyQuant X",
        "inputDatabank": args.input_databank,
        "partsToImprove": ["entry rules", "exit rules"],
        "preserved": ["order types", "market", "costs", "risk", "OOS split"],
        "executionBudget": {"population": 16, "generations": 2, "maxMinutes": 15},
        "status": "IMPORT_ARTIFACT_READY",
        "evidenceStatus": "IMPROVEMENT_NOT_EXECUTED",
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
