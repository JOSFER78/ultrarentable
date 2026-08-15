#!/usr/bin/env python3
"""Create an isolated, bounded StrategyQuant X Builder project.

The stock Builder is treated as a format template only. It is never modified or
executed by this script. The generated project uses history already managed by
the running SQX installation and is deliberately small enough for a first
connectivity/execution proof; its output is candidate evidence, not validation.
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


DEFAULT_SQX_HOME = Path("/home/ubuntu/StrategyQuantX")
DEFAULT_SOURCE = DEFAULT_SQX_HOME / "user/projects/Builder/project.cfx"
DEFAULT_PROJECT = "Ultra_Auto_Pilot"


def require(root: ET.Element, path: str) -> ET.Element:
    node = root.find(path)
    if node is None:
        raise RuntimeError(f"Missing expected SQX setting: {path}")
    return node


def set_text(root: ET.Element, path: str, value: str) -> None:
    require(root, path).text = value


def make_commissions() -> ET.Element:
    commissions = ET.Element("Commissions")
    method = ET.SubElement(commissions, "Method", {"type": "PercentageBased", "use": "true"})
    params = ET.SubElement(method, "Params")
    param = ET.SubElement(
        params,
        "Param",
        {
            "key": "CommissionPct",
            "name": "Commission",
            "dataType": "2",
            "min": "-100.0",
            "max": "100.000000",
            "step": "0.01",
            "value": "0.05",
            "description": "Commission in % of price per full lot",
            "decimals": "4",
            "className": "PercentageBased",
            "category": "Default",
            "engine": "*",
        },
    )
    param.text = None
    return commissions


def configure_task(
    root: ET.Element,
    *,
    symbol: str,
    timeframe: str,
    date_from: str,
    date_to: str,
    oos_from: str,
) -> None:
    strategy_type = require(root, "./WhatToBuild/StrategyType")
    strategy_type.set("type", "simple")
    strategy_type.set("additionalCharts", "0")
    strategy_type.set("architecture", "sq4")
    strategy_type.attrib.pop("improveType", None)
    strategy_type.attrib.pop("strategyFile", None)

    complexity = require(root, "./WhatToBuild/RulesComplexity/Chart")
    complexity.set("minConditions", "1")
    complexity.set("maxConditions", "3")
    complexity.set("minExitConditions", "0")
    complexity.set("maxExitConditions", "2")
    complexity.set("minPeriod", "5")
    complexity.set("maxPeriod", "120")
    complexity.set("minShift", "1")
    complexity.set("maxShift", "2")

    slpt = require(root, "./WhatToBuild/SLPTOptions")
    set_text(slpt, "./SLRequired", "true")
    set_text(slpt, "./SLFixedPips", "false")
    set_text(slpt, "./SLATR", "true")
    set_text(slpt, "./MinSLATRMultiple", "1")
    set_text(slpt, "./MaxSLATRMultiple", "4")
    set_text(slpt, "./MinSLATRPeriod", "7")
    set_text(slpt, "./MaxSLATRPeriod", "40")
    set_text(slpt, "./PTRequired", "true")
    set_text(slpt, "./SeparatedSettings", "true")
    set_text(slpt, "./PTFixedPips", "false")
    set_text(slpt, "./PTATR", "true")
    set_text(slpt, "./MinPTATRMultiple", "1")
    set_text(slpt, "./MaxPTATRMultiple", "8")
    set_text(slpt, "./MinPTATRPeriod", "7")
    set_text(slpt, "./MaxPTATRPeriod", "40")
    set_text(slpt, "./SLValueType", "atr")
    set_text(slpt, "./PTValueType", "atr")

    build = require(root, "./WhatToBuild/BuildMode")
    build.set("generationType", "genetic-evolution")
    set_text(build, "./PopulationSize", "24")
    set_text(build, "./MaxGenerations", "3")
    set_text(build, "./Islands", "1")
    conditions = build.find("./Conditions")
    if conditions is not None:
        build.remove(conditions)

    money = require(root, "./RiskMoneyManagement/MoneyManagement")
    set_text(money, "./InitialCapital", "1000")
    for method in money.findall("./Method"):
        method.set("use", "true" if method.get("type") == "RiskFixedBalancePct" else "false")
    risk_method = next((m for m in money.findall("./Method") if m.get("type") == "RiskFixedBalancePct"), None)
    if risk_method is None:
        raise RuntimeError("RiskFixedBalancePct is not available in the Builder template")
    risk_params = {p.get("key"): p for p in risk_method.findall("./Params/Param")}
    risk_params["Risk"].text = "2"
    risk_params["Decimals"].text = "3"
    risk_params["LotsIfNoMM"].text = "0.001"

    setup = require(root, "./Data/Setups/Setup")
    setup.set("dateFrom", date_from)
    setup.set("dateTo", date_to)
    setup.set("testPrecision", "1")
    setup.set("slippage", "1")
    setup.set("engine", "MetaTrader4")
    chart = require(setup, "./Chart")
    chart.set("symbol", symbol)
    chart.set("timeframe", timeframe)
    chart.set("spread", "0")
    previous_commissions = setup.find("./Commissions")
    if previous_commissions is not None:
        setup.remove(previous_commissions)
    setup.append(make_commissions())

    data = require(root, "./Data")
    previous_oos = require(data, "./OutOfSample")
    data.remove(previous_oos)
    oos = ET.SubElement(data, "OutOfSample", {"showGraph": "false"})
    ET.SubElement(oos, "Range", {"dateFrom": oos_from, "dateTo": date_to})

    rankings = require(root, "./Rankings")
    set_text(rankings, "./MaxStrategies", "24")
    ranking = require(rankings, "./FitnessCriteria/Settings/Ranking")
    ranking.set("type", "NetProfit")
    conditions = require(rankings, "./Conditions")
    conditions.clear()
    stop = require(rankings, "./StopCondition")
    stop.set("type", "databank-full")
    stop.set("passedStrategies", "24")
    stop.set("restartCount", "0")
    stop.set("days", "0")
    stop.set("hours", "0")
    stop.set("minutes", "30")

    cross_checks = require(root, "./CrossChecks")
    cross_checks.set("use", "false")
    cross_checks.set("evaluateAll", "false")

    notes = require(root, "./Notes")
    notes.text = (
        "Ultrarentable autonomous execution pilot. Candidate generation only; "
        "requires subsequent OOS, robustness and independent venue validation."
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--sqx-home", type=Path, default=DEFAULT_SQX_HOME)
    parser.add_argument("--project", default=DEFAULT_PROJECT)
    parser.add_argument("--symbol", default="BTCUSDT_AUTO")
    parser.add_argument("--timeframe", default="H1")
    parser.add_argument("--date-from", default="2026.2.26")
    parser.add_argument("--date-to", default="2026.8.4")
    parser.add_argument("--oos-from", default="2026.6.18")
    parser.add_argument("--manifest", type=Path, default=Path("artifacts/sqx/active-project.json"))
    args = parser.parse_args()

    target_dir = args.sqx_home / "user/projects" / args.project
    target = target_dir / "project.cfx"
    if target.exists():
        raise SystemExit(f"Refusing to overwrite existing project: {target}")
    if not args.source.is_file():
        raise SystemExit(f"Builder template not found: {args.source}")

    with tempfile.TemporaryDirectory(prefix="ultrarentable-sqx-") as temp_name:
        temp_dir = Path(temp_name)
        with zipfile.ZipFile(args.source) as archive:
            archive.extractall(temp_dir)

        config_path = temp_dir / "config.xml"
        task_paths = sorted(temp_dir.glob("*-Task*.xml"))
        if len(task_paths) != 1:
            raise RuntimeError(f"Expected exactly one Builder task, found {len(task_paths)}")
        task_path = task_paths[0]

        config_tree = ET.parse(config_path)
        config_root = config_tree.getroot()
        config_root.set("name", args.project)
        task_ref = require(config_root, "./Tasks/Task")
        task_ref.set("name", "Autonomous candidate search")
        config_tree.write(config_path, encoding="utf-8", xml_declaration=False)

        task_tree = ET.parse(task_path)
        configure_task(
            task_tree.getroot(),
            symbol=args.symbol,
            timeframe=args.timeframe,
            date_from=args.date_from,
            date_to=args.date_to,
            oos_from=args.oos_from,
        )
        task_tree.write(task_path, encoding="utf-8", xml_declaration=False)

        target_dir.mkdir(parents=True, exist_ok=False)
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(temp_dir.iterdir()):
                archive.write(path, path.name)

    manifest = {
        "schema": "ultrarentable.sqx.project.v1",
        "createdAt": datetime.now(UTC).isoformat(),
        "project": args.project,
        "projectFile": str(target),
        "projectSha256": sha256(target),
        "sourceTemplate": str(args.source),
        "sourceTemplateSha256": sha256(args.source),
        "sourceWasModified": False,
        "purpose": "bounded MCP execution proof and candidate generation",
        "status": "CONFIGURED_NOT_STARTED",
        "market": {
            "symbol": args.symbol,
            "timeframe": args.timeframe,
            "historyOwner": "StrategyQuant X",
            "dateFrom": args.date_from,
            "dateTo": args.date_to,
            "outOfSampleFrom": args.oos_from,
        },
        "executionBudget": {"population": 24, "generations": 3, "maxMinutes": 30},
        "costModel": {"commissionPctPerSide": 0.05, "slippageTicks": 1},
        "evidenceStatus": "CANDIDATES_WILL_BE_UNVERIFIED",
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
