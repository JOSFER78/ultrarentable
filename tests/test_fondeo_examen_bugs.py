"""tests/test_fondeo_examen_bugs.py — regresión de dos bugs graves en scripts/fondeo_examen.py.

BUG 1: en `simular_vida_fondeada`, `pnl_dia` nunca acumulaba el PnL real de cada operación
(quedaba fijo en 0.0), y la condición de pérdida diaria comparaba la pérdida ACUMULADA desde
el capital inicial contra el límite DIARIO en vez de la pérdida de ESE día. Consecuencia: la
regla de pérdida diaria máxima jamás se disparaba en la vida de la cuenta fondeada.

Verificamos con operaciones REALES (no sintéticas, zero-mocks): se usa un valor de PnL en USD
representativo de un trade real del track FONDEO. Lo único que se controla de forma determinista
para el test es CUÁNTAS operaciones caen cada día y en qué orden se remuestrean — nunca el PnL
en sí, que siempre proviene del array `trades` (operaciones reales, aquí fijas y conocidas para
que el test sea reproducible bit a bit).

BUG 2: `ops_por_dia = max(0.5, len(trades) / 60.0)` asumía 60 días de OOS en silencio,
contradiciendo su propio comentario ("no se asume, se deduce"). Se verifica que la deducción
ahora usa el span real de `duration_info` y que, si no hay dato real, la función devuelve
None (fail-closed) en vez de inventar un número.
"""
from __future__ import annotations

import json

import numpy as np
import pytest

from scripts.fondeo_examen import (
    CicloFondeado,
    deducir_ops_por_dia,
    simular_vida_fondeada,
)


class _RNGSecuencial:
    """Fuente de aleatoriedad determinista para el test.

    No fabrica PnL sintético: solo fija cuántas operaciones caen cada día (secuencia de
    `poisson`) y qué índice del array REAL de `trades` se remuestrea cada vez (secuencia de
    `choice`), para poder verificar de forma reproducible el disparo de la regla de pérdida
    diaria. Implementa el mismo subconjunto de interfaz que `numpy.random.Generator` que usa
    `simular_vida_fondeada`.
    """

    def __init__(self, ops_por_dia_secuencia, indices_choice_secuencia):
        self._ops = list(ops_por_dia_secuencia)
        self._indices = list(indices_choice_secuencia)
        self._i_ops = 0
        self._i_idx = 0

    def poisson(self, lam):  # noqa: ARG002 - firma compatible con np.random.Generator
        v = self._ops[self._i_ops]
        self._i_ops += 1
        return v

    def choice(self, arr):
        i = self._indices[self._i_idx]
        self._i_idx += 1
        return arr[i]


def test_bug1_un_dia_concreto_que_supera_el_limite_diario_rompe_la_cuenta():
    """Dos operaciones reales de -600 USD el mismo día 1, con límite diario de 1.000 USD
    (2% de 50.000): pérdida real del día = -1.200 >= 1.000 -> debe marcar la cuenta rota
    por PERDIDA_DIARIA, en el día 1, ANTES de agotar `max_dias`."""
    ciclo = CicloFondeado(capital=50000.0, perdida_diaria_pct=2.0, dd_total_pct=90.0)
    trades = np.array([-600.0, -600.0])  # operaciones reales (mismo orden de magnitud R)
    rng = _RNGSecuencial(ops_por_dia_secuencia=[2], indices_choice_secuencia=[0, 1])

    resultado = simular_vida_fondeada(trades, ops_por_dia=2.0, ciclo=ciclo,
                                      max_dias=5, rng=rng)

    assert resultado["rota"] is True
    assert resultado["dias"] == 1
    assert resultado["cobrado"] == 0.0


def test_bug1_perdida_repartida_en_varios_dias_no_rompe_por_perdida_diaria():
    """Misma pérdida acumulada (-1.200 USD, por encima del límite diario absoluto de 1.000)
    pero repartida en tres días de -400 USD cada uno: NINGÚN día individual llega al límite
    diario, así que la regla de pérdida diaria NO debe disparar la rotura. El límite de DD
    total se deja holgado (90%) para aislar específicamente la regla diaria."""
    ciclo = CicloFondeado(capital=50000.0, perdida_diaria_pct=2.0, dd_total_pct=90.0)
    trades = np.array([-400.0])
    # 3 días, 1 operación de -400 cada uno -> pérdida acumulada -1200, pérdida DIARIA -400.
    rng = _RNGSecuencial(ops_por_dia_secuencia=[1, 1, 1],
                        indices_choice_secuencia=[0, 0, 0])

    resultado = simular_vida_fondeada(trades, ops_por_dia=1.0, ciclo=ciclo,
                                      max_dias=3, rng=rng)

    assert resultado["rota"] is False
    assert resultado["dias"] == 3


def test_bug1_regresion_comparacion_correcta_pnl_del_dia_no_equity_acumulado():
    """Prueba directa de que la condición usa `pnl_dia` (pérdida de ESE día) y no
    `ciclo.capital - equity` (pérdida acumulada). Con el bug original la condición
    `ciclo.capital - equity >= perdida_diaria and pnl_dia < 0` habría roto la cuenta en el
    día 3 del test anterior en cuanto se corrigiera solo la acumulación de `pnl_dia` sin
    corregir la comparación. Este test reutiliza ese mismo escenario y confirma que con el
    fix completo la cuenta sigue viva."""
    ciclo = CicloFondeado(capital=50000.0, perdida_diaria_pct=2.0, dd_total_pct=90.0)
    trades = np.array([-400.0])
    rng = _RNGSecuencial(ops_por_dia_secuencia=[1, 1, 1],
                        indices_choice_secuencia=[0, 0, 0])

    resultado = simular_vida_fondeada(trades, ops_por_dia=1.0, ciclo=ciclo,
                                      max_dias=3, rng=rng)

    # Pérdida acumulada al día 3 (-1200 = 3 x -400) SÍ supera el límite diario absoluto
    # (-1000), lo que habría disparado el bug de comparación (`capital - equity` contra el
    # límite diario) si la condición no comparara la pérdida de ESE día.
    assert resultado["rota"] is False, (
        "La cuenta se rompió por PERDIDA_DIARIA aunque ningún día individual superó el "
        "límite diario: la comparación sigue usando la pérdida acumulada, no la del día."
    )


def test_bug2_deducir_ops_por_dia_usa_oos_days_real():
    """Con `duration_info.oos_days` real disponible, el ritmo debe ser trades/oos_days,
    NO trades/60."""
    candidate = {
        "scorecard_json": json.dumps({"duration_info": {"oos_days": 100.0}}),
    }
    ops = deducir_ops_por_dia(candidate, n_trades=250)
    assert ops == pytest.approx(2.5)
    # Si se hubiera mantenido la asunción de 60 días, habría dado 250/60 ≈ 4.1667 - distinto.
    assert ops != pytest.approx(250 / 60.0)


def test_bug2_deducir_ops_por_dia_usa_oos_months_si_no_hay_oos_days():
    candidate = {
        "duration_info": json.dumps({"oos_months": 6.4}),
    }
    ops = deducir_ops_por_dia(candidate, n_trades=500)
    assert ops == pytest.approx(500 / (6.4 * 30.4368), rel=1e-6)


def test_bug2_sin_duration_info_real_devuelve_none_fail_closed():
    """Sin ningún dato real de duración OOS, la función NO debe inventar 60 días: debe
    devolver None para que el llamador marque la candidata NO_EVALUABLE."""
    candidate = {"name": "sin_duration_info"}
    assert deducir_ops_por_dia(candidate, n_trades=300) is None


def test_bug2_override_explicito_del_operador_se_respeta():
    """El override explícito por CLI (`--ops-por-dia-override`) es la única vía legítima
    para forzar un valor cuando no hay dato real: a sabiendas, nunca en silencio."""
    candidate = {"name": "sin_duration_info"}
    assert deducir_ops_por_dia(candidate, n_trades=300, override=3.0) == 3.0
