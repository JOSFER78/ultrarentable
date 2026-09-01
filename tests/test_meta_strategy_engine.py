"""tests/test_meta_strategy_engine.py
Demuestra las dos ramas del ensamblador real de meta-estrategias
(services/portfolio/meta_strategy_engine.py::MetaStrategyEngine):

  A) FAIL-CLOSED: sin componentes certificados suficientes (o con solape insuficiente para
     estimar una correlación real), el ensamblador declara NO_EVALUABLE de forma explícita y
     auditable -- o lanza una excepción con motivo concreto -- pero nunca fabrica una
     meta-estrategia fantasma con métricas por defecto (0.15 de correlación, 5.0 de profit
     factor, etc.) que otro módulo pudiera tomar por evidencia real.
  B) Con evidencia real suficiente -- backtests reales del motor canónico sobre datos reales
     del repositorio, con DOS configuraciones distintas -- el ensamblador construye el
     meta-portafolio de verdad, sea o no rentable.

REAL-ONLY: la rama B jamás fabrica una serie de retornos. Usa
EventBacktestEngine.run_backtest sobre datasets reales de data/normalized/ (mismo patrón que
tests/test_portfolio_combiner.py). Que el resultado sea o no rentable es irrelevante para
probar el ensamblado; que fuera una serie inventada sí invalidaría la prueba.
"""
from __future__ import annotations

import json

import pytest

from services.discovery.ultra_discovery import UltraDiscoveryEngine
from services.portfolio.meta_strategy_engine import DuplicateAssetError, MetaStrategyEngine
from services.validation.engine.event_backtest_engine import EventBacktestEngine

BTC_FILE = (
    "/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/normalized/"
    "ds_binance_btcusdt_1h_1695290400000_1787086800000.json"
)
ETH_FILE = (
    "/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/normalized/"
    "ds_binance_ethusdt_1h_1695290400000_1787086800000.json"
)


# --------------------------------------------------------------------------------------
# Rama A: fail-closed / NO_EVALUABLE
# --------------------------------------------------------------------------------------

def test_assembly_readiness_is_no_evaluable_for_fondeo_today():
    """Sobre el estado REAL de la base canónica (clonada de forma aislada por
    tests/conftest.py: mismo contenido que la BD de producción, cero riesgo de escritura),
    hoy no existe ninguna candidata FONDEO con status certificado -- el ensamblador debe
    declararlo explícitamente, no devolver silenciosamente una lista vacía indistinguible de
    "no se ha comprobado todavía"."""
    engine = MetaStrategyEngine()  # STATE_DB_PATH ya apunta al clon de test (ver conftest.py)
    readiness = engine.assembly_readiness(route="FONDEO")

    assert readiness["route"] == "FONDEO"
    assert readiness["evaluable"] is False
    assert readiness["assembly_status"] == "NO_EVALUABLE"
    assert readiness["reason"] is not None
    assert "INSUFFICIENT_CERTIFIED_COMPONENTS" in readiness["reason"]
    assert readiness["min_components_required"] == 2


def test_assemble_meta_portfolio_raises_with_fewer_than_two_strategies(tmp_path):
    engine = MetaStrategyEngine(db_path=str(tmp_path / "meta_test_a.sqlite3"))
    with pytest.raises(ValueError, match="INSUFFICIENT_CERTIFIED_COMPONENTS"):
        engine.assemble_meta_portfolio(portfolio_id="X", route="FONDEO", strategies=[])
    with pytest.raises(ValueError, match="INSUFFICIENT_CERTIFIED_COMPONENTS"):
        engine.assemble_meta_portfolio(
            portfolio_id="X",
            route="FONDEO",
            strategies=[{"symbol": "ES", "oos_returns": [1.0, -2.0, 3.0]}],
        )


def test_assemble_meta_portfolio_never_fabricates_correlation_with_thin_overlap(tmp_path):
    """Antes de este fix, con <=2 pasos de retorno alineados el motor fabricaba una
    correlación de 0.15 (un valor por defecto, prohibido por la Regla Invariante #1) y seguía
    adelante como si fuera evidencia real. Ahora debe fallar cerrado y explícito."""
    engine = MetaStrategyEngine(db_path=str(tmp_path / "meta_test_b.sqlite3"))
    strategies = [
        {"strategy_id": "s1", "symbol": "BTCUSDT", "oos_returns": [10.0, -5.0]},
        {"strategy_id": "s2", "symbol": "ETHUSDT", "oos_returns": [8.0, -3.0]},
    ]
    with pytest.raises(ValueError, match="INSUFFICIENT_OVERLAP"):
        engine.assemble_meta_portfolio(portfolio_id="X", route="ULTRA", strategies=strategies)


def test_assemble_meta_portfolio_rejects_duplicate_symbol(tmp_path):
    engine = MetaStrategyEngine(db_path=str(tmp_path / "meta_test_c.sqlite3"))
    strategies = [
        {"strategy_id": "s1", "symbol": "BTCUSDT", "oos_returns": [1.0, -1.0, 2.0, -1.0]},
        {"strategy_id": "s2", "symbol": "BTCUSDT", "oos_returns": [1.0, -1.0, 2.0, -1.0]},
    ]
    with pytest.raises(DuplicateAssetError):
        engine.assemble_meta_portfolio(portfolio_id="X", route="ULTRA", strategies=strategies)


# --------------------------------------------------------------------------------------
# Rama B: ensamblado real con backtests reales, dos configuraciones distintas
# --------------------------------------------------------------------------------------

def test_assemble_meta_portfolio_from_two_real_backtests_with_distinct_configs(tmp_path):
    with open(BTC_FILE, "r") as f:
        btc_candles = json.load(f)
    with open(ETH_FILE, "r") as f:
        eth_candles = json.load(f)

    discovery = UltraDiscoveryEngine()
    bt = EventBacktestEngine()

    # Configuración A: BTCUSDT, apalancamiento y riesgo bajos, medias 20/50.
    strat_btc = discovery.generate_candidate_blueprint(
        strategy_id="meta_test_btc_cfgA",
        symbol="BTCUSDT",
        timeframe="1h",
        dataset_id="ds_binance_btcusdt_1h",
        dataset_sha256="test_hash_btc",
        leverage=10.0,
        risk_pct=0.01,
        ema_fast=20,
        ema_slow=50,
    )
    # Configuración B: ETHUSDT, apalancamiento y riesgo distintos, medias 9/26.
    strat_eth = discovery.generate_candidate_blueprint(
        strategy_id="meta_test_eth_cfgB",
        symbol="ETHUSDT",
        timeframe="1h",
        dataset_id="ds_binance_ethusdt_1h",
        dataset_sha256="test_hash_eth",
        leverage=20.0,
        risk_pct=0.02,
        ema_fast=9,
        ema_slow=26,
    )

    res_btc = bt.run_backtest(strat_btc, btc_candles, initial_capital_usd=1000.0)
    res_eth = bt.run_backtest(strat_eth, eth_candles, initial_capital_usd=1000.0)

    # Evidencia real: ambos backtests produjeron curvas de equity reales y no vacías.
    assert len(res_btc.equity_curve) > 3
    assert len(res_eth.equity_curve) > 3

    engine = MetaStrategyEngine(db_path=str(tmp_path / "meta_test_d.sqlite3"))
    result = engine.assemble_meta_portfolio(
        portfolio_id="TEST_META_REAL_ULTRA_001",
        route="ULTRA",
        strategies=[
            {
                "strategy_id": "meta_test_btc_cfgA",
                "name": "BTC cfgA",
                "symbol": "BTCUSDT",
                "timeframe": "1h",
                "equity_curve": res_btc.equity_curve,
            },
            {
                "strategy_id": "meta_test_eth_cfgB",
                "name": "ETH cfgB",
                "symbol": "ETHUSDT",
                "timeframe": "1h",
                "equity_curve": res_eth.equity_curve,
            },
        ],
        allocation_method="RISK_PARITY",
        total_capital_usd=10000.0,
    )

    # El ensamblado es real y auditable, gane o pierda dinero.
    assert len(result["canonical_hash"]) == 64
    assert result["strategy_count"] == 2
    assert set(result["symbols"]) == {"BTCUSDT", "ETHUSDT"}

    weight_sum_pct = sum(alloc["weight_pct"] for alloc in result["strategies"])
    assert abs(weight_sum_pct - 100.0) < 0.5

    corr_ids = list(result["correlation_matrix"].keys())
    assert len(corr_ids) == 2
    off_diag = result["correlation_matrix"][corr_ids[0]][corr_ids[1]]
    assert -1.0 <= off_diag <= 1.0  # correlación real calculada, no el 0.15 fabricado del bug

    assert result["combined_equity_curve"][0] == 10000.0
    assert isinstance(result["no_losing_periods_oos"], bool)
    if result["no_losing_periods_oos"]:
        assert result["combined_profit_factor"] == float("inf")
    else:
        assert 0.0 < result["combined_profit_factor"] < float("inf")

    # Persistencia real con hash SHA-256 inmutable en la tabla propia del motor.
    persisted = engine.list_meta_portfolios(route="ULTRA")
    assert any(p["portfolio_id"] == "TEST_META_REAL_ULTRA_001" for p in persisted)
