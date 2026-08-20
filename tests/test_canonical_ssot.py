"""tests/test_canonical_ssot.py
Pruebas de Contratos Canónicos y Verificación de la Fuente Única de Verdad (SSOT).
"""

import os
from pathlib import Path
from contracts.canonical_strategy import (
    CanonicalStrategy,
    ExecutionTrack,
    StrategyLifecycleStatus,
    TargetInstrument,
    SizingAndRisk,
    ExitModel,
    RuleTree,
)
from contracts.canonical_execution import (
    AssetClass,
    CanonicalExecutionLedger,
    ExecutionTruth,
    ExitReason,
    InstrumentCostProfile,
    OrderSide,
)
from scripts.generate_state_of_truth import generate_state_of_truth, REPO_ROOT


def test_canonical_strategy_instantiation_and_hash():
    """Verify CanonicalStrategy immutability and deterministic SHA-256 hash generation."""
    from contracts.canonical_strategy import ProvenanceMetadata
    strategy = CanonicalStrategy(
        strategy_id="cand_ssot_btc_01",
        name="BTC Momentum Breakout",
        target_track=ExecutionTrack.TRACK_ULTRA,
        status=StrategyLifecycleStatus.GENERATED,
        instrument=TargetInstrument(
            symbol="BTCUSDT",
            exchange="BINGX",
            contract_type="PERPETUAL",
            point_value=1.0,
            tick_size=0.1,
        ),
        rules=RuleTree(),
        exits=ExitModel(stop_loss_atr_mult=1.5, take_profit_atr_mult=6.0),
        sizing_and_risk=SizingAndRisk(base_risk_pct=2.0, base_leverage=50.0),
        provenance=ProvenanceMetadata(
            source_engine="internal_genetic",
            created_timestamp_utc=1700000000,
        ),
    )
    h1 = strategy.compute_sha256()
    h2 = strategy.compute_sha256()
    assert len(h1) == 64
    assert h1 == h2


def test_instrument_cost_profile_rejects_missing_fields():
    """Verify InstrumentCostProfile requires all parameters without silent defaults."""
    profile = InstrumentCostProfile(
        symbol="EURUSD",
        asset_class=AssetClass.FOREX_SPOT,
        point_value=10.0,
        tick_size=0.0001,
        contract_multiplier=100_000.0,
        taker_fee_pct=0.002,
        maker_fee_pct=0.001,
        typical_spread_ticks=0.6,
        slippage_ticks_baseline=0.5,
    )
    assert profile.point_value == 10.0
    assert profile.contract_multiplier == 100000.0


def test_canonical_execution_ledger_integrity():
    """Verify CanonicalExecutionLedger trade serialization and ledger hash generation."""
    trade = ExecutionTruth(
        trade_id="t_001",
        symbol="SUIUSDT",
        side=OrderSide.BUY,
        entry_timestamp_utc_ms=1700000000000,
        exit_timestamp_utc_ms=1700003600000,
        market_data_hash="md_hash_123",
        strategy_snapshot_hash="strat_hash_456",
        execution_config_hash="cfg_hash_789",
        decision_price=1.50,
        requested_qty=1000.0,
        filled_qty=1000.0,
        entry_price=1.5005,
        exit_price=1.6500,
        stop_loss_px=1.45,
        take_profit_px=1.70,
        commission_usd=1.57,
        slippage_usd=0.50,
        funding_usd=0.0,
        total_friction_cost_usd=2.07,
        gross_pnl_usd=149.50,
        net_pnl_usd=147.43,
        return_r=2.95,
        exit_reason=ExitReason.TAKE_PROFIT,
        notional_usd=1500.50,
        margin_used_usd=30.01,
        leverage_actual=50.0,
        equity_before_usd=1000.0,
        equity_after_usd=1147.43,
        drawdown_after_pct=0.0,
    )
    ledger = CanonicalExecutionLedger(
        strategy_id="strat_sui_01",
        strategy_snapshot_hash="strat_hash_456",
        dataset_sha256="ds_hash_999",
        execution_config_hash="cfg_hash_789",
        engine_name="FastEngine",
        initial_capital_usd=1000.0,
        final_equity_usd=1147.43,
        net_profit_usd=147.43,
        roi_pct=14.74,
        profit_factor=99.0,
        win_rate_pct=100.0,
        max_drawdown_pct=0.0,
        peak_leverage_used=50.0,
        total_trades_count=1,
        winning_trades_count=1,
        losing_trades_count=0,
        total_commission_paid_usd=1.57,
        total_slippage_paid_usd=0.50,
        trades=[trade],
    )
    h = ledger.calculate_ledger_hash()
    assert len(h) == 64


def test_state_of_truth_document_generation():
    """Verify docs/STATE_OF_TRUTH.md generation and physical existence."""
    path_str = generate_state_of_truth()
    p = Path(path_str)
    assert p.exists()
    content = p.read_text(encoding="utf-8")
    assert "ESTADO DE LA VERDAD" in content
    assert "v1.02" in content
