from __future__ import annotations

import hashlib
import json
import time
from datetime import UTC, datetime
from itertools import pairwise
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from services.api.app.bingx.client import BingXPyRestClient
from services.api.app.config import DATA_DIR
from services.api.app.db.database import DatasetModel, RawIngestLogModel

DAY_MS = 86_400_000
SOURCE_INTERVAL = "1m"
SOURCE_STEP_MS = 60_000
TARGET_INTERVALS = {"1m": 1, "5m": 5, "15m": 15, "1h": 60}


class HistoricalIngestionError(RuntimeError):
    """Raised when a requested real-data window cannot be proven complete."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _repo_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve())).replace("\\", "/")
    except ValueError:
        return str(path.resolve()).replace("\\", "/")


def _data_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path(DATA_DIR).resolve())).replace("\\", "/")
    except ValueError:
        return _repo_relative(path)


def _write_atomic(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(payload)
    temporary.replace(path)


def _normalize_candle(item: dict[str, Any]) -> dict[str, float | int]:
    return {
        "time": int(item["time"]),
        "open": float(item["open"]),
        "high": float(item["high"]),
        "low": float(item["low"]),
        "close": float(item["close"]),
        "volume": float(item["volume"]),
    }


def fetch_closed_eth_minutes(
    client: BingXPyRestClient,
    *,
    days: int,
    now_ms: int | None = None,
    page_limit: int = 1440,
) -> tuple[list[dict[str, float | int]], list[dict[str, Any]], dict[str, Any]]:
    """Fetch a complete closed-candle ETH window backwards using BingX pagination."""
    if days < 1:
        raise ValueError("DAYS_MUST_BE_POSITIVE")
    now_ms = now_ms or int(time.time() * 1000)
    last_closed = (now_ms // SOURCE_STEP_MS) * SOURCE_STEP_MS - SOURCE_STEP_MS
    requested_start = last_closed - (days * DAY_MS) + SOURCE_STEP_MS
    cursor = last_closed
    by_time: dict[int, dict[str, float | int]] = {}
    raw_records: dict[int, dict[str, Any]] = {}
    pages: list[dict[str, Any]] = []

    while cursor >= requested_start:
        rows = client.get_klines(
            "ETH-USDT",
            SOURCE_INTERVAL,
            limit=page_limit,
            end_time=cursor,
        )
        if not rows:
            break
        page_times = [int(row["time"]) for row in rows]
        earliest = min(page_times)
        pages.append({"endTime": cursor, "firstTime": earliest, "recordCount": len(rows)})
        for row in rows:
            candle = _normalize_candle(row)
            candle_time = int(candle["time"])
            if requested_start <= candle_time <= last_closed:
                by_time[candle_time] = candle
                raw_records[candle_time] = row
        next_cursor = earliest - SOURCE_STEP_MS
        if next_cursor >= cursor:
            raise HistoricalIngestionError("BINGX_PAGINATION_DID_NOT_ADVANCE")
        cursor = next_cursor

    expected_count = days * 1440
    expected_times = range(requested_start, last_closed + SOURCE_STEP_MS, SOURCE_STEP_MS)
    missing_times = [candle_time for candle_time in expected_times if candle_time not in by_time]
    retry_audit: list[dict[str, Any]] = []
    if 0 < len(missing_times) <= 100:
        for missing_time in missing_times:
            rows = client.get_klines(
                "ETH-USDT",
                SOURCE_INTERVAL,
                limit=3,
                start_time=missing_time,
                end_time=missing_time + SOURCE_STEP_MS - 1,
            )
            recovered = False
            for row in rows:
                if int(row["time"]) == missing_time:
                    by_time[missing_time] = _normalize_candle(row)
                    raw_records[missing_time] = row
                    recovered = True
                    break
            retry_audit.append({"time": missing_time, "recovered": recovered})

    records = [by_time[key] for key in sorted(by_time)]
    if len(records) != expected_count:
        first = int(records[0]["time"]) if records else None
        unresolved = [
            candle_time
            for candle_time in range(
                requested_start,
                last_closed + SOURCE_STEP_MS,
                SOURCE_STEP_MS,
            )
            if candle_time not in by_time
        ]
        raise HistoricalIngestionError(
            f"INCOMPLETE_BINGX_WINDOW expected={expected_count} actual={len(records)} "
            f"requested_start={requested_start} actual_start={first} "
            f"missing={unresolved[:20]}"
        )
    for previous, current in pairwise(records):
        if int(current["time"]) - int(previous["time"]) != SOURCE_STEP_MS:
            raise HistoricalIngestionError(
                f"BINGX_SOURCE_GAP previous={previous['time']} current={current['time']}"
            )
    audit = {
        "symbol": "ETH-USDT",
        "interval": SOURCE_INTERVAL,
        "requestedDays": days,
        "requestedStartTime": requested_start,
        "requestedEndTime": last_closed,
        "pageLimit": page_limit,
        "pages": pages,
        "missingCandleRetries": retry_audit,
    }
    raw = [raw_records[key] for key in sorted(raw_records)]
    return records, raw, audit


def resample_minutes(
    records: list[dict[str, float | int]], target_interval: str
) -> list[dict[str, float | int]]:
    factor = TARGET_INTERVALS[target_interval]
    if factor == 1:
        return list(records)
    target_step = factor * SOURCE_STEP_MS
    buckets: dict[int, list[dict[str, float | int]]] = {}
    for candle in records:
        bucket = (int(candle["time"]) // target_step) * target_step
        buckets.setdefault(bucket, []).append(candle)
    result: list[dict[str, float | int]] = []
    for bucket in sorted(buckets):
        group = buckets[bucket]
        expected_times = [bucket + index * SOURCE_STEP_MS for index in range(factor)]
        if [int(item["time"]) for item in group] != expected_times:
            continue
        result.append(
            {
                "time": bucket,
                "open": float(group[0]["open"]),
                "high": max(float(item["high"]) for item in group),
                "low": min(float(item["low"]) for item in group),
                "close": float(group[-1]["close"]),
                "volume": sum(float(item["volume"]) for item in group),
            }
        )
    if len(result) < 2:
        raise HistoricalIngestionError(f"INSUFFICIENT_RESAMPLED_DATA interval={target_interval}")
    for previous, current in pairwise(result):
        if int(current["time"]) - int(previous["time"]) != target_step:
            raise HistoricalIngestionError(f"RESAMPLED_GAP interval={target_interval}")
    return result


def _save_raw_capture(
    db: Session,
    *,
    raw_records: list[dict[str, Any]],
    audit: dict[str, Any],
) -> tuple[Path, str, int]:
    received_ms = int(time.time() * 1000)
    envelope = {
        "venue": "BINGX",
        "endpoint": "/openApi/swap/v3/quote/klines",
        "requestAudit": audit,
        "receiveTimestamp": received_ms,
        "capturedAt": datetime.now(UTC).isoformat(),
        "payload": raw_records,
    }
    raw_bytes = _canonical_json(envelope).encode("utf-8")
    checksum = _sha256(raw_bytes)
    stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%S-%fZ")
    path = Path(DATA_DIR) / "raw" / "rest" / "klines" / "ETH-USDT" / "1m" / f"{stamp}.json"
    _write_atomic(path, raw_bytes)
    db.add(
        RawIngestLogModel(
            endpoint="/openApi/swap/v3/quote/klines",
            params_json=_canonical_json(audit),
            raw_body_path=_repo_relative(path),
            sha256_raw=checksum,
            exchange_start_time=audit["requestedStartTime"],
            exchange_end_time=audit["requestedEndTime"],
            receive_time=received_ms,
            status_code=200,
            client_version="python-rest-v3-paginated",
            transformer_version="eth-research-pipeline-v1",
        )
    )
    return path, checksum, received_ms


def _save_approved_dataset(
    db: Session,
    *,
    interval: str,
    records: list[dict[str, float | int]],
    raw_path: Path,
    raw_checksum: str,
    requested_days: int,
) -> dict[str, Any]:
    payload = _canonical_json(records).encode("utf-8")
    checksum = _sha256(payload)
    first = int(records[0]["time"])
    last = int(records[-1]["time"])
    step_ms = TARGET_INTERVALS[interval] * SOURCE_STEP_MS
    expected_count = ((last - first) // step_ms) + 1
    gap_count = max(expected_count - len(records), 0)
    coverage = round((len(records) / expected_count) * 100, 8)
    dataset_id = f"ds_bingx_ETH_USDT_{interval}_{first}_{last}_{checksum[:10]}"
    normalized_path = Path(DATA_DIR) / "normalized" / f"{dataset_id}.json"
    manifest_path = Path(DATA_DIR) / "normalized" / f"{dataset_id}_manifest.json"
    _write_atomic(normalized_path, payload)
    manifest = {
        "datasetId": dataset_id,
        "venue": "BINGX",
        "symbol": "ETH-USDT",
        "feedType": f"kline_{interval}",
        "interval": interval,
        "timestampUnit": "milliseconds",
        "startTime": first,
        "endTime": last,
        "recordCount": len(records),
        "gapCount": gap_count,
        "duplicateCount": 0,
        "outOfOrderCount": 0,
        "coveragePct": coverage,
        "checksumSha256": checksum,
        "rawChecksumSha256": raw_checksum,
        "rawPath": _data_relative(raw_path),
        "normalizedPath": _data_relative(normalized_path),
        "createdAt": datetime.now(UTC).isoformat(),
        "closedRecordsOnly": True,
        "completeRequestedWindow": True,
        "requestedHistoryDays": requested_days,
        "sourceInterval": "1m",
        "derivedFromInterval": None if interval == "1m" else "1m",
    }
    _write_atomic(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False).encode("utf-8"))
    status = "APPROVED" if gap_count == 0 and coverage == 100.0 else "REJECTED"
    db.merge(
        DatasetModel(
            dataset_id=dataset_id,
            venue="BINGX",
            symbol="ETH-USDT",
            feed_type=f"kline_{interval}",
            interval=interval,
            start_time=first,
            end_time=last,
            record_count=len(records),
            gap_count=gap_count,
            duplicate_count=0,
            out_of_order_count=0,
            coverage_pct=coverage,
            checksum_sha256=checksum,
            status=status,
            file_path=_repo_relative(normalized_path),
            manifest_path=_repo_relative(manifest_path),
        )
    )
    if status != "APPROVED":
        raise HistoricalIngestionError(f"DATASET_QUALITY_REJECTED interval={interval}")
    return {
        "datasetId": dataset_id,
        "interval": interval,
        "recordCount": len(records),
        "startTime": first,
        "endTime": last,
        "coveragePct": coverage,
        "status": status,
        "derivedFrom": None if interval == "1m" else "1m",
    }


def build_eth_research_datasets(
    db: Session,
    *,
    days: int,
    client: BingXPyRestClient | None = None,
    now_ms: int | None = None,
) -> dict[str, Any]:
    """Download one real ETH window and atomically register all research timeframes."""
    client = client or BingXPyRestClient()
    minutes, raw_records, audit = fetch_closed_eth_minutes(
        client,
        days=days,
        now_ms=now_ms,
    )
    raw_path, raw_checksum, _ = _save_raw_capture(
        db,
        raw_records=raw_records,
        audit=audit,
    )
    datasets = []
    for interval in TARGET_INTERVALS:
        datasets.append(
            _save_approved_dataset(
                db,
                interval=interval,
                records=resample_minutes(minutes, interval),
                raw_path=raw_path,
                raw_checksum=raw_checksum,
                requested_days=days,
            )
        )
    db.commit()
    return {
        "status": "APPROVED",
        "symbol": "ETH-USDT",
        "source": "BINGX",
        "requestedDays": days,
        "sourcePages": len(audit["pages"]),
        "datasets": datasets,
    }
