"""Mandatory tests for Phase E — FAST Engine Determinista Real."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from services.api.app.db.database import (
    Base,
    DatasetModel,
    InstrumentModel,
    StrategyModel,
    engine as db_engine,
    get_db,
    init_db,
)
from services.api.app.dsl.engine import StrategyDSL, compile_to_ir, canonical_hash
from services.api.app.engine.fast_engine import FastEngine, FastEngineException


@pytest.fixture(scope="module")
def db_session() -> Session:
    init_db()
    session = Session(bind=db_engine)
    yield session
    session.close()


def _make_valid_dsl() -> dict:
    return {
        "dslVersion": "1.0.0",
        "metadata": {
            "name": "Fast Test Strategy",
            "family": "breakout",
            "parents": [],
            "origin": "MANUAL",
        },
        "market": {
            "venue": "BINGX",
            "symbol": "ETH-USDT",
            "timeframe": "1h",
        },
        "signals": {
            "longEntry": {
                "nodeType": "COMPARISON",
                "op": "GT",
                "left": {"type": "SERIES", "series": "CLOSE", "offset": 0},
                "right": {
                    "type": "INDICATOR",
                    "indicator": "EMA",
                    "source": {"type": "SERIES", "series": "CLOSE", "offset": 0},
                    "params": {"period": 5},
                    "offset": 0,
                },
            },
            "shortEntry": {
                "nodeType": "COMPARISON",
                "op": "LT",
                "left": {"type": "SERIES", "series": "CLOSE", "offset": 0},
                "right": {
                    "type": "INDICATOR",
                    "indicator": "EMA",
                    "source": {"type": "SERIES", "series": "CLOSE", "offset": 0},
                    "params": {"period": 5},
                    "offset": 0,
                },
            },
            "longExit": {
                "nodeType": "COMPARISON",
                "op": "CROSS_BELOW",
                "left": {"type": "SERIES", "series": "CLOSE", "offset": 0},
                "right": {
                    "type": "INDICATOR",
                    "indicator": "SMA",
                    "source": {"type": "SERIES", "series": "CLOSE", "offset": 0},
                    "params": {"period": 10},
                    "offset": 0,
                },
            },
            "shortExit": {
                "nodeType": "COMPARISON",
                "op": "CROSS_ABOVE",
                "left": {"type": "SERIES", "series": "CLOSE", "offset": 0},
                "right": {
                    "type": "INDICATOR",
                    "indicator": "SMA",
                    "source": {"type": "SERIES", "series": "CLOSE", "offset": 0},
                    "params": {"period": 10},
                    "offset": 0,
                },
            },
        },
        "position": {
            "marginMode": "ISOLATED",
            "leverage": 5,
            "allocationPct": 100.0,
            "compound": True,
            "pyramiding": {"enabled": False, "maxEntries": 1},
        },
        "execution": {
            "entryOrderType": "MARKET",
            "exitOrderType": "MARKET",
            "signalTiming": "BAR_CLOSE_EXECUTE_NEXT_OPEN",
        },
    }


def test_missing_fee_snapshot_throws_exception(db_session: Session) -> None:
    """Missing fee snapshot for symbol must raise MISSING_FEE_SNAPSHOT exception."""
    # Ensure ETH-USDT has missing fees
    db_session.query(InstrumentModel).filter(InstrumentModel.symbol == "ETH-USDT").delete()
    db_session.commit()

    dsl = StrategyDSL(**_make_valid_dsl())
    ir = compile_to_ir(dsl)
    engine = FastEngine(db_session, allow_legacy_risk=True)

    # Select the active approved dataset compatible with the strategy fixture.
    dataset = (
        db_session.query(DatasetModel)
        .filter(
            DatasetModel.symbol == dsl.market.symbol,
            DatasetModel.interval == dsl.market.timeframe,
            DatasetModel.status == "APPROVED",
        )
        .first()
    )
    assert dataset is not None, "Approved active dataset matching strategy market required"
    ds_id = dataset.dataset_id

    with pytest.raises(FastEngineException) as exc_info:
        engine.execute(strategy_dsl=dsl, compiled_ir=ir, dataset_id=ds_id)

    assert exc_info.value.code == "MISSING_FEE_SNAPSHOT"


def test_fast_engine_execution_reproducibility(db_session: Session) -> None:
    """Fast Engine must produce identical results and checksums on identical execution."""
    from datetime import datetime, timezone
    from services.api.app.db.database import InstrumentRuleSnapshotModel, AccountFeeSnapshotModel

    import json
    # Refresh snapshot timestamps and provenance fields so rule validation passes in test environment
    now_utc = datetime.now(timezone.utc)
    tiers_json = json.dumps([
        {"max_notional": 300000, "maintenance_margin_rate": 0.003167, "maintenance_amount": 0, "max_leverage": 150}
    ])
    for row in db_session.query(InstrumentRuleSnapshotModel).all():
        row.captured_at = now_utc
        if not row.source_endpoint:
            row.source_endpoint = "/api/v1/quote/contract/marginTiered/get"
        if not row.raw_sha256 or len(row.raw_sha256) != 64:
            row.raw_sha256 = "a" * 64
        if not row.maintenance_tiers_json:
            row.maintenance_tiers_json = tiers_json
        if not row.max_leverage:
            row.max_leverage = 150
        if not row.maintenance_margin_rate:
            row.maintenance_margin_rate = 0.003167
    for row in db_session.query(AccountFeeSnapshotModel).all():
        row.captured_at = now_utc
        if not row.source_endpoint:
            row.source_endpoint = "/openApi/swap/v2/quote/contracts"
        if not row.raw_sha256 or len(row.raw_sha256) != 64:
            row.raw_sha256 = "b" * 64

    # Insert real fee snapshot for ETH-USDT
    db_session.merge(
        InstrumentModel(
            symbol="ETH-USDT",
            asset="ETH",
            currency="USDT",
            maker_fee_rate=0.0002,
            taker_fee_rate=0.0005,
            status=1,
        )
    )
    db_session.commit()

    dsl = StrategyDSL(**_make_valid_dsl())
    ir = compile_to_ir(dsl)
    engine = FastEngine(db_session)

    dataset = (
        db_session.query(DatasetModel)
        .filter(
            DatasetModel.symbol == dsl.market.symbol,
            DatasetModel.interval == dsl.market.timeframe,
            DatasetModel.status == "APPROVED",
        )
        .first()
    )
    assert dataset is not None, "Approved active dataset matching strategy market required"
    ds_id = dataset.dataset_id

    res_1 = engine.execute(strategy_dsl=dsl, compiled_ir=ir, dataset_id=ds_id, initial_capital=10000.0)
    res_2 = engine.execute(strategy_dsl=dsl, compiled_ir=ir, dataset_id=ds_id, initial_capital=10000.0)

    assert res_1["checksum"] == res_2["checksum"]
    assert res_1["metrics"]["final_equity"] == res_2["metrics"]["final_equity"]
    assert res_1["engineType"] == "FAST_APPROXIMATE"
    assert res_1["engineType"] != "CANONICAL"


def test_unapproved_dataset_rejected(db_session: Session) -> None:
    """Unapproved datasets must be rejected."""
    dsl = StrategyDSL(**_make_valid_dsl())
    ir = compile_to_ir(dsl)
    engine = FastEngine(db_session)

    # Insert fake unapproved dataset
    db_session.merge(
        DatasetModel(
            dataset_id="ds_unapproved_test",
            venue="BINGX",
            symbol="ETH-USDT",
            feed_type="kline_1h",
            interval="1h",
            start_time=1700000000000,
            end_time=1700003600000,
            record_count=10,
            checksum_sha256="fake",
            status="VALIDATING",
            file_path="data/normalized/fake.json",
            manifest_path="data/normalized/fake_manifest.json",
        )
    )
    db_session.commit()

    with pytest.raises(FastEngineException) as exc_info:
        engine.execute(strategy_dsl=dsl, compiled_ir=ir, dataset_id="ds_unapproved_test")

    assert exc_info.value.code == "DATASET_NOT_APPROVED"
