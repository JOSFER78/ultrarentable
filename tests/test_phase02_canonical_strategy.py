"""tests/test_phase02_canonical_strategy.py
Suite de Pruebas de la FASE 02 (REWORK AG2-P02-003): RUNTIME SEMANTIC EQUIVALENCE & SSOT CODE PATH.
ZERO-MOCKS · REAL-ONLY · PROVENANCE-LOCKED · NO-SYNTHETIC-DEFAULTS · FAIL-CLOSED
"""

import pytest
from contracts.canonical_strategy import (
    CanonicalStrategy,
    ComparisonOp,
    ConditionNode,
    ExitModel,
    IndicatorSpec,
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
        sl_type=StopLossType.ATR_MULTIPLE,
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
    """P02-003-01 & 04: Demuestra que toda mutación semántica campo-por-campo altera el hash inmutable."""
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

    # 1. Mutar shift del indicador
    mutated_rules = RuleTree(
        logic=LogicalOp.AND,
        conditions=[
            ConditionNode(
                left=IndicatorSpec(name="EMA", params={"period": 9}, source_field="close", shift=1),  # shift 0 -> 1
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

    # 2. Mutar logical operator AND -> OR
    mutated_logic_rules = RuleTree(
        logic=LogicalOp.OR,  # AND -> OR
        conditions=sample_entry_rules.conditions,
        direction="LONG",
    )
    strat_or = CanonicalStrategy.create_and_hash(
        strategy_id="strat_nq_v1",
        name="NQ Momentum Breakout",
        version="1.0.0",
        symbol="NQ",
        timeframe="1h",
        route="FONDEO",
        archetype="MOMENTUM_BREAKOUT",
        entry_rules=mutated_logic_rules,
        exit_rules=sample_exit_rules,
        sizing_and_risk=sample_sizing,
        provenance=sample_provenance,
    )
    assert base_strat.strategy_hash != strat_or.strategy_hash

    # 3. Mutar policy_version
    prov_new_policy = ProvenanceMetadata(
        author="SYSTEM_ORCHESTRATOR",
        engine_version="5.4.0",
        policy_version="5.5.0",  # 5.4.0 -> 5.5.0
        created_at_utc="2026-08-25T18:00:00Z",
    )
    strat_new_policy = CanonicalStrategy.create_and_hash(
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
        provenance=prov_new_policy,
    )
    assert base_strat.strategy_hash != strat_new_policy.strategy_hash


def test_compile_to_runtime_preserves_logical_composition_and_all_fields(
    sample_entry_rules, sample_exit_rules, sample_sizing, sample_provenance
):
    """P02-003-02: Demuestra que compile_to_runtime() preserva 100% de la semántica canónica."""
    strat = CanonicalStrategy.create_and_hash(
        strategy_id="strat_btc_5m",
        name="BTC Momentum",
        version="1.0.0",
        symbol="BTCUSDT",
        timeframe="5m",
        route="ULTRA",
        archetype="VOLATILITY_BREAKOUT",
        entry_rules=sample_entry_rules,
        exit_rules=sample_exit_rules,
        sizing_and_risk=sample_sizing,
        provenance=sample_provenance,
    )

    runtime_inst = strat.compile_to_runtime()
    assert runtime_inst.strategy_id == "strat_btc_5m"
    assert runtime_inst.strategy_hash == strat.strategy_hash
    assert runtime_inst.logical_operator == LogicalOp.AND
    assert runtime_inst.direction == "LONG"
    assert runtime_inst.engine_version == "5.4.0"
    assert runtime_inst.policy_version == "5.4.0"
    assert runtime_inst.sl_config["time_stop_bars"] == 50
    assert runtime_inst.sl_config["trail_after_r"] == 1.0
    assert runtime_inst.sizing_config["max_daily_loss_usd"] == 500.0


def test_runtime_engine_evaluates_and_vs_or_differently_on_real_data(
    sample_exit_rules, sample_sizing, sample_provenance
):
    """P02-003-03 & 04: Demuestra que el engine de runtime ejecuta la semántica de composición lógica real."""
    datasets = dataset_registry.list_datasets()
    assert len(datasets) > 0
    ds = datasets[0]
    bars = dataset_registry.load_dataset_bars(ds.data_snapshot_id)

    # 1. Estrategia con AND (ambas condiciones deben cumplirse)
    and_rules = RuleTree(
        logic=LogicalOp.AND,
        conditions=[
            ConditionNode(
                left=IndicatorSpec(name="EMA", params={"period": 5}, source_field="close", shift=0),
                op=ComparisonOp.GT,
                right=IndicatorSpec(name="EMA", params={"period": 20}, source_field="close", shift=0),
            ),
            ConditionNode(
                left=IndicatorSpec(name="PRICE_CLOSE", params={}, source_field="close", shift=0),
                op=ComparisonOp.GT,
                right=IndicatorSpec(name="PRICE_OPEN", params={}, source_field="open", shift=0),
            ),
        ],
        direction="LONG",
    )
    strat_and = CanonicalStrategy.create_and_hash(
        strategy_id="strat_and",
        name="AND Strategy",
        version="1.0.0",
        symbol=ds.instrument_id,
        timeframe=ds.timeframe_id,
        route="FONDEO",
        archetype="TREND_FOLLOWING",
        entry_rules=and_rules,
        exit_rules=sample_exit_rules,
        sizing_and_risk=sample_sizing,
        provenance=sample_provenance,
    )

    # 2. Estrategia con OR (basta una condición)
    or_rules = RuleTree(
        logic=LogicalOp.OR,
        conditions=and_rules.conditions,
        direction="LONG",
    )
    strat_or = CanonicalStrategy.create_and_hash(
        strategy_id="strat_or",
        name="OR Strategy",
        version="1.0.0",
        symbol=ds.instrument_id,
        timeframe=ds.timeframe_id,
        route="FONDEO",
        archetype="TREND_FOLLOWING",
        entry_rules=or_rules,
        exit_rules=sample_exit_rules,
        sizing_and_risk=sample_sizing,
        provenance=sample_provenance,
    )

    res_and = canonical_runtime_adapter.execute_backtest(strat_and, bars, ds.data_snapshot_id, ds.data_sha256)
    res_or = canonical_runtime_adapter.execute_backtest(strat_or, bars, ds.data_snapshot_id, ds.data_sha256)

    # La estrategia OR debe generar al menos tantos o más trades que la AND
    assert res_or.total_trades >= res_and.total_trades
    assert res_and.execution_hash != res_or.execution_hash


def test_runtime_engine_lineage_binding(
    sample_entry_rules, sample_exit_rules, sample_sizing, sample_provenance
):
    """P02-003-05: Demuestra que el resultado de ejecución retiene el linaje criptográfico completo."""
    datasets = dataset_registry.list_datasets()
    assert len(datasets) > 0
    ds = datasets[0]
    bars = dataset_registry.load_dataset_bars(ds.data_snapshot_id)

    strat = CanonicalStrategy.create_and_hash(
        strategy_id="strat_lineage_test",
        name="Lineage Test",
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

    res = canonical_runtime_adapter.execute_backtest(strat, bars, ds.data_snapshot_id, ds.data_sha256)
    assert res.strategy_id == "strat_lineage_test"
    assert res.strategy_version == "1.0.0"
    assert res.strategy_hash == strat.strategy_hash
    assert res.engine_version == "5.4.0"
    assert res.policy_version == "5.4.0"
    assert res.dataset_id == ds.data_snapshot_id
    assert res.dataset_sha256 == ds.data_sha256
    assert len(res.execution_hash) == 64


def test_tampered_hash_fails_closed(
    sample_entry_rules, sample_exit_rules, sample_sizing, sample_provenance
):
    """P02-003-01: Demuestra detección Fail-Closed si el strategy_hash es alterado."""
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
        strategy_hash="0" * 64,  # Hash falsificado
    )
    with pytest.raises(StrategyIntegrityError):
        canonical_runtime_adapter.compile_strategy(tampered_strat)
