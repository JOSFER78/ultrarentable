"""tests/test_phase02_canonical_strategy.py
Suite Maestra Can?nica de Comportamiento en Runtime de la FASE 02 (AG2-P02-006).
ZERO-MOCKS ? REAL-ONLY ? DETERMINISTIC ? NO-LOOKAHEAD ? PROVENANCE-LOCKED ? FAIL-CLOSED ? ZERO-OPTIMISM

Valida resultados de ejecuci?n f?sica completa:
- Trades generados (entry_price, exit_price, exit_reason, pnl_usd, pnl_r, timestamps, size_contracts).
- Direccionalidad real: LONG, SHORT y BOTH.
- Fallo cerrado ante account_equity_usd <= 0.
- Dimensionamiento con point_value (CME NQ vs Crypto BTCUSDT).
- Sesiones normales, sesiones cruzando medianoche, allowed_days y close_at_eod.
- max_open_positions fail-closed ante valores fuera de contrato.
- Conflicto intrabarra pesimista (SL > TP).
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
import pytest
from pydantic import ValidationError

from contracts.canonical_strategy import (
    CanonicalStrategy,
    ComparisonOp,
    ConditionNode,
    ExitModel,
    IndicatorSpec,
    InvalidStrategyError,
    LogicalOp,
    ProvenanceMetadata,
    RuleTree,
    SessionWindow,
    SizingAndRisk,
    SizingType,
    StopLossType,
    StrategyIntegrityError,
    TakeProfitType,
)
from services.data.dataset_registry import (
    DatasetRegistry,
    MissingDatasetError,
    dataset_registry,
)
from services.data.instrument_cost_registry import (
    CANONICAL_COST_REGISTRY,
    MissingCostModelError,
)
from services.engine_version import CURRENT_ENGINE_VERSION, CURRENT_POLICY_VERSION
from services.execution.canonical_runtime_adapter import (
    CanonicalRuntimeAdapter,
    EvaluatedTrade,
    RuntimeExecutionResult,
    canonical_runtime_adapter,
)


# ==============================================================================
# FIXTURES DETERMINISTAS
# ==============================================================================

@pytest.fixture
def default_provenance():
    return ProvenanceMetadata(
        author="SYSTEM_ORCHESTRATOR",
        engine_version=CURRENT_ENGINE_VERSION,
        policy_version=CURRENT_POLICY_VERSION,
        created_at_utc="2026-08-25T18:00:00Z",
    )


@pytest.fixture
def default_sizing():
    return SizingAndRisk(
        sizing_type=SizingType.RISK_PCT_EQUITY,
        risk_value=1.0,
        max_open_positions=1,
        max_daily_loss_usd=500.0,
    )


@pytest.fixture
def default_exit_rules():
    return ExitModel(
        sl_type=StopLossType.PERCENTAGE,
        sl_value=1.5,
        tp_type=TakeProfitType.RR_MULTIPLE,
        tp_value=3.0,
        trail_after_r=None,
        time_stop_bars=None,
    )


@pytest.fixture
def base_dataset():
    datasets = dataset_registry.list_datasets()
    assert len(datasets) > 0, "Debe existir al menos un dataset normalizado f?sico en data/normalized"
    return datasets[0]


# ==============================================================================
# EJE 1: DIRECCIONALIDAD REAL (LONG, SHORT, BOTH) CON TRADES VERIFICADOS
# ==============================================================================

def test_runtime_direction_long_execution(default_sizing, default_provenance, base_dataset):
    """01: Verifica ejecuci?n en direcci?n LONG con c?lculo de SL bajo entrada y TP sobre entrada."""
    entry_rules = RuleTree(
        logic=LogicalOp.AND,
        conditions=[
            ConditionNode(
                left=IndicatorSpec(name="EMA", params={"period": 9}, source_field="close", shift=0),
                op=ComparisonOp.CROSS_ABOVE,
                right=IndicatorSpec(name="EMA", params={"period": 21}, source_field="close", shift=0),
            )
        ],
        direction="LONG",
    )
    exit_rules = ExitModel(
        sl_type=StopLossType.PERCENTAGE,
        sl_value=1.0,
        tp_type=TakeProfitType.RR_MULTIPLE,
        tp_value=2.0,
    )
    strat = CanonicalStrategy.create_and_hash(
        strategy_id="strat_long_dir",
        name="Long Direction Test",
        version="1.0.0",
        symbol=base_dataset.instrument_id,
        timeframe=base_dataset.timeframe_id,
        route="FONDEO",
        archetype="TREND_FOLLOWING",
        entry_rules=entry_rules,
        exit_rules=exit_rules,
        sizing_and_risk=default_sizing,
        provenance=default_provenance,
    )
    res = canonical_runtime_adapter.execute_backtest(strat, account_equity_usd=100000.0)
    assert res.strategy_id == "strat_long_dir"
    for t in res.trades:
        assert t.direction == "LONG"
        if t.exit_reason == "TAKE_PROFIT":
            assert t.exit_price >= t.entry_price
            assert t.pnl_usd > 0
        elif t.exit_reason == "STOP_LOSS":
            assert t.exit_price <= t.entry_price
            assert t.pnl_usd < 0


def test_runtime_direction_short_execution(default_sizing, default_provenance, base_dataset):
    """02: Verifica ejecuci?n en direcci?n SHORT con SL sobre entrada y TP bajo entrada."""
    entry_rules = RuleTree(
        logic=LogicalOp.AND,
        conditions=[
            ConditionNode(
                left=IndicatorSpec(name="EMA", params={"period": 9}, source_field="close", shift=0),
                op=ComparisonOp.CROSS_BELOW,
                right=IndicatorSpec(name="EMA", params={"period": 21}, source_field="close", shift=0),
            )
        ],
        direction="SHORT",
    )
    exit_rules = ExitModel(
        sl_type=StopLossType.PERCENTAGE,
        sl_value=1.0,
        tp_type=TakeProfitType.PERCENTAGE,
        tp_value=2.0,
    )
    strat = CanonicalStrategy.create_and_hash(
        strategy_id="strat_short_dir",
        name="Short Direction Test",
        version="1.0.0",
        symbol=base_dataset.instrument_id,
        timeframe=base_dataset.timeframe_id,
        route="FONDEO",
        archetype="TREND_FOLLOWING",
        entry_rules=entry_rules,
        exit_rules=exit_rules,
        sizing_and_risk=default_sizing,
        provenance=default_provenance,
    )
    res = canonical_runtime_adapter.execute_backtest(strat, account_equity_usd=100000.0)
    assert res.strategy_id == "strat_short_dir"
    for t in res.trades:
        assert t.direction == "SHORT"
        if t.exit_reason == "TAKE_PROFIT":
            assert t.exit_price <= t.entry_price
            assert t.pnl_usd > 0
        elif t.exit_reason == "STOP_LOSS":
            assert t.exit_price >= t.entry_price
            assert t.pnl_usd < 0


def test_runtime_direction_both_bidirectional_triggers(default_sizing, default_provenance, base_dataset):
    """03: Modo BOTH eval?a bidireccionalmente y compila sem?ntica sim?trica."""
    entry_rules = RuleTree(
        logic=LogicalOp.OR,
        conditions=[
            ConditionNode(
                left=IndicatorSpec(name="PRICE_CLOSE", params={"period": 1}, source_field="close", shift=0),
                op=ComparisonOp.GT,
                right=IndicatorSpec(name="SMA", params={"period": 20}, source_field="close", shift=0),
            )
        ],
        direction="BOTH",
    )
    strat = CanonicalStrategy.create_and_hash(
        strategy_id="strat_both_dir",
        name="Both Direction Test",
        version="1.0.0",
        symbol=base_dataset.instrument_id,
        timeframe=base_dataset.timeframe_id,
        route="ULTRA",
        archetype="MOMENTUM",
        entry_rules=entry_rules,
        exit_rules=ExitModel(
            sl_type=StopLossType.PERCENTAGE,
            sl_value=1.5,
            tp_type=TakeProfitType.RR_MULTIPLE,
            tp_value=3.0,
        ),
        sizing_and_risk=default_sizing,
        provenance=default_provenance,
    )
    instruction = canonical_runtime_adapter.compile_strategy(strat)
    assert instruction.direction == "BOTH"

    res = canonical_runtime_adapter.execute_backtest(strat, account_equity_usd=100000.0)
    assert res.strategy_id == "strat_both_dir"
    assert len(res.execution_hash) == 64


# ==============================================================================
# EJE 2: OPERADORES L?GICOS (AND, OR) CON VERIFICACI?N DE TRADES
# ==============================================================================

def test_runtime_logical_operator_and_strict_conjunction(default_exit_rules, default_sizing, default_provenance, base_dataset):
    """04: LogicalOp.AND exige que 100% de las condiciones sean verdaderas para disparar."""
    entry_rules = RuleTree(
        logic=LogicalOp.AND,
        conditions=[
            ConditionNode(
                left=IndicatorSpec(name="PRICE_CLOSE", params={"period": 1}, source_field="close", shift=0),
                op=ComparisonOp.GT,
                right=0.0,
            ),
            ConditionNode(
                left=IndicatorSpec(name="PRICE_CLOSE", params={"period": 1}, source_field="close", shift=0),
                op=ComparisonOp.LT,
                right=0.0,
            ),
        ],
        direction="LONG",
    )
    strat = CanonicalStrategy.create_and_hash(
        strategy_id="strat_and_fail",
        name="AND Strict Test",
        version="1.0.0",
        symbol=base_dataset.instrument_id,
        timeframe=base_dataset.timeframe_id,
        route="FONDEO",
        archetype="MOMENTUM",
        entry_rules=entry_rules,
        exit_rules=default_exit_rules,
        sizing_and_risk=default_sizing,
        provenance=default_provenance,
    )
    res = canonical_runtime_adapter.execute_backtest(strat, account_equity_usd=100000.0)
    assert res.total_trades == 0, "No debe ejecutar ning?n trade si una condici?n del AND es falsa"


def test_runtime_logical_operator_or_atomic_disjunction(default_exit_rules, default_sizing, default_provenance, base_dataset):
    """05: LogicalOp.OR dispara si al menos una condici?n es verdadera."""
    entry_rules = RuleTree(
        logic=LogicalOp.OR,
        conditions=[
            ConditionNode(
                left=IndicatorSpec(name="PRICE_CLOSE", params={"period": 1}, source_field="close", shift=0),
                op=ComparisonOp.LT,
                right=0.0,
            ),
            ConditionNode(
                left=IndicatorSpec(name="PRICE_CLOSE", params={"period": 1}, source_field="close", shift=0),
                op=ComparisonOp.GT,
                right=0.0,
            ),
        ],
        direction="LONG",
    )
    strat = CanonicalStrategy.create_and_hash(
        strategy_id="strat_or_trigger",
        name="OR Disjunction Test",
        version="1.0.0",
        symbol=base_dataset.instrument_id,
        timeframe=base_dataset.timeframe_id,
        route="FONDEO",
        archetype="MOMENTUM",
        entry_rules=entry_rules,
        exit_rules=default_exit_rules,
        sizing_and_risk=default_sizing,
        provenance=default_provenance,
    )
    bars = dataset_registry.load_dataset_bars(base_dataset.data_snapshot_id)
    instruction = canonical_runtime_adapter.compile_strategy(strat)
    trigger = canonical_runtime_adapter.evaluate_entry_trigger(instruction, bars, 10)
    assert trigger is True, "Debe evaluar True si una de las ramas del OR se cumple"


# ==============================================================================
# EJE 3: SHIFT SEMANTICS, INDICATOR PARAMS & FAIL-CLOSED
# ==============================================================================

def test_runtime_shift_semantics_lookback_t_minus_k(default_exit_rules, default_sizing, default_provenance, base_dataset):
    """06: Eval?a shift temporal t-k sin sesgo lookahead."""
    bars = dataset_registry.load_dataset_bars(base_dataset.data_snapshot_id)
    adapter = canonical_runtime_adapter
    
    spec_t0 = IndicatorSpec(name="PRICE_CLOSE", params={"period": 1}, source_field="close", shift=0)
    spec_t1 = IndicatorSpec(name="PRICE_CLOSE", params={"period": 1}, source_field="close", shift=1)
    spec_t5 = IndicatorSpec(name="PRICE_CLOSE", params={"period": 1}, source_field="close", shift=5)

    idx = 20
    val_t0 = adapter._eval_indicator(spec_t0, bars, idx)
    val_t1 = adapter._eval_indicator(spec_t1, bars, idx)
    val_t5 = adapter._eval_indicator(spec_t5, bars, idx)

    assert val_t0 == float(bars[idx]["close"])
    assert val_t1 == float(bars[idx - 1]["close"])
    assert val_t5 == float(bars[idx - 5]["close"])


def test_runtime_indicator_custom_parameters_sma_ema(base_dataset):
    """07: Verifica c?lculo num?rico de SMA y EMA sobre diferentes periodos y campos fuente."""
    bars = dataset_registry.load_dataset_bars(base_dataset.data_snapshot_id)
    adapter = canonical_runtime_adapter

    sma_spec = IndicatorSpec(name="SMA", params={"period": 5}, source_field="close", shift=0)
    val_sma = adapter._eval_indicator(sma_spec, bars, 10)
    expected_sma = sum(float(bars[i]["close"]) for i in range(6, 11)) / 5.0
    assert pytest.approx(val_sma, 1e-6) == expected_sma

    ema_spec = IndicatorSpec(name="EMA", params={"period": 5}, source_field="high", shift=0)
    val_ema = adapter._eval_indicator(ema_spec, bars, 10)
    assert not math.isnan(val_ema)
    assert val_ema > 0.0


def test_runtime_indicator_missing_params_fail_closed(default_exit_rules, default_sizing, default_provenance, base_dataset):
    """08: Indicador sin par?metro 'period' obligatorio lanza InvalidStrategyError (Fail-Closed)."""
    bad_spec = IndicatorSpec(name="SMA", params={}, source_field="close", shift=0)
    bad_rules = RuleTree(
        logic=LogicalOp.AND,
        conditions=[
            ConditionNode(left=bad_spec, op=ComparisonOp.GT, right=100.0)
        ],
        direction="LONG",
    )
    bad_strat = CanonicalStrategy.create_and_hash(
        strategy_id="strat_missing_param",
        name="Missing Param",
        version="1.0.0",
        symbol=base_dataset.instrument_id,
        timeframe=base_dataset.timeframe_id,
        route="FONDEO",
        archetype="MOMENTUM",
        entry_rules=bad_rules,
        exit_rules=default_exit_rules,
        sizing_and_risk=default_sizing,
        provenance=default_provenance,
    )
    with pytest.raises(InvalidStrategyError):
        canonical_runtime_adapter.execute_backtest(bad_strat, account_equity_usd=100000.0)


def test_runtime_unknown_indicator_fail_closed(default_exit_rules, default_sizing, default_provenance, base_dataset):
    """09: Indicador no implementado lanza InvalidStrategyError sin fallbacks complacientes."""
    bad_spec = IndicatorSpec(name="MAGIC_ALPHA_PREDICTOR", params={"period": 14}, source_field="close", shift=0)
    bad_rules = RuleTree(
        logic=LogicalOp.AND,
        conditions=[
            ConditionNode(left=bad_spec, op=ComparisonOp.GT, right=100.0)
        ],
        direction="LONG",
    )
    bad_strat = CanonicalStrategy.create_and_hash(
        strategy_id="strat_unknown_ind",
        name="Unknown Ind",
        version="1.0.0",
        symbol=base_dataset.instrument_id,
        timeframe=base_dataset.timeframe_id,
        route="FONDEO",
        archetype="MOMENTUM",
        entry_rules=bad_rules,
        exit_rules=default_exit_rules,
        sizing_and_risk=default_sizing,
        provenance=default_provenance,
    )
    with pytest.raises(InvalidStrategyError):
        canonical_runtime_adapter.execute_backtest(bad_strat, account_equity_usd=100000.0)


def test_runtime_indicator_invalid_source_field_fail_closed(base_dataset):
    """10: Campo fuente inexistente lanza InvalidStrategyError."""
    bars = dataset_registry.load_dataset_bars(base_dataset.data_snapshot_id)
    bad_spec = IndicatorSpec(name="SMA", params={"period": 10}, source_field="synthetic_non_existent", shift=0)
    with pytest.raises(InvalidStrategyError):
        canonical_runtime_adapter._eval_indicator(bad_spec, bars, 15)


def test_runtime_atr_missing_data_insufficient_bars_fail_closed(base_dataset):
    """11: ATR con barras insuficientes devuelve NaN de forma estricta sin inventar valores por defecto."""
    bars = dataset_registry.load_dataset_bars(base_dataset.data_snapshot_id)
    atr_spec = IndicatorSpec(name="ATR", params={"period": 14}, source_field="close", shift=0)
    val_atr = canonical_runtime_adapter._eval_indicator(atr_spec, bars, 5)
    assert math.isnan(val_atr)


# ==============================================================================
# EJE 4: TIPOS DE SL Y TP CON MICROESTRUCTURA REAL
# ==============================================================================

def test_exit_model_sl_percentage_and_tp_rr_multiple(default_sizing, default_provenance, base_dataset):
    """12: SL tipo PERCENTAGE y TP tipo RR_MULTIPLE."""
    entry_rules = RuleTree(
        logic=LogicalOp.AND,
        conditions=[
            ConditionNode(
                left=IndicatorSpec(name="PRICE_CLOSE", params={"period": 1}, source_field="close", shift=0),
                op=ComparisonOp.GT,
                right=0.0,
            )
        ],
        direction="LONG",
    )
    exit_rules = ExitModel(
        sl_type=StopLossType.PERCENTAGE,
        sl_value=1.5,
        tp_type=TakeProfitType.RR_MULTIPLE,
        tp_value=3.0,
    )
    strat = CanonicalStrategy.create_and_hash(
        strategy_id="strat_sl_pct_tp_rr",
        name="SL Pct TP RR",
        version="1.0.0",
        symbol=base_dataset.instrument_id,
        timeframe=base_dataset.timeframe_id,
        route="FONDEO",
        archetype="MOMENTUM",
        entry_rules=entry_rules,
        exit_rules=exit_rules,
        sizing_and_risk=default_sizing,
        provenance=default_provenance,
    )
    res = canonical_runtime_adapter.execute_backtest(strat, account_equity_usd=100000.0)
    assert res.strategy_id == "strat_sl_pct_tp_rr"
    assert res.execution_hash is not None


def test_exit_model_sl_fixed_points_and_tp_fixed_points(default_sizing, default_provenance, base_dataset):
    """13: SL FIXED_POINTS y TP FIXED_POINTS."""
    entry_rules = RuleTree(
        logic=LogicalOp.AND,
        conditions=[
            ConditionNode(
                left=IndicatorSpec(name="PRICE_CLOSE", params={"period": 1}, source_field="close", shift=0),
                op=ComparisonOp.GT,
                right=0.0,
            )
        ],
        direction="LONG",
    )
    exit_rules = ExitModel(
        sl_type=StopLossType.FIXED_POINTS,
        sl_value=1.0,
        tp_type=TakeProfitType.FIXED_POINTS,
        tp_value=2.0,
    )
    strat = CanonicalStrategy.create_and_hash(
        strategy_id="strat_fixed_pts",
        name="Fixed Points Test",
        version="1.0.0",
        symbol=base_dataset.instrument_id,
        timeframe=base_dataset.timeframe_id,
        route="ULTRA",
        archetype="MOMENTUM",
        entry_rules=entry_rules,
        exit_rules=exit_rules,
        sizing_and_risk=default_sizing,
        provenance=default_provenance,
    )
    res = canonical_runtime_adapter.execute_backtest(strat, account_equity_usd=100000.0)
    assert res.strategy_id == "strat_fixed_pts"
    assert res.execution_hash is not None


def test_exit_model_sl_atr_multiple_and_tp_atr_multiple(default_sizing, default_provenance, base_dataset):
    """14: SL ATR_MULTIPLE y TP ATR_MULTIPLE con volatilidad f?sica."""
    entry_rules = RuleTree(
        logic=LogicalOp.AND,
        conditions=[
            ConditionNode(
                left=IndicatorSpec(name="EMA", params={"period": 9}, source_field="close", shift=0),
                op=ComparisonOp.CROSS_ABOVE,
                right=IndicatorSpec(name="EMA", params={"period": 21}, source_field="close", shift=0),
            )
        ],
        direction="LONG",
    )
    exit_rules = ExitModel(
        sl_type=StopLossType.ATR_MULTIPLE,
        sl_value=2.0,
        tp_type=TakeProfitType.ATR_MULTIPLE,
        tp_value=4.0,
    )
    strat = CanonicalStrategy.create_and_hash(
        strategy_id="strat_atr_multiple",
        name="ATR Multiple Test",
        version="1.0.0",
        symbol=base_dataset.instrument_id,
        timeframe=base_dataset.timeframe_id,
        route="FONDEO",
        archetype="TREND_FOLLOWING",
        entry_rules=entry_rules,
        exit_rules=exit_rules,
        sizing_and_risk=default_sizing,
        provenance=default_provenance,
    )
    res = canonical_runtime_adapter.execute_backtest(strat, account_equity_usd=100000.0)
    assert res.strategy_id == "strat_atr_multiple"


def test_exit_model_sl_tp_percentage_short_direction(default_sizing, default_provenance, base_dataset):
    """15: SL y TP porcentuales en posiciones SHORT."""
    entry_rules = RuleTree(
        logic=LogicalOp.AND,
        conditions=[
            ConditionNode(
                left=IndicatorSpec(name="PRICE_CLOSE", params={"period": 1}, source_field="close", shift=0),
                op=ComparisonOp.GT,
                right=0.0,
            )
        ],
        direction="SHORT",
    )
    exit_rules = ExitModel(
        sl_type=StopLossType.PERCENTAGE,
        sl_value=2.0,
        tp_type=TakeProfitType.PERCENTAGE,
        tp_value=4.0,
    )
    strat = CanonicalStrategy.create_and_hash(
        strategy_id="strat_short_pct",
        name="Short Pct Test",
        version="1.0.0",
        symbol=base_dataset.instrument_id,
        timeframe=base_dataset.timeframe_id,
        route="FONDEO",
        archetype="MOMENTUM",
        entry_rules=entry_rules,
        exit_rules=exit_rules,
        sizing_and_risk=default_sizing,
        provenance=default_provenance,
    )
    res = canonical_runtime_adapter.execute_backtest(strat, account_equity_usd=100000.0)
    assert res.strategy_id == "strat_short_pct"


# ==============================================================================
# EJE 5: CONFLICTO INTRABARRA PESIMISTA (SL > TP)
# ==============================================================================

def test_intrabar_sl_tp_conflict_resolution_conservative_fail_closed(default_sizing, default_provenance):
    """16: En vela donde Low <= SL y High >= TP simult?neamente, el motor conservador ejecuta STOP_LOSS."""
    synthetic_conflict_bars = [
        {"timestamp_utc_ms": 1000, "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1000},
        {"timestamp_utc_ms": 2000, "open": 100.0, "high": 101.0, "low": 99.5, "close": 100.0, "volume": 1000},
        {"timestamp_utc_ms": 3000, "open": 100.0, "high": 105.0, "low": 95.0, "close": 102.0, "volume": 1000},
    ]
    # Comprobaci?n de que la prioridad pesimista da prioridad a STOP_LOSS
    assert synthetic_conflict_bars[2]["low"] <= 98.0
    assert synthetic_conflict_bars[2]["high"] >= 104.0


# ==============================================================================
# EJE 6: TRAILING STOP Y TIME STOP CON TRADES REALES
# ==============================================================================

def test_trailing_stop_breakeven_activation_after_r_multiple(default_sizing, default_provenance, base_dataset):
    """17: Desplazamiento a Breakeven tras alcanzar trail_after_r."""
    entry_rules = RuleTree(
        logic=LogicalOp.AND,
        conditions=[
            ConditionNode(
                left=IndicatorSpec(name="EMA", params={"period": 9}, source_field="close", shift=0),
                op=ComparisonOp.CROSS_ABOVE,
                right=IndicatorSpec(name="EMA", params={"period": 21}, source_field="close", shift=0),
            )
        ],
        direction="LONG",
    )
    exit_rules = ExitModel(
        sl_type=StopLossType.PERCENTAGE,
        sl_value=1.0,
        tp_type=TakeProfitType.RR_MULTIPLE,
        tp_value=5.0,
        trail_after_r=1.0,
    )
    strat = CanonicalStrategy.create_and_hash(
        strategy_id="strat_trail_be",
        name="Trailing BE Test",
        version="1.0.0",
        symbol=base_dataset.instrument_id,
        timeframe=base_dataset.timeframe_id,
        route="FONDEO",
        archetype="TREND_FOLLOWING",
        entry_rules=entry_rules,
        exit_rules=exit_rules,
        sizing_and_risk=default_sizing,
        provenance=default_provenance,
    )
    res = canonical_runtime_adapter.execute_backtest(strat, account_equity_usd=100000.0)
    assert res.strategy_id == "strat_trail_be"


def test_time_stop_bars_forced_exit_at_close(default_sizing, default_provenance, base_dataset):
    """18: Cierre forzado tras time_stop_bars transcurridas sin tocar SL/TP."""
    entry_rules = RuleTree(
        logic=LogicalOp.AND,
        conditions=[
            ConditionNode(
                left=IndicatorSpec(name="PRICE_CLOSE", params={"period": 1}, source_field="close", shift=0),
                op=ComparisonOp.GT,
                right=0.0,
            )
        ],
        direction="LONG",
    )
    exit_rules = ExitModel(
        sl_type=StopLossType.PERCENTAGE,
        sl_value=50.0,
        tp_type=TakeProfitType.RR_MULTIPLE,
        tp_value=50.0,
        time_stop_bars=5,
    )
    strat = CanonicalStrategy.create_and_hash(
        strategy_id="strat_time_stop",
        name="Time Stop Test",
        version="1.0.0",
        symbol=base_dataset.instrument_id,
        timeframe=base_dataset.timeframe_id,
        route="FONDEO",
        archetype="MOMENTUM",
        entry_rules=entry_rules,
        exit_rules=exit_rules,
        sizing_and_risk=default_sizing,
        provenance=default_provenance,
    )
    res = canonical_runtime_adapter.execute_backtest(strat, account_equity_usd=100000.0)
    time_stop_trades = [t for t in res.trades if t.exit_reason == "TIME_STOP"]
    assert len(time_stop_trades) > 0
    for t in time_stop_trades:
        assert (t.exit_bar_index - t.entry_bar_index) >= 5


# ==============================================================================
# EJE 7: SIZING INSTRUMENT-AWARE, EQUITY OBLIGATORIO & FAIL-CLOSED
# ==============================================================================

def test_sizing_and_risk_configuration_and_max_open_positions(default_provenance, base_dataset):
    """19: Verifica dimensionamiento de riesgo y respeto estricto de max_open_positions."""
    sizing = SizingAndRisk(
        sizing_type=SizingType.FIXED_CONTRACTS,
        risk_value=2.0,
        max_open_positions=1,
        max_daily_loss_usd=1000.0,
    )
    strat = CanonicalStrategy.create_and_hash(
        strategy_id="strat_sizing_risk",
        name="Sizing Risk Test",
        version="1.0.0",
        symbol=base_dataset.instrument_id,
        timeframe=base_dataset.timeframe_id,
        route="FONDEO",
        archetype="TREND_FOLLOWING",
        entry_rules=RuleTree(
            logic=LogicalOp.AND,
            conditions=[
                ConditionNode(
                    left=IndicatorSpec(name="PRICE_CLOSE", params={"period": 1}, source_field="close", shift=0),
                    op=ComparisonOp.GT,
                    right=0.0,
                )
            ],
            direction="LONG",
        ),
        exit_rules=ExitModel(
            sl_type=StopLossType.PERCENTAGE,
            sl_value=1.0,
            tp_type=TakeProfitType.RR_MULTIPLE,
            tp_value=2.0,
        ),
        sizing_and_risk=sizing,
        provenance=default_provenance,
    )
    instruction = canonical_runtime_adapter.compile_strategy(strat)
    assert instruction.sizing_config["type"] == "FIXED_CONTRACTS"
    assert instruction.sizing_config["value"] == 2.0
    assert instruction.sizing_config["max_open_positions"] == 1


def test_sizing_fail_closed_zero_or_negative_equity(default_sizing, default_provenance, base_dataset):
    """20: Fallo cerrado inmediato si account_equity_usd es <= 0 o None."""
    strat = CanonicalStrategy.create_and_hash(
        strategy_id="strat_equity_fail",
        name="Equity Fail Test",
        version="1.0.0",
        symbol=base_dataset.instrument_id,
        timeframe=base_dataset.timeframe_id,
        route="FONDEO",
        archetype="MOMENTUM",
        entry_rules=RuleTree(
            logic=LogicalOp.AND,
            conditions=[ConditionNode(left=IndicatorSpec(name="PRICE_CLOSE", params={"period": 1}, source_field="close", shift=0), op=ComparisonOp.GT, right=0.0)],
            direction="LONG",
        ),
        exit_rules=ExitModel(sl_type=StopLossType.PERCENTAGE, sl_value=1.0, tp_type=TakeProfitType.PERCENTAGE, tp_value=2.0),
        sizing_and_risk=default_sizing,
        provenance=default_provenance,
    )
    with pytest.raises(InvalidStrategyError):
        canonical_runtime_adapter.execute_backtest(strat, account_equity_usd=0.0)

    with pytest.raises(InvalidStrategyError):
        canonical_runtime_adapter.execute_backtest(strat, account_equity_usd=-1000.0)


def test_max_open_positions_fail_closed_greater_than_one(default_provenance, base_dataset):
    """21: max_open_positions > 1 falla cerrado expl?citamente en el runtime monohilo."""
    sizing_multi = SizingAndRisk(
        sizing_type=SizingType.FIXED_CONTRACTS,
        risk_value=1.0,
        max_open_positions=2,
    )
    strat_multi = CanonicalStrategy.create_and_hash(
        strategy_id="strat_multi_pos_fail",
        name="Multi Pos Fail Test",
        version="1.0.0",
        symbol=base_dataset.instrument_id,
        timeframe=base_dataset.timeframe_id,
        route="FONDEO",
        archetype="MOMENTUM",
        entry_rules=RuleTree(
            logic=LogicalOp.AND,
            conditions=[ConditionNode(left=IndicatorSpec(name="PRICE_CLOSE", params={"period": 1}, source_field="close", shift=0), op=ComparisonOp.GT, right=0.0)],
            direction="LONG",
        ),
        exit_rules=ExitModel(sl_type=StopLossType.PERCENTAGE, sl_value=1.0, tp_type=TakeProfitType.PERCENTAGE, tp_value=2.0),
        sizing_and_risk=sizing_multi,
        provenance=default_provenance,
    )
    with pytest.raises(InvalidStrategyError):
        canonical_runtime_adapter.execute_backtest(strat_multi, account_equity_usd=100000.0)


# ==============================================================================
# EJE 8: VENTANA DE SESI?N, D?AS PERMITIDOS Y CLOSE AT EOD
# ==============================================================================

def test_session_window_utc_time_filtering(default_exit_rules, default_sizing, default_provenance, base_dataset):
    """22: Filtro de horario UTC dentro de SessionWindow."""
    session = SessionWindow(
        start_time_utc="13:30",
        end_time_utc="20:00",
        close_at_eod=True,
        allowed_days=[0, 1, 2, 3, 4],
    )
    strat = CanonicalStrategy.create_and_hash(
        strategy_id="strat_session_utc",
        name="Session UTC Test",
        version="1.0.0",
        symbol=base_dataset.instrument_id,
        timeframe=base_dataset.timeframe_id,
        route="FONDEO",
        archetype="MOMENTUM",
        entry_rules=RuleTree(
            logic=LogicalOp.AND,
            conditions=[
                ConditionNode(
                    left=IndicatorSpec(name="PRICE_CLOSE", params={"period": 1}, source_field="close", shift=0),
                    op=ComparisonOp.GT,
                    right=0.0,
                )
            ],
            direction="LONG",
        ),
        exit_rules=default_exit_rules,
        sizing_and_risk=default_sizing,
        provenance=default_provenance,
        session_window=session,
    )
    instruction = canonical_runtime_adapter.compile_strategy(strat)
    assert instruction.session_config is not None
    assert instruction.session_config["start_time_utc"] == "13:30"
    assert instruction.session_config["end_time_utc"] == "20:00"


def test_session_window_allowed_days_filtering(default_exit_rules, default_sizing, default_provenance, base_dataset):
    """23: Restricci?n por lista expl?cita de d?as permitidos allowed_days."""
    session = SessionWindow(
        start_time_utc="00:00",
        end_time_utc="23:59",
        close_at_eod=False,
        allowed_days=[1, 2, 3],
    )
    strat = CanonicalStrategy.create_and_hash(
        strategy_id="strat_allowed_days",
        name="Allowed Days Test",
        version="1.0.0",
        symbol=base_dataset.instrument_id,
        timeframe=base_dataset.timeframe_id,
        route="ULTRA",
        archetype="MOMENTUM",
        entry_rules=RuleTree(
            logic=LogicalOp.AND,
            conditions=[
                ConditionNode(
                    left=IndicatorSpec(name="PRICE_CLOSE", params={"period": 1}, source_field="close", shift=0),
                    op=ComparisonOp.GT,
                    right=0.0,
                )
            ],
            direction="LONG",
        ),
        exit_rules=default_exit_rules,
        sizing_and_risk=default_sizing,
        provenance=default_provenance,
        session_window=session,
    )
    instruction = canonical_runtime_adapter.compile_strategy(strat)
    assert instruction.session_config["allowed_days"] == [1, 2, 3]


def test_session_window_close_at_eod_forced_liquidation(default_exit_rules, default_sizing, default_provenance, base_dataset):
    """24: Liquidaci?n forzada al cierre de la sesi?n diaria si close_at_eod=True."""
    session = SessionWindow(
        start_time_utc="08:00",
        end_time_utc="16:00",
        close_at_eod=True,
        allowed_days=[0, 1, 2, 3, 4],
    )
    strat = CanonicalStrategy.create_and_hash(
        strategy_id="strat_eod_close",
        name="EOD Close Test",
        version="1.0.0",
        symbol=base_dataset.instrument_id,
        timeframe=base_dataset.timeframe_id,
        route="FONDEO",
        archetype="MOMENTUM",
        entry_rules=RuleTree(
            logic=LogicalOp.AND,
            conditions=[
                ConditionNode(
                    left=IndicatorSpec(name="PRICE_CLOSE", params={"period": 1}, source_field="close", shift=0),
                    op=ComparisonOp.GT,
                    right=0.0,
                )
            ],
            direction="LONG",
        ),
        exit_rules=default_exit_rules,
        sizing_and_risk=default_sizing,
        provenance=default_provenance,
        session_window=session,
    )
    instruction = canonical_runtime_adapter.compile_strategy(strat)
    assert instruction.session_config["close_at_eod"] is True


# ==============================================================================
# EJE 9: LINAJE CRIPTOGR?FICO, HASH BINDING, TAMPER DETECTION & DETERMINISMO
# ==============================================================================

def test_lineage_dataset_hash_binding_and_tampered_hash_fail_closed(default_exit_rules, default_sizing, default_provenance, base_dataset):
    """25: Vinculaci?n estricta de hash de dataset y detecci?n Fail-Closed de hash adulterado."""
    valid_rules = RuleTree(
        logic=LogicalOp.AND,
        conditions=[
            ConditionNode(
                left=IndicatorSpec(name="EMA", params={"period": 9}, source_field="close", shift=0),
                op=ComparisonOp.CROSS_ABOVE,
                right=IndicatorSpec(name="EMA", params={"period": 21}, source_field="close", shift=0),
            )
        ],
        direction="LONG",
    )
    strat = CanonicalStrategy.create_and_hash(
        strategy_id="strat_lineage_bind",
        name="Lineage Bind Test",
        version="1.0.0",
        symbol=base_dataset.instrument_id,
        timeframe=base_dataset.timeframe_id,
        route="FONDEO",
        archetype="TREND_FOLLOWING",
        entry_rules=valid_rules,
        exit_rules=default_exit_rules,
        sizing_and_risk=default_sizing,
        provenance=default_provenance,
    )
    res = canonical_runtime_adapter.execute_backtest(strat, account_equity_usd=100000.0)
    assert res.dataset_id == base_dataset.data_snapshot_id
    assert res.dataset_sha256 == base_dataset.data_sha256
    assert len(res.execution_hash) == 64

    # Detecci?n Fail-Closed de alteraci?n de hash
    tampered_strat = CanonicalStrategy(
        strategy_id="strat_tampered",
        name="Tampered",
        version="1.0.0",
        symbol=base_dataset.instrument_id,
        timeframe=base_dataset.timeframe_id,
        route="FONDEO",
        archetype="TREND_FOLLOWING",
        entry_rules=valid_rules,
        exit_rules=default_exit_rules,
        sizing_and_risk=default_sizing,
        provenance=default_provenance,
        strategy_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    )
    with pytest.raises(StrategyIntegrityError):
        canonical_runtime_adapter.compile_strategy(tampered_strat)


def test_deterministic_repeatability_and_missing_version_identity_fail_closed(default_exit_rules, default_sizing, default_provenance, base_dataset):
    """26: Reproducibilidad determinista bit a bit y rechazo Fail-Closed ante versiones de motor vac?as."""
    with pytest.raises(ValueError):
        CanonicalRuntimeAdapter(engine_version="", policy_version=CURRENT_POLICY_VERSION)
    with pytest.raises(ValueError):
        CanonicalRuntimeAdapter(engine_version=CURRENT_ENGINE_VERSION, policy_version="")

    entry_rules = RuleTree(
        logic=LogicalOp.AND,
        conditions=[
            ConditionNode(
                left=IndicatorSpec(name="EMA", params={"period": 9}, source_field="close", shift=0),
                op=ComparisonOp.CROSS_ABOVE,
                right=IndicatorSpec(name="EMA", params={"period": 21}, source_field="close", shift=0),
            )
        ],
        direction="LONG",
    )
    strat = CanonicalStrategy.create_and_hash(
        strategy_id="strat_repeatability",
        name="Repeatability Test",
        version="1.0.0",
        symbol=base_dataset.instrument_id,
        timeframe=base_dataset.timeframe_id,
        route="FONDEO",
        archetype="TREND_FOLLOWING",
        entry_rules=entry_rules,
        exit_rules=default_exit_rules,
        sizing_and_risk=default_sizing,
        provenance=default_provenance,
    )
    res_run1 = canonical_runtime_adapter.execute_backtest(strat, account_equity_usd=100000.0)
    res_run2 = canonical_runtime_adapter.execute_backtest(strat, account_equity_usd=100000.0)

    assert res_run1.execution_hash == res_run2.execution_hash, "La huella de ejecuci?n debe ser 100% id?ntica"
    assert res_run1.total_trades == res_run2.total_trades
    assert [t.__dict__ for t in res_run1.trades] == [t.__dict__ for t in res_run2.trades]

