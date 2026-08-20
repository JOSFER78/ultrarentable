"""Unit tests for Pydantic V2 Canonical Contracts (Fase 1)."""

import pytest
from pydantic import ValidationError

from contracts import (
    CanonicalStrategy,
    StrategyLifecycleStatus,
    ExecutionTrack,
    TargetInstrument,
    RuleTree,
    RuleCondition,
    IndicatorSpec,
    ExitModel,
    SizingAndRisk,
    SessionWindow,
    ProvenanceMetadata,
    FondeoValidationCriteria,
    FondeoValidationResult,
    UltraValidationCriteria,
    UltraValidationResult,
    ValidationTrack,
    BalaState,
    BalaExecutionRecord,
    EvidenceGateDecision,
    BacktestRequest,
    BacktestResult,
    EngineType,
    DatasetSnapshot,
    TradeLog,
    PortfolioRequest,
    PortfolioAllocation,
    AssetWeight,
    AllocationMethod,
    IsolatedBullet,
    BulletTradeDirection,
    VaultRatchetConfig,
    PropChallengeConfig,
)


def create_sample_strategy() -> CanonicalStrategy:
    return CanonicalStrategy(
        strategy_id="UR-CANON-001",
        name="NQ Momentum Breakout H1",
        target_track=ExecutionTrack.TRACK_FONDEO,
        status=StrategyLifecycleStatus.GENERATED,
        instrument=TargetInstrument(
            symbol="NQ",
            exchange="CME",
            contract_type="FUTURES",
            point_value=20.0,
            tick_size=0.25,
        ),
        timeframe="1h",
        session=SessionWindow(
            timezone="America/New_York",
            start_time="09:30",
            end_time="16:00",
            force_close_at_end=True,
        ),
        rules=RuleTree(
            long_conditions=[
                RuleCondition(
                    left_indicator=IndicatorSpec(name="RSI", timeframe="1h", period=14),
                    operator="GREATER_THAN",
                    threshold_value=50.0,
                )
            ]
        ),
        exits=ExitModel(stop_loss_ticks=20, take_profit_ticks=60),
        sizing_and_risk=SizingAndRisk(base_risk_pct=1.0, max_contracts_or_lots=4.0),
        provenance=ProvenanceMetadata(
            source_engine="strategyquant",
            project_name="Ultra_Auto_Pilot",
            databank_name="Results",
            build_id="build_001",
            created_timestamp_utc=1771437600000,
            author_or_agent="SQX_MCP_BRIDGE",
        ),
    )


def test_canonical_strategy_creation_and_immutability():
    """Verify CanonicalStrategy builds cleanly and enforces immutability (frozen)."""
    strategy = create_sample_strategy()
    assert strategy.strategy_id == "UR-CANON-001"
    assert strategy.instrument.symbol == "NQ"
    assert strategy.session.force_close_at_end is True

    # Check hash is deterministic
    h1 = strategy.compute_sha256()
    h2 = strategy.compute_sha256()
    assert h1 == h2
    assert len(h1) == 64

    # Verify immutability
    with pytest.raises(ValidationError):
        strategy.name = "Mutated Strategy Name"  # type: ignore


def test_canonical_strategy_json_roundtrip():
    """Verify serialization to JSON and deserialization maintains exact equality."""
    strategy = create_sample_strategy()
    json_str = strategy.model_dump_json()
    recovered = CanonicalStrategy.model_validate_json(json_str)

    assert recovered.strategy_id == strategy.strategy_id
    assert recovered.compute_sha256() == strategy.compute_sha256()


def test_fondeo_validation_contracts():
    """Verify Fondeo criteria and result models."""
    criteria = FondeoValidationCriteria(
        min_sharpe=2.0,
        min_deflated_sharpe=2.0,
        max_drawdown_pct=4.5,
        max_daily_loss_limit_usd=1000.0,
    )
    assert criteria.min_sharpe == 2.0

    result = FondeoValidationResult(
        strategy_id="UR-CANON-001",
        passed=True,
        sharpe_ratio=2.45,
        deflated_sharpe_ratio=2.15,
        max_drawdown_pct=3.8,
        daily_loss_limit_violations=0,
        ruin_probability_pct=0.00,
        walk_forward_efficiency=0.85,
        top2_outlier_dependency_pct=12.0,
        consistency_score=88.0,
    )
    assert result.passed is True
    assert result.track == ValidationTrack.TRACK_FONDEO


def test_ultra_validation_contracts():
    """Verify Ultra criteria and execution records."""
    criteria = UltraValidationCriteria(
        min_payoff_ratio=3.0,
        min_expected_r_per_bala=0.20,
        min_tail_gain_ratio=0.60,
    )
    assert criteria.min_payoff_ratio == 3.0

    bala = BalaExecutionRecord(
        bala_id="bala_eth_001",
        entry_time_ms=1771437600000,
        exit_time_ms=1771441200000,
        margin_cost_usd=100.0,
        gross_pnl_usd=1850.0,
        net_pnl_usd=1842.0,
        return_r=18.42,
        reached_state=BalaState.COSECHA_VAULT,
        pyramid_levels_executed=3,
        friction_cost_usd=8.0,
    )
    assert bala.return_r == 18.42
    assert bala.reached_state == BalaState.COSECHA_VAULT


def test_backtest_contracts():
    """Verify BacktestRequest and BacktestResult contracts."""
    dataset = DatasetSnapshot(
        dataset_id="ds_btc_h1_2026",
        symbol="BTC-USDT",
        timeframe="1h",
        start_timestamp_utc_ms=1770000000000,
        end_timestamp_utc_ms=1771437600000,
        total_bars=3840,
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        is_in_sample=False,
    )
    request = BacktestRequest(
        request_id="req_bt_001",
        strategy_id="UR-CANON-001",
        engine_type=EngineType.FAST_APPROXIMATE,
        dataset=dataset,
        initial_capital_usd=10000.0,
        leverage=20,
    )
    assert request.engine_type == EngineType.FAST_APPROXIMATE

    result = BacktestResult(
        request_id="req_bt_001",
        strategy_id="UR-CANON-001",
        engine_type=EngineType.FAST_APPROXIMATE,
        dataset_id="ds_btc_h1_2026",
        ledger_hash="ledger_sha256_mock",
        initial_capital_usd=10000.0,
        final_equity_usd=14200.0,
        net_profit_usd=4200.0,
        net_return_pct=42.0,
        total_trades=101,
        winning_trades=58,
        losing_trades=43,
        win_rate_pct=57.4,
        profit_factor=1.42,
        max_drawdown_pct=8.2,
        max_drawdown_usd=820.0,
        provenance_hash_sha256="abc123hash",
    )
    assert result.net_profit_usd == 4200.0


def test_portfolio_contracts():
    """Verify Portfolio and Fondeo/Ultra contracts."""
    prop_cfg = PropChallengeConfig(
        firm_name="Topstep 50K",
        account_size_usd=50000.0,
        profit_target_usd=3000.0,
        max_trailing_drawdown_usd=2000.0,
        daily_loss_limit_usd=1000.0,
        consistency_max_profit_share_pct=50.0,
    )
    assert prop_cfg.profit_target_usd == 3000.0

    vault_cfg = VaultRatchetConfig(
        milestone_2x_lock_pct=0.50,
        milestone_3x_lock_pct=0.65,
        milestone_5x_lock_pct=0.75,
    )
    assert vault_cfg.milestone_2x_lock_pct == 0.50

    allocation = PortfolioAllocation(
        portfolio_id="port_fondeo_01",
        timestamp_utc_ms=1771437600000,
        total_capital_usd=50000.0,
        weights=[
            AssetWeight(
                symbol="MES",
                weight=0.60,
                target_capital_usd=30000.0,
                max_contracts_or_lots=4.0,
            ),
            AssetWeight(
                symbol="MNQ",
                weight=0.40,
                target_capital_usd=20000.0,
                max_contracts_or_lots=2.0,
            ),
        ],
        expected_sharpe=2.35,
        diversification_ratio=1.42,
        max_historical_drawdown_pct=3.2,
        provenance_hash_sha256="port_sha256_hash",
    )
    assert len(allocation.weights) == 2
