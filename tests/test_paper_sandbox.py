"""Unit tests for PaperSandboxEngine and IncubationEvaluator (Fase 7)."""

import pytest

from contracts import (
    BacktestResult,
    CanonicalStrategy,
    EngineType,
    ExecutionTrack,
    StrategyLifecycleStatus,
    TradeLog,
)
from services.paper import (
    IncubationEvaluator,
    IncubationVerdict,
    PaperSandboxEngine,
    PositionSide,
)
from services.semantic_ai import SemanticQuantEngine
from services.validation import CandidateRegistry


def test_paper_sandbox_execution_and_fill_simulation():
    """Verify PaperSandbox opens positions with slippage and executes Stop Loss."""
    sandbox = PaperSandboxEngine(default_latency_ms=50, slippage_ticks=1.0)
    semantic_ai = SemanticQuantEngine()
    strat = semantic_ai.generate_candidate(symbol="NQ", track=ExecutionTrack.TRACK_FONDEO)

    # 1. Abrir posición LONG a $20,000 con SL de 20 ticks (5 puntos en NQ = $19,995) y TP de 40 ticks
    pos = sandbox.open_position(
        strategy=strat,
        side=PositionSide.LONG,
        market_price=20000.0,
        quantity=2.0,
        timestamp_ms=1000,
        stop_loss_ticks=20,
        take_profit_ticks=40,
    )

    # Con slippage de 1 tick (0.25): Fill price = 20000.25
    assert pos.side == PositionSide.LONG
    assert pos.entry_price_avg == 20000.25
    assert pos.stop_loss_price == 20000.25 - 5.0

    # 2. Actualizar precio a la baja hasta disparar Stop Loss
    updated_pos, trade_log = sandbox.update_market_price(
        strategy=strat,
        current_price=19994.0,  # Below SL (19995.25)
        timestamp_ms=5000,
    )

    assert updated_pos.side == PositionSide.FLAT
    assert trade_log is not None
    assert trade_log.exit_reason == "STOP_LOSS"
    assert trade_log.net_pnl_usd < 0.0
    assert len(updated_pos.trade_history) == 1


def test_incubation_evaluator_drift_and_promotion():
    """Verify IncubationEvaluator handles ongoing, abort, and promotion scenarios."""
    evaluator = IncubationEvaluator(min_observation_days=14.0, min_trades=10)
    semantic_ai = SemanticQuantEngine()
    strat = semantic_ai.generate_candidate(symbol="MES", track=ExecutionTrack.TRACK_FONDEO)

    backtest_baseline = BacktestResult(
        request_id="bt_req_01",
        strategy_id=strat.strategy_id,
        engine_type=EngineType.FAST_APPROXIMATE,
        dataset_id="ds_mes_01",
        ledger_hash="ledger_hash_mes_01",
        initial_capital_usd=10000.0,
        final_equity_usd=13500.0,
        net_profit_usd=3500.0,
        net_return_pct=35.0,
        total_trades=80,
        sharpe_ratio=2.4,
        max_drawdown_pct=3.0,
        provenance_hash_sha256="hash_mes",
    )

    start_time_ms = 1770000000000

    # 1. Escenario: 5 días observados (Continúa incubando)
    trades_5_days = [
        TradeLog(
            trade_id=f"t_{i}",
            direction="LONG",
            entry_time_utc_ms=start_time_ms + i * 3600000,
            exit_time_utc_ms=start_time_ms + (i + 1) * 3600000,
            entry_price=5000.0,
            exit_price=5010.0 if i % 2 == 0 else 4995.0,
            quantity=1.0,
            gross_pnl_usd=50.0 if i % 2 == 0 else -25.0,
            net_pnl_usd=47.5 if i % 2 == 0 else -27.5,
            return_pct=1.0,
            return_r=1.0,
            exit_reason="TP",
        )
        for i in range(6)
    ]

    report_5d = evaluator.evaluate(
        strategy=strat,
        backtest_baseline=backtest_baseline,
        paper_trades=trades_5_days,
        observation_start_ms=start_time_ms,
        current_time_ms=start_time_ms + 5 * 86400 * 1000,
    )
    assert report_5d.verdict == IncubationVerdict.CONTINUE_INCUBATING

    # 2. Escenario: Degradación severa (Max DD excede límite)
    bad_trades = [
        TradeLog(
            trade_id=f"bad_t_{i}",
            direction="LONG",
            entry_time_utc_ms=start_time_ms,
            exit_time_utc_ms=start_time_ms + 1000,
            entry_price=5000.0,
            exit_price=4800.0,
            quantity=2.0,
            gross_pnl_usd=-1000.0,
            net_pnl_usd=-1005.0,
            return_pct=-4.0,
            return_r=-4.0,
            exit_reason="SL",
        )
        for i in range(3)
    ]

    report_abort = evaluator.evaluate(
        strategy=strat,
        backtest_baseline=backtest_baseline,
        paper_trades=bad_trades,
        observation_start_ms=start_time_ms,
        current_time_ms=start_time_ms + 7 * 86400 * 1000,
    )
    assert report_abort.verdict == IncubationVerdict.ABORT_AND_REJECT

    # 3. Escenario: 14 días completados con métricas sólidas -> Promoción a LIVE
    healthy_trades_14d = [
        TradeLog(
            trade_id=f"good_t_{i}",
            direction="LONG",
            entry_time_utc_ms=start_time_ms + i * 3600000,
            exit_time_utc_ms=start_time_ms + (i + 1) * 3600000,
            entry_price=5000.0,
            exit_price=5015.0 if i % 3 != 0 else 4995.0,
            quantity=1.0,
            gross_pnl_usd=75.0 if i % 3 != 0 else -25.0,
            net_pnl_usd=72.5 if i % 3 != 0 else -27.5,
            return_pct=1.5,
            return_r=1.5,
            exit_reason="TP",
        )
        for i in range(16)
    ]

    registry = CandidateRegistry()
    strat_candidate = strat.model_copy(update={"status": StrategyLifecycleStatus.CANDIDATE})
    registry.register(strat_candidate)
    registry.transition(strat.strategy_id, StrategyLifecycleStatus.INCUBATION_PAPER, "Entrada a sandbox")

    report_promote = evaluator.evaluate(
        strategy=strat,
        backtest_baseline=backtest_baseline,
        paper_trades=healthy_trades_14d,
        observation_start_ms=start_time_ms,
        current_time_ms=start_time_ms + 15 * 86400 * 1000,
        registry=registry,
    )
    assert report_promote.verdict == IncubationVerdict.PROMOTE_TO_LIVE
    assert registry.get_status(strat.strategy_id) == StrategyLifecycleStatus.LIVE_ACTIVE
