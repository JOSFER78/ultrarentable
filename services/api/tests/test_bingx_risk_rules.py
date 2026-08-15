from __future__ import annotations

import hashlib
import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.api.app.db.database import (
    AccountFeeSnapshotModel,
    Base,
    InstrumentRuleSnapshotModel,
)
from services.api.app.ingestion.bingx_risk_rules import (
    BingXRiskCaptureError,
    normalize_margin_payload,
    normalize_public_contract_fees,
    persist_public_fee_snapshot,
    persist_risk_snapshot,
)


def payload(tiers: str):
    return {"code": 0, "msg": "", "data": {"maintenanceTiered": tiers}}


def test_parser_preserves_arbitrary_dynamic_leverages_and_tier_amounts() -> None:
    rules = normalize_margin_payload(
        payload("0-300000:0.003167:150:0;300000-3000000:0.0032:125:10"),
        "ETH-USDT",
    )
    assert rules.max_leverage == 150
    assert rules.maintenance_tiers[0]["max_leverage"] == 150
    assert rules.maintenance_tiers[1]["max_leverage"] == 125
    assert rules.maintenance_tiers[1]["maintenance_amount"] == 10.0


def test_exchange_max_above_product_cap_is_clamped_to_500() -> None:
    rules = normalize_margin_payload(payload("0-1000000:0.001:1000:0"), "XAU-USDT")
    assert rules.max_leverage == 500
    assert rules.maintenance_tiers[0]["max_leverage"] == 500


def test_non_contiguous_or_malformed_tiers_fail_closed() -> None:
    with pytest.raises(BingXRiskCaptureError, match="contiguous"):
        normalize_margin_payload(
            payload("0-300000:0.003:150:0;400000-500000:0.004:100:1"),
            "ETH-USDT",
        )
    with pytest.raises(BingXRiskCaptureError, match="malformed"):
        normalize_margin_payload(payload("broken"), "ETH-USDT")


def test_persistence_is_checksummed_and_keeps_complete_tiers(tmp_path) -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    try:
        rules = normalize_margin_payload(
            payload("0-300000:0.003167:150:0;300000-3000000:0.0032:125:10"),
            "ETH-USDT",
        )
        snapshot = persist_risk_snapshot(db, rules, raw_dir=tmp_path)
        stored = db.get(InstrumentRuleSnapshotModel, snapshot.snapshot_id)
        assert stored is not None
        assert stored.max_leverage == 150
        assert len(json.loads(stored.maintenance_tiers_json)) == 2
        raw = (tmp_path / f"{snapshot.snapshot_id}.json").read_bytes()
        assert hashlib.sha256(raw).hexdigest() == stored.raw_sha256
    finally:
        db.close()


def test_public_default_fees_are_distinct_checksummed_provenance(tmp_path) -> None:
    fees = normalize_public_contract_fees(
        {
            "symbol": "ETH-USDT",
            "makerFeeRate": 0.0002,
            "takerFeeRate": 0.0005,
        },
        "ETH-USDT",
    )
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    try:
        snapshot = persist_public_fee_snapshot(db, fees, raw_dir=tmp_path)
        stored = db.get(AccountFeeSnapshotModel, snapshot.snapshot_id)
        assert stored is not None
        assert stored.account_hash == "PUBLIC_DEFAULT"
        assert stored.taker_fee == 0.0005
        assert len(stored.raw_sha256) == 64
    finally:
        db.close()
