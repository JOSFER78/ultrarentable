"""Unit tests for AsyncEventBus and Domain Event Decoupling (Fase 2)."""

import asyncio
import pytest
from datetime import datetime, timezone

from contracts import (
    CanonicalStrategy,
    StrategyLifecycleStatus,
    ExecutionTrack,
    TargetInstrument,
    RuleTree,
    ExitModel,
    SizingAndRisk,
    SessionWindow,
    ProvenanceMetadata,
    BacktestRequest,
    BacktestResult,
    EngineType,
    DatasetSnapshot,
)
from services.core.event_bus import (
    AsyncEventBus,
    StrategyGeneratedEvent,
    BacktestRequestedEvent,
    BacktestCompletedEvent,
    SystemAlertEvent,
)


@pytest.mark.asyncio
async def test_event_bus_publish_subscribe():
    """Verify event bus delivers events to registered subscribers."""
    bus = AsyncEventBus()
    received_events = []

    async def on_strategy_generated(event: StrategyGeneratedEvent):
        received_events.append(event)

    bus.subscribe(StrategyGeneratedEvent, on_strategy_generated)

    strategy = CanonicalStrategy(
        strategy_id="UR-TEST-001",
        name="Test Strategy",
        target_track=ExecutionTrack.TRACK_FONDEO,
        status=StrategyLifecycleStatus.GENERATED,
        instrument=TargetInstrument(
            symbol="NQ",
            exchange="CME",
            contract_type="FUTURES",
            point_value=20.0,
            tick_size=0.25,
        ),
        timeframe="1h",
        provenance=ProvenanceMetadata(
            source_engine="manual",
            created_timestamp_utc=int(datetime.now(timezone.utc).timestamp() * 1000),
            author_or_agent="TEST_SUITE",
        ),
    )

    event = StrategyGeneratedEvent(event_id="evt_001", strategy=strategy)
    await bus.publish(event)

    assert len(received_events) == 1
    assert received_events[0].strategy.strategy_id == "UR-TEST-001"
    assert len(bus.get_history()) == 1


@pytest.mark.asyncio
async def test_event_bus_error_isolation():
    """Verify failing subscriber does not halt other subscribers."""
    bus = AsyncEventBus()
    successful_calls = []

    async def broken_handler(event: SystemAlertEvent):
        raise RuntimeError("Intentional handler failure")

    async def working_handler(event: SystemAlertEvent):
        successful_calls.append(event.message)

    bus.subscribe(SystemAlertEvent, broken_handler)
    bus.subscribe(SystemAlertEvent, working_handler)

    alert = SystemAlertEvent(event_id="alert_001", severity="WARNING", component="DataWorker", message="Feed latency spike")
    await bus.publish(alert)

    assert len(successful_calls) == 1
    assert successful_calls[0] == "Feed latency spike"


@pytest.mark.asyncio
async def test_event_bus_multi_subscriber_flow():
    """Verify multi-service workflow decoupled via events."""
    bus = AsyncEventBus()
    pipeline_state = {"backtest_requested": False, "backtest_completed": False}

    async def on_backtest_requested(event: BacktestRequestedEvent):
        pipeline_state["backtest_requested"] = True
        # Simulate backtest engine completion
        result = BacktestResult(
            request_id=event.request.request_id,
            strategy_id=event.request.strategy_id,
            engine_type=event.request.engine_type,
            dataset_id=event.request.dataset.dataset_id,
            ledger_hash="ledger_hash_event_bus",
            initial_capital_usd=10000.0,
            final_equity_usd=12500.0,
            net_profit_usd=2500.0,
            net_return_pct=25.0,
            total_trades=45,
            provenance_hash_sha256="hash123",
        )
        await bus.publish(BacktestCompletedEvent(event_id="evt_bt_done", result=result))

    async def on_backtest_completed(event: BacktestCompletedEvent):
        pipeline_state["backtest_completed"] = True
        pipeline_state["final_profit"] = event.result.net_profit_usd

    bus.subscribe(BacktestRequestedEvent, on_backtest_requested)
    bus.subscribe(BacktestCompletedEvent, on_backtest_completed)

    dataset = DatasetSnapshot(
        dataset_id="ds_nq_h1",
        symbol="NQ",
        timeframe="1h",
        start_timestamp_utc_ms=1770000000000,
        end_timestamp_utc_ms=1771437600000,
        total_bars=1000,
        sha256_hash="hash_nq",
        is_in_sample=True,
    )
    request = BacktestRequest(
        request_id="req_001",
        strategy_id="UR-TEST-001",
        engine_type=EngineType.FAST_APPROXIMATE,
        dataset=dataset,
    )

    await bus.publish(BacktestRequestedEvent(event_id="evt_req_001", request=request))

    assert pipeline_state["backtest_requested"] is True
    assert pipeline_state["backtest_completed"] is True
    assert pipeline_state["final_profit"] == 2500.0
