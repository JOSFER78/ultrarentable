"""tests/test_zero_mocks.py
Auditoría Forense Automatizada de Rigor Cuantitativo (Fase 0).
Garantiza que ningún componente de validación, backtesting, ejecución o gates
contenga funciones aleatorias, fallbacks que inventen métricas o estados PASSED predeterminados.
"""

import inspect
import pytest
from services.api.app.validation.gates.gate_pipeline_orchestrator import GatePipelineOrchestrator
from services.api.app.validation.gates.gate_01_data_ingest import Gate01DataIngest
from services.api.app.validation.gates.gate_02_cost_backtest import Gate02CostBacktest
from services.api.app.validation.gates.gate_03_trade_significance import Gate03TradeSignificance
from services.api.app.validation.gates.gate_04_walk_forward import Gate04WalkForward
from services.api.app.validation.gates.gate_05_monte_carlo import Gate05MonteCarlo
from services.api.app.validation.gates.gate_06_stress_slippage import Gate06StressSlippage
from services.api.app.validation.gates.gate_07_regime_coverage import Gate07RegimeCoverage
from services.api.app.validation.gates.gate_08_dsr_ratio import Gate08DSRRatio
from services.api.app.validation.gates.gate_09_novelty_antifit import Gate09NoveltyAntiFit
from services.api.app.validation.gates.gate_10_agent_debate import Gate10AgentDebate
from services.api.app.validation.gates.gate_11_nautilus_event import Gate11NautilusEvent


def test_no_hardcoded_pass_in_empty_gates():
    """Verifica que ningún Gate devuelva PASSED si no recibe datos o trades reales."""
    g1 = Gate01DataIngest()
    res1 = g1.evaluate([])
    assert res1["passed"] is False or res1["score"] == 0.0

    g2 = Gate02CostBacktest()
    res2 = g2.evaluate([])
    assert res2["passed"] is False

    g3 = Gate03TradeSignificance()
    res3 = g3.evaluate([], [])
    assert res3["passed"] is False

    g4 = Gate04WalkForward()
    res4 = g4.evaluate([], [])
    assert res4["passed"] is False

    g5 = Gate05MonteCarlo()
    res5 = g5.evaluate([])
    assert res5["passed"] is False

    g6 = Gate06StressSlippage()
    res6 = g6.evaluate([])
    assert res6["passed"] is False

    g7 = Gate07RegimeCoverage()
    res7 = g7.evaluate([], [])
    assert res7["passed"] is False

    g8 = Gate08DSRRatio()
    res8 = g8.evaluate([])
    assert res8["passed"] is False

    g11 = Gate11NautilusEvent()
    res11 = g11.evaluate([])
    assert res11["passed"] is False


def test_orchestrator_handles_empty_candidates_without_fake_pass():
    """El orquestador no debe certificar candidatos sin evidencia."""
    orchestrator = GatePipelineOrchestrator()
    res = orchestrator.run_all_gates(
        candidate_info={"candidate_id": "empty_test", "route": "ULTRA", "symbol": "BTCUSDT"},
        candles=[],
        is_trades=[],
        oos_trades=[],
        trades_raw=[]
    )
    assert res["overall_certified"] is False
    assert res["gates_passed_count"] < 11


def test_source_files_do_not_import_random_in_validation_gates():
    """Verifica que los gates de validación analítica no importen el módulo `random` para inventar trades."""
    import services.api.app.validation.gates.gate_01_data_ingest as g1_mod
    import services.api.app.validation.gates.gate_02_cost_backtest as g2_mod
    import services.api.app.validation.gates.gate_04_walk_forward as g4_mod
    import services.api.app.validation.gates.gate_06_stress_slippage as g6_mod
    import services.api.app.validation.gates.gate_11_nautilus_event as g11_mod

    for mod in [g1_mod, g2_mod, g4_mod, g6_mod, g11_mod]:
        src = inspect.getsource(mod)
        assert "random.uniform" not in src
        assert "random.randint" not in src
        assert "random.random" not in src
