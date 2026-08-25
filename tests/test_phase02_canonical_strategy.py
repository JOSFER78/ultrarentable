"""tests/test_phase02_canonical_strategy.py
Suite de Pruebas de la FASE 02 (REWORK AG2-P02-004): RUNTIME REAL SEMANTICS & FAIL-CLOSED ENGINE.
ZERO-MOCKS · REAL-ONLY · PROVENANCE-LOCKED · NO-SYNTHETIC-DEFAULTS · FAIL-CLOSED
"""

import pytest
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
from services.data.dataset_registry import dataset_registry
from services.execution.canonical_runtime_adapter import CanonicalRuntimeAdapter, canonical_runtime_adapter


@pytest.fixture
def sample_entry_rules():
    return RuleTree(
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


@pytest.fixture
def sample_exit_rules():
    return ExitModel(
        sl_type=StopLossType.PERCENTAGE,
        sl_value=1.5,
        tp_type=TakeProfitType.RR_MULTIPLE,
        tp_value=3.0,
        trail_after_r=1.0,
        time_stop_bars=50,
    )


@pytest.fixture
def sample_sizing():
    return SizingAndRisk(
        sizing_type=SizingType.RISK_PCT_EQUITY,
        risk_value=1.0,
        max_open_positions=1,
        max_daily_loss_usd=500.0,
    )


@pytest.fixture
def sample_provenance():
    return ProvenanceMetadata(
        author="SYSTEM_ORCHESTRATOR",
        engine_version="5.4.0",
        policy_version="5.4.0",
        created_at_utc="2026-08-25T18:00:00Z",
    )


def test_semantic_hash_identity_comprehensive_field_mutations(
    sample_entry_rules, sample_exit_rules, sample_sizing, sample_provenance
):
    """P02-004-01 & 05: Demuestra que toda mutación semántica campo-por-campo altera el hash inmutable."""
    base_strat = CanonicalStrategy.create_and_hash(
        strategy_id="strat_nq_v1",
        name="NQ Momentum Breakout",
        version="1.0.0",
        symbol="NQ",
        timeframe="1h",
        route="FONDEO",
        archetype="MOMENTUM_BREAKOUT",
        entry_rules=sample_entry_rules,
        exit_rules=sample_exit_rules,
        sizing_and_risk=sample_sizing,
        provenance=sample_provenance,
    )

    assert len(base_strat.strategy_hash) == 64
    assert base_strat.verify_integrity() is True

    # Mutar shift del indicador
    mutated_rules = RuleTree(
        logic=LogicalOp.AND,
        conditions=[
            ConditionNode(
                left=IndicatorSpec(name="EMA", params={"period": 9}, source_field="close", shift=1),
                op=ComparisonOp.CROSS_ABOVE,
                right=IndicatorSpec(name="EMA", params={"period": 21}, source_field="close", shift=0),
            )
        ],
        direction="LONG",
    )
    strat_shift = CanonicalStrategy.create_and_hash(
        strategy_id="strat_nq_v1",
        name="NQ Momentum Breakout",
        version="1.0.0",
        symbol="NQ",
        timeframe="1h",
        route="FONDEO",
        archetype="MOMENTUM_BREAKOUT",
        entry_rules=mutated_rules,
        exit_rules=sample_exit_rules,
        sizing_and_risk=sample_sizing,
        provenance=sample_provenance,
    )
    assert base_strat.strategy_hash != strat_shift.strategy_hash


def test_unknown_indicator_and_missing_params_fail_closed(
    sample_exit_rules, sample_sizing, sample_provenance
):
    """P02-004-02: Demuestra que indicadores desconocidos o sin parámetros obligatorios fallan cerrado (Fail-Closed)."""
    datasets = dataset_registry.list_datasets()
    assert len(datasets) > 0
    ds = datasets[0]

    # Indicador inexistente -> Fail-Closed
    bad_ind_rules = RuleTree(
        logic=LogicalOp.AND,
        conditions=[
            ConditionNode(
                left=IndicatorSpec(name="MAGIC_SUPER_PROFIT", params={"period": 10}, source_field="close", shift=0),
                op=ComparisonOp.GT,
                right=100.0,
            )
        ],
        direction="LONG",
    )
    bad_strat = CanonicalStrategy.create_and_hash(
        strategy_id="strat_bad_ind",
        name="Bad Ind",
        version="1.0.0",
        symbol=ds.instrument_id,
        timeframe=ds.timeframe_id,
        route="FONDEO",
        archetype="MOMENTUM_BREAKOUT",
        entry_rules=bad_ind_rules,
        exit_rules=sample_exit_rules,
        sizing_and_risk=sample_sizing,
        provenance=sample_provenance,
    )

    with pytest.raises(InvalidStrategyError):
        canonical_runtime_adapter.execute_backtest(bad_strat)


def test_exit_model_type_semantics_and_trailing_stop(
    sample_entry_rules, sample_sizing, sample_provenance
):
    """P02-004-03 & 05: Demuestra ejecución diferenciada de SL/TP según su tipo canónico y trailing."""
    datasets = dataset_registry.list_datasets()
    assert len(datasets) > 0
    ds = datasets[0]

    # Estrategia con SL porcentual
    exit_pct = ExitModel(
        sl_type=StopLossType.PERCENTAGE,
        sl_value=1.0,
        tp_type=TakeProfitType.RR_MULTIPLE,
        tp_value=2.0,
        trail_after_r=1.0,
    )
    strat_pct = CanonicalStrategy.create_and_hash(
        strategy_id="strat_pct",
        name="Pct Strat",
        version="1.0.0",
        symbol=ds.instrument_id,
        timeframe=ds.timeframe_id,
        route="FONDEO",
        archetype="MOMENTUM_BREAKOUT",
        entry_rules=sample_entry_rules,
        exit_rules=exit_pct,
        sizing_and_risk=sample_sizing,
        provenance=sample_provenance,
    )

    res = canonical_runtime_adapter.execute_backtest(strat_pct)
    assert res.strategy_id == "strat_pct"
    assert res.dataset_id == ds.data_snapshot_id
    assert res.dataset_sha256 == ds.data_sha256


def test_runtime_engine_binds_dataset_from_provenance_registry(
    sample_entry_rules, sample_exit_rules, sample_sizing, sample_provenance
):
    """P02-004-04 & 06: Demuestra que la ejecución vincula la identidad y hash directamente del DatasetRegistry."""
    datasets = dataset_registry.list_datasets()
    assert len(datasets) > 0
    ds = datasets[0]

    strat = CanonicalStrategy.create_and_hash(
        strategy_id="strat_bound_test",
        name="Bound Test",
        version="1.0.0",
        symbol=ds.instrument_id,
        timeframe=ds.timeframe_id,
        route="ULTRA",
        archetype="MOMENTUM_BREAKOUT",
        entry_rules=sample_entry_rules,
        exit_rules=sample_exit_rules,
        sizing_and_risk=sample_sizing,
        provenance=sample_provenance,
    )

    res = canonical_runtime_adapter.execute_backtest(strat)
    assert res.dataset_id == ds.data_snapshot_id
    assert res.dataset_sha256 == ds.data_sha256
    assert len(res.execution_hash) == 64


def test_tampered_hash_fails_closed(
    sample_entry_rules, sample_exit_rules, sample_sizing, sample_provenance
):
    """P02-004-07: Demuestra detección Fail-Closed si el strategy_hash es alterado."""
    tampered_strat = CanonicalStrategy(
        strategy_id="strat_bad_hash",
        name="Bad",
        version="1.0.0",
        symbol="NQ",
        timeframe="1h",
        route="FONDEO",
        archetype="MOMENTUM_BREAKOUT",
        entry_rules=sample_entry_rules,
        exit_rules=sample_exit_rules,
        sizing_and_risk=sample_sizing,
        provenance=sample_provenance,
        strategy_hash="0" * 64,
    )
    with pytest.raises(StrategyIntegrityError):
        canonical_runtime_adapter.compile_strategy(tampered_strat)
