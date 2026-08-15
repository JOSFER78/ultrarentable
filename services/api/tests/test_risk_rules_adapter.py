from datetime import datetime, timedelta, timezone
import json

import pytest

from services.api.app.engine.risk_rules_adapter import (
    RiskRulesUnavailable,
    load_verified_bingx_risk_rules,
)
from services.api.app.db.database import InstrumentRuleSnapshotModel


NOW = datetime(2026, 8, 1, 12, tzinfo=timezone.utc)
HASH = "a" * 64


def test_rule_snapshot_schema_can_persist_complete_maintenance_tiers() -> None:
    assert "maintenance_tiers_json" in InstrumentRuleSnapshotModel.__table__.c


def rule_snapshot(**updates):
    value = {
        "symbol": "ETH-USDT",
        "captured_at": NOW - timedelta(minutes=10),
        "source_endpoint": "/verified/bingx/risk-limits",
        "raw_sha256": HASH,
        "max_leverage": 500,
        "maintenance_tiers_json": json.dumps(
            [
                {"maxNotional": 10_000, "maintenanceMarginRate": 0.004},
                {
                    "maxNotional": None,
                    "maintenanceMarginRate": 0.006,
                    "maintenanceAmount": 20,
                },
            ]
        ),
    }
    value.update(updates)
    return value


def fee_snapshot(**updates):
    value = {
        "symbol": "ETH-USDT",
        "captured_at": NOW - timedelta(minutes=5),
        "source_endpoint": "/openApi/swap/v2/user/commissionRate",
        "raw_sha256": "b" * 64,
        "taker_fee": 0.0005,
    }
    value.update(updates)
    return value


def test_complete_fresh_snapshots_build_500x_rules() -> None:
    result = load_verified_bingx_risk_rules(
        rule_snapshot(), fee_snapshot(), now=NOW
    )

    assert result.symbol == "ETH-USDT"
    assert result.max_leverage == 500
    assert result.taker_fee_rate == 0.0005
    assert len(result.maintenance_tiers) == 2


def test_legacy_flat_maintenance_rate_is_not_silently_used() -> None:
    snapshot = rule_snapshot(maintenance_tiers_json=None, maintenance_margin_rate=0.004)

    with pytest.raises(RiskRulesUnavailable, match="tiers are missing"):
        load_verified_bingx_risk_rules(snapshot, fee_snapshot(), now=NOW)


@pytest.mark.parametrize("target", ["rule", "fee"])
def test_stale_snapshot_fails_closed(target) -> None:
    rule = rule_snapshot()
    fee = fee_snapshot()
    if target == "rule":
        rule["captured_at"] = NOW - timedelta(days=2)
    else:
        fee["captured_at"] = NOW - timedelta(days=2)

    with pytest.raises(RiskRulesUnavailable, match="snapshot is stale"):
        load_verified_bingx_risk_rules(rule, fee, now=NOW)


def test_missing_checksum_fails_closed() -> None:
    with pytest.raises(RiskRulesUnavailable, match="raw_sha256"):
        load_verified_bingx_risk_rules(
            rule_snapshot(raw_sha256="bad"), fee_snapshot(), now=NOW
        )


def test_snapshot_from_the_future_fails_closed() -> None:
    with pytest.raises(RiskRulesUnavailable, match="captured_at is in the future"):
        load_verified_bingx_risk_rules(
            rule_snapshot(captured_at=NOW + timedelta(minutes=6)),
            fee_snapshot(),
            now=NOW,
        )


def test_fee_for_another_symbol_fails_closed() -> None:
    with pytest.raises(RiskRulesUnavailable, match="different symbol"):
        load_verified_bingx_risk_rules(
            rule_snapshot(), fee_snapshot(symbol="BTC-USDT"), now=NOW
        )
