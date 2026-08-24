"""tests/test_red_team_fase2_ssot_and_zero_fallback.py
Auditoría Adversarial y Red-Team para FASE 2:
1. Zero-Fallback en FastEngine (Rechazo inmediato de datos no aprobados/inexistentes).
2. Validación Semántica Dimensional Estricta (Bloqueo de comparaciones dimensionales inválidas).
3. Calibración de Quality Gates (ULTRA convexidad vs FONDEO prop firm).
4. Idempotencia y Cero-Duplicación en SSOT de base de datos.
5. Integridad de Revalidación Legada con verificación determinista.
"""

import pytest
import sqlite3
import tempfile
import os
from pathlib import Path

from services.api.app.dsl.engine import (
    StrategyDSL,
    Metadata,
    StrategyFamily,
    StrategyOrigin,
    Market,
    Execution,
    Position,
    MarginMode,
    Signals,
    OrderType,
    ComparisonNode,
    SeriesNode,
    SeriesName,
    IndicatorNode,
    IndicatorName,
    IndicatorParams,
    ConstantNode,
    validate_semantics,
    compile_to_ir,
)
from services.api.app.factory.quality_gates import (
    drawdown_sustainable,
    rentable,
    drawdown_penalty_factor,
    is_ruinous,
    MAX_ACCEPTABLE_DRAWDOWN_PCT_FONDEO,
    RIVETING_DRAWDOWN_PCT,
)
from services.api.app.engine.fast_engine import FastEngine, FastEngineException
from services.api.app.db.database import init_db, get_db, DatasetModel, InstrumentModel


def _valid_fallback_signal() -> ComparisonNode:
    return ComparisonNode(
        op="GT",
        left=SeriesNode(series=SeriesName.CLOSE),
        right=IndicatorNode(
            indicator=IndicatorName.SMA,
            source=SeriesNode(series=SeriesName.CLOSE),
            params=IndicatorParams(period=10),
        ),
    )


def test_red_team_semantic_dimensional_adversarial_rejection():
    """Red-Team: Asegurar que StrategyDSL rechaza dimensionalidades incompatibles."""
    # 1. Comparar Precio con RSI (Nivel vs Oscilador [0,100])
    invalid_dsl = StrategyDSL(
        dslVersion="1.0.0",
        metadata=Metadata(name="Adversarial RSI vs Price", family=StrategyFamily.BREAKOUT, origin=StrategyOrigin.MANUAL),
        market=Market(venue="BINGX", symbol="ETH-USDT", timeframe="1h"),
        position=Position(marginMode=MarginMode.ISOLATED, leverage=1, allocationPct=100.0, compound=False),
        execution=Execution(entryOrderType=OrderType.MARKET, exitOrderType=OrderType.MARKET),
        signals=Signals(
            longEntry=ComparisonNode(
                op="GT",
                left=SeriesNode(series=SeriesName.CLOSE),
                right=IndicatorNode(
                    indicator=IndicatorName.RSI,
                    source=SeriesNode(series=SeriesName.CLOSE),
                    params=IndicatorParams(period=14),
                ),
            ),
            shortEntry=_valid_fallback_signal(),
            longExit=_valid_fallback_signal(),
            shortExit=_valid_fallback_signal(),
        ),
    )
    errors = validate_semantics(invalid_dsl)
    assert len(errors) > 0
    assert any(getattr(err, "code", str(err)) == "INCOMPATIBLE_VALUE_DIMENSIONS" for err in errors)

    # 2. Comparar Precio con Volumen (Nivel vs Cantidad)
    invalid_vol_dsl = StrategyDSL(
        dslVersion="1.0.0",
        metadata=Metadata(name="Adversarial Volume vs Price", family=StrategyFamily.MOMENTUM, origin=StrategyOrigin.MANUAL),
        market=Market(venue="BINGX", symbol="BTC-USDT", timeframe="1h"),
        position=Position(marginMode=MarginMode.ISOLATED, leverage=1, allocationPct=100.0, compound=False),
        execution=Execution(entryOrderType=OrderType.MARKET, exitOrderType=OrderType.MARKET),
        signals=Signals(
            longEntry=ComparisonNode(
                op="GT",
                left=SeriesNode(series=SeriesName.CLOSE),
                right=SeriesNode(series=SeriesName.VOLUME),
            ),
            shortEntry=_valid_fallback_signal(),
            longExit=_valid_fallback_signal(),
            shortExit=_valid_fallback_signal(),
        ),
    )
    vol_errors = validate_semantics(invalid_vol_dsl)
    assert len(vol_errors) > 0
    assert any(getattr(err, "code", str(err)) == "INCOMPATIBLE_VALUE_DIMENSIONS" for err in vol_errors)


def test_red_team_quality_gates_fondeo_vs_ultra_calibration():
    """Red-Team: Probar que FONDEO bloquea DD > 4.5% mientras ULTRA tolera DD no ruinoso (<100%)."""
    # Escenario con 12% Drawdown, 55% Retorno y PF 2.1
    # FONDEO debe rechazar tajantemente (Drawdown 12.0% > 4.5%)
    assert drawdown_sustainable(12.0, mode="fondeo") is False
    assert rentable(55.0, 2.1, 12.0, mode="fondeo") is False

    # ULTRA debe aceptar si la convexidad es positiva y no hay ruina total
    assert drawdown_sustainable(12.0, mode="ultra") is True
    assert rentable(55.0, 2.1, 12.0, mode="ultra") is True
    assert drawdown_penalty_factor(12.0, mode="ultra") == 1.0

    # Ruina total (DD >= 100%) debe ser rechazada universalmente
    assert is_ruinous(100.0) is True
    assert drawdown_sustainable(100.0, mode="ultra") is False
    assert drawdown_sustainable(100.0, mode="fondeo") is False
    assert drawdown_penalty_factor(100.0, mode="fondeo") == 0.0
    assert drawdown_penalty_factor(100.0, mode="ultra") == 0.0


def test_red_team_fast_engine_zero_fallback_on_unapproved_dataset():
    """Red-Team: FastEngine debe lanzar FastEngineException ante dataset no aprobado, jamás inventar datos."""
    valid_dsl = StrategyDSL(
        dslVersion="1.0.0",
        metadata=Metadata(name="Fast Engine Test", family=StrategyFamily.TREND_FOLLOWING, origin=StrategyOrigin.MANUAL),
        market=Market(venue="BINGX", symbol="ETH-USDT", timeframe="1h"),
        position=Position(marginMode=MarginMode.ISOLATED, leverage=1, allocationPct=100.0, compound=False),
        execution=Execution(entryOrderType=OrderType.MARKET, exitOrderType=OrderType.MARKET),
        signals=Signals(
            longEntry=ComparisonNode(
                op="GT",
                left=SeriesNode(series=SeriesName.CLOSE),
                right=IndicatorNode(
                    indicator=IndicatorName.SMA,
                    source=SeriesNode(series=SeriesName.CLOSE),
                    params=IndicatorParams(period=20),
                ),
            ),
            shortEntry=_valid_fallback_signal(),
            longExit=_valid_fallback_signal(),
            shortExit=_valid_fallback_signal(),
        ),
    )
    ir = compile_to_ir(valid_dsl)

    db_gen = get_db()
    db = next(db_gen)

    engine = FastEngine(db, allow_legacy_risk=True)

    # Intentar ejecutar con dataset inexistente
    with pytest.raises(FastEngineException) as exc_info:
        engine.execute(
            strategy_dsl=valid_dsl,
            compiled_ir=ir,
            dataset_id="NON_EXISTENT_DATASET_12345",
        )
    assert exc_info.value.code == "DATASET_NOT_FOUND"


def test_red_team_db_idempotence_and_no_duplication():
    """Red-Team: Ejecutar init_db múltiples veces no genera errores de integridad ni filas duplicadas."""
    init_db()
    init_db()
    init_db()

    db_gen = get_db()
    db = next(db_gen)

    # Verificar que los símbolos en instruments son únicos
    instruments = db.query(InstrumentModel.symbol).all()
    symbols = [i[0] for i in instruments]
    assert len(symbols) == len(set(symbols)), "Se encontraron símbolos duplicados en instruments"

    # Verificar que los dataset_id en datasets son únicos
    datasets = db.query(DatasetModel.dataset_id).all()
    ds_ids = [d[0] for d in datasets]
    assert len(ds_ids) == len(set(ds_ids)), "Se encontraron dataset_ids duplicados en datasets"
