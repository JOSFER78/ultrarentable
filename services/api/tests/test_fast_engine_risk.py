from __future__ import annotations

import hashlib
import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.api.app.db.database import Base, DatasetModel, InstrumentModel
from services.api.app.engine.fast_engine import FastEngine
from services.api.app.factory.seed_factory import SeedFactory


def _engine(tmp_path, candles):
    path = tmp_path / "candles.json"
    raw = json.dumps(candles, separators=(",", ":")).encode()
    path.write_bytes(raw)
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add(InstrumentModel(
        symbol="ETH-USDT",
        asset="ETH",
        currency="USDT",
        maker_fee_rate=0.0,
        taker_fee_rate=0.0,
        status=1,
    ))
    session.add(DatasetModel(
        dataset_id="risk-test",
        venue="BINGX",
        symbol="ETH-USDT",
        feed_type="CANDLES",
        interval="15m",
        start_time=candles[0]["time"],
        end_time=candles[-1]["time"],
        record_count=len(candles),
        gap_count=0,
        duplicate_count=0,
        out_of_order_count=0,
        coverage_pct=100.0,
        checksum_sha256=hashlib.sha256(raw).hexdigest(),
        status="APPROVED",
        file_path=str(path),
        manifest_path=str(tmp_path / "unused.json"),
    ))
    session.commit()
    return FastEngine(session, allow_legacy_risk=True), session


def _constant_signal(value: bool):
    return {
        "nodeType": "COMPARISON",
        "op": "GT",
        "left": {"type": "CONSTANT", "value": 2.0 if value else 0.0},
        "right": {"type": "CONSTANT", "value": 1.0},
    }


def _strategy(*, exit_signal: bool, leverage: int = 1):
    strategy = SeedFactory(seed=10).create_template_strategy(0, timeframe="15m")
    strategy["signals"] = {
        "longEntry": _constant_signal(True),
        "shortEntry": _constant_signal(False),
        "longExit": _constant_signal(exit_signal),
        "shortExit": _constant_signal(False),
    }
    strategy["position"]["leverage"] = leverage
    strategy["position"]["allocationPct"] = 25.0
    return strategy


def test_same_bar_stop_wins_ambiguous_stop_and_target(tmp_path) -> None:
    candles = [
        {"time": 0, "open": 100, "high": 101, "low": 99, "close": 100, "volume": 1},
        {"time": 900000, "open": 100, "high": 106, "low": 94, "close": 100, "volume": 1},
        {"time": 1800000, "open": 100, "high": 101, "low": 99, "close": 100, "volume": 1},
    ]
    engine, session = _engine(tmp_path, candles)
    try:
        result = engine.run_backtest(
            _strategy(exit_signal=False),
            dataset_id="risk-test",
            persist_artifacts=False,
        )
        assert result["trades"][0]["exit_reason"] == "STOP_LOSS"
        # Trailing 1.5% is tighter than the fixed 2% stop at entry.
        assert result["trades"][0]["exit_price"] == 98.5
        assert list(engine._dataset_cache) == ["risk-test"]
    finally:
        session.close()


def test_pending_open_exit_precedes_current_bar_liquidation(tmp_path) -> None:
    candles = [
        {"time": 0, "open": 100, "high": 101, "low": 99, "close": 100, "volume": 1},
        {"time": 900000, "open": 100, "high": 101, "low": 99, "close": 100, "volume": 1},
        {"time": 1800000, "open": 100, "high": 101, "low": 80, "close": 90, "volume": 1},
    ]
    engine, session = _engine(tmp_path, candles)
    strategy = _strategy(exit_signal=True, leverage=20)
    strategy["position"]["riskManagement"] = {
        "stopLossPct": 50.0,
        "takeProfitPct": 500.0,
        "trailingStopPct": None,
        "maxHoldingBars": 200,
    }
    try:
        result = engine.run_backtest(
            strategy,
            dataset_id="risk-test",
            persist_artifacts=False,
        )
        assert result["trades"][0]["exit_reason"] == "SIGNAL"
        assert result["trades"][0]["exit_price"] == 100.0
        assert result["liquidated"] is False
    finally:
        session.close()
