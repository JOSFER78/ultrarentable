from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from services.api.app.bingx.client import BingXPyRestClient
from services.api.app.db.database import Base, DatasetModel, OpportunityMatrixModel
from services.api.app.factory.autopilot import UniverseScanner

INTERVAL_MS = {"1m": 60_000, "5m": 300_000, "15m": 900_000}


@pytest.fixture()
def db_session(tmp_path: Path):
    engine = create_engine(f"sqlite:///{tmp_path / 'scanner.sqlite3'}")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _register_dataset(
    db: Session,
    root: Path,
    interval: str,
    records: list[dict[str, float | int]],
    *,
    dataset_suffix: str = "verified",
    corrupt_manifest_checksum: bool = False,
) -> DatasetModel:
    dataset_id = f"ds_bingx_ETH_USDT_{interval}_{dataset_suffix}"
    normalized_dir = root / "normalized"
    raw_dir = root / "raw"
    normalized_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    normalized_path = normalized_dir / f"{dataset_id}.json"
    normalized_path.write_text(json.dumps(records, separators=(",", ":")), encoding="utf-8")
    raw_path = raw_dir / f"{dataset_id}.json"
    raw_path.write_text(json.dumps({"payload": records}), encoding="utf-8")
    normalized_checksum = _sha256(normalized_path)
    manifest_path = normalized_dir / f"{dataset_id}_manifest.json"
    manifest = {
        "datasetId": dataset_id,
        "venue": "BINGX",
        "symbol": "ETH-USDT",
        "interval": interval,
        "recordCount": len(records),
        "gapCount": 0,
        "duplicateCount": 0,
        "outOfOrderCount": 0,
        "coveragePct": 100.0,
        "checksumSha256": ("0" * 64 if corrupt_manifest_checksum else normalized_checksum),
        "rawChecksumSha256": _sha256(raw_path),
        "rawPath": str(raw_path),
        "normalizedPath": str(normalized_path),
        "closedRecordsOnly": True,
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    dataset = DatasetModel(
        dataset_id=dataset_id,
        venue="BINGX",
        symbol="ETH-USDT",
        feed_type=f"kline_{interval}",
        interval=interval,
        start_time=int(records[0]["time"]),
        end_time=int(records[-1]["time"]),
        record_count=len(records),
        gap_count=0,
        duplicate_count=0,
        out_of_order_count=0,
        coverage_pct=100.0,
        checksum_sha256=normalized_checksum,
        status="APPROVED",
        file_path=str(normalized_path),
        manifest_path=str(manifest_path),
    )
    db.add(dataset)
    db.commit()
    return dataset


def _candles(
    interval: str, closes: list[float], volumes: list[float]
) -> list[dict[str, float | int]]:
    step_ms = INTERVAL_MS[interval]
    start_ms = 1_577_836_800_000
    return [
        {
            "time": start_ms + index * step_ms,
            "open": close * 0.999,
            "high": close * 1.002,
            "low": close * 0.998,
            "close": close,
            "volume": volumes[index],
        }
        for index, close in enumerate(closes)
    ]


def test_empty_database_never_creates_fabricated_opportunities(db_session: Session) -> None:
    scanner = UniverseScanner(minimum_history_days=0)

    assert scanner.scan_opportunities(db_session) == []
    assert db_session.query(OpportunityMatrixModel).count() == 0
    assert {item["interval"] for item in scanner.rejections} == {"1m", "5m", "15m"}


def test_scanner_ranks_only_verified_complete_universe(db_session: Session, tmp_path: Path) -> None:
    _register_dataset(
        db_session,
        tmp_path / "one-minute",
        "1m",
        _candles("1m", [100, 101, 99, 104, 98, 106], [50, 55, 52, 60, 58, 65]),
    )
    _register_dataset(
        db_session,
        tmp_path / "five-minute",
        "5m",
        _candles("5m", [100, 100.5, 100.1, 101, 100.8, 101.2], [200] * 6),
    )
    _register_dataset(
        db_session,
        tmp_path / "fifteen-minute",
        "15m",
        _candles("15m", [100, 102, 101, 103, 100, 104], [400] * 6),
    )

    scanner = UniverseScanner(minimum_history_days=0)
    opportunities = scanner.scan_opportunities(db_session)

    assert len(opportunities) == 3
    assert [item["rank"] for item in opportunities] == [1, 2, 3]
    assert {item["interval"] for item in opportunities} == {"1m", "5m", "15m"}
    assert all(item["dataset_id"].startswith("ds_bingx_ETH_USDT_") for item in opportunities)
    assert all(item["history_days"] > 0 for item in opportunities)
    assert len({item["daily_volatility_pct"] for item in opportunities}) == 3
    assert db_session.query(OpportunityMatrixModel).count() == 3


def test_one_invalid_required_dataset_blocks_the_whole_universe(
    db_session: Session, tmp_path: Path
) -> None:
    for interval in ("1m", "5m"):
        _register_dataset(
            db_session,
            tmp_path / interval,
            interval,
            _candles(interval, [100, 101, 102], [10, 11, 12]),
        )
    _register_dataset(
        db_session,
        tmp_path / "15m",
        "15m",
        _candles("15m", [100, 101, 102], [10, 11, 12]),
        corrupt_manifest_checksum=True,
    )

    scanner = UniverseScanner(minimum_history_days=0)

    assert scanner.scan_opportunities(db_session) == []
    assert any(
        "MANIFEST_CHECKSUM_MISMATCH" in rejection["errors"] for rejection in scanner.rejections
    )
    assert any(
        rejection.get("interval") == "15m"
        and "MISSING_REQUIRED_APPROVED_DATASET" in rejection["errors"]
        for rejection in scanner.rejections
    )


@pytest.mark.skipif(
    os.getenv("RUN_LIVE_BINGX_TESTS") != "1",
    reason="Set RUN_LIVE_BINGX_TESTS=1 to run the real BingX scanner gate.",
)
def test_scanner_with_real_bingx_ohlcv(db_session: Session, tmp_path: Path) -> None:
    client = BingXPyRestClient()
    for interval in ("1m", "5m", "15m"):
        step_ms = INTERVAL_MS[interval]
        received_ms = __import__("time").time_ns() // 1_000_000
        raw = client.get_klines("ETH-USDT", interval, limit=50)
        records = sorted(
            (
                {
                    "time": int(item["time"]),
                    "open": float(item["open"]),
                    "high": float(item["high"]),
                    "low": float(item["low"]),
                    "close": float(item["close"]),
                    "volume": float(item["volume"]),
                }
                for item in raw
                if int(item["time"]) + step_ms <= received_ms
            ),
            key=lambda item: int(item["time"]),
        )
        assert len(records) >= 40
        _register_dataset(db_session, tmp_path / interval, interval, records, dataset_suffix="live")

    scanner = UniverseScanner(minimum_history_days=0)
    opportunities = scanner.scan_opportunities(db_session)

    assert len(opportunities) == 3
    assert [item["rank"] for item in opportunities] == [1, 2, 3]
    assert all(item["median_turnover_per_minute"] > 0 for item in opportunities)
    assert all(item["daily_volatility_pct"] > 0 for item in opportunities)
