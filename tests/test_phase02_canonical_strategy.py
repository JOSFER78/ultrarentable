"""tests/test_phase02_canonical_strategy.py
Suite de Pruebas de la FASE 02 (REWORK AG2-P02-002): CANONICAL STRATEGY COMPLETE HASH & RUNTIME SSOT.
ZERO-MOCKS · REAL-ONLY · PROVENANCE-LOCKED · FAIL-CLOSED
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


@pytest.fixture
def sample_entry_rules():
    return RuleTree(
        logic=LogicalOp.AND,
        conditions=[
            ConditionNode(
                left=IndicatorSpec(name="EMA", params={"period": 9}),
                op=ComparisonOp.CROSS_ABOVE,
                right=IndicatorSpec(name="EMA", params={"period": 21}),
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
    )


@pytest.fixture
def sample_sizing():
    return SizingAndRisk(
        sizing_type=SizingType.RISK_PCT_EQUITY,
        risk_value=1.0,
        max_open_positions=1,
    )


@pytest.fixture
def sample_provenance():
    return ProvenanceMetadata(
        author="SYSTEM_ORCHESTRATOR",
        engine_version="5.4.0",
        policy_version="5.4.0",
    )


def test_complete_semantic_hash_identity_and_mutation_invalidation(
    sample_entry_rules, sample_exit_rules, sample_sizing, sample_provenance
):
    """P02-002-01: Verifica que todo cambio material (incluyendo motor/política) invalide el hash canónico."""
    strat = CanonicalStrategy.create_and_hash(
        strategy_id="strat_nq_v1",
        name="NQ Trend 9/21",
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

    assert len(strat.strategy_hash) == 64
    assert strat.verify_integrity() is True

    # 1. Mutar versión de motor
    mutated_prov = ProvenanceMetadata(
        author="SYSTEM_ORCHESTRATOR",
        engine_version="5.5.0",  # Cambio de versión
        policy_version="5.4.0",
    )
    strat_new_engine = CanonicalStrategy.create_and_hash(
        strategy_id="strat_nq_v1",
        name="NQ Trend 9/21",
        version="1.0.0",
        symbol="NQ",
        timeframe="1h",
        route="FONDEO",
        archetype="MOMENTUM_BREAKOUT",
        entry_rules=sample_entry_rules,
        exit_rules=sample_exit_rules,
        sizing_and_risk=sample_sizing,
        provenance=mutated_prov,
    )
    assert strat.strategy_hash != strat_new_engine.strategy_hash

    # 2. Mutar parámetro SL
    mutated_exit = ExitModel(
        sl_type=StopLossType.ATR_MULTIPLE,
        sl_value=2.0,  # Cambio de SL
        tp_type=TakeProfitType.RR_MULTIPLE,
        tp_value=3.0,
    )
    strat_new_exit = CanonicalStrategy.create_and_hash(
        strategy_id="strat_nq_v1",
        name="NQ Trend 9/21",
        version="1.0.0",
        symbol="NQ",
        timeframe="1h",
        route="FONDEO",
        archetype="MOMENTUM_BREAKOUT",
        entry_rules=sample_entry_rules,
        exit_rules=mutated_exit,
        sizing_and_risk=sample_sizing,
        provenance=sample_provenance,
    )
    assert strat.strategy_hash != strat_new_exit.strategy_hash


def test_compile_to_runtime_semantic_equivalence(
    sample_entry_rules, sample_exit_rules, sample_sizing, sample_provenance
):
    """P02-002-02 & P02-002-05: Verifica que CanonicalStrategy se compile a instrucciones de runtime exactas."""
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
    assert runtime_inst.symbol == "BTCUSDT"
    assert runtime_inst.timeframe == "5m"
    assert runtime_inst.sl_config["value"] == 1.5
    assert runtime_inst.tp_config["value"] == 3.0
    assert len(runtime_inst.compiled_conditions) == 1


def test_tampered_strategy_compile_fails_closed(
    sample_entry_rules, sample_exit_rules, sample_sizing, sample_provenance
):
    """P02-002-04: Verifica que una estrategia con hash alterado sea rechazada en compilación (Fail-Closed)."""
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
        tampered_strat.compile_to_runtime()


def test_single_strategy_authority_and_immutability(
    sample_entry_rules, sample_exit_rules, sample_sizing, sample_provenance
):
    """P02-002-03: Verifica inmutabilidad estricta (frozen=True) y rechazo de mutaciones directas."""
    strat = CanonicalStrategy.create_and_hash(
        strategy_id="strat_immut",
        name="Immutable Strat",
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
    with pytest.raises(Exception):
        strat.symbol = "ES"


def test_strategy_snapshot_creation_and_binding(sample_entry_rules, sample_exit_rules, sample_sizing):
    """P02-002-06: Verifica congelación inmutable ligada a dataset físico en StrategySnapshot."""
    snapshot = StrategySnapshot.create_and_hash(
        strategy_id="strat_btc_rsi_v1",
        route=StrategyRoute.ULTRA,
        symbol="BTCUSDT",
        timeframe="5m",
        entry_rules=sample_entry_rules,
        exit_rules=sample_exit_rules,
        sizing_and_risk=sample_sizing,
        dataset_id_reference="ds_bingx_BTC_USDT_5m_1771748700000_1785572100000_9fb81720ca",
        dataset_sha256_reference="9fb81720ca883719bca901823901238910238123901238910238129038102381",
    )

    assert snapshot.canonical_hash is not None
    assert len(snapshot.canonical_hash) == 64
    assert snapshot.verify_integrity() is True
