"""tests/universal_engine/test_universal_engine.py
Adversarial & Forensic Verification Suite for Universal Dynamic Engine (v3.0.0).

DOCTRINA ZERO-MOCKS & REAL-ONLY VALIDATION:
1. Dataset unavailable / corrupted -> BLOCKED.
2. Bit-for-bit reproducibility & Merkle provenance hash integrity.
3. Multi-asset universality (Crypto, CME Futures, Forex).
4. Multi-strategy universality (Trend Following, Breakout, Mean Reversion).
5. Route ULTRA vs Route FONDEO mathematical constraints.
6. Forensic metrics (zero fake approximations, explicit NOT_COMPUTABLE states).
"""

from __future__ import annotations

import json
import os
import pytest
import numpy as np

from contracts.dataset_specification import DatasetSpecification
from contracts.execution_model import ExecutionModel
from contracts.instrument_specification import AssetClass, InstrumentSpecification
from contracts.risk_model import RiskDoctrine, RiskModel
from contracts.universal_strategy import (
    ComparisonOperator,
    ConditionNode,
    DynamicEntryRules,
    DynamicExitRules,
    DynamicValueNode,
    IndicatorType,
    LogicalOperator,
    RuleGroup,
    StrategyFamily,
    StrategySpecification,
)
from services.engine.dataset_loader import (
    DatasetIntegrityError,
    DatasetUnavailableError,
    UniversalDataLoader,
)
from services.engine.indicator_engine import DynamicIndicatorEngine
from services.engine.instrument_registry import InstrumentRegistry
from services.engine.metrics_engine import UniversalMetricsEngine
from services.engine.rule_evaluator import DynamicRuleEvaluator
from services.engine.universal_backtest_engine import UniversalDeterministicBacktestEngine


# === Fixtures de Datos Reales ===
@pytest.fixture
def real_btc_dataset() -> tuple[DatasetSpecification, list[dict]]:
    loader = UniversalDataLoader()
    return loader.load_dataset("BTCUSDT", "1h")


@pytest.fixture
def real_nq_dataset() -> tuple[DatasetSpecification, list[dict]]:
    loader = UniversalDataLoader()
    return loader.load_dataset("NQ", "1h")


@pytest.fixture
def real_eurusd_dataset() -> tuple[DatasetSpecification, list[dict]]:
    loader = UniversalDataLoader()
    return loader.load_dataset("EURUSD", "1h")


# === 1. Test Zero-Mocks & Missing Dataset Blocking ===
def test_missing_dataset_blocks_immediately():
    loader = UniversalDataLoader()
    with pytest.raises(DatasetUnavailableError):
        loader.load_dataset("NON_EXISTENT_ASSET_XYZ", "1m")


def test_corrupted_dataset_blocks_immediately(tmp_path):
    bad_file = tmp_path / "ds_fake_btc_1h.json"
    # OHLC con High < Low (corrupto)
    corrupted_data = [
        {"timestamp_ms": 1000, "open": 100, "high": 90, "low": 110, "close": 105, "volume": 10}
    ]
    bad_file.write_text(json.dumps(corrupted_data))

    loader = UniversalDataLoader(data_root_dir=str(tmp_path))
    with pytest.raises(DatasetIntegrityError):
        loader.load_dataset("btc", "1h", explicit_filepath=str(bad_file))


# === 2. Test Multi-Strategy Universality on Real Data ===
def test_universal_engine_executes_trend_following(real_btc_dataset):
    ds_spec, candles = real_btc_dataset
    instrument = InstrumentRegistry.get("BTC-USDT")

    # Estrategia 1: EMA Fast (10) cruza EMA Slow (30)
    strat = StrategySpecification(
        strategy_id="STRAT_EMA_TREND_BTC",
        family=StrategyFamily.TREND_FOLLOWING,
        target_symbol="BTC-USDT",
        base_timeframe="1h",
        entry_rules=DynamicEntryRules(
            long_rules=RuleGroup(
                logical_operator=LogicalOperator.ALL,
                conditions=[
                    ConditionNode(
                        left=DynamicValueNode.indicator(IndicatorType.EMA, 10),
                        operator=ComparisonOperator.CROSSES_ABOVE,
                        right=DynamicValueNode.indicator(IndicatorType.EMA, 30),
                    )
                ],
            ),
            short_rules=RuleGroup(
                logical_operator=LogicalOperator.ALL,
                conditions=[
                    ConditionNode(
                        left=DynamicValueNode.indicator(IndicatorType.EMA, 10),
                        operator=ComparisonOperator.CROSSES_BELOW,
                        right=DynamicValueNode.indicator(IndicatorType.EMA, 30),
                    )
                ],
            ),
        ),
        exit_rules=DynamicExitRules(
            stop_loss_type="ATR_MULTIPLE",
            stop_loss_value=2.0,
            take_profit_type="ATR_MULTIPLE",
            take_profit_value=5.0,
        ),
        dataset_reference_id=ds_spec.dataset_id,
        dataset_sha256=ds_spec.sha256_hash,
    )

    engine = UniversalDeterministicBacktestEngine()
    exec_model = ExecutionModel()
    risk_model = RiskModel.create_ultra(base_capital=1000.0, risk_pct=10.0)

    res = engine.run(strat, instrument, ds_spec, candles, exec_model, risk_model)

    assert res.total_trades > 0
    assert len(res.bar_ledger) == len(candles)
    assert len(res.equity_curve) == len(candles)
    assert len(res.provenance_hash) == 64


def test_universal_engine_executes_donchian_breakout(real_btc_dataset):
    ds_spec, candles = real_btc_dataset
    instrument = InstrumentRegistry.get("BTC-USDT")

    # Estrategia 2: Breakout Donchian 20 + Trailing Stop
    strat = StrategySpecification(
        strategy_id="STRAT_DONCHIAN_BREAKOUT_BTC",
        family=StrategyFamily.MOMENTUM_BREAKOUT,
        target_symbol="BTC-USDT",
        base_timeframe="1h",
        entry_rules=DynamicEntryRules(
            long_rules=RuleGroup(
                logical_operator=LogicalOperator.ALL,
                conditions=[
                    ConditionNode(
                        left=DynamicValueNode.series(IndicatorType.PRICE_CLOSE),
                        operator=ComparisonOperator.GREATER_EQUAL,
                        right=DynamicValueNode.indicator(IndicatorType.DONCHIAN_HIGH, 20, offset=1),
                    )
                ],
            ),
            short_rules=RuleGroup(
                logical_operator=LogicalOperator.ALL,
                conditions=[
                    ConditionNode(
                        left=DynamicValueNode.series(IndicatorType.PRICE_CLOSE),
                        operator=ComparisonOperator.LESS_EQUAL,
                        right=DynamicValueNode.indicator(IndicatorType.DONCHIAN_LOW, 20, offset=1),
                    )
                ],
            ),
        ),
        exit_rules=DynamicExitRules(
            stop_loss_type="ATR_MULTIPLE",
            stop_loss_value=1.5,
            take_profit_type="RISK_REWARD_MULTIPLE",
            take_profit_value=3.0,
            trailing_stop_enabled=True,
            trailing_trigger_r=1.5,
            trailing_step_atr_mult=1.5,
        ),
        dataset_reference_id=ds_spec.dataset_id,
        dataset_sha256=ds_spec.sha256_hash,
    )

    engine = UniversalDeterministicBacktestEngine()
    exec_model = ExecutionModel()
    risk_model = RiskModel.create_ultra(base_capital=1000.0, risk_pct=12.5)

    res = engine.run(strat, instrument, ds_spec, candles, exec_model, risk_model)

    assert res.total_trades > 0
    assert res.final_equity_usd > 0
    assert res.max_drawdown_pct <= 100.0


# === 3. Test Multi-Asset Universality (Crypto, CME Futures, Forex) ===
def test_universal_engine_executes_cme_futures(real_nq_dataset):
    ds_spec, candles = real_nq_dataset
    instrument = InstrumentRegistry.get("NQ")

    assert instrument.asset_class == AssetClass.CME_FUTURES
    assert instrument.point_value == 20.0
    assert instrument.tick_size == 0.25

    strat = StrategySpecification(
        strategy_id="STRAT_NQ_FONDEO",
        family=StrategyFamily.MOMENTUM_BREAKOUT,
        target_symbol="NQ",
        base_timeframe="1h",
        entry_rules=DynamicEntryRules(
            long_rules=RuleGroup(
                logical_operator=LogicalOperator.ALL,
                conditions=[
                    ConditionNode(
                        left=DynamicValueNode.indicator(IndicatorType.RSI, 14),
                        operator=ComparisonOperator.GREATER_THAN,
                        right=DynamicValueNode.constant(55.0),
                    )
                ],
            ),
            short_rules=RuleGroup(
                logical_operator=LogicalOperator.ALL,
                conditions=[
                    ConditionNode(
                        left=DynamicValueNode.indicator(IndicatorType.RSI, 14),
                        operator=ComparisonOperator.LESS_THAN,
                        right=DynamicValueNode.constant(45.0),
                    )
                ],
            ),
        ),
        exit_rules=DynamicExitRules(
            stop_loss_type="ATR_MULTIPLE",
            stop_loss_value=2.0,
            take_profit_type="RISK_REWARD_MULTIPLE",
            take_profit_value=3.0,
        ),
        dataset_reference_id=ds_spec.dataset_id,
        dataset_sha256=ds_spec.sha256_hash,
    )

    engine = UniversalDeterministicBacktestEngine()
    exec_model = ExecutionModel(cme_clearing_fee_per_contract=2.50)
    risk_model = RiskModel.create_fondeo(base_capital=50000.0, max_contracts=1.0)

    res = engine.run(strat, instrument, ds_spec, candles, exec_model, risk_model)

    assert res.total_trades > 0
    # Verificar que las comisiones se cobraron por contrato CME ($2.50)
    assert res.total_commissions_usd >= res.total_trades * 2.50


def test_universal_engine_executes_forex(real_eurusd_dataset):
    ds_spec, candles = real_eurusd_dataset
    instrument = InstrumentRegistry.get("EURUSD")

    assert instrument.asset_class == AssetClass.FOREX_MAJOR
    assert instrument.point_value == 10.0

    strat = StrategySpecification(
        strategy_id="STRAT_EURUSD_MOMENTUM",
        family=StrategyFamily.TREND_FOLLOWING,
        target_symbol="EURUSD",
        base_timeframe="1h",
        entry_rules=DynamicEntryRules(
            long_rules=RuleGroup(
                logical_operator=LogicalOperator.ALL,
                conditions=[
                    ConditionNode(
                        left=DynamicValueNode.indicator(IndicatorType.SMA, 20),
                        operator=ComparisonOperator.GREATER_THAN,
                        right=DynamicValueNode.indicator(IndicatorType.SMA, 50),
                    )
                ],
            ),
            short_rules=RuleGroup(
                logical_operator=LogicalOperator.ALL,
                conditions=[
                    ConditionNode(
                        left=DynamicValueNode.indicator(IndicatorType.SMA, 20),
                        operator=ComparisonOperator.LESS_THAN,
                        right=DynamicValueNode.indicator(IndicatorType.SMA, 50),
                    )
                ],
            ),
        ),
        exit_rules=DynamicExitRules(
            stop_loss_type="ATR_MULTIPLE",
            stop_loss_value=1.5,
            take_profit_type="RISK_REWARD_MULTIPLE",
            take_profit_value=2.5,
        ),
        dataset_reference_id=ds_spec.dataset_id,
        dataset_sha256=ds_spec.sha256_hash,
    )

    engine = UniversalDeterministicBacktestEngine()
    exec_model = ExecutionModel()
    risk_model = RiskModel.create_ultra(base_capital=1000.0, risk_pct=5.0)

    res = engine.run(strat, instrument, ds_spec, candles, exec_model, risk_model)

    assert res.total_trades > 0
    assert len(res.trades) == res.total_trades


# === 4. Test Deterministic Reproducibility & Provenance Hash ===
def test_bit_for_bit_reproducibility(real_btc_dataset):
    ds_spec, candles = real_btc_dataset
    instrument = InstrumentRegistry.get("BTC-USDT")

    strat = StrategySpecification(
        strategy_id="STRAT_REPRO_TEST",
        family=StrategyFamily.MOMENTUM_BREAKOUT,
        target_symbol="BTC-USDT",
        base_timeframe="1h",
        entry_rules=DynamicEntryRules(
            long_rules=RuleGroup(
                logical_operator=LogicalOperator.ALL,
                conditions=[
                    ConditionNode(
                        left=DynamicValueNode.indicator(IndicatorType.RSI, 14),
                        operator=ComparisonOperator.GREATER_THAN,
                        right=DynamicValueNode.constant(60.0),
                    )
                ],
            ),
        ),
        exit_rules=DynamicExitRules(stop_loss_value=2.0, take_profit_value=4.0),
        dataset_reference_id=ds_spec.dataset_id,
        dataset_sha256=ds_spec.sha256_hash,
    )

    engine = UniversalDeterministicBacktestEngine()
    exec_model = ExecutionModel()
    risk_model = RiskModel.create_ultra()

    # Ejecución 1
    res1 = engine.run(strat, instrument, ds_spec, candles, exec_model, risk_model)
    # Ejecución 2 (con idénticas entradas)
    res2 = engine.run(strat, instrument, ds_spec, candles, exec_model, risk_model)

    assert res1.provenance_hash == res2.provenance_hash
    assert res1.net_profit_usd == res2.net_profit_usd
    assert res1.total_trades == res2.total_trades
    assert res1.equity_curve == res2.equity_curve
    assert len(res1.trades) == len(res2.trades)


def test_parameter_change_produces_different_provenance_hash(real_btc_dataset):
    ds_spec, candles = real_btc_dataset
    instrument = InstrumentRegistry.get("BTC-USDT")

    strat_a = StrategySpecification(
        strategy_id="STRAT_HASH_A",
        family=StrategyFamily.MOMENTUM_BREAKOUT,
        target_symbol="BTC-USDT",
        base_timeframe="1h",
        entry_rules=DynamicEntryRules(
            long_rules=RuleGroup(
                conditions=[ConditionNode(left=DynamicValueNode.indicator(IndicatorType.RSI, 14), operator=ComparisonOperator.GREATER_THAN, right=DynamicValueNode.constant(50.0))]
            )
        ),
        exit_rules=DynamicExitRules(stop_loss_value=2.0),
        dataset_reference_id=ds_spec.dataset_id,
        dataset_sha256=ds_spec.sha256_hash,
    )

    strat_b = StrategySpecification(
        strategy_id="STRAT_HASH_B",
        family=StrategyFamily.MOMENTUM_BREAKOUT,
        target_symbol="BTC-USDT",
        base_timeframe="1h",
        entry_rules=DynamicEntryRules(
            long_rules=RuleGroup(
                conditions=[ConditionNode(left=DynamicValueNode.indicator(IndicatorType.RSI, 14), operator=ComparisonOperator.GREATER_THAN, right=DynamicValueNode.constant(60.0))]
            )
        ),
        exit_rules=DynamicExitRules(stop_loss_value=2.0),
        dataset_reference_id=ds_spec.dataset_id,
        dataset_sha256=ds_spec.sha256_hash,
    )

    engine = UniversalDeterministicBacktestEngine()
    exec_model = ExecutionModel()
    risk_model = RiskModel.create_ultra()

    res_a = engine.run(strat_a, instrument, ds_spec, candles, exec_model, risk_model)
    res_b = engine.run(strat_b, instrument, ds_spec, candles, exec_model, risk_model)

    assert res_a.provenance_hash != res_b.provenance_hash


# === 5. Test Forensic Metrics Calculation ===
def test_forensic_metrics_not_computable_handling(real_btc_dataset):
    ds_spec, candles = real_btc_dataset
    instrument = InstrumentRegistry.get("BTC-USDT")

    # Estrategia con condición inalcanzable (0 trades)
    strat_empty = StrategySpecification(
        strategy_id="STRAT_EMPTY",
        family=StrategyFamily.MOMENTUM_BREAKOUT,
        target_symbol="BTC-USDT",
        base_timeframe="1h",
        entry_rules=DynamicEntryRules(
            long_rules=RuleGroup(
                conditions=[ConditionNode(left=DynamicValueNode.indicator(IndicatorType.RSI, 14), operator=ComparisonOperator.GREATER_THAN, right=DynamicValueNode.constant(999.0))]
            )
        ),
        exit_rules=DynamicExitRules(),
        dataset_reference_id=ds_spec.dataset_id,
        dataset_sha256=ds_spec.sha256_hash,
    )

    engine = UniversalDeterministicBacktestEngine()
    res = engine.run(strat_empty, instrument, ds_spec, candles, ExecutionModel(), RiskModel.create_ultra())

    metrics = UniversalMetricsEngine.compute_all(res.trades, res.bar_ledger, base_capital=1000.0, trials_tested=None)

    assert metrics.total_trades == 0
    assert metrics.expectancy_r.status == "NOT_COMPUTABLE"
    assert metrics.sharpe_ratio.status == "NOT_COMPUTABLE"
    assert metrics.deflated_sharpe_ratio.status == "NOT_COMPUTABLE"
    assert metrics.deflated_sharpe_ratio.reason == "MISSING_TRIALS_TESTED_EVIDENCE"
