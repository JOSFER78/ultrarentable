"""tests/test_snapshots_integrity.py
Verificación de Inmutabilidad y Hashing Criptográfico de StrategySnapshot y DatasetSnapshot (Fases 1 y 2).
"""

import os
import pytest
from pydantic import ValidationError

from contracts.canonical_strategy import RuleTree, ExitModel, SizingAndRisk, IndicatorSpec, RuleCondition, ComparisonOperator, LogicalOp, SizingType, StopLossType, TakeProfitType
from contracts.snapshots.strategy_snapshot import StrategySnapshot, StrategyRoute, PyramidingPolicy, MarginPolicy
from contracts.snapshots.dataset_snapshot import DatasetSnapshot


def test_strategy_snapshot_creation_and_immutability():
    """Verifica que StrategySnapshot compute su hash y sea 100% inmutable."""
    entry_rules = RuleTree(
    logic=LogicalOp.AND,
    direction="LONG",
    long_conditions=[
            RuleCondition(left=IndicatorSpec(name="RSI", params={'period': 14}, source_field="close", shift=0), op=ComparisonOperator.GT, right=50.0)
        ]
)
    exit_rules = ExitModel(
    sl_type=StopLossType.ATR_MULTIPLE,
    sl_value=2.0,
    tp_type=TakeProfitType.ATR_MULTIPLE,
    tp_value=6.0
)
    sizing = SizingAndRisk(
        sizing_type=SizingType.RISK_PCT_EQUITY,
        risk_value=2.0,
        max_open_positions=1
    )

    snap = StrategySnapshot.create_and_hash(
        strategy_id="strat_test_btc_01",
        route=StrategyRoute.ULTRA,
        symbol="BTCUSDT",
        timeframe="1h",
        entry_rules=entry_rules,
        exit_rules=exit_rules,
        sizing_and_risk=sizing,
        dataset_id_reference="ds_binance_btcusdt_1h_sample",
        dataset_sha256_reference="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    )

    assert len(snap.canonical_hash) == 64
    assert snap.verify_integrity() is True

    # Verificar inmutabilidad: no se pueden modificar atributos
    with pytest.raises(ValidationError):
        snap.symbol = "ETHUSDT"


def test_dataset_snapshot_from_real_file():
    """Verifica la carga e indexación de un dataset real de disco."""
    sample_file = "/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/normalized/ds_binance_btcusdt_1h_1695290400000_1787086800000.json"
    assert os.path.exists(sample_file)

    ds_snap = DatasetSnapshot.from_file(sample_file)
    assert ds_snap.symbol == "BTCUSDT"
    assert ds_snap.bar_count > 100
    assert len(ds_snap.sha256_hash) == 64
    assert ds_snap.verify_file_integrity() is True
