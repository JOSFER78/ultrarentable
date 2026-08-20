from __future__ import annotations

import hashlib
import json
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_active_normalized_dataset_has_real_raw_chain_and_closed_candles() -> None:
    root = _repo_root()
    manifests = list((root / "data" / "normalized").glob("*_manifest.json"))
    assert manifests, "At least one captured real dataset must exist"

    for manifest_path in manifests:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        
        # Path resolution
        if "normalizedPath" in manifest:
            normalized_path = root / "data" / str(manifest["normalizedPath"]).replace("\\", "/")
        else:
            normalized_path = manifest_path.parent / (manifest_path.name.replace("_manifest.json", ".json"))
            
        assert normalized_path.exists(), f"Dataset file {normalized_path} does not exist"
        normalized_bytes = normalized_path.read_bytes()
        records = json.loads(normalized_bytes)

        checksum = manifest.get("checksum_sha256") or manifest.get("checksumSha256")
        if checksum:
            assert hashlib.sha256(normalized_bytes).hexdigest() == checksum
            
        record_count = manifest.get("record_count") or manifest.get("recordCount")
        if record_count is not None:
            assert len(records) == record_count
            
        if len(records) > 1:
            time_key = (
                "timestamp_utc_ms"
                if "timestamp_utc_ms" in records[0]
                else ("time" if "time" in records[0] else "timestamp")
            )
            assert all(records[index][time_key] < records[index + 1][time_key] for index in range(len(records) - 1))
