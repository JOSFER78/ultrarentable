from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_active_normalized_dataset_has_real_raw_chain_and_closed_candles() -> None:
    root = _repo_root()
    manifests = list((root / "data" / "normalized").glob("*_manifest.json"))
    assert manifests, "At least one captured real dataset must exist"

    for manifest_path in manifests:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        normalized_path = root / "data" / str(manifest["normalizedPath"]).replace("\\", "/")
        raw_path = root / "data" / str(manifest["rawPath"]).replace("\\", "/")
        normalized_bytes = normalized_path.read_bytes()
        raw_bytes = raw_path.read_bytes()
        records = json.loads(normalized_bytes)

        assert manifest["timestampUnit"] == "milliseconds" if "timestampUnit" in manifest else manifest["startTime"] > 10**12
        assert manifest["closedRecordsOnly"] is True
        assert hashlib.sha256(normalized_bytes).hexdigest() == manifest["checksumSha256"]
        assert hashlib.sha256(raw_bytes).hexdigest() == manifest["rawChecksumSha256"]
        assert len(records) == manifest["recordCount"]
        assert all(records[index]["time"] < records[index + 1]["time"] for index in range(len(records) - 1))

        captured_ms = int(datetime.fromisoformat(manifest["createdAt"].replace("Z", "+00:00")).timestamp() * 1000)
        interval_ms_by_name = {
            "1m": 60_000,
            "5m": 300_000,
            "15m": 900_000,
            "1h": 3_600_000,
        }
        interval_ms = interval_ms_by_name.get(manifest["interval"])
        assert interval_ms is not None, f"Unsupported interval: {manifest['interval']}"
        assert records[-1]["time"] + interval_ms <= captured_ms
