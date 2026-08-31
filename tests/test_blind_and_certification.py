"""tests/test_blind_and_certification.py
Verificación de Blind Testing, Shadow Execution y Certificación Multi-Ruta (Fases 14, 15 y 16).
"""

import json
import pytest
from services.discovery.ultra_discovery import UltraDiscoveryEngine
from services.validation.engine.event_backtest_engine import EventBacktestEngine
from services.validation.blind_test_validator import BlindTestValidator
from services.paper.shadow_dispatcher import ShadowExecutionEngine, ShadowDeploymentConfig
from services.validation.certification_registry import CertificationRegistry
from contracts.snapshots.strategy_snapshot import StrategyRoute


def test_blind_test_validator_on_real_candles():
    sample_file = "/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/normalized/ds_binance_btcusdt_1h_1695290400000_1787086800000.json"
    with open(sample_file, "r") as f:
        candles = json.load(f)

    # Tomar las últimas 500 velas como partición de Blind Test
    blind_candles = candles[-500:]

    ultra_discovery = UltraDiscoveryEngine()
    strategy = ultra_discovery.generate_candidate_blueprint(
        strategy_id="cand_blind_test_01",
        symbol="BTCUSDT",
        timeframe="1h",
        dataset_id="ds_binance_btcusdt_1h",
        dataset_sha256="hash_blind_btc_123",
        leverage=20.0,
        risk_pct=0.015,  # re-pin motor 5.10.0 (unidad de riesgo = fraccion, no porcentaje)
    )

    validator = BlindTestValidator()
    result = validator.evaluate_blind(
        strategy=strategy,
        blind_candles=blind_candles,
        blind_dataset_id="blind_btc_500bars",
        account_size_usd=1000.0,
    )

    assert result.strategy_id == "cand_blind_test_01"
    assert result.blind_dataset_id == "blind_btc_500bars"
    assert isinstance(result.passed, bool)
    assert result.verdict.startswith("BLIND_")


def test_shadow_execution_deployment():
    engine = ShadowExecutionEngine()
    config = ShadowDeploymentConfig(
        strategy_id="strat_shadow_01",
        canonical_hash="abcdef1234567890",
        target_venue="BINGX_DEMO",
        route=StrategyRoute.ULTRA,
        allocated_capital_usd=1000.0,
        max_position_size=2.0,
    )
    deploy_res = engine.deploy_to_shadow(config)
    assert deploy_res["status"] == "SHADOW_ACTIVE"
    assert deploy_res["target_venue"] == "BINGX_DEMO"

    stop_res = engine.stop_shadow("strat_shadow_01")
    assert stop_res["status"] == "SHADOW_STOPPED"


def test_certification_registry_multi_route_verdicts():
    registry = CertificationRegistry()
    ultra_discovery = UltraDiscoveryEngine()
    strategy_ultra = ultra_discovery.generate_candidate_blueprint(
        strategy_id="strat_cert_ultra",
        symbol="BTCUSDT",
        timeframe="1h",
        dataset_id="ds_btc",
        dataset_sha256="hash_btc",
        risk_pct=0.015,  # re-pin motor 5.10.0 (unidad de riesgo = fraccion, no porcentaje)
    )

    engine = EventBacktestEngine()
    sample_file = "/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/normalized/ds_binance_btcusdt_1h_1695290400000_1787086800000.json"
    with open(sample_file, "r") as f:
        candles = json.load(f)

    bt_res = engine.run_backtest(strategy_ultra, candles, initial_capital_usd=1000.0)

    verdict = registry.certify_candidate(
        strategy=strategy_ultra,
        backtest_result=bt_res,
        gates_passed_count=9,
        scorecard_average=88.5,
    )

    assert verdict.strategy_id == "strat_cert_ultra"
    assert verdict.certified_status in ["ULTRA_CERTIFIED", "REJECTED_GATES_INCOMPLETE", "REJECTED_ALTO_DRAWDOWN", "REJECTED_BAJO_PF", "BLOCKED_NO_EVIDENCE"]
    assert len(verdict.canonical_hash) == 64
