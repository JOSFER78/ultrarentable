"""Unit and Integration tests for AsyncEventBus and Clean Architecture Domain Isolation (Fase 2)."""

import asyncio
import pytest

from contracts import (
    BacktestRequest,
    BacktestResult,
    CanonicalStrategy,
    EngineType,
    EvidenceGateDecision,
    ExecutionTrack,
    FondeoValidationCriteria,
    UltraValidationCriteria,
)
from services.core import (
    AsyncEventBus,
    BacktestCompletedEvent,
    BacktestRequestedEvent,
    StrategyGeneratedEvent,
    ValidationCompletedEvent,
)
from services.data import DatasetRepository
from services.backtest import FastEngineAdapter
from services.validation import GateEvaluator
from services.evidence import EvidenceVault
from services.semantic_ai import SemanticMutationEngine
from services.portfolio import PortfolioAllocator, BulletLifecycleManager
from services.fondeo.challenge_evaluator import PropChallengeEvaluator
from services.paper import PaperBrokerSimulator, PaperOrder
from services.execution import OrderRouter
from services.monitoring import HealthMonitor


@pytest.mark.asyncio
async def test_async_event_bus_pub_sub():
    """Verify AsyncEventBus registers handlers, publishes events, and tracks history."""
    bus = AsyncEventBus()
    received_events = []

    async def on_strategy_generated(event: StrategyGeneratedEvent):
        received_events.append(event)

    bus.subscribe(StrategyGeneratedEvent, on_strategy_generated)

    mutation_engine = SemanticMutationEngine()
    strategy = mutation_engine.generate_candidate(symbol="NQ", timeframe="1h", track=ExecutionTrack.TRACK_FONDEO)
    event = StrategyGeneratedEvent(strategy=strategy)

    await bus.publish(event)

    assert len(received_events) == 1
    assert received_events[0].strategy.strategy_id == strategy.strategy_id
    assert len(bus.history) == 1

    # Unsubscribe test
    assert bus.unsubscribe(StrategyGeneratedEvent, on_strategy_generated) is True
    await bus.publish(event)
    assert len(received_events) == 1  # Should not increase


@pytest.mark.asyncio
async def test_end_to_end_decoupled_pipeline():
    """Verify full end-to-end decoupled workflow from Generation -> Backtest -> Validation -> Evidence."""
    bus = AsyncEventBus()
    dataset_repo = DatasetRepository()
    backtest_engine = FastEngineAdapter()
    gate_evaluator = GateEvaluator()
    evidence_vault = EvidenceVault()
    mutation_engine = SemanticMutationEngine()

    validation_decisions: list[EvidenceGateDecision] = []

    # Wire up decoupled event listeners
    async def handle_strategy_generated(event: StrategyGeneratedEvent):
        snapshot = dataset_repo.get_snapshot(symbol=event.strategy.instrument.symbol, timeframe=event.strategy.timeframe)
        bt_req = BacktestRequest(
            request_id=f"bt_req_{event.strategy.strategy_id}",
            strategy_id=event.strategy.strategy_id,
            engine_type=EngineType.FAST_APPROXIMATE,
            dataset=snapshot,
            initial_capital_usd=10000.0,
            leverage=1,
        )
        await bus.publish(BacktestRequestedEvent(request=bt_req))

    async def handle_backtest_requested(event: BacktestRequestedEvent):
        bt_res = backtest_engine.execute_backtest(event.request)
        await bus.publish(BacktestCompletedEvent(result=bt_res))

    async def handle_backtest_completed(event: BacktestCompletedEvent):
        decision = gate_evaluator.evaluate_fondeo(
            strategy_id=event.result.strategy_id,
            backtest_result=event.result,
        )
        validation_decisions.append(decision)
        await bus.publish(ValidationCompletedEvent(decision=decision))

    bus.subscribe(StrategyGeneratedEvent, handle_strategy_generated)
    bus.subscribe(BacktestRequestedEvent, handle_backtest_requested)
    bus.subscribe(BacktestCompletedEvent, handle_backtest_completed)

    # Trigger pipeline
    sample_strat = mutation_engine.generate_candidate(symbol="NQ", timeframe="1h", track=ExecutionTrack.TRACK_FONDEO)
    await bus.publish(StrategyGeneratedEvent(strategy=sample_strat))

    assert len(validation_decisions) == 1
    decision = validation_decisions[0]
    assert decision.strategy_id == sample_strat.strategy_id

    # Store evidence
    pack_hash = evidence_vault.store_evidence(sample_strat, decision)
    assert len(pack_hash) == 64
    assert evidence_vault.verify_integrity(pack_hash) is True


def test_domain_services_isolation():
    """Verify all domain services instantiate cleanly without circular imports."""
    # Data
    ds = DatasetRepository()
    snapshot = ds.get_snapshot("BTC-USDT", "1h")
    assert snapshot.total_bars > 0

    # Portfolio
    allocator = PortfolioAllocator()
    bullet_mgr = BulletLifecycleManager()
    assert allocator is not None
    assert bullet_mgr is not None

    # Fondeo
    evaluator = PropChallengeEvaluator()
    assert evaluator is not None

    # Paper & Execution
    paper = PaperBrokerSimulator()
    fill = paper.execute_order(PaperOrder(order_id="o1", symbol="BTC-USDT", side="BUY", quantity=1.0), mark_price=60000.0)
    assert fill.fill_price > 0.0

    router = OrderRouter()
    route = router.route_instrument(snapshot_dummy := SemanticMutationEngine().generate_candidate("BTC-USDT", "1h").instrument)
    assert route == "CONNECTOR_BINGX_PERPETUAL"

    # Monitoring
    monitor = HealthMonitor()
    health = monitor.check_health()
    assert health.status == "HEALTHY"
