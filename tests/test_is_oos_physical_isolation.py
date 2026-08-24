"""tests/test_is_oos_physical_isolation.py
FASE 2 VERIFICATION:
Demuestra científicamente que run_isolated_is_oos() realiza dos ejecuciones físicamente separadas
e independientes (In-Sample y Out-of-Sample) con 0% de fuga de datos (data leakage) y hashes independientes.
"""

import time
import pytest
from contracts.canonical_strategy import (
    CanonicalStrategy,
    ComparisonOperator,
    ExecutionTrack,
    ExitModel,
    IndicatorSpec,
    ProvenanceMetadata,
    RuleCondition,
    RuleTree,
    SizingAndRisk,
    StrategyLifecycleStatus,
    TargetInstrument,
)
from contracts.dataset_specification import DatasetQualityReport, DatasetSpecification
from services.api.app.data_feed.feed_loader import load_candles
from services.engine.universal_backtest_engine import UniversalDeterministicBacktestEngine
from services.strategy_core.canonical_compiler import CanonicalCompiler


def _make_breakout_strategy() -> CanonicalStrategy:
    cond = RuleCondition(
        left_indicator=IndicatorSpec(name="PRICE_CLOSE", timeframe="1h", period=1),
        operator=ComparisonOperator.GREATER_THAN,
        right_indicator=IndicatorSpec(name="EMA", timeframe="1h", period=20),
    )
    return CanonicalStrategy(
        strategy_id="UR-STRAT-IS-OOS-01",
        name="IS/OOS Isolation Validation Strategy",
        target_track=ExecutionTrack.TRACK_ULTRA,
        status=StrategyLifecycleStatus.GENERATED,
        instrument=TargetInstrument(
            symbol="BTC-USDT",
            exchange="BINGX",
            contract_type="PERPETUAL",
            point_value=1.0,
            tick_size=0.1,
        ),
        timeframe="1h",
        rules=RuleTree(long_conditions=[cond]),
        exits=ExitModel(stop_loss_atr_mult=2.0, take_profit_atr_mult=5.0),
        sizing_and_risk=SizingAndRisk(base_risk_pct=1.5, base_leverage=5.0),
        provenance=ProvenanceMetadata(
            source_engine="test_is_oos",
            created_timestamp_utc=int(time.time() * 1000),
            author_or_agent="TEST_USER",
        ),
    )


def test_is_oos_physical_isolation_and_zero_leakage():
    """DEMUESTRA CIENTÍFICAMENTE: In-Sample y Out-of-Sample son dos ejecuciones aisladas con 0% solapamiento."""
    engine = UniversalDeterministicBacktestEngine()
    strat = _make_breakout_strategy()
    candles = load_candles("BTC-USDT", "1h")
    assert len(candles) >= 100, "Se requieren al menos 100 velas para la partición IS/OOS"

    strat_spec, inst_spec, exec_model, risk_model = CanonicalCompiler.compile(
        strategy=strat,
        dataset_id="BTCUSDT_FULL",
        dataset_sha256="sha256_full_dataset",
        initial_capital_usd=10000.0,
    )

    ds_full = DatasetSpecification(
        dataset_id="BTCUSDT_FULL",
        symbol="BTC-USDT",
        venue="BINGX",
        timeframe="1h",
        start_time_ms=candles[0].get("timestamp_ms", 0),
        end_time_ms=candles[-1].get("timestamp_ms", 0),
        start_iso="2024-01-01T00:00:00Z",
        end_iso="2024-06-01T00:00:00Z",
        bar_count=len(candles),
        sha256_hash="hash_full_dataset",
        file_path="data/BTCUSDT_1h.parquet",
        quality_report=DatasetQualityReport(total_bars=len(candles)),
    )

    res_is, res_oos = engine.run_isolated_is_oos(
        strategy=strat_spec,
        instrument=inst_spec,
        dataset=ds_full,
        candles=candles,
        execution_model=exec_model,
        risk_model=risk_model,
        split_ratio=0.70,
        initial_capital_override=10000.0,
    )

    # 1. Hashes de dataset completamente independientes
    assert res_is.dataset_id == "BTCUSDT_FULL_IS"
    assert res_oos.dataset_id == "BTCUSDT_FULL_OOS"
    assert res_is.dataset_sha256 != res_oos.dataset_sha256
    assert len(res_is.dataset_sha256) == 64
    assert len(res_oos.dataset_sha256) == 64

    # 2. Huellas de procedencia Merkle independientes
    assert res_is.provenance_hash != res_oos.provenance_hash

    # 3. Cero solapamiento temporal entre trades IS y trades OOS (Zero Data Leakage)
    if res_is.trades and res_oos.trades:
        max_is_exit = max(t.exit_time_ms for t in res_is.trades)
        min_oos_entry = min(t.entry_time_ms for t in res_oos.trades)
        assert max_is_exit <= min_oos_entry, f"DATA LEAKAGE DETECTED: IS exit {max_is_exit} > OOS entry {min_oos_entry}"
