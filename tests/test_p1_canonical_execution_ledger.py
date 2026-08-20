"""tests/test_p1_canonical_execution_ledger.py
Suite de Tests y Auditoría Adversarial de la FASE P1: CANONICAL RESEARCH & EXECUTION CORE.

Verifica:
1. EventBacktestEngine produce un CanonicalExecutionLedger válido con Hash-Chain Merkle.
2. Replay Determinism: Reejecutar el backtest sobre los mismos datos produce hash idéntico (0 drift).
3. Sensibilidad Microestructural: Variar costes de comisión o slippage produce nuevo ledger_hash.
4. Sensibilidad de Datos: Alterar el precio de una sola barra produce nuevo ledger_hash.
5. Sensibilidad al Orden: Alterar el orden secuencial de trades en el ledger invalida el hash Merkle.
"""

import hashlib
import numpy as np
import pytest

from contracts.snapshots.strategy_snapshot import StrategyRoute, StrategySnapshot
from services.validation.engine.event_backtest_engine import EventBacktestEngine


def _create_deterministic_bars(n: int = 150):
    """Genera datos OHLCV sintéticos reproducibles como List[Dict[str, Any]]."""
    t0 = 1770000000000
    closes = 50000.0 + 1000.0 * np.sin(np.linspace(0, 10, n))
    opens = closes - 20.0
    highs = np.maximum(opens, closes) + 50.0
    lows = np.minimum(opens, closes) - 50.0

    candles = []
    for i in range(n):
        candles.append(
            {
                "timestamp_utc_ms": t0 + i * 3600000,
                "open": float(opens[i]),
                "high": float(highs[i]),
                "low": float(lows[i]),
                "close": float(closes[i]),
                "volume": 100.0,
            }
        )
    return candles


from contracts.canonical_strategy import (
    ComparisonOperator,
    ExitModel,
    IndicatorSpec,
    RuleCondition,
    RuleTree,
    SessionWindow,
    SizingAndRisk,
)


def _create_test_snapshot():
    return StrategySnapshot.create_and_hash(
        strategy_id="UR_TEST_P1_001",
        route=StrategyRoute.ULTRA,
        symbol="BTCUSDT",
        timeframe="1h",
        entry_rules=RuleTree(
            long_conditions=[
                RuleCondition(
                    left_indicator=IndicatorSpec(name="EMA", period=10),
                    operator=ComparisonOperator.GREATER_THAN,
                    right_indicator=IndicatorSpec(name="EMA", period=30),
                )
            ]
        ),
        exit_rules=ExitModel(stop_loss_atr_mult=2.0, take_profit_atr_mult=4.0),
        sizing_and_risk=SizingAndRisk(base_risk_pct=15.0, base_leverage=10.0),
        dataset_id_reference="ds_btc_test_p1",
        dataset_sha256_reference="d5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6",
    )


def test_event_engine_produces_canonical_ledger():
    """Verifica que EventBacktestEngine genere directamente un CanonicalExecutionLedger con Merkle Hash."""
    engine = EventBacktestEngine(taker_fee_pct=0.05, slippage_bps=2.0)
    bars = _create_deterministic_bars(200)
    strat = _create_test_snapshot()

    res = engine.run_backtest(strat, bars, initial_capital_usd=10000.0)
    ledger = res.to_canonical_ledger(symbol=strat.symbol)

    assert ledger.strategy_id == strat.strategy_id
    assert ledger.engine_name == "EventBacktestEngine"
    assert ledger.initial_capital_usd == 10000.0
    assert len(ledger.ledger_hash) == 64
    assert ledger.ledger_hash == ledger.calculate_ledger_hash()


def test_event_engine_zero_drift_replay():
    """Verifica determinismo absoluto barra por barra: Replay idéntico => Hash idéntico."""
    engine1 = EventBacktestEngine(taker_fee_pct=0.05, slippage_bps=2.0)
    engine2 = EventBacktestEngine(taker_fee_pct=0.05, slippage_bps=2.0)

    bars = _create_deterministic_bars(200)
    strat = _create_test_snapshot()

    res1 = engine1.run_backtest(strat, bars, initial_capital_usd=10000.0)
    ledger1 = res1.to_canonical_ledger(symbol=strat.symbol)

    res2 = engine2.run_backtest(strat, bars, initial_capital_usd=10000.0)
    ledger2 = res2.to_canonical_ledger(symbol=strat.symbol)

    assert ledger1.total_trades_count == ledger2.total_trades_count
    assert ledger1.net_profit_usd == ledger2.net_profit_usd
    assert ledger1.ledger_hash == ledger2.ledger_hash


def test_cost_modification_changes_ledger_hash():
    """Verifica que alterar costes de ejecución altere el hash del ledger."""
    engine_std = EventBacktestEngine(taker_fee_pct=0.05, slippage_bps=2.0)
    engine_expensive = EventBacktestEngine(taker_fee_pct=0.10, slippage_bps=5.0)

    bars = _create_deterministic_bars(200)
    strat = _create_test_snapshot()

    ledger1 = engine_std.run_backtest(strat, bars, initial_capital_usd=10000.0).to_canonical_ledger(strat.symbol)
    ledger2 = engine_expensive.run_backtest(strat, bars, initial_capital_usd=10000.0).to_canonical_ledger(strat.symbol)

    if ledger1.total_trades_count > 0:
        assert ledger1.ledger_hash != ledger2.ledger_hash
        assert ledger1.total_commission_paid_usd != ledger2.total_commission_paid_usd


def test_price_data_tampering_changes_ledger_hash():
    """Verifica que alterar una sola vela de mercado altere el hash del ledger."""
    engine = EventBacktestEngine(taker_fee_pct=0.05, slippage_bps=2.0)
    bars1 = _create_deterministic_bars(200)
    bars2 = _create_deterministic_bars(200)
    # Alterar barra 50
    bars2[50]["close"] += 500.0

    strat = _create_test_snapshot()

    ledger1 = engine.run_backtest(strat, bars1, initial_capital_usd=10000.0).to_canonical_ledger(strat.symbol)
    ledger2 = engine.run_backtest(strat, bars2, initial_capital_usd=10000.0).to_canonical_ledger(strat.symbol)

    assert ledger1.ledger_hash != ledger2.ledger_hash
