"""tests/test_universal_optimizer.py
Test de verificación del Motor Universal de Optimización y Síntesis Paramétrica.
Doctrina Zero-Mocks & Real-Only.
"""

import pytest
from services.optimization.universal_optimizer_engine import UniversalStrategyOptimizer, universal_optimizer


def test_universal_optimizer_initialization():
    opt = UniversalStrategyOptimizer()
    assert opt.db_path.exists()
    assert opt.ultra_discovery is not None
    assert opt.funding_discovery is not None
    assert opt.gates_orchestrator is not None


def test_universal_optimizer_resolve_datasets():
    # Probar que resuelve dinámicamente diferentes tipos de activos
    btc_file = universal_optimizer.resolve_dataset_file("BTC-USDT", "15m")
    assert btc_file is not None
    assert btc_file.exists()

    eth_file = universal_optimizer.resolve_dataset_file("ETH-USDT", "1h")
    assert eth_file is not None
    assert eth_file.exists()

    nq_file = universal_optimizer.resolve_dataset_file("NQ", "15m")
    assert nq_file is not None
    assert nq_file.exists()


def test_universal_optimizer_closed_loop_execution():
    # Ejecutar una iteración de optimización universal sobre un candidato real
    conn_status = universal_optimizer.optimize_candidate_closed_loop(
        candidate_id="UR_ULTRA_LINK_USDT_4H",
        max_iterations=1,
    )
    assert "candidate_id" in conn_status
    assert conn_status["candidate_id"] == "UR_ULTRA_LINK_USDT_4H"
    assert "final_gates_passed" in conn_status
    assert "optimized_parameters" in conn_status
    assert "microstructure_profile" in conn_status
    assert "hurst" in conn_status["microstructure_profile"]
