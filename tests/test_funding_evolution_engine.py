from services.discovery.funding_evolution_engine import FundingEvolutionEngine


def _params() -> dict:
    return {
        "ema_fast": 9,
        "ema_slow": 21,
        "rsi_period": 14,
        "rsi_threshold_long": 52.0,
        "rsi_threshold_short": 48.0,
        "stop_loss_ticks": 15.0,
        "target_profit_ticks": 45.0,
        "risk_per_trade_pct": 0.25,
        "time_stop_bars": 36,
        "session_profile": "US_CORE",
        "session_start_utc": "13:30",
        "session_end_utc": "20:00",
    }


def test_fondeo_evolution_is_deterministic_and_diverse() -> None:
    engine = FundingEvolutionEngine()
    first = engine.propose("f-parent", _params(), limit=3)
    second = engine.propose("f-parent", _params(), limit=3)

    assert first == second
    assert len(first) == 3
    types = {p.mutation_type for p in first}
    assert types & {"RELAX_CONFIRMATION", "TIGHTEN_CONFIRMATION", "SHIFT_FAST_REACTION", "SHIFT_SLOW_ANCHOR"}
    assert types & {"WIDEN_STOP", "TIGHTEN_STOP", "WIDEN_TARGET", "TIGHTEN_TARGET", "CHANGE_RISK_PER_TRADE"}
    assert types & {"CHANGE_SESSION", "CHANGE_TIME_STOP"}


def test_fondeo_session_mutation_changes_executable_window() -> None:
    engine = FundingEvolutionEngine()
    proposals = engine.propose("f-session", _params(), limit=12)
    session = next(p for p in proposals if p.mutation_type == "CHANGE_SESSION")

    assert session.parameters["session_start_utc"] != "13:30"
    assert session.parameters["session_end_utc"] != "20:00"


def test_funding_discovery_supports_atr_and_intraday_eod() -> None:
    from services.discovery.funding_discovery import FundingDiscoveryEngine
    engine = FundingDiscoveryEngine()
    snapshot = engine.generate_candidate_blueprint(
        strategy_id="UR_FONDEO_NQ_15M_INTRADAY",
        symbol="NQ",
        timeframe="15m",
        dataset_id="ds_trad_nq_15m.json",
        dataset_sha256="hash_dummy_123",
        sl_atr_mult=1.5,
        tp_atr_mult=3.0,
        archetype="INSTITUTIONAL_SESSION_MOMENTUM",
        session_start_utc="13:30",
        session_end_utc="20:00",
    )
    assert snapshot.route.value == "FONDEO"
    assert snapshot.exit_rules.sl_value == 1.5
    assert snapshot.exit_rules.sl_type.value in ["ATR_MULTIPLE", "StopLossType.ATR_MULTIPLE"]
    assert snapshot.session_window.close_at_eod is True

