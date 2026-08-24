"""tests/test_fail_closed_engine_and_dataset.py
Adversarial Fail-Closed Unit Tests for Ultrarentable v5.3.0.

Demuestra de forma irrefutable:
1. FastEngine bloquea inmediatamente si falta dataset aprobado exacto (cero fallbacks de dataset).
2. DynamicIndicatorEngine lanza excepción determinista ante indicadores no soportados (cero fallbacks a closes).
3. DynamicRuleEvaluator exige indicator_type explícito para nodos indicadores.
4. UniversalDeterministicBacktestEngine bloquea timestamps corruptos o no monótonos.
5. CanonicalStrategy no impone multiplicadores fijos de CME sobre activos cripto o forex.
"""

import pytest
import numpy as np
from unittest.mock import MagicMock

from contracts.canonical_strategy import (
    CanonicalStrategy,
    ExecutionTrack,
    ProvenanceMetadata,
    TargetInstrument,
    RuleTree,
    ExitModel,
    SizingAndRisk,
    SessionWindow,
    StrategyLifecycleStatus,
)
from contracts.dataset_specification import DatasetSpecification, DatasetQualityReport
from contracts.execution_model import ExecutionModel
from contracts.instrument_specification import AssetClass, CommissionType, InstrumentSpecification
from contracts.risk_model import RiskDoctrine, RiskModel
from contracts.universal_strategy import (
    DynamicValueNode,
    IndicatorType,
    StrategyFamily,
    StrategySpecification,
    ValueSource,
)
from services.engine.indicator_engine import DynamicIndicatorEngine
from services.engine.rule_evaluator import DynamicRuleEvaluator
from services.engine.universal_backtest_engine import UniversalDeterministicBacktestEngine
from services.api.app.engine.fast_engine import FastEngine, FastEngineException
from services.api.app.dsl.engine import StrategyDSL


def test_fast_engine_blocks_when_dataset_missing():
    """Verifica que FastEngine no busque datasets alternativos ni los auto-apruebe."""
    mock_db = MagicMock()
    # Simular que la base de datos no tiene ningún dataset aprobado para BTC-USDT 1h
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    engine = FastEngine(db=mock_db, allow_legacy_risk=False)
    strategy_input = {
        "dslVersion": "1.0.0",
        "metadata": {
            "name": "Test Strategy",
            "family": "trend_following",
            "parents": [],
            "origin": "MANUAL",
        },
        "market": {
            "venue": "BINGX",
            "symbol": "BTC-USDT",
            "timeframe": "1h",
        },
        "position": {
            "marginMode": "ISOLATED",
            "leverage": 5,
            "allocationPct": 10.0,
            "compound": False,
        },
        "execution": {
            "entryOrderType": "MARKET",
            "exitOrderType": "MARKET",
            "signalTiming": "BAR_CLOSE_EXECUTE_NEXT_OPEN",
        },
        "signals": {
            "longEntry": {
                "nodeType": "COMPARISON",
                "left": {
                    "type": "INDICATOR",
                    "indicator": "EMA",
                    "source": {"type": "SERIES", "series": "CLOSE"},
                    "params": {"period": 9},
                },
                "op": "GT",
                "right": {
                    "type": "INDICATOR",
                    "indicator": "EMA",
                    "source": {"type": "SERIES", "series": "CLOSE"},
                    "params": {"period": 21},
                },
            },
            "shortEntry": {
                "nodeType": "COMPARISON",
                "left": {
                    "type": "INDICATOR",
                    "indicator": "EMA",
                    "source": {"type": "SERIES", "series": "CLOSE"},
                    "params": {"period": 9},
                },
                "op": "LT",
                "right": {
                    "type": "INDICATOR",
                    "indicator": "EMA",
                    "source": {"type": "SERIES", "series": "CLOSE"},
                    "params": {"period": 21},
                },
            },
            "longExit": {
                "nodeType": "COMPARISON",
                "left": {
                    "type": "INDICATOR",
                    "indicator": "EMA",
                    "source": {"type": "SERIES", "series": "CLOSE"},
                    "params": {"period": 9},
                },
                "op": "LT",
                "right": {
                    "type": "INDICATOR",
                    "indicator": "EMA",
                    "source": {"type": "SERIES", "series": "CLOSE"},
                    "params": {"period": 21},
                },
            },
            "shortExit": {
                "nodeType": "COMPARISON",
                "left": {
                    "type": "INDICATOR",
                    "indicator": "EMA",
                    "source": {"type": "SERIES", "series": "CLOSE"},
                    "params": {"period": 9},
                },
                "op": "GT",
                "right": {
                    "type": "INDICATOR",
                    "indicator": "EMA",
                    "source": {"type": "SERIES", "series": "CLOSE"},
                    "params": {"period": 21},
                },
            },
        },
    }
    
    with pytest.raises(FastEngineException) as exc_info:
        engine.run_backtest(strategy_input=strategy_input, dataset_id=None)
    
    assert exc_info.value.code == "DATASET_NOT_FOUND"
    assert "No approved dataset available" in exc_info.value.message


def test_indicator_engine_fail_closed_on_unsupported():
    """Verifica que DynamicIndicatorEngine lance error determinista si se pide un indicador no soportado."""
    closes = np.array([100.0, 101.0, 102.0, 103.0, 104.0])
    ind_engine = DynamicIndicatorEngine(opens=closes, highs=closes, lows=closes, closes=closes)
    
    with pytest.raises(ValueError) as exc_info:
        ind_engine.get_series("NON_EXISTENT_QUANT_INDICATOR", period=14)
    
    assert "UNSUPPORTED_INDICATOR" in str(exc_info.value)


def test_rule_evaluator_requires_explicit_indicator():
    """Verifica que DynamicRuleEvaluator rechace nodos indicadores sin indicator_type."""
    closes = np.array([100.0, 101.0, 102.0, 103.0, 104.0])
    ind_engine = DynamicIndicatorEngine(opens=closes, highs=closes, lows=closes, closes=closes)
    evaluator = DynamicRuleEvaluator(ind_engine)
    
    node = DynamicValueNode(source_type=ValueSource.INDICATOR, indicator_type=None)
    with pytest.raises(ValueError) as exc_info:
        evaluator.resolve_value_series(node)
    
    assert "INVALID_VALUE_NODE" in str(exc_info.value)


def test_universal_engine_blocks_invalid_timestamps():
    """Verifica que el motor universal falle cerrado si las velas tienen timestamps corruptos o nulos."""
    engine = UniversalDeterministicBacktestEngine()
    
    candles_bad_ts = [
        {"open": 100, "high": 105, "low": 99, "close": 102, "volume": 1000, "timestamp_ms": 0}
        for _ in range(25)
    ]
    
    strat = StrategySpecification(
        strategy_id="TEST-STRAT-001",
        version="1.0.0",
        family=StrategyFamily.TREND_FOLLOWING,
        target_symbol="BTC-USDT",
        base_timeframe="1h",
        dataset_reference_id="ds_test",
        dataset_sha256="sha256_dummy",
    )
    inst = InstrumentSpecification(
        symbol="BTC-USDT",
        raw_symbol="BTCUSDT",
        asset_class=AssetClass.CRYPTO_PERPETUAL,
        exchange_or_venue="BINGX",
        base_currency="BTC",
        quote_currency="USDT",
        tick_size=0.1,
        point_value=1.0,
        contract_size=1.0,
        min_quantity=0.001,
        quantity_step=0.001,
        price_precision=1,
        quantity_precision=3,
        commission_type=CommissionType.PERCENTAGE_OF_NOTIONAL,
        taker_fee_rate=0.0005,
        maker_fee_rate=0.0002,
    )
    dataset = DatasetSpecification(
        dataset_id="ds_test",
        symbol="BTC-USDT",
        venue="BINGX",
        timeframe="1h",
        start_time_ms=1700000000000,
        end_time_ms=1700001500000,
        start_iso="2026-01-01T00:00:00Z",
        end_iso="2026-01-02T00:00:00Z",
        bar_count=25,
        sha256_hash="dummy_hash",
        file_path="data/test.parquet",
        quality_report=DatasetQualityReport(total_bars=25),
    )
    
    with pytest.raises(ValueError) as exc_info:
        engine.run(
            strategy=strat,
            instrument=inst,
            dataset=dataset,
            candles=candles_bad_ts,
            execution_model=ExecutionModel(),
            risk_model=RiskModel(base_capital_usd=10000.0),
        )
    
    assert "INVALID_TIMESTAMP" in str(exc_info.value)


def test_universal_engine_blocks_non_monotonic_timestamps():
    """Verifica que el motor universal falle cerrado si los timestamps no son estrictamente crecientes."""
    engine = UniversalDeterministicBacktestEngine()
    
    # 25 velas con timestamps desordenados
    candles_unordered = [
        {"open": 100, "high": 105, "low": 99, "close": 102, "volume": 1000, "timestamp_ms": 1700000000000 + i * 60000}
        for i in range(25)
    ]
    # Invertir el orden de una vela
    candles_unordered[10]["timestamp_ms"] = candles_unordered[9]["timestamp_ms"] - 5000
    
    strat = StrategySpecification(
        strategy_id="TEST-STRAT-001",
        version="1.0.0",
        family=StrategyFamily.TREND_FOLLOWING,
        target_symbol="BTC-USDT",
        base_timeframe="1h",
        dataset_reference_id="ds_test",
        dataset_sha256="sha256_dummy",
    )
    inst = InstrumentSpecification(
        symbol="BTC-USDT",
        raw_symbol="BTCUSDT",
        asset_class=AssetClass.CRYPTO_PERPETUAL,
        exchange_or_venue="BINGX",
        base_currency="BTC",
        quote_currency="USDT",
        tick_size=0.1,
        point_value=1.0,
        contract_size=1.0,
        min_quantity=0.001,
        quantity_step=0.001,
        price_precision=1,
        quantity_precision=3,
        commission_type=CommissionType.PERCENTAGE_OF_NOTIONAL,
        taker_fee_rate=0.0005,
        maker_fee_rate=0.0002,
    )
    dataset = DatasetSpecification(
        dataset_id="ds_test",
        symbol="BTC-USDT",
        venue="BINGX",
        timeframe="1h",
        start_time_ms=1700000000000,
        end_time_ms=1700001500000,
        start_iso="2026-01-01T00:00:00Z",
        end_iso="2026-01-02T00:00:00Z",
        bar_count=25,
        sha256_hash="dummy_hash",
        file_path="data/test.parquet",
        quality_report=DatasetQualityReport(total_bars=25),
    )
    
    with pytest.raises(ValueError) as exc_info:
        engine.run(
            strategy=strat,
            instrument=inst,
            dataset=dataset,
            candles=candles_unordered,
            execution_model=ExecutionModel(),
            risk_model=RiskModel(base_capital_usd=10000.0),
        )
    
    assert "NON_MONOTONIC_TIMESTAMPS" in str(exc_info.value)


def test_canonical_strategy_clean_crypto_instrument():
    """Verifica que crear una CanonicalStrategy para BTC no herede parámetros CME por defecto."""
    strat = CanonicalStrategy(
        strategy_id="UR-BTC-001",
        name="Crypto Trend",
        target_track=ExecutionTrack.TRACK_ULTRA,
        status=StrategyLifecycleStatus.GENERATED,
        instrument=TargetInstrument(symbol="BTC-USDT"),
        timeframe="1h",
        session=SessionWindow(is_24_7=True),
        provenance=ProvenanceMetadata(
            source_engine="internal_genetic",
            created_timestamp_utc=1700000000,
            author_or_agent="SYSTEM_GENERATOR",
        ),
    )
    
    assert strat.instrument.symbol == "BTC-USDT"
    assert strat.instrument.exchange is None
    assert strat.instrument.point_value is None
    assert strat.session.is_24_7 is True
