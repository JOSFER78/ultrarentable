"""tests/test_discovery_engines.py
Verificación de los tres motores de Discovery (Fase 3: Ultra, Fondeo, Portfolio).
"""

import pytest
from services.discovery.ultra_discovery import UltraDiscoveryEngine
from services.discovery.funding_discovery import FundingDiscoveryEngine
from services.discovery.portfolio_discovery import PortfolioDiscoveryEngine
from contracts.snapshots.strategy_snapshot import StrategyRoute


def test_ultra_discovery_generates_valid_snapshot():
    engine = UltraDiscoveryEngine()
    snap = engine.generate_candidate_blueprint(
        strategy_id="strat_ultra_sui_01",
        symbol="SUIUSDT",
        timeframe="1h",
        dataset_id="ds_binance_suiusdt_1h",
        dataset_sha256="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        leverage=50.0,
        sl_atr_mult=1.8,
        tp_atr_mult=6.5,
        pyramiding_tiers_count=3,
    )
    assert snap.route == StrategyRoute.ULTRA
    assert snap.symbol == "SUIUSDT"
    assert snap.pyramiding_policy.enabled is True
    assert len(snap.pyramiding_policy.tiers) == 3
    assert snap.verify_integrity() is True


def test_funding_discovery_generates_valid_snapshot():
    engine = FundingDiscoveryEngine()
    snap = engine.generate_candidate_blueprint(
        strategy_id="strat_fondeo_nq_01",
        symbol="NQ",
        timeframe="5m",
        dataset_id="ds_trad_nq_5m",
        dataset_sha256="123456abcdef7890123456abcdef7890123456abcdef7890123456abcdef7890",
        risk_per_trade_pct=0.5,
        target_profit_ticks=40,
        stop_loss_ticks=20,
    )
    assert snap.route == StrategyRoute.FONDEO
    assert snap.symbol == "NQ"
    assert snap.pyramiding_policy.enabled is False
    assert snap.session_window is not None
    assert snap.verify_integrity() is True


def test_portfolio_discovery_computes_hrp_weights():
    engine = PortfolioDiscoveryEngine()
    returns_map = {
        "strat_a": [10.0, -5.0, 15.0, -2.0, 8.0, 12.0],
        "strat_b": [2.0, -1.0, 3.0, -1.0, 2.5, 3.0],  # Lower vol -> higher weight
    }
    weights = engine.compute_hrp_allocations(returns_map)
    assert "strat_a" in weights
    assert "strat_b" in weights
    assert weights["strat_b"] > weights["strat_a"]  # Lower volatility gets higher weight
    assert abs(sum(weights.values()) - 1.0) < 0.01
