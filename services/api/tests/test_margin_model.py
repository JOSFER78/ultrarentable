import math

import pytest

from services.api.app.engine.margin_model import (
    BingXIsolatedMarginModel,
    BingXMarketRiskRules,
    IsolatedPosition,
    MaintenanceTier,
    MarginModelError,
    PositionSide,
)


def rules(*, max_leverage=500, maintenance_rate=0.004, taker_fee=0.0005):
    return BingXMarketRiskRules(
        symbol="ETH-USDT",
        max_leverage=max_leverage,
        taker_fee_rate=taker_fee,
        maintenance_tiers=(MaintenanceTier(math.inf, maintenance_rate),),
    )


def test_500x_is_supported_but_rejected_if_initial_margin_cannot_cover_risk() -> None:
    model = BingXIsolatedMarginModel(rules(max_leverage=500))
    position = IsolatedPosition(PositionSide.LONG, 2_000, 1, 500)

    result = model.assess(position, mark_price=2_000, last_price=2_000)

    assert position.position_margin == 4.0
    assert result.mark.required_margin == 9.0
    assert result.executable_at_entry is False
    assert result.liquidated is False
    assert result.reason == "INSUFFICIENT_INITIAL_MARGIN"


def test_200x_can_remain_executable_under_the_same_verified_rules() -> None:
    model = BingXIsolatedMarginModel(rules(max_leverage=500))
    position = IsolatedPosition(PositionSide.LONG, 2_000, 1, 200)

    result = model.assess(position, mark_price=2_000, last_price=2_000)

    assert position.position_margin == 10.0
    assert result.mark.required_margin == 9.0
    assert result.executable_at_entry is True
    assert result.liquidated is False


def test_dual_price_requires_both_mark_and_last_to_cross_threshold() -> None:
    model = BingXIsolatedMarginModel(rules(max_leverage=100))
    position = IsolatedPosition(PositionSide.LONG, 2_000, 1, 100)

    only_mark = model.assess(position, mark_price=1_988, last_price=1_995)
    both = model.assess(position, mark_price=1_988, last_price=1_988)

    assert only_mark.mark.threshold_reached is True
    assert only_mark.last.threshold_reached is False
    assert only_mark.liquidated is False
    assert both.liquidated is True
    assert both.reason == "DUAL_PRICE_LIQUIDATION"


def test_short_position_liquidates_when_both_prices_rise() -> None:
    model = BingXIsolatedMarginModel(rules(max_leverage=100))
    position = IsolatedPosition(PositionSide.SHORT, 2_000, 1, 100)

    result = model.assess(position, mark_price=2_012, last_price=2_012)

    assert result.mark.unrealized_pnl == -12.0
    assert result.liquidated is True


def test_funding_is_deducted_before_liquidation_risk_is_evaluated() -> None:
    model = BingXIsolatedMarginModel(rules(max_leverage=100))
    position = IsolatedPosition(
        PositionSide.LONG,
        2_000,
        1,
        100,
        funding_paid=12.0,
    )

    result = model.assess(position, mark_price=2_000, last_price=2_000)

    assert result.executable_at_entry is True
    assert result.mark.remaining_margin == 8.0
    assert result.mark.required_margin == 9.0
    assert result.liquidated is True
    assert result.reason == "DUAL_PRICE_LIQUIDATION"


def test_maintenance_amount_and_notional_tier_are_applied() -> None:
    market_rules = BingXMarketRiskRules(
        symbol="ETH-USDT",
        max_leverage=100,
        taker_fee_rate=0.0005,
        maintenance_tiers=(
            MaintenanceTier(10_000, 0.004),
            MaintenanceTier(math.inf, 0.006, maintenance_amount=20),
        ),
    )
    model = BingXIsolatedMarginModel(market_rules)
    position = IsolatedPosition(PositionSide.LONG, 2_000, 10, 10)

    result = model.assess(position, mark_price=2_000, last_price=2_000)

    assert result.mark.maintenance_margin == 100.0
    assert result.mark.closing_fee == 10.0


def test_campaign_tiers_are_filtered_by_market_cap_and_entry_feasibility() -> None:
    model = BingXIsolatedMarginModel(rules(max_leverage=500))

    filtered = model.executable_leverages(
        [1, 20, 100, 125, 150, 200, 500],
        entry_price=2_000,
        quantity=1,
    )

    assert filtered == (1, 20, 100, 125, 150, 200)


def test_leverage_above_verified_market_max_fails_closed() -> None:
    model = BingXIsolatedMarginModel(rules(max_leverage=125))

    with pytest.raises(MarginModelError, match="exceeds verified"):
        model.assess(
            IsolatedPosition(PositionSide.LONG, 2_000, 1, 150),
            mark_price=2_000,
            last_price=2_000,
        )


def test_notional_above_verified_tiers_is_rejected() -> None:
    market_rules = BingXMarketRiskRules(
        symbol="ETH-USDT",
        max_leverage=100,
        taker_fee_rate=0.0005,
        maintenance_tiers=(MaintenanceTier(10_000, 0.004),),
    )
    with pytest.raises(MarginModelError, match="no maintenance tier"):
        market_rules.tier_for(10_001)


def test_tier_specific_max_leverage_depends_on_position_notional() -> None:
    market_rules = BingXMarketRiskRules(
        symbol="ETH-USDT",
        max_leverage=150,
        taker_fee_rate=0.0005,
        maintenance_tiers=(
            MaintenanceTier(300_000, 0.003167, max_leverage=150),
            MaintenanceTier(3_000_000, 0.0032, 10.0, max_leverage=125),
        ),
    )
    model = BingXIsolatedMarginModel(market_rules)
    small = model.assess(
        IsolatedPosition(PositionSide.LONG, 2_000, 1, 147),
        mark_price=2_000,
        last_price=2_000,
    )
    large = model.assess(
        IsolatedPosition(PositionSide.LONG, 2_000, 200, 147),
        mark_price=2_000,
        last_price=2_000,
    )
    assert small.executable_at_entry is True
    assert large.executable_at_entry is False
    assert large.reason == "TIER_LEVERAGE_EXCEEDED"
