"""Real StrategyQuant X (SQX) VPS ingestion bridge.

This bridge treats SQX as an external hypothesis factory. It does not infer
profitability from filenames or exported metrics. It scans configured VPS
locations, records immutable file hashes, copies nothing implicitly, and
produces a manifest that the research pipeline can use to locate the exact
SQX artifact and optional databank export used for a campaign.

Supported inputs:
- StrategyQuant .sqx strategy files (opaque provenance artifacts)
- SQX databank exports: .csv / .xls / .xlsx (metadata/metric evidence only)
- Optional JSON rule exports produced by a custom SQX snippet

The proprietary .sqx file is never parsed heuristically. To backtest a SQX
strategy independently, a rule export must be supplied or a supported source
export must be translated into the canonical strategy AST.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, List, Optional

DEFAULT_ROOTS = (
    "/opt/StrategyQuantX/user/projects",
    "/opt/strategyquant/user/projects",
    "/root/StrategyQuantX/user/projects",
    "/root/strategyquant/user/projects",
)

SUPPORTED_SUFFIXES = {".sqx", ".csv", ".xls", ".xlsx", ".json"}


@dataclass(frozen=True)
class SQXArtifact:
    path: str
    suffix: str
    size_bytes: int
    sha256: str
    mtime_utc: str
    artifact_kind: str
    readable: bool


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def infer_kind(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".sqx":
        return "SQX_STRATEGY_PROVENANCE"
    if suffix == ".csv":
        return "SQX_DATABANK_EXPORT"
    if suffix in {".xls", ".xlsx"}:
        return "SQX_DATABANK_EXPORT"
    if suffix == ".json":
        return "SQX_RULE_EXPORT"
    return "UNKNOWN"


def scan_roots(roots: Iterable[Path]) -> List[SQXArtifact]:
    results: List[SQXArtifact] = []
    seen: set[str] = set()
    for root in roots:
        if not root.exists() or not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
                continue
            resolved = str(path.resolve())
            if resolved in seen:
                continue
            seen.add(resolved)
            stat = path.stat()
            results.append(
                SQXArtifact(
                    path=resolved,
                    suffix=path.suffix.lower(),
                    size_bytes=int(stat.st_size),
                    sha256=sha256_file(path),
                    mtime_utc=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                    artifact_kind=infer_kind(path),
                    readable=os.access(path, os.R_OK),
                )
            )
    return results


def csv_columns(path: Path) -> List[str]:
    if path.suffix.lower() != ".csv":
        return []
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        sample = fh.read(4096)
        fh.seek(0)
        try:
            return next(csv.reader(fh)) if sample else []
        except csv.Error:
            return []


def build_manifest(roots: List[Path], campaign_id: str) -> dict[str, Any]:
    artifacts = scan_roots(roots)
    return {
        "schema": "sqx-vps-ingest-v1",
        "campaign_id": campaign_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "roots": [str(p) for p in roots],
        "artifact_count": len(artifacts),
        "sqx_strategy_count": sum(a.artifact_kind == "SQX_STRATEGY_PROVENANCE" for a in artifacts),
        "databank_export_count": sum(a.artifact_kind == "SQX_DATABANK_EXPORT" for a in artifacts),
        "rule_export_count": sum(a.artifact_kind == "SQX_RULE_EXPORT" for a in artifacts),
        "artifacts": [asdict(a) for a in artifacts],
        "rule_exports": [
            {"path": a.path, "sha256": a.sha256}
            for a in artifacts
            if a.artifact_kind == "SQX_RULE_EXPORT"
        ],
        "csv_exports": [
            {"path": a.path, "sha256": a.sha256, "columns": csv_columns(Path(a.path))}
            for a in artifacts
            if a.artifact_kind == "SQX_DATABANK_EXPORT" and a.suffix == ".csv"
        ],
        "profitability_certified": False,
        "note": "SQX artifacts are source evidence only; canonical ULTRARENTABLE validation is required before any strategy promotion.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", action="append", dest="roots", help="SQX project root; may be repeated")
    parser.add_argument("--output", default="data/sqx-ingest/latest_manifest.json")
    parser.add_argument("--campaign-id", default="manual")
    args = parser.parse_args()

    roots = [Path(p) for p in (args.roots or os.getenv("SQX_PROJECT_ROOTS", "").split(os.pathsep) if (args.roots or os.getenv("SQX_PROJECT_ROOTS")) else DEFAULT_ROOTS)]
    manifest = build_manifest(roots, args.campaign_id)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ("campaign_id", "artifact_count", "sqx_strategy_count", "databank_export_count", "rule_export_count", "profitability_certified")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
