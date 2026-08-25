"""tests/test_phase02_canonical_strategy.py
Suite de Pruebas de la FASE 02 (ORDEN AG2-P02-001): CANONICAL STRATEGY & EXECUTION CONTRACT.
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


def test_canonical_strategy_creation_hashing_and_immutability(sample_entry_rules, sample_exit_rules, sample_sizing):
    """P02-001-01 & 02: Verifica creación, determinismo de hash e inmutabilidad (frozen)."""
    strat = CanonicalStrategy.create_and_hash(
        strategy_id="strat_nq_trend_v1",
        name="NQ Trend Follower 9/21",
        symbol="NQ",
        timeframe="1h",
        route="FONDEO",
        entry_rules=sample_entry_rules,
        exit_rules=sample_exit_rules,
        sizing_and_risk=sample_sizing,
        provenance=ProvenanceMetadata(
            author="SYSTEM_ORCHESTRATOR",
            engine_version="5.4.0",
            policy_version="5.4.0",
        ),
    )

    assert len(strat.strategy_hash) == 64
    assert strat.verify_integrity() is True

    # Inmutabilidad (frozen)
    with pytest.raises(Exception):
        strat.symbol = "ES"  # Violación de inmutabilidad


def test_deterministic_serialization_reproducibility(sample_entry_rules, sample_exit_rules, sample_sizing):
    """P02-001-02: Verifica que bytes canónicos idénticos produzcan exactamente el mismo hash SHA-256."""
    strat_a = CanonicalStrategy.create_and_hash(
        strategy_id="strat_btc_breakout_v1",
        name="BTC Breakout",
        symbol="BTCUSDT",
        timeframe="5m",
        route="ULTRA",
        entry_rules=sample_entry_rules,
        exit_rules=sample_exit_rules,
        sizing_and_risk=sample_sizing,
    )
    strat_b = CanonicalStrategy.create_and_hash(
        strategy_id="strat_btc_breakout_v1",
        name="BTC Breakout",
        symbol="BTCUSDT",
        timeframe="5m",
        route="ULTRA",
        entry_rules=sample_entry_rules,
        exit_rules=sample_exit_rules,
        sizing_and_risk=sample_sizing,
    )

    assert strat_a.strategy_hash == strat_b.strategy_hash, "El hash debe ser 100% determinista y reproducible"


def test_material_mutation_produces_new_hash_and_lineage(sample_entry_rules, sample_exit_rules, sample_sizing):
    """P02-001-05: Verifica que una mutación material altere el hash y requiera nuevo linaje."""
    strat_parent = CanonicalStrategy.create_and_hash(
        strategy_id="strat_nq_v1",
        name="NQ Base",
        symbol="NQ",
        timeframe="1h",
        route="FONDEO",
        entry_rules=sample_entry_rules,
        exit_rules=sample_exit_rules,
        sizing_and_risk=sample_sizing,
    )

    # Mutar parámetro de salida
    mutated_exit = ExitModel(
        sl_type=StopLossType.ATR_MULTIPLE,
        sl_value=2.0,  # Cambio de 1.5 a 2.0
        tp_type=TakeProfitType.RR_MULTIPLE,
        tp_value=3.0,
    )

    strat_child = CanonicalStrategy.create_and_hash(
        strategy_id="strat_nq_v2",
        name="NQ Mutated Stop",
        symbol="NQ",
        timeframe="1h",
        route="FONDEO",
        entry_rules=sample_entry_rules,
        exit_rules=mutated_exit,
        sizing_and_risk=sample_sizing,
        provenance=ProvenanceMetadata(
            parent_hash=strat_parent.strategy_hash,
            mutation_type="STOP_LOSS_PARAM_TUNING",
            engine_version="5.4.0",
        ),
    )

    assert strat_child.strategy_hash != strat_parent.strategy_hash
    assert strat_child.provenance.parent_hash == strat_parent.strategy_hash


def test_fail_closed_on_tampered_hash(sample_entry_rules, sample_exit_rules, sample_sizing):
    """P02-001-04: Verifica detección Fail-Closed si el strategy_hash no coincide con el AST."""
    strat = CanonicalStrategy(
        strategy_id="strat_tampered",
        name="Tampered",
        symbol="NQ",
        timeframe="1h",
        route="FONDEO",
        entry_rules=sample_entry_rules,
        exit_rules=sample_exit_rules,
        sizing_and_risk=sample_sizing,
        strategy_hash="f" * 64,  # Hash falsificado
    )
    assert strat.verify_integrity() is False


def test_strategy_snapshot_creation_and_binding(sample_entry_rules, sample_exit_rules, sample_sizing):
    """P02-001-03: Verifica la congelación inmutable de la estrategia con el dataset en StrategySnapshot."""
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
