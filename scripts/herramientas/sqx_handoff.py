#!/usr/bin/env python3
"""RETIRED DRAFT: depends on full-bank exports; do not deploy.

Current policy requires selection and robustness evidence inside SQX before
export. This historical prototype does not satisfy that policy.

Extract a bounded IS-only research shortlist from completed native SQX exports.

No SQX API calls, no runner mutations, no improvement or validation claims.
The handoff index contains the latest processed batch per project. Original
exports and immutable batch manifests remain available for audit.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import math
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import zipfile

POLICY = "is-round-robin-v1"
FIELDS = {
    "net_profit": "Net profit (IS)",
    "trades": "# of trades (IS)",
    "profit_factor": "Profit factor (IS)",
    "sharpe": "Sharpe Ratio (IS)",
    "stability": "Stability (IS)",
    "ret_dd": "Ret/DD Ratio (IS)",
    "drawdown": "Drawdown (IS)",
}
AXES = ("net_profit", "ret_dd", "sharpe", "stability")


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def atomic_bytes(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(tmp, path)
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_json(path, value):
    atomic_bytes(path, (json.dumps(value, ensure_ascii=False, indent=2,
                                  allow_nan=False) + "\n").encode())


def confined(raw, root):
    if not raw:
        raise ValueError("Missing source path")
    path = Path(raw).resolve()
    path.relative_to(root.resolve())
    return path


def read_rows(source, record):
    data = source.read_bytes()
    if digest(data) != record.get("csv_sha256"):
        raise ValueError("CSV hash differs from completed runner record")
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")), delimiter=";")
    required = {"Strategy Name", "Symbol (IS)", "TimeFrame (IS)", *FIELDS.values()}
    if not required.issubset(reader.fieldnames or []):
        raise ValueError("CSV missing required IS fields")
    rows = list(reader)
    if len(rows) != record.get("csv_filas"):
        raise ValueError("CSV row count differs from completed runner record")
    return rows


def rank_rows(rows, min_trades):
    """Interleave four IS rankings; OOS fields are never read or scored."""
    eligible = []
    seen = set()
    for row in rows:
        name = row["Strategy Name"]
        if name in seen:
            raise ValueError("Duplicate strategy name in one native export")
        seen.add(name)
        if not name or "/" in name or "\\" in name or name in (".", ".."):
            raise ValueError("Unsafe strategy name")
        try:
            metrics = {key: float(row[column]) for key, column in FIELDS.items()}
        except (TypeError, ValueError):
            continue
        if not all(math.isfinite(v) for v in metrics.values()):
            continue
        if (metrics["trades"] < min_trades or not metrics["trades"].is_integer()
                or metrics["net_profit"] <= 0 or metrics["profit_factor"] <= 1
                or metrics["drawdown"] < 0):
            continue
        eligible.append({"strategy_name": name, "symbol": row["Symbol (IS)"],
                         "timeframe": row["TimeFrame (IS)"], "metrics_is": metrics})
    lists = {axis: sorted(eligible, key=lambda c: (-c["metrics_is"][axis],
                                                 c["strategy_name"])) for axis in AXES}
    positions = {axis: 0 for axis in AXES}
    used = set()
    ordered = []
    while len(used) < len(eligible):
        for axis in AXES:
            items = lists[axis]
            index = positions[axis]
            while index < len(items) and items[index]["strategy_name"] in used:
                index += 1
            positions[axis] = index + 1
            if index < len(items):
                candidate = dict(items[index], selected_by=axis, rank_on_axis=index + 1)
                used.add(candidate["strategy_name"])
                ordered.append(candidate)
    return ordered


def checked_artifact(path):
    data = path.read_bytes()
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for member in ("settings.xml", "strategy_Portfolio.xml"):
            info = archive.getinfo(member)
            if info.file_size > 32 * 1024 * 1024:
                raise ValueError("SQX XML exceeds inspection limit")
            ET.fromstring(archive.read(member))
        bad = archive.testzip()
        if bad:
            raise ValueError("SQX ZIP CRC failure: " + bad)
    return data, digest(data)


def process_batch(base, output, project, record, limit, min_trades):
    source = confined(record.get("csv"), base / "resultados")
    artifacts = confined(record.get("artefactos_dir"), base / "artefactos")
    rows = read_rows(source, record)
    ranked = rank_rows(rows, min_trades)
    selected, hashes, missing = [], set(), []
    for candidate in ranked:
        if len(selected) >= limit:
            break
        path = confined(artifacts / (candidate["strategy_name"] + ".sqx"), artifacts)
        try:
            data, sha = checked_artifact(path)
        except (OSError, ValueError, KeyError, zipfile.BadZipFile, ET.ParseError) as exc:
            missing.append({"strategy_name": candidate["strategy_name"], "error": str(exc)})
            continue
        if sha in hashes:
            continue
        hashes.add(sha)
        target = output / "artifacts" / (sha + ".sqx")
        if not target.exists() or digest(target.read_bytes()) != sha:
            atomic_bytes(target, data)
        selected.append(dict(candidate, candidate_id="sqx-sha256:" + sha,
                             source_sqx=str(path), sqx_sha256=sha, sqx_path=str(target),
                             evidence_status="CANDIDATE_UNVERIFIED",
                             next_step="PENDING_IMPROVEMENT",
                             canonical_replay="NO DATA", funding_suitability="NO DATA"))
    # A damaged selected export must be retried, not silently marked processed.
    if missing:
        raise ValueError("Missing or invalid shortlisted artifacts: " + json.dumps(missing[:5]))
    return {"schema_version": 1, "policy": POLICY, "created_at": now(),
            "project": project, "round": record["ronda"], "completed_at": record["fin"],
            "source_csv": str(source), "csv_sha256": record["csv_sha256"],
            "csv_rows": len(rows), "eligible_is_rows": len(ranked),
            "limit": limit, "min_trades": min_trades, "selection_inputs": "IS_ONLY",
            "oos_status": "NOT_USED_FOR_SELECTION; independence not established",
            "ranking_axes": list(AXES),
            "limitations": ["Heuristic research shortlist, not proven best strategies",
                            "Native backtest metrics, no independent replay",
                            "Content deduplication only, not semantic rule deduplication"],
            "candidates": selected}


def run(base, output, limit, min_trades, max_batches):
    state = json.loads((base / "estado.json").read_text())
    index_path = output / "index.json"
    index = json.loads(index_path.read_text()) if index_path.exists() else {
        "schema_version": 1, "policy": POLICY, "projects": {}}
    completed = []
    for project, cell in state["celdas"].items():
        rounds = [r for r in cell.get("rondas", []) if r.get("fin") and r.get("csv_sha256")
                  and r.get("artefactos_dir") and r.get("artefactos_contados", 0) > 0]
        if rounds:
            completed.append((project, max(rounds, key=lambda r: r["fin"])))
    completed.sort(key=lambda item: item[1]["fin"], reverse=True)
    processed, failures = [], []
    for project, record in completed:
        key = digest(json.dumps([POLICY, project, record["ronda"], record["csv_sha256"],
                                 limit, min_trades]).encode())
        previous = index["projects"].get(project, {})
        if previous.get("batch_id") == key:
            continue
        try:
            batch = process_batch(base, output, project, record, limit, min_trades)
            manifest = output / "batches" / (key + ".json")
            atomic_json(manifest, batch)
            index["projects"][project] = {
                "batch_id": key, "round": record["ronda"], "manifest": str(manifest),
                "candidate_count": len(batch["candidates"]),
                "csv_sha256": record["csv_sha256"], "completed_at": record["fin"]}
            index["updated_at"] = now()
            atomic_json(index_path, index)
            processed.append({"project": project, "round": record["ronda"],
                              "candidates": len(batch["candidates"]), "batch_id": key})
            if len(processed) >= max_batches:
                break
        except (OSError, ValueError, KeyError, csv.Error) as exc:
            failures.append({"project": project, "error": str(exc)})
    result = {"at": now(), "processed": processed, "errors": failures,
              "projects_in_handoff": len(index["projects"]),
              "candidate_entries": sum(p["candidate_count"] for p in index["projects"].values()),
              "index": str(index_path)}
    atomic_json(output / "last_run.json", result)
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return 1 if failures else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--min-trades", type=int, default=30)
    parser.add_argument("--max-batches", type=int, default=2)
    args = parser.parse_args()
    if min(args.limit, args.min_trades, args.max_batches) < 1:
        parser.error("Limits must be positive")
    args.output.mkdir(parents=True, exist_ok=True)
    import fcntl
    with (args.output / ".lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('{"status":"already_running"}')
            return 0
        return run(args.base.resolve(), args.output.resolve(), args.limit,
                   args.min_trades, args.max_batches)


if __name__ == "__main__":
    sys.exit(main())
