"""tests/test_phase02_canonical_strategy.py
Suite de Pruebas de la FASE 02: CANONICAL STRATEGY + VERSION GOVERNANCE.
ZERO-MOCKS · REAL-ONLY · PROVENANCE-LOCKED
"""

import pytest
from contracts.canonical_strategy import (
    CanonicalStrategy,
    ComparisonOp,
    ConditionNode,
    ExitModel,
    IndicatorSpec,
    LogicalOp,
    RuleTree,
    SessionWindow,
    SizingAndRisk,
    SizingType,
    StopLossType,
    TakeProfitType,
)
from contracts.snapshots.strategy_snapshot import StrategyRoute, StrategySnapshot


def test_canonical_strategy_ast_immutability():
    """Verifica que CanonicalStrategy sea inmutable (frozen) y determinista."""
    entry = RuleTree(
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
    exit_m = ExitModel(
        sl_type=StopLossType.ATR_MULTIPLE,
        sl_value=1.5,
        tp_type=TakeProfitType.RR_MULTIPLE,
        tp_value=3.0,
    )
    sizing = SizingAndRisk(
        sizing_type=SizingType.RISK_PCT_EQUITY,
        risk_value=1.0,
    )

    payload = {
        "strategy_id": "strat_nq_ema_cross_v1",
        "symbol": "NQ",
        "timeframe": "1h",
        "route": "FONDEO",
        "entry_rules": entry.model_dump(),
        "exit_rules": exit_m.model_dump(),
        "sizing_and_risk": sizing.model_dump(),
    }
    hash_a = CanonicalStrategy.compute_strategy_hash(payload)
    hash_b = CanonicalStrategy.compute_strategy_hash(payload)

    assert hash_a == hash_b, "El cálculo del hash canónico debe ser 100% determinista"
    assert len(hash_a) == 64

    strat = CanonicalStrategy(
        strategy_id="strat_nq_ema_cross_v1",
        name="NQ EMA Cross 9/21",
        symbol="NQ",
        timeframe="1h",
        route="FONDEO",
        entry_rules=entry,
        exit_rules=exit_m,
        sizing_and_risk=sizing,
        strategy_hash=hash_a,
    )

    with pytest.raises(Exception):
        strat.name = "Mutated Name"  # Frozen check


def test_strategy_snapshot_creation_and_integrity():
    """Verifica la creación del StrategySnapshot ligando datos y reglas canónicas."""
    entry = RuleTree(
        logic=LogicalOp.AND,
        conditions=[
            ConditionNode(
                left=IndicatorSpec(name="RSI", params={"period": 14}),
                op=ComparisonOp.LT,
                right=30.0,
            )
        ],
        direction="LONG",
    )
    exit_m = ExitModel(
        sl_type=StopLossType.PERCENTAGE,
        sl_value=1.0,
        tp_type=TakeProfitType.PERCENTAGE,
        tp_value=2.5,
    )
    sizing = SizingAndRisk(
        sizing_type=SizingType.RISK_PCT_EQUITY,
        risk_value=0.5,
    )

    snapshot = StrategySnapshot.create_and_hash(
        strategy_id="strat_btc_rsi_v1",
        route=StrategyRoute.ULTRA,
        symbol="BTCUSDT",
        timeframe="5m",
        entry_rules=entry,
        exit_rules=exit_m,
        sizing_and_risk=sizing,
        dataset_id_reference="ds_bingx_BTC_USDT_5m_1771748700000_1785572100000_9fb81720ca",
        dataset_sha256_reference="9fb81720ca883719bca901823901238910238123901238910238129038102381",
    )

    assert snapshot.canonical_hash is not None
    assert len(snapshot.canonical_hash) == 64
    assert snapshot.verify_integrity() is True
