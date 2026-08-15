"""Unit tests for StrategySpec neutral format (Fase 3)."""

from services.strategy_core.spec import (
    StrategySpec,
    StrategyStatus,
    InstrumentSpec,
    OriginSpec,
    EntriesSpec,
    ExitsSpec,
    RuleConditionSpec,
    ValidationMetricsSpec
)


def test_strategy_spec_creation_full():
    """Verify construction and validation of StrategySpec according to Section 7."""
    spec = StrategySpec(
        strategy_id="UR-000001",
        version=1,
        name="NQ Breakout 1h SQX Candidate",
        status=StrategyStatus.CANDIDATE,
        origin=OriginSpec(
            engine="strategyquant",
            project="NQ BREAKOUT FUTURES H1 - Tradestation",
            databank="MainDatabank",
            build_id="build_2026_08_02_001"
        ),
        instrument=InstrumentSpec(
            symbol="NQ",
            exchange="CME",
            contract_type="FUTURES",
            point_value=20.0,
            tick_size=0.25
        ),
        timeframe="1h",
        entries=EntriesSpec(
            long=[
                RuleConditionSpec(indicator="RSI", timeframe="1h", period=14, comparison="GREATER_THAN", threshold_value=55.0)
            ],
            short=[
                RuleConditionSpec(indicator="RSI", timeframe="1h", period=14, comparison="LESS_THAN", threshold_value=45.0)
            ]
        ),
        exits=ExitsSpec(
            stop_loss_ticks=20,
            take_profit_ticks=60,
            time_exit_bars=48
        ),
        validation=ValidationMetricsSpec(
            dataset_hash="hash_cme_nq_2026",
            trades_count=145,
            profit_factor=1.82,
            net_profit_usd=24500.0,
            max_drawdown_pct=7.8,
            win_rate=58.5,
            walk_forward_passed=True,
            monte_carlo_passed=True
        )
    )

    assert spec.strategy_id == "UR-000001"
    assert spec.instrument.symbol == "NQ"
    assert spec.origin.engine == "strategyquant"
    assert spec.validation.profit_factor == 1.82
    assert spec.status == StrategyStatus.CANDIDATE


def test_strategy_spec_serialization():
    """Verify StrategySpec serializes cleanly to dict and JSON."""
    spec = StrategySpec(
        strategy_id="UR-000002",
        name="ES Mean Reversion",
        instrument=InstrumentSpec(symbol="ES", point_value=50.0, tick_size=0.25)
    )
    spec_json = spec.model_dump_json()
    assert "UR-000002" in spec_json
    assert "ES" in spec_json

    reloaded = StrategySpec.model_validate_json(spec_json)
    assert reloaded.strategy_id == spec.strategy_id
    assert reloaded.instrument.symbol == "ES"
