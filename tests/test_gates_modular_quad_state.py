"""tests/test_gates_modular_quad_state.py
Verificación de los 11 Gates Cuantitativos Modulares con Particionado Ciego 60/20/20 y Evidencia Criptográfica en Disco.
"""

import json
import pytest
from services.discovery.ultra_discovery import UltraDiscoveryEngine
from services.validation.engine.event_backtest_engine import EventBacktestEngine
from services.api.app.validation.gates.gate_pipeline_orchestrator import GatePipelineOrchestrator
from services.discovery.discovery_validation_pipeline import compute_file_sha256


def test_11_gates_pipeline_evaluates_real_backtest(monkeypatch):
    # re-pin motor 5.10.0 (unidad de riesgo = fraccion): Gate 9 (ANTI-CURVE-FIT) reconstruye
    # internamente variantes perturbadas de la estrategia vía
    # UltraDiscoveryEngine.generate_candidate_blueprint sin pasar risk_pct, heredando el
    # default legacy risk_pct=1.5 (150% en fraccion) que la guardia fail-closed rechaza.
    # Se parchea el default de la clase (solo durante este test) para inyectar el
    # equivalente fraccional (1.5% == 0.015) sin tocar services/.
    original_blueprint = UltraDiscoveryEngine.generate_candidate_blueprint

    def _blueprint_with_fraction_risk(self, *args, **kwargs):
        kwargs.setdefault("risk_pct", 0.015)
        return original_blueprint(self, *args, **kwargs)

    monkeypatch.setattr(UltraDiscoveryEngine, "generate_candidate_blueprint", _blueprint_with_fraction_risk)

    sample_file = "/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/normalized/ds_binance_suiusdt_1h_1695290400000_1787086800000.json"
    with open(sample_file, "r") as f:
        candles = json.load(f)

    # 1. Particionado Ciego 60% IS, 20% Val, 20% Blind OOS
    n = len(candles)
    idx_is = int(n * 0.60)
    idx_val = int(n * 0.80)

    candles_is = candles[:idx_is]
    candles_val = candles[idx_is:idx_val]
    candles_blind_oos = candles[idx_val:]

    real_sha = compute_file_sha256(sample_file)

    ultra_discovery = UltraDiscoveryEngine()
    strategy = ultra_discovery.generate_candidate_blueprint(
        strategy_id="cand_ultra_sui_test_01",
        symbol="SUIUSDT",
        timeframe="1h",
        dataset_id="ds_binance_suiusdt_1h",
        dataset_sha256=real_sha,
        leverage=50.0,
        sl_atr_mult=1.5,
        tp_atr_mult=7.0,
        pyramiding_tiers_count=3,
        risk_pct=0.015,  # re-pin motor 5.10.0 (unidad de riesgo = fraccion, no porcentaje)
    )

    # 2. Ejecutar Backtest Determinista sobre In-Sample y Blind OOS
    bt_engine = EventBacktestEngine()
    bt_is = bt_engine.run_backtest(strategy, candles_is, initial_capital_usd=1000.0)
    bt_oos = bt_engine.run_backtest(strategy, candles_blind_oos, initial_capital_usd=1000.0)

    is_trades = [t.net_pnl_usd for t in bt_is.trades]
    oos_trades = [t.net_pnl_usd for t in bt_oos.trades]
    trades_raw = [
        {
            "entry_price": t.entry_price, "exit_price": t.exit_price,
            "qty": t.qty, "side": t.side, "net_pnl_usd": t.net_pnl_usd,
            "entry_bar_idx": t.entry_bar, "exit_bar_idx": t.exit_bar,
            "entry_time_ms": t.entry_time_ms, "exit_time_ms": t.exit_time_ms,
        }
        for t in bt_oos.trades
    ]

    # 3. Evaluar a través de los 11 Gates Modulares con Blind OOS intocado
    orchestrator = GatePipelineOrchestrator()
    candidate_info = {
        "candidate_id": strategy.strategy_id,
        "route": strategy.route.value,
        "symbol": strategy.symbol,
        "timeframe": strategy.timeframe,
        "dataset_id": "ds_binance_suiusdt_1h",
        "dataset_sha256": real_sha,
        "dataset_filepath": sample_file,
        "profit_factor_oos": bt_oos.profit_factor,
        "max_drawdown_pct": bt_oos.max_drawdown_pct,
        "trades_count": len(oos_trades),
        "trials_tested": 15,
        "parameters": {"sl_atr_mult": 1.5, "tp_atr_mult": 7.0, "ema_fast": 20, "ema_slow": 50},
        "rules": ["EMA_FAST > EMA_SLOW", "RSI > 52", "DONCHIAN_BREAKOUT"],
        "indicators_count": 3,
    }

    gates_res = orchestrator.run_all_gates(
        candidate_info=candidate_info,
        candles=candles_blind_oos,
        is_trades=is_trades,
        oos_trades=oos_trades,
        trades_raw=trades_raw,
        strategy_snapshot=strategy,
    )

    assert "gates" in gates_res
    assert len(gates_res["gates"]) == 11
    assert "overall_certified" in gates_res
    assert "scorecard_average" in gates_res
    assert gates_res["evidence_count"] == 11

    # Cada uno de los 11 gates debe tener id, name, passed, score y evidence
    for g in gates_res["gates"]:
        assert "gate_id" in g
        assert "name" in g
        assert "passed" in g
        assert "score" in g
        assert "evidence" in g
        assert isinstance(g["score"], (int, float))
