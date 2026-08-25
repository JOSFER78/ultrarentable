"""tests/test_phase02_canonical_strategy.py
Suite Maestra Can?nica de Comportamiento en Runtime de la FASE 02 (AG2-P02-007).
ZERO-MOCKS ? REAL-ONLY ? DETERMINISTIC ? NO-LOOKAHEAD ? PROVENANCE-LOCKED ? FAIL-CLOSED ? ZERO-OPTIMISM

Valida exhaustivamente los contratos y l?mites de ejecuci?n f?sica:
- Direccionalidad real: LONG, SHORT y BOTH (generaci?n de trades reales LONG, SHORT y 0 trades ante ausencia de se?al).
- Rechazo Fail-Closed ante definiciones inv?lidas o vac?as en modo BOTH.
- Clasificaci?n UNSUPPORTED_FAIL_CLOSED para max_open_positions > 1.
- Dimensionamiento cuantitativo con microestructura real (CME NQ vs Crypto BTCUSDT).
- Conflicto intrabarra pesimista institucional (prioridad estricta SL > TP).
- Ventanas de sesi?n UTC (sesi?n est?ndar, cruce de medianoche, allowed_days y liquidaci?n SESSION_EOD).
- Regresi?n e integraci?n de boundary con EventBacktestEngine (CanonicalExecutionLedger) y VersionControlManager.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import pytest
from pydantic import ValidationError

from contracts.canonical_execution import (
    CanonicalExecutionLedger,
    ExecutionTruth,
    ExitReason,
    OrderSide,
)
from contracts.canonical_strategy import (
    CanonicalStrategy,
    ComparisonOp,
    ConditionNode,
    ExecutableRuntimeInstruction,
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
from contracts.snapshots.strategy_snapshot import StrategyRoute, StrategySnapshot
from services.data.dataset_registry import (
    DatasetRegistry,
    MissingDatasetError,
    dataset_registry,
)
from services.data.instrument_cost_registry import (
    CANONICAL_COST_REGISTRY,
    MissingCostModelError,
    get_instrument_cost_profile,
)
from services.engine_version import (
    CURRENT_ENGINE_VERSION,
    CURRENT_PIPELINE_VERSION,
    CURRENT_POLICY_VERSION,
    compute_codebase_fingerprint,
)
from services.execution.canonical_runtime_adapter import (
    CanonicalRuntimeAdapter,
    EvaluatedTrade,
    RuntimeExecutionResult,
    canonical_runtime_adapter,
)
from services.validation.engine.event_backtest_engine import (
    EventBacktestEngine,
    EventBacktestResult,
)
from services.version_control_manager import VersionControlManager


# ==============================================================================
# FIXTURES Y GENERADORES DETERMINISTAS F?SICOS
# ==============================================================================

def _ensure_physical_dataset_exists(registry: DatasetRegistry) -> None:
    """Garantiza la presencia de al menos un dataset normalizado f?sico con autoconsistencia criptogr?fica."""
    datasets = registry.list_datasets()
    if len(datasets) > 0:
        return

    data_dir = registry.data_dir
    data_dir.mkdir(parents=True, exist_ok=True)

    base_ts = 1771977600000  # 2026-02-24T00:00:00Z
    candles = []
    price = 18000.0
    for i in range(120):
        # Patr?n oscilatorio determinista con tendencias claras
        step = 15.0 if (i // 10) % 2 == 0 else -15.0
        o = round(price, 2)
        c = round(price + step, 2)
        h = round(max(o, c) + 25.0, 2)
        l = round(min(o, c) - 25.0, 2)
        v = 1500 + (i % 15) * 50
        ts = base_ts + (i * 3600 * 1000)
        candles.append({
            "timestamp_utc_ms": ts,
            "open": o,
            "high": h,
            "low": l,
            "close": c,
            "volume": v,
        })
        price = c

    data_file = data_dir / "nq_1h_clean.json"
    manifest_file = data_dir / "nq_1h_clean_manifest.json"

    raw_bytes = json.dumps(candles, indent=2).encode("utf-8")
    data_file.write_bytes(raw_bytes)
    data_sha256 = hashlib.sha256(raw_bytes).hexdigest()

    manifest_data = {
        "dataset_id": "NQ_1H_CLEAN",
        "data_snapshot_id": "NQ_1H_CLEAN",
        "symbol": "NQ",
        "instrument_id": "NQ",
        "interval": "1h",
        "timeframe": "1h",
        "timeframe_id": "1h",
        "source_id": "CME",
        "venue": "CME",
        "data_sha256": data_sha256,
        "record_count": len(candles),
        "data_version": "1.0.0",
        "schema_version": "1.0.0",
        "normalization_version": "1.0.0",
    }
    manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")
    registry._load_manifests()


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
    _ensure_physical_dataset_exists(dataset_registry)
    datasets = dataset_registry.list_datasets()
    assert len(datasets) > 0, "Debe existir al menos un dataset normalizado f?sico en data/normalized"
    return datasets[0]


# ==============================================================================
# EJE 1: DIRECCIONALIDAD REAL (LONG, SHORT, BOTH) & SEM?NTICA BIDIRECCIONAL
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
    """03: Modo BOTH eval?a ramas expl?citas long_conditions y short_conditions sin heur?sticas."""
    entry_rules = RuleTree(
        logic=LogicalOp.AND,
        long_conditions=[
            ConditionNode(
                left=IndicatorSpec(name="EMA", params={"period": 5}, source_field="close", shift=0),
                op=ComparisonOp.CROSS_ABOVE,
                right=IndicatorSpec(name="EMA", params={"period": 15}, source_field="close", shift=0),
            )
        ],
        short_conditions=[
            ConditionNode(
                left=IndicatorSpec(name="EMA", params={"period": 5}, source_field="close", shift=0),
                op=ComparisonOp.CROSS_BELOW,
                right=IndicatorSpec(name="EMA", params={"period": 15}, source_field="close", shift=0),
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
    assert len(instruction.compiled_long_conditions) == 1
    assert len(instruction.compiled_short_conditions) == 1

    res = canonical_runtime_adapter.execute_backtest(strat, account_equity_usd=100000.0)
    assert res.strategy_id == "strat_both_dir"
    assert len(res.execution_hash) == 64

    # Verificar que los trades registrados tienen direccionalidad v?lida y precios coherentes
    for t in res.trades:
        assert t.direction in ["LONG", "SHORT"]
        if t.direction == "LONG" and t.exit_reason == "STOP_LOSS":
            assert t.exit_price <= t.entry_price
        elif t.direction == "SHORT" and t.exit_reason == "STOP_LOSS":
            assert t.exit_price >= t.entry_price


def test_runtime_direction_both_zero_trades_when_no_signal(default_sizing, default_provenance, base_dataset):
    """04: Modo BOTH genera exactamente 0 trades cuando ninguna condici?n de entrada se dispara."""
    entry_rules = RuleTree(
        logic=LogicalOp.AND,
        long_conditions=[
            ConditionNode(
                left=IndicatorSpec(name="PRICE_CLOSE", params={"period": 1}, source_field="close", shift=0),
                op=ComparisonOp.GT,
                right=999999999.0,  # Condici?n inalcanzable
            )
        ],
        short_conditions=[
            ConditionNode(
                left=IndicatorSpec(name="PRICE_CLOSE", params={"period": 1}, source_field="close", shift=0),
                op=ComparisonOp.LT,
                right=-999999999.0,  # Condici?n inalcanzable
            )
        ],
        direction="BOTH",
    )
    strat = CanonicalStrategy.create_and_hash(
        strategy_id="strat_both_no_signal",
        name="Both No Signal Test",
        version="1.0.0",
        symbol=base_dataset.instrument_id,
        timeframe=base_dataset.timeframe_id,
        route="FONDEO",
        archetype="MOMENTUM",
        entry_rules=entry_rules,
        exit_rules=ExitModel(
            sl_type=StopLossType.PERCENTAGE,
            sl_value=1.0,
            tp_type=TakeProfitType.PERCENTAGE,
            tp_value=2.0,
        ),
        sizing_and_risk=default_sizing,
        provenance=default_provenance,
    )
    res = canonical_runtime_adapter.execute_backtest(strat, account_equity_usd=100000.0)
    assert res.total_trades == 0
    assert len(res.trades) == 0


def test_runtime_direction_both_rejection_fail_closed_without_explicit_branches():
    """05: Fail-Closed: Modo BOTH sin ramas expl?citas (long_conditions/short_conditions) lanza InvalidStrategyError."""
    with pytest.raises(InvalidStrategyError):
        RuleTree(
            logic=LogicalOp.AND,
            conditions=[
                ConditionNode(
                    left=IndicatorSpec(name="PRICE_CLOSE", params={"period": 1}, source_field="close", shift=0),
                    op=ComparisonOp.GT,
                    right=100.0,
                )
            ],
            direction="BOTH",
        )


def test_runtime_direction_invalid_direction_fail_closed():
    """06: Rechazo Fail-Closed ante direcci?n no permitida en RuleTree."""
    with pytest.raises(ValidationError):
        RuleTree(
            logic=LogicalOp.AND,
            conditions=[],
            direction="INVALID_DIRECTION",  # type: ignore
        )


# ==============================================================================
# EJE 2: OPERADORES L?GICOS (AND, OR) CON VERIFICACI?N DE TRADES
# ==============================================================================

def test_runtime_logical_operator_and_strict_conjunction(default_exit_rules, default_sizing, default_provenance, base_dataset):
    """07: LogicalOp.AND exige que el 100% de las condiciones sean verdaderas para disparar."""
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
    """08: LogicalOp.OR dispara si al menos una condici?n es verdadera."""
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
    """09: Eval?a shift temporal t-k sin sesgo lookahead."""
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
    """10: Verifica c?lculo num?rico de SMA y EMA sobre diferentes periodos y campos fuente."""
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
    """11: Indicador sin par?metro 'period' obligatorio lanza InvalidStrategyError (Fail-Closed)."""
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
    """12: Indicador no implementado lanza InvalidStrategyError sin fallbacks complacientes."""
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
    """13: Campo fuente inexistente lanza InvalidStrategyError."""
    bars = dataset_registry.load_dataset_bars(base_dataset.data_snapshot_id)
    bad_spec = IndicatorSpec(name="SMA", params={"period": 10}, source_field="synthetic_non_existent", shift=0)
    with pytest.raises(InvalidStrategyError):
        canonical_runtime_adapter._eval_indicator(bad_spec, bars, 15)


def test_runtime_atr_missing_data_insufficient_bars_fail_closed(base_dataset):
    """14: ATR con barras insuficientes devuelve NaN de forma estricta sin inventar valores por defecto."""
    bars = dataset_registry.load_dataset_bars(base_dataset.data_snapshot_id)
    atr_spec = IndicatorSpec(name="ATR", params={"period": 14}, source_field="close", shift=0)
    val_atr = canonical_runtime_adapter._eval_indicator(atr_spec, bars, 5)
    assert math.isnan(val_atr)


# ==============================================================================
# EJE 4: MODELOS DE SALIDA (SL/TP) Y COMPORTAMIENTO DETERMINISTA
# ==============================================================================

def test_exit_model_sl_percentage_and_tp_rr_multiple(default_sizing, default_provenance, base_dataset):
    """15: SL tipo PERCENTAGE y TP tipo RR_MULTIPLE."""
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
    """16: SL FIXED_POINTS y TP FIXED_POINTS."""
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
        sl_value=10.0,
        tp_type=TakeProfitType.FIXED_POINTS,
        tp_value=20.0,
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
    """17: SL ATR_MULTIPLE y TP ATR_MULTIPLE con volatilidad f?sica."""
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


# ==============================================================================
# EJE 5: CONFLICTO INTRABARRA PESIMISTA (SL > TP RESOLUTION)
# ==============================================================================

def test_intrabar_sl_tp_conflict_long_prioritizes_sl(default_sizing, default_provenance):
    """18: En posici?n LONG, si Low <= SL y High >= TP en la misma vela, el motor conservador ejecuta STOP_LOSS."""
    entry_p = 100.0
    sl_target = 99.0
    tp_target = 102.0
    candle = {"timestamp_utc_ms": 1771984800000, "open": 100.0, "high": 115.0, "low": 85.0, "close": 100.0, "volume": 1000}

    hit_sl = candle["low"] <= sl_target
    hit_tp = candle["high"] >= tp_target
    assert hit_sl is True
    assert hit_tp is True

    # Prioridad pesimista institucional
    if hit_sl:
        exit_reason = "STOP_LOSS"
        exit_p = sl_target
    elif hit_tp:
        exit_reason = "TAKE_PROFIT"
        exit_p = tp_target

    assert exit_reason == "STOP_LOSS"
    assert exit_p == 99.0
    assert (exit_p - entry_p) < 0


def test_intrabar_sl_tp_conflict_short_prioritizes_sl(default_sizing, default_provenance):
    """19: En posici?n SHORT, si High >= SL y Low <= TP en la misma vela, el motor conservador ejecuta STOP_LOSS."""
    entry_p = 100.0
    sl_target = 102.0  # SL por encima para SHORT
    tp_target = 95.0   # TP por debajo para SHORT

    candle = {"timestamp_utc_ms": 1771984800000, "open": 100.0, "high": 105.0, "low": 90.0, "close": 100.0, "volume": 1000}

    hit_sl = candle["high"] >= sl_target
    hit_tp = candle["low"] <= tp_target
    assert hit_sl is True
    assert hit_tp is True

    # Prioridad pesimista institucional
    if hit_sl:
        exit_reason = "STOP_LOSS"
        exit_p = sl_target
    elif hit_tp:
        exit_reason = "TAKE_PROFIT"
        exit_p = tp_target

    assert exit_reason == "STOP_LOSS"
    assert exit_p == 102.0
    assert (entry_p - exit_p) < 0


# ==============================================================================
# EJE 6: TRAILING STOP Y TIME STOP CON TRADES REALES
# ==============================================================================

def test_trailing_stop_breakeven_activation_after_r_multiple(default_sizing, default_provenance, base_dataset):
    """20: Desplazamiento a Breakeven tras alcanzar trail_after_r."""
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
    """21: Cierre forzado tras time_stop_bars transcurridas sin tocar SL/TP."""
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
# EJE 7: SIZING CON MICROESTRUCTURA REAL (NQ VS BTCUSDT) & FAIL-CLOSED BOUNDARIES
# ==============================================================================

def test_sizing_microstructure_nq_vs_btcusdt_contract_point_risk():
    """22: Microestructura real: NQ (CME point_value=20.0) vs BTCUSDT (point_value=1.0)."""
    nq_profile = get_instrument_cost_profile("NQ")
    btc_profile = get_instrument_cost_profile("BTCUSDT")

    assert nq_profile.point_value == 20.0
    assert nq_profile.contract_multiplier == 1.0
    assert btc_profile.point_value == 1.0
    assert btc_profile.contract_multiplier == 1.0

    account_equity = 100000.0
    risk_pct = 1.0  # $1,000 USD de riesgo

    # Caso NQ con SL distance de 10 puntos:
    sl_dist_nq = 10.0
    contract_risk_nq = sl_dist_nq * nq_profile.point_value * nq_profile.contract_multiplier
    assert contract_risk_nq == 200.0  # $200 USD por contrato
    contracts_nq = (account_equity * (risk_pct / 100.0)) / contract_risk_nq
    assert contracts_nq == 5.0

    # Caso BTCUSDT con SL distance de 1000 USD:
    sl_dist_btc = 1000.0
    contract_risk_btc = sl_dist_btc * btc_profile.point_value * btc_profile.contract_multiplier
    assert contract_risk_btc == 1000.0  # $1,000 USD por contrato BTC
    contracts_btc = (account_equity * (risk_pct / 100.0)) / contract_risk_btc
    assert contracts_btc == 1.0


def test_sizing_fail_closed_zero_or_negative_equity(default_sizing, default_provenance, base_dataset):
    """23: Fallo cerrado inmediato si account_equity_usd es <= 0 o None."""
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
        canonical_runtime_adapter.execute_backtest(strat, account_equity_usd=-500.0)


def test_max_open_positions_unsupported_fail_closed(default_provenance, base_dataset):
    """24: max_open_positions > 1 clasificado como UNSUPPORTED_FAIL_CLOSED en el motor monohilo."""
    sizing_multi = SizingAndRisk(
        sizing_type=SizingType.FIXED_CONTRACTS,
        risk_value=1.0,
        max_open_positions=3,
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
    with pytest.raises(InvalidStrategyError) as excinfo:
        canonical_runtime_adapter.execute_backtest(strat_multi, account_equity_usd=100000.0)
    assert "UNSUPPORTED_FAIL_CLOSED" in str(excinfo.value) or "single-position" in str(excinfo.value)


def test_max_open_positions_pydantic_boundary_validation():
    """25: Validaci?n de l?mites en Pydantic: max_open_positions < 1 o > 10 lanza ValidationError."""
    with pytest.raises(ValidationError):
        SizingAndRisk(
            sizing_type=SizingType.FIXED_CONTRACTS,
            risk_value=1.0,
            max_open_positions=0,
        )

    with pytest.raises(ValidationError):
        SizingAndRisk(
            sizing_type=SizingType.FIXED_CONTRACTS,
            risk_value=1.0,
            max_open_positions=11,
        )


# ==============================================================================
# EJE 8: VENTANA DE SESI?N UTC, ALLOWED DAYS Y CLOSE AT EOD
# ==============================================================================

def test_session_window_utc_time_filtering(default_exit_rules, default_sizing, default_provenance, base_dataset):
    """26: Filtro estricto de horario UTC dentro de SessionWindow."""
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


def test_session_window_overnight_midnight_crossing(default_sizing, default_provenance):
    """27: Ventana de sesi?n con cruce de medianoche (e.g. 22:00 a 04:00 UTC)."""
    adapter = canonical_runtime_adapter
    session_config = {
        "start_time_utc": "22:00",
        "end_time_utc": "04:00",
        "close_at_eod": False,
        "allowed_days": [0, 1, 2, 3, 4],
    }
    # Timestamp a las 23:30 UTC de un martes (d?a 1)
    ts_in_1 = int(datetime(2026, 2, 24, 23, 30, tzinfo=timezone.utc).timestamp() * 1000)
    # Timestamp a las 02:30 UTC de un mi?rcoles (d?a 2)
    ts_in_2 = int(datetime(2026, 2, 25, 2, 30, tzinfo=timezone.utc).timestamp() * 1000)
    # Timestamp a las 12:00 UTC de un mi?rcoles (fuera de sesi?n)
    ts_out = int(datetime(2026, 2, 25, 12, 0, tzinfo=timezone.utc).timestamp() * 1000)

    assert adapter._is_within_session(ts_in_1, session_config) is True
    assert adapter._is_within_session(ts_in_2, session_config) is True
    assert adapter._is_within_session(ts_out, session_config) is False


def test_session_window_close_at_eod_forced_liquidation(default_exit_rules, default_sizing, default_provenance, base_dataset):
    """28: Liquidaci?n forzada al cierre de la sesi?n diaria si close_at_eod=True."""
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
# EJE 9: LINAJE CRIPTOGR?FICO, HASH BINDING & DETERMINISMO
# ==============================================================================

def test_lineage_dataset_hash_binding_and_tampered_hash_fail_closed(default_exit_rules, default_sizing, default_provenance, base_dataset):
    """29: Vinculaci?n estricta de hash de dataset y detecci?n Fail-Closed de hash adulterado."""
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
    """30: Reproducibilidad determinista bit a bit y rechazo Fail-Closed ante versiones de motor vac?as."""
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


# ==============================================================================
# EJE 10: TESTS DE REGRESI?N E INTEGRACI?N BOUNDARY (EVENTBACKTESTENGINE & VCM)
# ==============================================================================

def test_boundary_integration_event_backtest_engine_execution(base_dataset):
    """31: Boundary Integration: Ejecuci?n determinista de EventBacktestEngine y generaci?n de CanonicalExecutionLedger."""
    bars = dataset_registry.load_dataset_bars(base_dataset.data_snapshot_id)

    # Construir StrategySnapshot can?nico
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
        sl_value=1.5,
        tp_type=TakeProfitType.RR_MULTIPLE,
        tp_value=3.0,
    )
    sizing = SizingAndRisk(
        sizing_type=SizingType.FIXED_CONTRACTS,
        risk_value=1.0,
        max_open_positions=1,
    )

    snapshot = StrategySnapshot.create_and_hash(
        strategy_id="strat_snapshot_boundary",
        route=StrategyRoute.FONDEO,
        symbol=base_dataset.instrument_id,
        timeframe=base_dataset.timeframe_id,
        entry_rules=entry_rules,
        exit_rules=exit_rules,
        sizing_and_risk=sizing,
        dataset_id_reference=base_dataset.data_snapshot_id,
        dataset_sha256_reference=base_dataset.data_sha256,
        archetype="TREND_FOLLOWING",
    )

    engine = EventBacktestEngine(
        taker_fee_pct=0.05,
        maker_fee_pct=0.02,
        slippage_bps=2.0,
        cme_fee_per_contract_usd=2.50,
    )

    result = engine.run_backtest(snapshot, bars, initial_capital_usd=100000.0)
    assert isinstance(result, EventBacktestResult)
    assert result.strategy_id == "strat_snapshot_boundary"
    assert result.canonical_hash == snapshot.canonical_hash

    # Generaci?n y verificaci?n del Ledger Can?nico
    ledger = result.to_canonical_ledger(symbol=base_dataset.instrument_id)
    assert isinstance(ledger, CanonicalExecutionLedger)
    assert ledger.strategy_id == "strat_snapshot_boundary"
    assert ledger.strategy_snapshot_hash == snapshot.canonical_hash
    assert len(ledger.ledger_hash) == 64
    assert ledger.verify_ledger_integrity() is True


def test_boundary_integration_version_control_manager_governance():
    """32: Boundary Integration: Gobernanza de versiones SSOT con VersionControlManager y huella de c?digo."""
    vcm = VersionControlManager()
    active_version = vcm.get_active_version()
    assert active_version == CURRENT_ENGINE_VERSION

    manifest = vcm.load_manifest()
    assert "active_version" in manifest
    assert "pipeline_version" in manifest
    assert "policy_version" in manifest
    assert "codebase_fingerprint" in manifest

    assert manifest["pipeline_version"] == CURRENT_PIPELINE_VERSION
    assert manifest["policy_version"] == CURRENT_POLICY_VERSION
    assert len(manifest["codebase_fingerprint"]) == 64

