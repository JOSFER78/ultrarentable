from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.api.app.db.database import (
    AccountFeeSnapshotModel,
    Base,
    DatasetModel,
    InstrumentRuleSnapshotModel,
)
from services.api.app.engine.fast_engine import FastEngine, FastEngineException
from services.api.app.factory.seed_factory import SeedFactory


def constant_signal(value: bool):
    return {
        "nodeType": "COMPARISON",
        "op": "GT",
        "left": {"type": "CONSTANT", "value": 2.0 if value else 0.0},
        "right": {"type": "CONSTANT", "value": 1.0},
    }


def build_engine(tmp_path, *, with_rules: bool = True):
    candles = [
        {"time": index * 900_000, "open": 100, "high": 101, "low": 99, "close": 100, "volume": 1}
        for index in range(5)
    ]
    raw = json.dumps(candles, separators=(",", ":")).encode()
    path = tmp_path / "candles.json"
    path.write_bytes(raw)
    sql_engine = create_engine("sqlite://")
    Base.metadata.create_all(sql_engine)
    db = sessionmaker(bind=sql_engine)()
    db.add(
        DatasetModel(
            dataset_id="verified-risk",
            venue="BINGX",
            symbol="ETH-USDT",
            feed_type="CANDLES",
            interval="15m",
            start_time=0,
            end_time=3_600_000,
            record_count=len(candles),
            gap_count=0,
            duplicate_count=0,
            out_of_order_count=0,
            coverage_pct=100.0,
            checksum_sha256=hashlib.sha256(raw).hexdigest(),
            status="APPROVED",
            file_path=str(path),
            manifest_path=str(tmp_path / "manifest.json"),
        )
    )
    if with_rules:
        now = datetime.now(timezone.utc)
        db.add(
            InstrumentRuleSnapshotModel(
                snapshot_id="risk-current",
                symbol="ETH-USDT",
                captured_at=now,
                source_endpoint="/api/v1/quote/contract/marginTiered/get",
                raw_path=str(tmp_path / "risk.json"),
                raw_sha256="a" * 64,
                max_leverage=150,
                maintenance_margin_rate=0.003167,
                maintenance_tiers_json=json.dumps(
                    [
                        {
                            "max_notional": 300_000,
                            "maintenance_margin_rate": 0.003167,
                            "maintenance_amount": 0,
                            "max_leverage": 150,
                        },
                        {
                            "max_notional": 3_000_000,
                            "maintenance_margin_rate": 0.0032,
                            "maintenance_amount": 10,
                            "max_leverage": 125,
                        },
                    ]
                ),
            )
        )
        db.add(
            AccountFeeSnapshotModel(
                snapshot_id="fee-current",
                account_hash="PUBLIC_DEFAULT",
                symbol="ETH-USDT",
                maker_fee=0.0002,
                taker_fee=0.0005,
                captured_at=now,
                source_endpoint="/openApi/swap/v2/quote/contracts",
                raw_path=str(tmp_path / "fee.json"),
                raw_sha256="b" * 64,
            )
        )
    db.commit()
    return FastEngine(db), db


def strategy(*, leverage: int = 100, allocation: float = 1.0, margin_mode: str = "ISOLATED"):
    value = SeedFactory(seed=12).create_template_strategy(0, timeframe="15m")
    value["signals"] = {
        "longEntry": constant_signal(True),
        "shortEntry": constant_signal(False),
        "longExit": constant_signal(True),
        "shortExit": constant_signal(False),
    }
    value["position"]["leverage"] = leverage
    value["position"]["allocationPct"] = allocation
    value["position"]["marginMode"] = margin_mode
    return value


def test_strict_engine_fails_closed_without_verified_snapshots(tmp_path) -> None:
    engine, db = build_engine(tmp_path, with_rules=False)
    try:
        with pytest.raises(FastEngineException) as caught:
            engine.run_backtest(strategy(), dataset_id="verified-risk", persist_artifacts=False)
        assert caught.value.code == "MISSING_VERIFIED_RISK_RULES"
    finally:
        db.close()


def test_strict_engine_reports_verified_rules_and_executes(tmp_path) -> None:
    engine, db = build_engine(tmp_path)
    try:
        result = engine.run_backtest(strategy(), dataset_id="verified-risk", persist_artifacts=False)
        assert result["riskRules"]["mode"] == "VERIFIED_BINGX_TIERED"
        assert result["riskRules"]["maxLeverage"] == 150
        assert result["riskRules"]["tierCount"] == 2
        assert result["tradesCount"] > 0
    finally:
        db.close()


def test_strict_engine_rejects_leverage_above_current_eth_cap(tmp_path) -> None:
    engine, db = build_engine(tmp_path)
    try:
        result = engine.run_backtest(
            strategy(leverage=151), dataset_id="verified-risk", persist_artifacts=False
        )
        assert result["tradesCount"] == 0
        assert result["riskRules"]["entryRejections"] > 0
    finally:
        db.close()


def test_cross_margin_fails_closed_until_portfolio_model_exists(tmp_path) -> None:
    engine, db = build_engine(tmp_path)
    try:
        with pytest.raises(FastEngineException) as caught:
            engine.run_backtest(
                strategy(margin_mode="CROSS"),
                dataset_id="verified-risk",
                persist_artifacts=False,
            )
        assert caught.value.code == "CROSS_MARGIN_MODEL_PENDING"
    finally:
        db.close()
