"""tests/test_motor_5_18_sesiones_dst.py
Tests unitarios exhaustivos para Motor 5.18.0 (W2.9):
Sesiones conscientes de DST por vela con zoneinfo y ventanas por familia.
"""

from datetime import datetime, timezone
import pytest

from contracts.canonical_strategy import (
    SessionWindow,
    RuleTree,
    ExitModel,
    SizingAndRisk,
    ProvenanceMetadata,
    StopLossType,
    TakeProfitType,
    SizingType,
    IndicatorSpec,
    ConditionNode,
    ComparisonOp,
    LogicalOp,
)
from contracts.snapshots.strategy_snapshot import StrategySnapshot, StrategyRoute
from services.discovery.funding_discovery import FundingDiscoveryEngine, resolve_session_window
from services.validation.engine.event_backtest_engine import EventBacktestEngine
from services.engine_version import CURRENT_ENGINE_VERSION


def test_motor_version_is_5_18_0():
    """Verifica el bump a 5.18.0."""
    assert CURRENT_ENGINE_VERSION == "5.18.0"


def test_dst_winter_session_window():
    """(a) 16-ene-2023 09:30 ET => 14:30 UTC dentro de sesion y 13:30 UTC fuera."""
    sw = SessionWindow(
        start_time_utc="13:30",
        end_time_utc="20:00",
        market_tz="America/New_York",
        start_time_local="09:30",
        end_time_local="16:00",
        close_at_eod=True,
        allowed_days=[0, 1, 2, 3, 4],
    )
    # Invierno: NY esta en EST (UTC-5)
    # 16-ene-2023 14:30 UTC == 09:30 EST (apertura de sesion RTH)
    dt_in = datetime(2023, 1, 16, 14, 30, tzinfo=timezone.utc)
    assert EventBacktestEngine._is_in_session_window(dt_in, sw) is True

    # 16-ene-2023 13:30 UTC == 08:30 EST (pre-mercado, fuera de sesion RTH)
    dt_out = datetime(2023, 1, 16, 13, 30, tzinfo=timezone.utc)
    assert EventBacktestEngine._is_in_session_window(dt_out, sw) is False


def test_dst_summer_session_window():
    """(b) 17-jul-2023 09:30 ET => 13:30 UTC dentro."""
    sw = SessionWindow(
        start_time_utc="13:30",
        end_time_utc="20:00",
        market_tz="America/New_York",
        start_time_local="09:30",
        end_time_local="16:00",
        close_at_eod=True,
        allowed_days=[0, 1, 2, 3, 4],
    )
    # Verano: NY esta en EDT (UTC-4)
    # 17-jul-2023 13:30 UTC == 09:30 EDT (apertura de sesion RTH)
    dt_in = datetime(2023, 7, 17, 13, 30, tzinfo=timezone.utc)
    assert EventBacktestEngine._is_in_session_window(dt_in, sw) is True

    # 17-jul-2023 12:30 UTC == 08:30 EDT (pre-mercado, fuera de sesion RTH)
    dt_out = datetime(2023, 7, 17, 12, 30, tzinfo=timezone.utc)
    assert EventBacktestEngine._is_in_session_window(dt_out, sw) is False


def test_canonical_hash_identity_without_new_fields():
    """(c) snapshot sin campos nuevos => canonical_hash identico al de 5.17.0."""
    sw_legacy = SessionWindow(
        start_time_utc="13:30",
        end_time_utc="20:00",
        close_at_eod=True,
        allowed_days=[0, 1, 2, 3, 4],
    )
    # Los nuevos campos no estan informados (None por defecto)
    assert sw_legacy.market_tz is None
    assert sw_legacy.start_time_local is None
    assert sw_legacy.end_time_local is None
    assert sw_legacy.flat_time_local is None
    assert sw_legacy.flat_tz is None

    # model_dump() no debe incluir las claves None
    dumped = sw_legacy.model_dump()
    assert "market_tz" not in dumped
    assert "start_time_local" not in dumped
    assert "flat_time_local" not in dumped
    assert set(dumped.keys()) == {"start_time_utc", "end_time_utc", "close_at_eod", "allowed_days"}

    # Crear StrategySnapshot con sw_legacy
    rules = RuleTree(
        logic=LogicalOp.AND,
        direction="BOTH",
        long_conditions=[
            ConditionNode(
                left=IndicatorSpec(name="EMA", params={"period": 20}, source_field="close", shift=0),
                op=ComparisonOp.GT,
                right=IndicatorSpec(name="EMA", params={"period": 50}, source_field="close", shift=0),
            )
        ],
        short_conditions=[
            ConditionNode(
                left=IndicatorSpec(name="EMA", params={"period": 20}, source_field="close", shift=0),
                op=ComparisonOp.LT,
                right=IndicatorSpec(name="EMA", params={"period": 50}, source_field="close", shift=0),
            )
        ],
    )
    exit_model = ExitModel(
        sl_type=StopLossType.FIXED_POINTS,
        sl_value=20.0,
        tp_type=TakeProfitType.FIXED_POINTS,
        tp_value=60.0,
    )
    sizing = SizingAndRisk(
        sizing_type=SizingType.RISK_PCT_EQUITY,
        risk_value=0.01,
        max_open_positions=1,
    )

    snap = StrategySnapshot.create_and_hash(
        strategy_id="TEST_LEGACY_HASH",
        route=StrategyRoute.FONDEO,
        symbol="ES",
        timeframe="15m",
        entry_rules=rules,
        exit_rules=exit_model,
        sizing_and_risk=sizing,
        dataset_id_reference="ds_test",
        dataset_sha256_reference="sha_test",
        session_window=sw_legacy,
    )
    # El hash debe ser determinista y verificable
    assert snap.verify_integrity() is True
    expected_hash = snap.canonical_hash
    assert len(expected_hash) == 64


def test_invalid_market_tz_fails_closed():
    """(d) market_tz invalido => excepcion explicita (fail-closed)."""
    with pytest.raises((ValueError, Exception)):
        SessionWindow(
            start_time_utc="13:30",
            end_time_utc="20:00",
            market_tz="Invalid/Timezone_That_Does_Not_Exist",
        )

    with pytest.raises((ValueError, Exception)):
        SessionWindow(
            start_time_utc="13:30",
            end_time_utc="20:00",
            flat_tz="Fake/City_Zone",
        )


def test_family_session_window_assignment():
    """(e) familia A/B/D recibe ventana Globex + flat 15:10 CT; familia C/ORB/VWAP recibe RTH."""
    engine = FundingDiscoveryEngine()

    # Familias A/B/D (Globex)
    for arch in ("REVERSION_ATR", "SQUEEZE_BREAKOUT", "STREAK_EDGE"):
        snap = engine.generate_candidate_blueprint(
            strategy_id=f"test_{arch}",
            symbol="ES",
            timeframe="15m",
            dataset_id="ds_test",
            dataset_sha256="sha_test",
            archetype=arch,
        )
        sw = snap.session_window
        assert sw is not None
        assert sw.market_tz == "America/New_York"
        assert sw.start_time_local == "18:00"
        assert sw.end_time_local == "17:00"
        assert sw.flat_time_local == "15:10"
        assert sw.flat_tz == "America/Chicago"
        assert sw.close_at_eod is True
        assert 6 in sw.allowed_days  # Incluye domingo apertura Globex

    # Familias C / ORB / VWAP (RTH)
    for arch in ("SESSION_MOMENTUM", "INSTITUTIONAL_SESSION_MOMENTUM", "OPENING_RANGE_BREAKOUT", "VWAP_REVERSION"):
        snap = engine.generate_candidate_blueprint(
            strategy_id=f"test_{arch}",
            symbol="ES",
            timeframe="15m",
            dataset_id="ds_test",
            dataset_sha256="sha_test",
            archetype=arch,
        )
        sw = snap.session_window
        assert sw is not None
        assert sw.market_tz == "America/New_York"
        assert sw.start_time_local == "09:30"
        assert sw.end_time_local == "16:00"
        assert sw.flat_time_local == "15:10"
        assert sw.flat_tz == "America/Chicago"
        assert sw.close_at_eod is True
        assert sw.allowed_days == [0, 1, 2, 3, 4]


def test_mandatory_flat_eod_close():
    """Verifica que flat obligatorio a las 15:10 CT cierra la posicion."""
    sw = SessionWindow(
        market_tz="America/New_York",
        start_time_local="18:00",
        end_time_local="17:00",
        flat_time_local="15:10",
        flat_tz="America/Chicago",
        close_at_eod=True,
        allowed_days=[0, 1, 2, 3, 4, 6],
    )
    # Lunes en invierno: 2023-01-16
    # Chicago esta en CST (UTC-6)
    # 21:10 UTC == 15:10 CST (hora exacta del flat obligatorio)
    dt_flat = datetime(2023, 1, 16, 21, 10, tzinfo=timezone.utc)
    assert EventBacktestEngine._is_session_end(dt_flat, sw) is True
    assert EventBacktestEngine._is_in_session_window(dt_flat, sw) is False

    # 21:05 UTC == 15:05 CST (antes del flat obligatorio)
    dt_before = datetime(2023, 1, 16, 21, 5, tzinfo=timezone.utc)
    assert EventBacktestEngine._is_session_end(dt_before, sw) is False
    assert EventBacktestEngine._is_in_session_window(dt_before, sw) is True

    # 23:00 UTC == 17:00 CST == 18:00 EST (reapertura Globex)
    dt_reopen = datetime(2023, 1, 16, 23, 0, tzinfo=timezone.utc)
    assert EventBacktestEngine._is_session_end(dt_reopen, sw) is False
    assert EventBacktestEngine._is_in_session_window(dt_reopen, sw) is True


def test_opening_range_levels_with_dst():
    """Verifica que _calc_opening_range_levels abre a las 14:30 UTC en invierno y 13:30 UTC en verano."""
    sw = SessionWindow(
        market_tz="America/New_York",
        start_time_local="09:30",
        end_time_local="16:00",
        close_at_eod=True,
        allowed_days=[0, 1, 2, 3, 4],
    )
    engine = EventBacktestEngine()

    # Invierno: 16-ene-2023 (14:15 pre, 14:30 open, 14:45 open-range 15m, 15:00 post)
    candles_winter = [
        {"timestamp_ms": int(datetime(2023, 1, 16, 14, 15, tzinfo=timezone.utc).timestamp() * 1000), "high": 3905.0, "low": 3900.0, "close": 3902.0},
        {"timestamp_ms": int(datetime(2023, 1, 16, 14, 30, tzinfo=timezone.utc).timestamp() * 1000), "high": 3910.0, "low": 3895.0, "close": 3905.0},
        {"timestamp_ms": int(datetime(2023, 1, 16, 14, 45, tzinfo=timezone.utc).timestamp() * 1000), "high": 3920.0, "low": 3900.0, "close": 3915.0},
        {"timestamp_ms": int(datetime(2023, 1, 16, 15, 0, tzinfo=timezone.utc).timestamp() * 1000), "high": 3930.0, "low": 3910.0, "close": 3925.0},
    ]
    import numpy as np
    highs = np.array([c["high"] for c in candles_winter], dtype=np.float64)
    lows = np.array([c["low"] for c in candles_winter], dtype=np.float64)

    or_high, or_low, sealed = engine._calc_opening_range_levels(candles_winter, highs, lows, sw, or_minutes=15)
    # 14:15 UTC esta fuera de sesion -> nan
    assert np.isnan(or_high[0])
    # 14:30 UTC esta dentro de sesion (primeros 15m) -> high=3910, low=3895, not sealed
    assert or_high[1] == 3910.0
    assert or_low[1] == 3895.0
    assert sealed[1] == False
    # 14:45 UTC ya pasaron 15m desde 09:30 EST -> sealed=True, mantiene rango de apertura
    assert or_high[2] == 3910.0
    assert or_low[2] == 3895.0
    assert sealed[2] == True
    # 15:00 UTC sealed=True
    assert or_high[3] == 3910.0
    assert or_low[3] == 3895.0
    assert sealed[3] == True
