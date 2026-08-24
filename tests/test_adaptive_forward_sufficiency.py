"""tests/test_adaptive_forward_sufficiency.py
Pruebas Unitarias para el Medidor Cuantitativo Adaptativo de Suficiencia Forward.
Especificación oficial según Sección 7 y 8 del Informe Maestro v5.3.0.
"""

import pytest
from contracts.queue_contracts import (
    ForwardSufficiencyRequest,
    ForwardSufficiencyVerdict,
)
from services.validation.forward_sufficiency import AdaptiveForwardSufficiency


def test_forward_insufficient_preliminary_data():
    """Verifica veredicto INSUFFICIENT_DATA cuando hay muy pocos días o trades."""
    req = ForwardSufficiencyRequest(
        strategy_id="strat_fwd_001",
        route="fondeo",
        forward_days=2,
        forward_trades=3,
        forward_net_profit_pct=1.5,
        forward_max_dd_pct=0.8,
        is_expected_return_pct=12.0,
        is_max_dd_pct=3.5,
    )
    res = AdaptiveForwardSufficiency.evaluate(req)

    assert res.verdict == ForwardSufficiencyVerdict.INSUFFICIENT_DATA
    assert res.is_certified_ready is False
    assert res.forward_days_completed == 2
    assert res.required_forward_days == 20


def test_forward_accumulating_progress():
    """Verifica veredicto FORWARD_ACCUMULATING cuando avanza normalmente sin degradación."""
    req = ForwardSufficiencyRequest(
        strategy_id="strat_fwd_002",
        route="fondeo",
        forward_days=12,
        forward_trades=18,
        forward_net_profit_pct=4.2,
        forward_max_dd_pct=1.9,
        is_expected_return_pct=10.0,
        is_max_dd_pct=3.5,
    )
    res = AdaptiveForwardSufficiency.evaluate(req)

    assert res.verdict == ForwardSufficiencyVerdict.FORWARD_ACCUMULATING
    assert res.is_certified_ready is False
    assert res.drawdown_consumption_pct < 50.0


def test_forward_certified_when_all_thresholds_met():
    """Verifica veredicto FORWARD_CERTIFIED al cumplir días, trades, estabilidad de DD y persistencia de retorno."""
    req = ForwardSufficiencyRequest(
        strategy_id="strat_fwd_003",
        route="fondeo",
        forward_days=22,
        forward_trades=35,
        forward_net_profit_pct=8.5,
        forward_max_dd_pct=2.4,
        is_expected_return_pct=10.0,
        is_max_dd_pct=3.5,
    )
    res = AdaptiveForwardSufficiency.evaluate(req)

    assert res.verdict == ForwardSufficiencyVerdict.FORWARD_CERTIFIED
    assert res.is_certified_ready is True
    assert res.forward_to_is_return_ratio == 0.85


def test_forward_degraded_abort_on_excessive_drawdown():
    """Verifica veredicto FORWARD_DEGRADED_ABORT cuando el drawdown supera el límite estricto de la ruta."""
    req = ForwardSufficiencyRequest(
        strategy_id="strat_fwd_004",
        route="fondeo",
        forward_days=8,
        forward_trades=14,
        forward_net_profit_pct=-2.0,
        forward_max_dd_pct=4.95,  # Excede 4.50% de Fondeo
        is_expected_return_pct=10.0,
        is_max_dd_pct=3.5,
    )
    res = AdaptiveForwardSufficiency.evaluate(req)

    assert res.verdict == ForwardSufficiencyVerdict.FORWARD_DEGRADED_ABORT
    assert res.is_certified_ready is False
    assert res.drawdown_consumption_pct > 100.0
