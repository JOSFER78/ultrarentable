"""tests/test_snapshots_integrity.py
Verificación de Inmutabilidad y Hashing Criptográfico de StrategySnapshot y DatasetSnapshot (Fases 1 y 2).
"""

import os
import pytest
from pydantic import ValidationError

from contracts.canonical_strategy import RuleTree, ExitModel, SizingAndRisk, IndicatorSpec, RuleCondition, ComparisonOperator
from contracts.snapshots.strategy_snapshot import StrategySnapshot, StrategyRoute, PyramidingPolicy, MarginPolicy
from contracts.snapshots.dataset_snapshot import DatasetSnapshot


def test_strategy_snapshot_creation_and_immutability():
    """Verifica que StrategySnapshot compute su hash y sea 100% inmutable."""
    entry_rules = RuleTree(
        long_conditions=[
            RuleCondition(
                left_indicator=IndicatorSpec(name="RSI", timeframe="1h", period=14),
                operator=ComparisonOperator.GREATER_THAN,
                threshold_value=50.0
            )
        ]
    )
    exit_rules = ExitModel(stop_loss_atr_mult=2.0, take_profit_atr_mult=6.0)
    sizing = SizingAndRisk(base_risk_pct=2.0, max_contracts_or_lots=10.0, base_leverage=20.0)

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
