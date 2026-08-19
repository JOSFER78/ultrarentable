"""tests/test_gates_modular_quad_state.py
Verificación de los 11 Gates Cuantitativos Modulares con Estado Cuádruple y Cero Mocks (Fases 8, 9, 10, 11 y 12).
"""

import json
import pytest
from services.discovery.ultra_discovery import UltraDiscoveryEngine
from services.validation.engine.event_backtest_engine import EventBacktestEngine
from services.api.app.validation.gates.gate_pipeline_orchestrator import GatePipelineOrchestrator


def test_11_gates_pipeline_evaluates_real_backtest():
    sample_file = "/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/normalized/ds_binance_suiusdt_1h_1695290400000_1787086800000.json"
    with open(sample_file, "r") as f:
        candles = json.load(f)

    ultra_discovery = UltraDiscoveryEngine()
    strategy = ultra_discovery.generate_candidate_blueprint(
        strategy_id="cand_ultra_sui_test_01",
        symbol="SUIUSDT",
        timeframe="1h",
        dataset_id="ds_binance_suiusdt_1h",
        dataset_sha256="test_sui_hash_123456",
        leverage=50.0,
        sl_atr_mult=1.5,
        tp_atr_mult=7.0,
        pyramiding_tiers_count=3,
    )

    # 1. Ejecutar Backtest Determinista
    bt_engine = EventBacktestEngine()
    bt_result = bt_engine.run_backtest(strategy, candles, initial_capital_usd=1000.0)

    # Separar In-Sample (70%) y Out-of-Sample (30%)
    split_idx = int(len(bt_result.trades) * 0.7)
    is_trades = [t.net_pnl_usd for t in bt_result.trades[:split_idx]]
    oos_trades = [t.net_pnl_usd for t in bt_result.trades[split_idx:]]
    trades_raw = [
        {"entry_price": t.entry_price, "exit_price": t.exit_price, "qty": t.qty, "side": t.side}
        for t in bt_result.trades
    ]

    # 2. Evaluar a través de los 11 Gates Modulares
    orchestrator = GatePipelineOrchestrator()
    candidate_info = {
        "candidate_id": strategy.strategy_id,
        "route": strategy.route.value,
        "symbol": strategy.symbol,
        "timeframe": strategy.timeframe,
        "profit_factor_oos": bt_result.profit_factor,
        "max_drawdown_pct": bt_result.max_drawdown_pct,
        "trades_count": len(oos_trades),
        "rules": ["EMA_FAST > EMA_SLOW", "RSI > 52", "DONCHIAN_BREAKOUT"],
        "indicators_count": 3,
    }

    gates_res = orchestrator.run_all_gates(
        candidate_info=candidate_info,
        candles=candles,
        is_trades=is_trades,
        oos_trades=oos_trades,
        trades_raw=trades_raw,
    )

    assert "gates" in gates_res
    assert len(gates_res["gates"]) == 11
    assert "overall_certified" in gates_res
    assert "scorecard_average" in gates_res

    # Cada uno de los 11 gates debe tener id, name, passed, score y evidence
    for g in gates_res["gates"]:
        assert "gate_id" in g
        assert "name" in g
        assert "passed" in g
        assert "score" in g
        assert "evidence" in g
        assert isinstance(g["score"], (int, float))
