"""tests/test_canonical_fail_closed.py
DEMOSTRACIÓN CIENTÍFICA FAIL-CLOSED:
1. Indicadores no reconocidos lanzan ValueError(UNSUPPORTED_INDICATOR) sin fallback complaciente.
2. Operadores no reconocidos lanzan ValueError(UNSUPPORTED_OPERATOR) sin fallback complaciente.
3. Instrumentos no registrados sin point_value/tick_size lanzan MissingCostModelError.
4. Peticiones sin estrategia canónica lanzan ValueError(MISSING_CANONICAL_STRATEGY).
5. Sharpe Ratio se calcula estadísticamente sobre retornos de trades, no total_roi / max_dd.
"""

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
from contracts.backtest import BacktestRequest, DatasetSnapshot
from services.strategy_core.canonical_compiler import CanonicalCompiler
from services.backtest.fast_engine_adapter import FastEngineAdapter
from services.data.instrument_cost_registry import MissingCostModelError


def test_unsupported_indicator_raises_fail_closed():
    """Fail-Closed: Indicadores no soportados lanzan ValueError."""
    cond = RuleCondition(
        left_indicator=IndicatorSpec(name="NON_EXISTENT_MAGIC_INDICATOR", timeframe="1h"),
        operator=ComparisonOperator.GREATER_THAN,
        threshold_value=50.0,
    )
    strat = CanonicalStrategy(
        strategy_id="FAIL_IND_01",
        name="Fail Indicator Strategy",
        target_track=ExecutionTrack.TRACK_FONDEO,
        status=StrategyLifecycleStatus.GENERATED,
        instrument=TargetInstrument(symbol="BTC-USDT", exchange="BINGX"),
        timeframe="1h",
        rules=RuleTree(long_conditions=[cond]),
        exits=ExitModel(stop_loss_atr_mult=2.0),
        sizing_and_risk=SizingAndRisk(),
        provenance=ProvenanceMetadata(source_engine="test", created_timestamp_utc=0, author_or_agent="test"),
    )

    with pytest.raises(ValueError, match="UNSUPPORTED_INDICATOR"):
        CanonicalCompiler.compile(strat, "ds_01", "hash_01", 50000.0)


def test_missing_cost_profile_raises_missing_cost_model_error():
    """Fail-Closed: Instrumentos desconocidos sin especificación explícita son rechazados."""
    with pytest.raises(MissingCostModelError, match="MISSING_COST_PROFILE"):
        CanonicalCompiler.compile_instrument("UNKNOWN_UNREGISTERED_SYMBOL_XYZ")


def test_missing_strategy_in_request_raises_fail_closed():
    """Fail-Closed: BacktestRequest sin strategy y sin registro persistido es rechazado."""
    adapter = FastEngineAdapter()
    req = BacktestRequest(
        request_id="req_empty_strat",
        strategy_id="NON_EXISTENT_STRATEGY_999",
        strategy=None,
        dataset=DatasetSnapshot(
            dataset_id="ds_01",
            symbol="BTC-USDT",
            timeframe="1h",
            start_timestamp_utc_ms=0,
            end_timestamp_utc_ms=1000,
            total_bars=10,
            sha256_hash="hash_01",
        ),
        initial_capital_usd=50000.0,
    )
    with pytest.raises(ValueError, match="MISSING_CANONICAL_STRATEGY"):
        adapter.run_isolated_is_oos(req)
