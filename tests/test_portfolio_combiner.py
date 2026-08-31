"""tests/test_portfolio_combiner.py
Verificación de combinación de portafolios y generación de PortfolioSnapshot (Fase 7).
"""

import json
import pytest
from services.discovery.ultra_discovery import UltraDiscoveryEngine
from services.validation.engine.event_backtest_engine import EventBacktestEngine
from services.portfolio.portfolio_combiner import PortfolioCombiner


def test_portfolio_combiner_aggregates_real_backtest_results():
    btc_file = "/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/normalized/ds_binance_btcusdt_1h_1695290400000_1787086800000.json"
    eth_file = "/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/normalized/ds_binance_ethusdt_1h_1695290400000_1787086800000.json"

    with open(btc_file, "r") as f:
        btc_candles = json.load(f)
    with open(eth_file, "r") as f:
        eth_candles = json.load(f)

    ultra_discovery = UltraDiscoveryEngine()
    strat_btc = ultra_discovery.generate_candidate_blueprint(
        strategy_id="strat_btc_ultra",
        symbol="BTCUSDT",
        timeframe="1h",
        dataset_id="ds_binance_btcusdt_1h",
        dataset_sha256="hash_btc_123",
        leverage=20.0,
        risk_pct=0.015,  # re-pin motor 5.10.0 (unidad de riesgo = fraccion, no porcentaje)
    )
    strat_eth = ultra_discovery.generate_candidate_blueprint(
        strategy_id="strat_eth_ultra",
        symbol="ETHUSDT",
        timeframe="1h",
        dataset_id="ds_binance_ethusdt_1h",
        dataset_sha256="hash_eth_123",
        leverage=20.0,
        risk_pct=0.015,  # re-pin motor 5.10.0 (unidad de riesgo = fraccion, no porcentaje)
    )

    engine = EventBacktestEngine()
    res_btc = engine.run_backtest(strat_btc, btc_candles, initial_capital_usd=1000.0)
    res_eth = engine.run_backtest(strat_eth, eth_candles, initial_capital_usd=1000.0)

    combiner = PortfolioCombiner()
    portfolio_snap = combiner.combine_strategies(
        portfolio_id="port_btc_eth_ultra",
        backtest_results=[res_btc, res_eth],
        total_capital_usd=10000.0,
    )

    assert portfolio_snap.portfolio_id == "port_btc_eth_ultra"
    assert len(portfolio_snap.strategies) == 2
    assert len(portfolio_snap.canonical_hash) == 64
    assert len(portfolio_snap.combined_equity_curve) > 100
    assert "strat_btc_ultra" in portfolio_snap.correlation_matrix
    assert "strat_eth_ultra" in portfolio_snap.correlation_matrix
