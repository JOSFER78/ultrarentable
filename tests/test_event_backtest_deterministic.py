"""tests/test_event_backtest_deterministic.py
Verificación del motor de backtesting determinista EventBacktestEngine (Fase 4).
"""

import json
import pytest
from services.discovery.ultra_discovery import UltraDiscoveryEngine
from services.validation.engine.event_backtest_engine import EventBacktestEngine


def test_event_backtest_runs_deterministically_on_real_candles():
    sample_file = "/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/normalized/ds_binance_btcusdt_1h_1695290400000_1787086800000.json"
    with open(sample_file, "r") as f:
        candles = json.load(f)

    ultra_discovery = UltraDiscoveryEngine()
    strategy = ultra_discovery.generate_candidate_blueprint(
        strategy_id="strat_det_btc_01",
        symbol="BTCUSDT",
        timeframe="1h",
        dataset_id="ds_binance_btcusdt_1h",
        dataset_sha256="test_hash_123456",
        leverage=20.0,
        sl_atr_mult=2.0,
        tp_atr_mult=6.0,
        pyramiding_tiers_count=2,
    )

    engine = EventBacktestEngine(taker_fee_pct=0.05, slippage_bps=2.0)
    
    # Run 1
    res1 = engine.run_backtest(strategy, candles, initial_capital_usd=1000.0)
    # Run 2
    res2 = engine.run_backtest(strategy, candles, initial_capital_usd=1000.0)

    # Verificación de Determinismo Absoluto (Bit-for-bit identical)
    assert res1.total_trades == res2.total_trades
    assert res1.net_profit_usd == res2.net_profit_usd
    assert res1.profit_factor == res2.profit_factor
    assert res1.max_drawdown_pct == res2.max_drawdown_pct
    assert res1.equity_curve == res2.equity_curve
    assert len(res1.trades) == len(res2.trades)

    # Verificación de Trazabilidad Real
    if res1.total_trades > 0:
        first_trade = res1.trades[0]
        assert first_trade.entry_price > 0.0
        assert first_trade.exit_price > 0.0
        assert first_trade.fees_usd > 0.0
        assert first_trade.slippage_usd > 0.0
        assert first_trade.exit_reason in ["STOP_LOSS", "TAKE_PROFIT", "LIQUIDATION", "END_OF_DATASET"]


def test_event_backtest_handles_empty_data_without_fabrication():
    ultra_discovery = UltraDiscoveryEngine()
    strategy = ultra_discovery.generate_candidate_blueprint(
        strategy_id="strat_empty",
        symbol="BTCUSDT",
        timeframe="1h",
        dataset_id="empty_ds",
        dataset_sha256="fake_sha",
    )

    engine = EventBacktestEngine()
    res = engine.run_backtest(strategy, [], initial_capital_usd=1000.0)

    assert res.total_trades == 0
    assert res.net_profit_usd == 0.0
    assert res.profit_factor == 0.0
    assert res.win_rate_pct == 0.0
    assert res.max_drawdown_pct == 0.0
    assert len(res.trades) == 0


def test_event_backtest_interprets_exact_snapshot_parameters():
    sample_file = "/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/normalized/ds_binance_btcusdt_1h_1695290400000_1787086800000.json"
    with open(sample_file, "r") as f:
        candles = json.load(f)

    ultra_discovery = UltraDiscoveryEngine()
    
    # Estrategia A: EMAs Rápidas (8 / 21)
    strat_a = ultra_discovery.generate_candidate_blueprint(
        strategy_id="strat_fast_ema",
        symbol="BTCUSDT",
        timeframe="1h",
        dataset_id="ds_binance_btcusdt_1h",
        dataset_sha256="test_hash_123",
        ema_fast=8,
        ema_slow=21,
        rsi_period=14,
        rsi_threshold_long=50.0,
        sl_atr_mult=1.5,
        tp_atr_mult=4.0,
    )

    # Estrategia B: EMAs Lentas (50 / 200)
    strat_b = ultra_discovery.generate_candidate_blueprint(
        strategy_id="strat_slow_ema",
        symbol="BTCUSDT",
        timeframe="1h",
        dataset_id="ds_binance_btcusdt_1h",
        dataset_sha256="test_hash_123",
        ema_fast=50,
        ema_slow=200,
        rsi_period=14,
        rsi_threshold_long=50.0,
        sl_atr_mult=3.0,
        tp_atr_mult=9.0,
    )

    engine = EventBacktestEngine(taker_fee_pct=0.05, slippage_bps=2.0)
    res_a = engine.run_backtest(strat_a, candles, initial_capital_usd=1000.0)
    res_b = engine.run_backtest(strat_b, candles, initial_capital_usd=1000.0)

    # Debe haber diferencias cuantitativas físicas entre ambas ejecuciones
    assert res_a.total_trades != res_b.total_trades
    assert res_a.net_profit_usd != res_b.net_profit_usd
    assert res_a.profit_factor != res_b.profit_factor
