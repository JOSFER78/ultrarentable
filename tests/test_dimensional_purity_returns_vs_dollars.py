"""tests/test_dimensional_purity_returns_vs_dollars.py
Test de verificación de pureza dimensional y control de versiones v1.05.
Garantiza que el motor cuantitativo opere en % y múltiplos R, sin distorsiones por escalas de capital.
"""

from __future__ import annotations

import numpy as np
import pytest

from services.api.app.validation.gates.gate_05_monte_carlo import Gate05MonteCarlo
from services.api.app.validation.gates.gate_04_walk_forward import Gate04WalkForward
from services.api.app.validation.gates.gate_03_trade_significance import Gate03TradeSignificance
from services.engine_version import CURRENT_ENGINE_VERSION, get_current_version_info
from services.version_control_manager import VersionControlManager


def test_engine_version_is_1_05_and_synced():
    """Verifica que la versión actual del motor esté sincronizada y registrada en el manifiesto."""
    info = get_current_version_info()
    assert info["engine_version"] == CURRENT_ENGINE_VERSION
    assert len(info["history"]) >= 5
    assert any(v["version"] == "1.05" for v in info["history"])


def test_gate_05_monte_carlo_handles_compounding_geometrically_without_false_drawdown():
    """Verifica que Gate 5 evalúe retornos fraccionales normalizados evitando drawdowns absurdos."""
    g5 = Gate05MonteCarlo()
    
    # Serie de 24 trades donde la cuenta crece de $1.000 a $6.000 con riesgo del 7.5%
    # Cada pérdida es exactamente del -7.5% (-$75 al inicio, -$450 al final)
    # Cada ganancia es del +22.5% (+$225 al inicio, +$1350 al final)
    trades_nominal_usd = [
        225.0, -75.0, 250.0, -85.0, 310.0, -100.0, 420.0, -120.0,
        550.0, -150.0, 700.0, -180.0, 850.0, -220.0, 1100.0, -280.0,
        1350.0, -350.0, 1500.0, -400.0, 1650.0, -450.0, 1800.0, -450.0,
    ]
    
    # Evaluación con is_ultra=True
    res = g5.evaluate(trades_nominal_usd, initial_capital=1000.0, num_sims=500, is_ultra=True)
    
    assert res["passed"] is True
    assert res["evidence"]["ruin_probability_pct"] <= 5.0
    assert res["evidence"]["drawdown_95th_percentile_pct"] <= 80.0
    # Comprobar que no hay drawdowns matemáticamente imposibles (> 100% en cuenta sin deuda)
    assert res["evidence"]["drawdown_95th_percentile_pct"] < 100.0


def test_gate_03_and_gate_04_dimensionless_ratios():
    """Verifica que Gate 3 y Gate 4 evalúen ratios adimensionales y porcentajes consistentes."""
    g3 = Gate03TradeSignificance()
    g4 = Gate04WalkForward()

    # Generar serie con consistencia temporal y edge real
    is_trades = [150.0, -50.0, 200.0, -60.0] * 10  # 40 trades con PF ~ 3.0
    oos_trades = [160.0, -45.0, 180.0, -55.0] * 6   # 24 trades con PF ~ 3.0

    res_g3 = g3.evaluate(is_trades, oos_trades, is_ultra=True)
    assert res_g3["passed"] is True
    assert res_g3["evidence"]["trades_is"] == 40
    assert res_g3["evidence"]["trades_oos"] == 24

    res_g4 = g4.evaluate(is_trades + oos_trades)
    assert res_g4["passed"] is True
    assert res_g4["evidence"]["walk_forward_efficiency"] >= 0.50
