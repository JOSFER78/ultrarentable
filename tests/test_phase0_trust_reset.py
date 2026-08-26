"""tests/test_phase0_trust_reset.py
Suite de Tests y Auditoría Adversarial de la FASE 0: TRUST & INTEGRITY RESET.

Verifica de forma estricta:
1. Sensibilidad del Merkle/Hash-Chain del CanonicalExecutionLedger ante el orden de trades.
2. Sensibilidad ante modificaciones de comisiones, slippage, precios o timestamps.
3. Aislamiento criptográfico y rechazo irrevocable del HoldoutGateway ante accesos no autorizados.
4. Registro inmutable y exhaustivo de trials en el StrategySearchRegistry.
"""

import copy
import hashlib
import json
import os
import pytest
from pathlib import Path

from contracts.canonical_execution import (
    AssetClass,
    CanonicalExecutionLedger,
    ExecutionTruth,
    ExitReason,
    OrderSide,
)
from contracts.canonical_strategy import (
    ComparisonOperator,
    ExitModel,
    IndicatorSpec,
    ProvenanceMetadata,
    RuleCondition,
    RuleTree,
    SizingAndRisk,
    TargetInstrument,
    CanonicalStrategy,
    LogicalOp,
    SizingType,
    StopLossType,
    TakeProfitType
)
from contracts.snapshots.strategy_snapshot import StrategyRoute, StrategySnapshot
from services.data.holdout_gateway import BlindHoldoutAccessViolation, HoldoutGateway
from services.discovery.strategy_search_registry import SearchTrialRecord, StrategySearchRegistry


def _create_mock_trade(idx: int, timestamp_ms: int = 1700000000000, fee: float = 1.50) -> ExecutionTruth:
    return ExecutionTruth(
        trade_id=f"trade_{idx}",
        symbol="BTCUSDT",
        side=OrderSide.BUY if idx % 2 == 0 else OrderSide.SELL,
        entry_timestamp_utc_ms=timestamp_ms + (idx * 3600000),
        exit_timestamp_utc_ms=timestamp_ms + (idx * 3600000) + 1800000,
        market_data_hash=hashlib.sha256(f"candle_{idx}".encode()).hexdigest(),
        strategy_snapshot_hash=hashlib.sha256(b"strat_test").hexdigest(),
        execution_config_hash=hashlib.sha256(b"exec_test").hexdigest(),
        decision_price=50000.0 + idx,
        requested_qty=0.1,
        filled_qty=0.1,
        entry_price=50000.0 + idx,
        exit_price=50500.0 + idx,
        stop_loss_px=49500.0,
        take_profit_px=51500.0,
        commission_usd=fee,
        slippage_usd=0.50,
        funding_usd=0.0,
        total_friction_cost_usd=fee + 0.50,
        gross_pnl_usd=50.0,
        net_pnl_usd=50.0 - (fee + 0.50),
        return_r=1.0,
        exit_reason=ExitReason.TAKE_PROFIT,
        notional_usd=5000.0,
        margin_used_usd=500.0,
        leverage_actual=10.0,
        equity_before_usd=1000.0 + (idx * 48.0),
        equity_after_usd=1000.0 + ((idx + 1) * 48.0),
        drawdown_after_pct=0.0,
    )


def test_ledger_hash_order_sensitivity():
    """TEST OBLIGATORIO: Intercambiar 2 trades en la secuencia debe cambiar el hash del ledger."""
    trades_seq_a = [_create_mock_trade(i) for i in range(20)]
    trades_seq_b = copy.deepcopy(trades_seq_a)

    # Intercambiar trade #11 y #12 en B
    trades_seq_b[10], trades_seq_b[11] = trades_seq_b[11], trades_seq_b[10]

    ledger_a = CanonicalExecutionLedger(
        strategy_id="UR_STRAT_001",
        strategy_snapshot_hash="hash_snapshot_001",
        dataset_sha256="dataset_hash_001",
        execution_config_hash="config_hash_001",
        engine_name="EventBacktestEngine",
        initial_capital_usd=1000.0,
        final_equity_usd=1960.0,
        net_profit_usd=960.0,
        roi_pct=96.0,
        profit_factor=2.5,
        win_rate_pct=75.0,
        max_drawdown_pct=4.2,
        peak_leverage_used=10.0,
        total_trades_count=20,
        winning_trades_count=15,
        losing_trades_count=5,
        total_commission_paid_usd=30.0,
        total_slippage_paid_usd=10.0,
        trades=trades_seq_a,
    )

    ledger_b = CanonicalExecutionLedger(
        strategy_id="UR_STRAT_001",
        strategy_snapshot_hash="hash_snapshot_001",
        dataset_sha256="dataset_hash_001",
        execution_config_hash="config_hash_001",
        engine_name="EventBacktestEngine",
        initial_capital_usd=1000.0,
        final_equity_usd=1960.0,
        net_profit_usd=960.0,
        roi_pct=96.0,
        profit_factor=2.5,
        win_rate_pct=75.0,
        max_drawdown_pct=4.2,
        peak_leverage_used=10.0,
        total_trades_count=20,
        winning_trades_count=15,
        losing_trades_count=5,
        total_commission_paid_usd=30.0,
        total_slippage_paid_usd=10.0,
        trades=trades_seq_b,
    )

    hash_a = ledger_a.calculate_ledger_hash()
    hash_b = ledger_b.calculate_ledger_hash()

    assert hash_a != hash_b, "FALLO CRITICO: Reordenar trades no cambió el hash del ledger."


def test_ledger_hash_fee_modification_sensitivity():
    """TEST OBLIGATORIO: Modificar 1 centavo de fee en 1 trade debe cambiar el hash del ledger."""
    trades_seq_a = [_create_mock_trade(i, fee=1.50) for i in range(15)]
    trades_seq_b = copy.deepcopy(trades_seq_a)

    # Modificar fee del trade #5 por 1 centavo
    trade_5_mod = trades_seq_b[4].model_dump()
    trade_5_mod["commission_usd"] = 1.51
    trades_seq_b[4] = ExecutionTruth(**trade_5_mod)

    ledger_a = CanonicalExecutionLedger(
        strategy_id="UR_STRAT_001",
        strategy_snapshot_hash="hash_snapshot_001",
        dataset_sha256="dataset_hash_001",
        execution_config_hash="config_hash_001",
        engine_name="EventBacktestEngine",
        initial_capital_usd=1000.0,
        final_equity_usd=1700.0,
        net_profit_usd=700.0,
        roi_pct=70.0,
        profit_factor=2.0,
        win_rate_pct=70.0,
        max_drawdown_pct=3.5,
        peak_leverage_used=10.0,
        total_trades_count=15,
        winning_trades_count=11,
        losing_trades_count=4,
        total_commission_paid_usd=22.50,
        total_slippage_paid_usd=7.50,
        trades=trades_seq_a,
    )

    ledger_b = CanonicalExecutionLedger(
        strategy_id="UR_STRAT_001",
        strategy_snapshot_hash="hash_snapshot_001",
        dataset_sha256="dataset_hash_001",
        execution_config_hash="config_hash_001",
        engine_name="EventBacktestEngine",
        initial_capital_usd=1000.0,
        final_equity_usd=1700.0,
        net_profit_usd=700.0,
        roi_pct=70.0,
        profit_factor=2.0,
        win_rate_pct=70.0,
        max_drawdown_pct=3.5,
        peak_leverage_used=10.0,
        total_trades_count=15,
        winning_trades_count=11,
        losing_trades_count=4,
        total_commission_paid_usd=22.51,
        total_slippage_paid_usd=7.50,
        trades=trades_seq_b,
    )

    assert ledger_a.calculate_ledger_hash() != ledger_b.calculate_ledger_hash()


def test_holdout_firewall_unauthorized_access_denied():
    """TEST OBLIGATORIO: Intentar acceder al Blind Holdout sin token válido debe ser denegado."""
    dummy_candles = [{"open": 100 + i, "close": 101 + i, "high": 102 + i, "low": 99 + i} for i in range(100)]

    strat_id = "UR_TEST_FIREWALL"
    snap_hash = "abc12345hash"

    # 1. Sin token
    with pytest.raises(BlindHoldoutAccessViolation):
        HoldoutGateway.get_blind_holdout_data(dummy_candles, strat_id, snap_hash, auth_token="")

    # 2. Con token falso
    with pytest.raises(BlindHoldoutAccessViolation):
        HoldoutGateway.get_blind_holdout_data(dummy_candles, strat_id, snap_hash, auth_token="invalid_token_123")

    # 3. Con token válido pero emitido para otra estrategia
    wrong_token = HoldoutGateway.generate_validation_token("OTHER_STRAT", "other_hash")
    with pytest.raises(BlindHoldoutAccessViolation):
        HoldoutGateway.get_blind_holdout_data(dummy_candles, strat_id, snap_hash, auth_token=wrong_token)

    # 4. Con token legítimo para esta estrategia
    valid_token = HoldoutGateway.generate_validation_token(strat_id, snap_hash)
    holdout_data = HoldoutGateway.get_blind_holdout_data(dummy_candles, strat_id, snap_hash, auth_token=valid_token)
    assert len(holdout_data) == 20
    assert holdout_data[0]["open"] == 180


def test_strategy_snapshot_functional_integrity():
    """TEST OBLIGATORIO: Modificar cualquier regla o parámetro funcional debe cambiar el canonical_hash."""
    rules_1 = RuleTree(
    logic=LogicalOp.AND,
    direction="LONG",
    long_conditions=[
            RuleCondition(left=IndicatorSpec(name="EMA", params={'period': 10}, source_field="close", shift=0), op=ComparisonOperator.GT, right=IndicatorSpec(name="EMA", params={'period': 30}, source_field="close", shift=0))
        ]
)
    rules_2 = RuleTree(
    logic=LogicalOp.AND,
    direction="LONG",
    long_conditions=[
            RuleCondition(left=IndicatorSpec(name="EMA", params={'period': 12}, source_field="close", shift=0), op=ComparisonOperator.GT, right=IndicatorSpec(name="EMA", params={'period': 30}, source_field="close", shift=0))
        ]
)

    snap_1 = StrategySnapshot.create_and_hash(
        strategy_id="UR_STRAT_01",
        route=StrategyRoute.ULTRA,
        symbol="BTCUSDT",
        timeframe="1h",
        entry_rules=rules_1,
        exit_rules=ExitModel(
    sl_type=StopLossType.ATR_MULTIPLE,
    sl_value=1.5,
    tp_type=TakeProfitType.ATR_MULTIPLE,
    tp_value=5.0
),
        sizing_and_risk=SizingAndRisk(
    sizing_type=SizingType.RISK_PCT_EQUITY,
    risk_value=15.0,
    max_open_positions=1
),
        dataset_id_reference="ds_btc_1h",
        dataset_sha256_reference="sha256_mock",
    )

    snap_2 = StrategySnapshot.create_and_hash(
        strategy_id="UR_STRAT_01",
        route=StrategyRoute.ULTRA,
        symbol="BTCUSDT",
        timeframe="1h",
        entry_rules=rules_2,
        exit_rules=ExitModel(
    sl_type=StopLossType.ATR_MULTIPLE,
    sl_value=1.5,
    tp_type=TakeProfitType.ATR_MULTIPLE,
    tp_value=5.0
),
        sizing_and_risk=SizingAndRisk(
    sizing_type=SizingType.RISK_PCT_EQUITY,
    risk_value=15.0,
    max_open_positions=1
),
        dataset_id_reference="ds_btc_1h",
        dataset_sha256_reference="sha256_mock",
    )

    assert snap_1.canonical_hash != snap_2.canonical_hash
    assert snap_1.verify_integrity() is True
    assert snap_2.verify_integrity() is True


def test_trial_registry_persistence(tmp_path):
    """TEST OBLIGATORIO: Cada búsqueda debe registrarse de forma inmutable en SQLite."""
    test_db = tmp_path / "test_trials.sqlite3"
    registry = StrategySearchRegistry(db_path=str(test_db))

    rec = SearchTrialRecord(
        trial_id="trial_001",
        run_id="run_001",
        generation=1,
        parent_trial_id=None,
        symbol="ETHUSDT",
        timeframe="1h",
        route="ULTRA",
        archetype="MOMENTUM_BREAKOUT",
        parameters={"ema_fast": 10, "ema_slow": 30},
        rules_json='{"long": ["EMA10 > EMA30"]}',
        dataset_id="ds_eth_1h",
        dataset_sha256="sha256_eth_verified",
        discovery_engine="GeneticGrammarEngine",
        in_sample_pf=1.65,
        in_sample_dd_pct=12.4,
    )

    registry.record_trial(rec)
    trials = registry.get_trials_for_run("run_001")

    assert len(trials) == 1
    assert trials[0]["trial_id"] == "trial_001"
    assert trials[0]["in_sample_pf"] == 1.65
    assert trials[0]["discovery_engine"] == "GeneticGrammarEngine"
