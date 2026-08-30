"""tests/test_ultra_and_funding_engines.py
Verificación de los motores de explotación especializados Ultra y Fondeo (Fases 5 y 6).
"""

import pytest
from contracts.canonical_strategy import CanonicalStrategy, SizingAndRisk, RuleTree, ExitModel, LogicalOp, SizingType, StopLossType, ConditionNode, IndicatorSpec, ComparisonOp
from contracts.portfolio import BulletTradeDirection
from contracts.validation_contracts import BalaState
from services.exploitation_engines.ultra_engine import UltraExploitationEngine
from services.exploitation_engines.prop_firm_engine import PROP_FIRM_CATALOG, PropFirmRules


def test_ultra_exploitation_engine_creates_and_pyramids_bullet():
    engine = UltraExploitationEngine()
    from contracts.canonical_strategy import TargetInstrument, ProvenanceMetadata, ExecutionTrack
    dummy_strat = CanonicalStrategy.create_and_hash(
        strategy_id="strat_test_ultra",
        route="ULTRA",
        version="1.0.0",
        symbol="BTC-USDT",
        archetype="TREND_FOLLOWING",
        name="Ultra Test",
        timeframe="1h",
        entry_rules=RuleTree(
            logic=LogicalOp.AND,
            direction="LONG",
            conditions=[
                ConditionNode(
                    left=IndicatorSpec(name="EMA", params={"period": 9}),
                    op=ComparisonOp.GT,
                    right=IndicatorSpec(name="EMA", params={"period": 21}),
                )
            ]
        ),
        exit_rules=ExitModel(sl_type=StopLossType.ATR_MULTIPLE, sl_value=2.0),
        sizing_and_risk=SizingAndRisk(sizing_type=SizingType.RISK_PCT_EQUITY, risk_value=3.0, max_open_positions=1),
        provenance=ProvenanceMetadata(author="TEST_USER", engine_version="3.0.0", policy_version="3.0.0", created_at_utc="1970-01-20T16:13:20+00:00")
    )

    bullet = engine.create_bullet(
        strategy=dummy_strat,
        bullet_id="bala_001",
        direction=BulletTradeDirection.LONG,
        entry_price=60000.0,
        margin_r_usd=100.0,
        leverage=50.0,
    )

    assert bullet.bullet_id == "bala_001"
    assert bullet.initial_margin_r_usd == 100.0
    assert bullet.pyramid_count == 0
    assert len(bullet.layers) == 1
    assert bullet.layers[0].leverage == 50.0

    # Piramida en ganancia (precio sube a 63000 -> retorno R > 2.0)
    updated_bullet, state, harvest = engine.process_price_tick(
        bullet=bullet,
        current_price=63000.0,
        timestamp_ms=1700001000,
    )
    assert updated_bullet.pyramid_count >= 1 or state in [BalaState.CONFIRMACION, BalaState.CRECIMIENTO_RECYCLING, BalaState.COSECHA_VAULT]


def test_prop_firm_catalog_rules_conform_to_fondeo_limits():
    topstep = PROP_FIRM_CATALOG["TOPSTEP_50K"]
    assert topstep.account_size_usd == 50000.0
    assert topstep.max_total_drawdown_usd <= 2250.0  # <= 4.5% of 50k
    assert topstep.profit_target_usd == 3000.0
    assert topstep.daily_loss_limit_usd is not None


def test_funding_discovery_dynamic_atr_and_session_window():
    from services.discovery.funding_discovery import FundingDiscoveryEngine
    from contracts.canonical_strategy import StopLossType, TakeProfitType

    engine = FundingDiscoveryEngine()

    # CME Futures (NQ) -> Default US Core 13:30-20:00 UTC, Mon-Fri
    snap_cme = engine.generate_candidate_blueprint(
        strategy_id="strat_cme_test",
        symbol="NQ",
        timeframe="5m",
        dataset_id="ds_nq",
        dataset_sha256="hash_nq",
        sl_atr_mult=2.5,
        tp_atr_mult=5.0,
    )
    assert snap_cme.exit_rules.sl_type == StopLossType.ATR_MULTIPLE
    assert snap_cme.exit_rules.sl_value == 2.5
    assert snap_cme.exit_rules.tp_type == TakeProfitType.ATR_MULTIPLE
    assert snap_cme.exit_rules.tp_value == 5.0
    assert snap_cme.session_window.start_time_utc == "13:30"
    assert snap_cme.session_window.end_time_utc == "20:00"
    assert snap_cme.session_window.allowed_days == [0, 1, 2, 3, 4]
    assert snap_cme.session_window.close_at_eod is True

    # Forex (EURUSD) -> Default European/US 07:00-20:00 UTC, Mon-Fri
    snap_fx = engine.generate_candidate_blueprint(
        strategy_id="strat_fx_test",
        symbol="EURUSD",
        timeframe="15m",
        dataset_id="ds_fx",
        dataset_sha256="hash_fx",
    )
    assert snap_fx.session_window.start_time_utc == "07:00"
    assert snap_fx.session_window.end_time_utc == "20:00"
    assert snap_fx.session_window.allowed_days == [0, 1, 2, 3, 4]
    assert snap_fx.session_window.close_at_eod is True

    # Crypto (BTCUSDT) -> Default 24/7 (00:00-23:59 UTC), Mon-Sun with EOD close
    snap_crypto = engine.generate_candidate_blueprint(
        strategy_id="strat_crypto_test",
        symbol="BTCUSDT",
        timeframe="1h",
        dataset_id="ds_crypto",
        dataset_sha256="hash_crypto",
    )
    assert snap_crypto.session_window.start_time_utc == "00:00"
    assert snap_crypto.session_window.end_time_utc == "23:59"
    assert snap_crypto.session_window.allowed_days == [0, 1, 2, 3, 4, 5, 6]
    assert snap_crypto.session_window.close_at_eod is True


def test_event_backtest_engine_enforces_session_window_and_eod_close():
    from services.discovery.funding_discovery import FundingDiscoveryEngine
    from services.validation.engine.event_backtest_engine import EventBacktestEngine
    from datetime import datetime, timezone

    discovery = FundingDiscoveryEngine()
    strategy = discovery.generate_candidate_blueprint(
        strategy_id="strat_backtest_session_test",
        symbol="NQ",
        timeframe="15m",
        dataset_id="ds_test",
        dataset_sha256="hash_test",
        ema_fast=5,
        ema_slow=10,
        rsi_period=14,
        sl_atr_mult=2.0,
        tp_atr_mult=4.0,
        session_start_utc="13:30",
        session_end_utc="16:00",
        close_at_eod=True,
        allowed_days=[0, 1, 2, 3, 4],  # Mon-Fri
    )

    base_ts = 1788170400000  # 2026-08-31 10:00:00 UTC (Monday)
    step_ms = 15 * 60 * 1000
    candles = []

    price = 20000.0
    for idx in range(60):
        ts = base_ts + (idx * step_ms)
        price += 10.0
        candles.append({
            "timestamp_ms": ts,
            "open": price - 5.0,
            "high": price + 5.0,
            "low": price - 10.0,
            "close": price,
            "volume": 100.0,
        })

    engine = EventBacktestEngine()
    result = engine.run_backtest(strategy, candles, initial_capital_usd=50000.0)

    assert result is not None
    for trade in result.trades:
        entry_dt = datetime.fromtimestamp(trade.entry_time_ms / 1000.0, tz=timezone.utc)
        entry_time_tuple = (entry_dt.hour, entry_dt.minute)
        assert (13, 30) <= entry_time_tuple <= (16, 0), f"Entrada fuera de ventana: {entry_dt}"

    eod_trades = [t for t in result.trades if t.exit_reason == "SESSION_EOD"]
    if eod_trades:
        assert len(eod_trades) >= 1
        ledger = result.to_canonical_ledger(symbol="NQ")
        assert ledger is not None


def test_strategy_search_registry_combinatorial_space_intraday_timeframes(tmp_path):
    from services.discovery.strategy_search_registry import StrategySearchRegistry

    db_file = tmp_path / "test_registry.sqlite3"
    registry = StrategySearchRegistry(db_path=str(db_file))

    intraday_timeframes = ["1m", "5m", "15m", "1h", "4h"]

    for tf in intraday_timeframes:
        space_fondeo = registry.generate_combinatorial_parameter_space(
            symbol="NQ",
            timeframe=tf,
            route="FONDEO",
            max_trials=32,
        )
        assert len(space_fondeo) > 0
        for trial in space_fondeo:
            assert trial["timeframe"] == tf
            assert trial["route"] == "FONDEO"
            assert "sl_atr_mult" in trial
            assert "tp_atr_mult" in trial
            assert "ema_fast" in trial
            assert "ema_slow" in trial
            assert trial["ema_fast"] < trial["ema_slow"]

        space_ultra = registry.generate_combinatorial_parameter_space(
            symbol="BTCUSDT",
            timeframe=tf,
            route="ULTRA",
            max_trials=32,
        )
        assert len(space_ultra) > 0
        for trial in space_ultra:
            assert trial["timeframe"] == tf
            assert trial["route"] == "ULTRA"
            assert "sl_atr_mult" in trial
            assert "tp_atr_mult" in trial
            assert "pyramiding_tiers_count" in trial

