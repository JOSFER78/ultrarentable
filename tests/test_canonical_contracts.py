"""Comprehensive Unit Tests for Canonical Contracts Package (Fase 1)."""

import pytest
from pydantic import ValidationError

from contracts import (
    ActionType,
    AssetClass,
    ASTEntryExitLogic,
    ASTIndicatorNode,
    ASTRuleCondition,
    BalaState,
    CanonicalStrategy,
    ComparisonOperator,
    ContractType,
    CostsConfig,
    EvidenceGateDecision,
    FondeoValidationCriteria,
    GateId,
    InstrumentConfig,
    IntrabarPolicy,
    IsolatedBullet,
    PropChallengeConfig,
    RiskSizingConfig,
    RouteType,
    SessionConfig,
    StrategyArchetype,
    StrategyStatus,
    UltraValidationCriteria,
    VaultRatchetConfig,
)


def _build_sample_canonical_strategy() -> CanonicalStrategy:
    return CanonicalStrategy(
        strategy_id="CS-SOL-5M-VOL-001",
        version="2.0.0",
        name="SOL High Volatility Expansion 5m",
        target_route="ULTRA",
        status=StrategyStatus.CANDIDATE,
        instrument=InstrumentConfig(
            symbol="SOL-USDT",
            exchange="BINGX",
            asset_class=AssetClass.CRYPTO_PERPETUAL,
            contract_type=ContractType.PERPETUAL,
            point_value=1.0,
            tick_size=0.01,
        ),
        timeframe="5m",
        session=SessionConfig(timezone="UTC", start_time="00:00", end_time="23:59", close_at_end=False),
        logic=ASTEntryExitLogic(
            archetype=StrategyArchetype.VOLATILITY_EXPANSION,
            long_entry_conditions=[
                ASTRuleCondition(
                    left_indicator=ASTIndicatorNode(name="ATR", timeframe="5m", period=14),
                    operator=ComparisonOperator.GREATER_THAN,
                    threshold_value=1.2,
                )
            ],
            stop_loss_atr_mult=1.5,
            take_profit_atr_mult=4.0,
            pyramiding_tiers=3,
        ),
        risk_sizing=RiskSizingConfig(
            method="CAPITAL_COMPOUND",
            risk_per_trade_pct=5.0,
            max_leverage=50.0,
            margin_reinvest_pct=80.0,
        ),
        costs=CostsConfig(
            maker_fee_bps=0.0002,
            taker_fee_bps=0.0005,
            spread_ticks=1.0,
            slippage_ticks=0.5,
        ),
    )


def test_canonical_strategy_immutability():
    """Verify CanonicalStrategy enforces frozen immutability."""
    strat = _build_sample_canonical_strategy()
    with pytest.raises(ValidationError):
        strat.target_route = "FONDEO"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        strat.instrument.symbol = "BTC-USDT"  # type: ignore[misc]


def test_canonical_strategy_provenance_hash():
    """Verify deterministic SHA-256 computation."""
    strat1 = _build_sample_canonical_strategy()
    strat2 = _build_sample_canonical_strategy()
    
    hash1 = strat1.compute_provenance_hash()
    hash2 = strat2.compute_provenance_hash()
    
    assert hash1 == hash2
    assert len(hash1) == 64
    
    strat_with_hash = strat1.with_provenance_hash()
    assert strat_with_hash.provenance_hash == hash1


def test_canonical_strategy_json_roundtrip():
    """Verify lossless serialization and deserialization."""
    strat = _build_sample_canonical_strategy().with_provenance_hash()
    json_data = strat.model_dump_json()
    reloaded = CanonicalStrategy.model_validate_json(json_data)
    
    assert reloaded.strategy_id == strat.strategy_id
    assert reloaded.instrument.symbol == "SOL-USDT"
    assert reloaded.logic.archetype == StrategyArchetype.VOLATILITY_EXPANSION
    assert reloaded.provenance_hash == strat.provenance_hash


def test_validation_criteria_fondeo_and_ultra():
    """Verify Fondeo and Ultra decoupled validation criteria."""
    fondeo = FondeoValidationCriteria()
    assert fondeo.max_trailing_dd_pct == 4.0
    assert fondeo.require_eod_flatten is True
    assert fondeo.max_single_day_profit_share_pct == 40.0
    
    ultra = UltraValidationCriteria()
    assert ultra.min_annualized_roi_pct == 100.0
    assert ultra.min_asymmetric_payoff == 3.0
    assert ultra.disallow_account_bust is True


def test_evidence_gate_decision_structure():
    """Verify gate decision structure and scores."""
    decision = EvidenceGateDecision(
        gate_id=GateId.GATE_2_OUT_OF_SAMPLE,
        passed=True,
        score=92.5,
        reason="OOS Profit Factor 1.65 exceeds minimum target 1.35",
        metrics={"oos_profit_factor": 1.65, "oos_trades": 38},
    )
    assert decision.passed is True
    assert decision.gate_id == GateId.GATE_2_OUT_OF_SAMPLE
    assert decision.score == 92.5


def test_portfolio_isolated_bullet_and_bala_states():
    """Verify BalaState enum contains all 6 canonical states."""
    expected_states = {"SEEDED", "ACTIVE", "RUNNER", "HARVESTING", "RECYCLE_PROFIT", "STOPPED"}
    actual_states = {s.value for s in BalaState}
    assert expected_states == actual_states

    bullet = IsolatedBullet(
        bullet_id="BALA-SOL-001",
        parent_vault_id="VAULT_MAIN_01",
        allocated_capital_usd=2500.0,
        current_equity_usd=5200.0,
        peak_equity_usd=5200.0,
        state=BalaState.RUNNER,
    )
    assert bullet.allocated_capital_usd == 2500.0
    assert bullet.state == BalaState.RUNNER


def test_vault_ratchet_and_prop_challenge_config():
    """Verify VaultRatchet and PropChallenge configurations."""
    vault = VaultRatchetConfig()
    assert vault.bullet_allocation_pct == 5.0
    assert vault.profit_harvest_threshold_roi_pct == 200.0

    prop = PropChallengeConfig(
        challenge_id="APEX-50K-001",
        prop_firm_name="Apex Trader Funding",
    )
    assert prop.account_size_usd == 50000.0
    assert prop.target_profit_usd == 3000.0
    assert prop.trailing_max_dd_usd == 2000.0
