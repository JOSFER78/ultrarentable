from __future__ import annotations

from datetime import UTC, datetime

from services.api.app.ingestion.eth_pipeline import (
    DAY_MS,
    SOURCE_STEP_MS,
    fetch_closed_eth_minutes,
    resample_minutes,
)


class FakeBingXClient:
    def __init__(self, records: list[dict[str, object]]) -> None:
        self.records = records
        self.calls: list[int] = []

    def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int,
        end_time: int | None = None,
    ) -> list[dict[str, object]]:
        assert symbol == "ETH-USDT"
        assert interval == "1m"
        assert end_time is not None
        self.calls.append(end_time)
        eligible = [row for row in self.records if int(row["time"]) <= end_time]
        return list(reversed(eligible[-limit:]))


def _rows(days: int, last_closed: int) -> list[dict[str, object]]:
    first = last_closed - days * DAY_MS + SOURCE_STEP_MS
    return [
        {
            "time": first + index * SOURCE_STEP_MS,
            "open": "100",
            "high": "102",
            "low": "99",
            "close": str(100 + (index % 2)),
            "volume": "3",
        }
        for index in range(days * 1440)
    ]


def test_paginated_fetch_is_complete_sorted_and_closed() -> None:
    now_ms = int(datetime(2026, 8, 1, tzinfo=UTC).timestamp() * 1000)
    last_closed = now_ms - SOURCE_STEP_MS
    client = FakeBingXClient(_rows(2, last_closed))

    records, raw, audit = fetch_closed_eth_minutes(client, days=2, now_ms=now_ms)

    assert len(records) == 2880
    assert len(raw) == 2880
    assert len(audit["pages"]) == 2
    assert len(client.calls) == 2
    assert records[0]["time"] < records[-1]["time"]
    assert records[-1]["time"] == last_closed


def test_resampling_uses_real_minute_ohlcv() -> None:
    now_ms = int(datetime(2026, 8, 1, tzinfo=UTC).timestamp() * 1000)
    rows = _rows(1, now_ms - SOURCE_STEP_MS)
    minutes = [
        {
            "time": int(row["time"]),
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "volume": float(row["volume"]),
        }
        for row in rows
    ]

    five_minutes = resample_minutes(minutes, "5m")
    one_hour = resample_minutes(minutes, "1h")

    assert len(five_minutes) == 288
    assert len(one_hour) == 24
    assert five_minutes[0]["open"] == minutes[0]["open"]
    assert five_minutes[0]["close"] == minutes[4]["close"]
    assert five_minutes[0]["volume"] == 15.0
