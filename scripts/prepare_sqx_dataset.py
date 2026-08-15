#!/usr/bin/env python3
"""Create a deterministic StrategyQuant CSV from an approved normalized dataset.

This command does not modify StrategyQuant. It only validates the source chain and
writes a CSV plus a manifest that can be reviewed before an import is requested.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPECTED_COLUMNS = ("time", "open", "high", "low", "close", "volume")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_timestamp(value: int) -> str:
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc).strftime(
        "%Y.%m.%d %H:%M:%S"
    )


def validate_records(records: Any, interval_ms: int) -> list[dict[str, Any]]:
    if not isinstance(records, list) or not records:
        raise ValueError("DATASET_EMPTY_OR_INVALID")

    previous_time: int | None = None
    for index, record in enumerate(records):
        if not isinstance(record, dict) or any(key not in record for key in EXPECTED_COLUMNS):
            raise ValueError(f"INVALID_RECORD_AT_{index}")
        timestamp = record["time"]
        if not isinstance(timestamp, int):
            raise ValueError(f"INVALID_TIMESTAMP_AT_{index}")
        if previous_time is not None and timestamp - previous_time != interval_ms:
            raise ValueError(f"NON_CONTIGUOUS_DATA_AT_{index}")
        if record["high"] < max(record["open"], record["close"]):
            raise ValueError(f"INVALID_HIGH_AT_{index}")
        if record["low"] > min(record["open"], record["close"]):
            raise ValueError(f"INVALID_LOW_AT_{index}")
        previous_time = timestamp

    return records


def write_atomic_csv(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as target:
        writer = csv.writer(target, lineterminator="\n")
        for record in records:
            writer.writerow(
                (
                    utc_timestamp(record["time"]),
                    record["open"],
                    record["high"],
                    record["low"],
                    record["close"],
                    record["volume"],
                )
            )
        target.flush()
        os.fsync(target.fileno())
    temporary.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--interval-ms", type=int, default=300_000)
    args = parser.parse_args()

    source = args.source.resolve()
    output = args.output.resolve()
    source_checksum = sha256(source)
    if source_checksum != args.expected_sha256:
        raise ValueError("SOURCE_CHECKSUM_MISMATCH")

    records = validate_records(
        json.loads(source.read_text(encoding="utf-8")), args.interval_ms
    )
    write_atomic_csv(output, records)

    manifest = {
        "schemaVersion": "sqx-import-v1",
        "datasetId": args.dataset_id,
        "sourcePath": str(source),
        "sourceSha256": source_checksum,
        "outputPath": str(output),
        "outputSha256": sha256(output),
        "recordCount": len(records),
        "firstTimestamp": records[0]["time"],
        "lastTimestamp": records[-1]["time"],
        "intervalMs": args.interval_ms,
        "timezone": "UTC",
        "dateFormat": "yyyy.MM.dd HH:mm:ss",
        "columnTypes": ["Date & Time", "Open", "High", "Low", "Close", "Volume"],
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    manifest_path = output.with_suffix(output.suffix + ".manifest.json")
    temporary_manifest = manifest_path.with_suffix(manifest_path.suffix + ".tmp")
    temporary_manifest.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary_manifest.replace(manifest_path)
    print(json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    main()
