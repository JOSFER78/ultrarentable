"""tests/test_mine_telemetria_bruto_neto.py — W2.7 (CARRIL TELEMETRIA): distinguir "la señal
no vale" de "la señal vale pero se la come el coste" dentro de la etiqueta "sin_ventaja".

Motivo (medido por el orquestador, ver orchestration/results/W27_telemetria_bruto_neto.md):
en ES 5m la comisión fija de MES (1,75 puntos RT) es el 64,6% del ATR; el PF neto mediano fue
0,535 con ~2.000 ops, compatible con una señal bruta neutra (PF bruto ~1,0) ahogada por la
fricción. Sin PF bruto en la telemetría, "sin_ventaja" no distinguía esas dos causas -- que se
arreglan de formas opuestas (cambiar de familia de estrategia vs cambiar de
timeframe/instrumento/broker con menos fricción).

Este test cubre, como TEST DE FUNCIÓN (objetos de resultado y registros de telemetría
construidos explícitamente, NO un backtest contra datos de mercado -- ver Regla #1 del
contrato: esto SÍ es legítimo porque queda etiquetado como tal):
  1. `_pf_bruto_y_coste()` -- calcula PF bruto, coste total y coste/bruto desde una lista de
     operaciones (ledger) construida a mano, incluidos los casos degenerados que el propio
     motor ya usa para el PF neto (ver event_backtest_engine.py línea ~1769).
  2. `resumir_causas()` -- el desglose nuevo `sin_ventaja_bruta` / `sin_ventaja_por_coste`
     dentro de cada etapa (y de `por_familia`), sin alterar el total agregado `sin_ventaja`
     preexistente (W2.6) ni el comportamiento con registros que no traen "pf_bruto".
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import pytest

from scripts.mine import _nueva_casilla_causas, _pf_bruto_y_coste, resumir_causas


@dataclass
class _TradeFalso:
    """Doble mínimo de TradeRecord (services/validation/engine/event_backtest_engine.py):
    solo los campos que `_pf_bruto_y_coste()` lee. Construido explícitamente a mano -- no es
    una operación de mercado real, es el objeto de la función bajo prueba."""
    gross_pnl_usd: float


@dataclass
class _BacktestResultFalso:
    """Doble mínimo de EventBacktestResult: solo los campos que `_pf_bruto_y_coste()` lee."""
    trades: List[_TradeFalso] = field(default_factory=list)
    profit_factor: float = 0.0
    total_fees_usd: float = 0.0
    total_slippage_usd: float = 0.0


def test_pf_bruto_y_coste_calcula_desde_el_ledger_de_operaciones():
    """Ledger a mano: ganancias brutas 250 (150+100), pérdidas brutas 50 -> pf_bruto=5.0.
    Coste total = fees(20) + slippage(5) = 25 -> 25/250*100 = 10.0% de las ganancias brutas."""
    bt = _BacktestResultFalso(
        trades=[
            _TradeFalso(gross_pnl_usd=150.0),
            _TradeFalso(gross_pnl_usd=-50.0),
            _TradeFalso(gross_pnl_usd=100.0),
        ],
        profit_factor=1.2,  # PF NETO, ya calculado por el motor -- se pasa tal cual (no se toca).
        total_fees_usd=20.0,
        total_slippage_usd=5.0,
    )
    out = _pf_bruto_y_coste(bt)
    assert out["pf_bruto"] == 5.0
    assert out["pf_neto"] == 1.2
    assert out["coste_total_usd"] == 25.0
    assert out["coste_pct_del_bruto"] == 10.0


def test_pf_bruto_y_coste_caso_degenerado_ganancias_sin_perdidas():
    """Sin pérdidas brutas que dividan: misma convención que ya usa el motor para el PF neto
    en este mismo caso (99.0), para que pf_bruto sea comparable al mismo umbral."""
    bt = _BacktestResultFalso(
        trades=[_TradeFalso(gross_pnl_usd=100.0), _TradeFalso(gross_pnl_usd=50.0)],
        profit_factor=99.0,
        total_fees_usd=3.0,
        total_slippage_usd=1.0,
    )
    out = _pf_bruto_y_coste(bt)
    assert out["pf_bruto"] == 99.0
    assert out["coste_pct_del_bruto"] == round(4.0 / 150.0 * 100, 2)


def test_pf_bruto_y_coste_sin_operaciones_da_pf_bruto_cero_y_coste_pct_none():
    """Sin operaciones no hay ganancias ni pérdidas brutas: pf_bruto=0.0 (misma convención
    degenerada que el motor), y coste_pct_del_bruto=None -- no se puede expresar un coste
    como porcentaje de cero ganancias brutas sin dividir por cero ni inventar un número."""
    bt = _BacktestResultFalso(trades=[], profit_factor=0.0, total_fees_usd=0.0, total_slippage_usd=0.0)
    out = _pf_bruto_y_coste(bt)
    assert out["pf_bruto"] == 0.0
    assert out["coste_pct_del_bruto"] is None
    assert out["coste_total_usd"] == 0.0


def test_pf_bruto_y_coste_solo_perdidas_brutas_da_coste_pct_none_pero_coste_total_real():
    """Ganancias brutas = 0 (todas las operaciones pierden en bruto): coste_pct_del_bruto no
    se puede expresar como % de un bruto que no ganó nada, pero coste_total_usd SIGUE siendo
    un dato real (no se descarta solo porque el ratio no se pueda calcular)."""
    bt = _BacktestResultFalso(
        trades=[_TradeFalso(gross_pnl_usd=-40.0), _TradeFalso(gross_pnl_usd=-10.0)],
        profit_factor=0.0,
        total_fees_usd=6.0,
        total_slippage_usd=2.0,
    )
    out = _pf_bruto_y_coste(bt)
    assert out["pf_bruto"] == 0.0
    assert out["coste_pct_del_bruto"] is None
    assert out["coste_total_usd"] == 8.0


def test_pf_bruto_y_coste_sin_lista_de_trades_declara_no_disponible():
    """Si el objeto de resultado no trae la lista de operaciones, no hay forma de calcular el
    PnL bruto sin tocar el motor: se declara NO DISPONIBLE con el motivo, nunca se inventa."""

    class _ResultadoSinTrades:
        profit_factor = 1.1
        total_fees_usd = 5.0
        total_slippage_usd = 1.0

    out = _pf_bruto_y_coste(_ResultadoSinTrades())
    assert out["pf_bruto"] == "NO DISPONIBLE"
    assert "pf_bruto_motivo" in out and out["pf_bruto_motivo"]
    assert out["coste_total_usd"] is None


def test_resumir_causas_desglosa_sin_ventaja_en_bruta_y_por_coste_sin_tocar_el_total():
    """Dos configuraciones OOS con pf NETO < 1.10 (ambas "sin_ventaja", igual que antes de
    W2.7): una con pf_bruto ya por debajo del umbral (señal mala) y otra con pf_bruto por
    encima (señal buena, ahogada por el coste). El agregado "sin_ventaja" no debe cambiar."""
    telemetria = [
        {"strategy_id": "s_bruta", "etapa": "OOS", "familia": "REVERSION_ATR",
         "trades": 250, "pf": 0.9, "pf_bruto": 0.95},
        {"strategy_id": "s_coste", "etapa": "OOS", "familia": "REVERSION_ATR",
         "trades": 300, "pf": 0.8, "pf_bruto": 1.4},
    ]
    causas = resumir_causas(telemetria)

    # El total agregado preexistente (W2.6) no cambia: sigue siendo la suma de ambas causas.
    assert causas["OOS"]["sin_ventaja"] == 2
    # El desglose nuevo SÍ distingue cada causa raíz.
    assert causas["OOS"]["sin_ventaja_bruta"] == 1
    assert causas["OOS"]["sin_ventaja_por_coste"] == 1
    # Y se propaga también al desglose por familia (W2.6).
    assert causas["OOS"]["por_familia"]["REVERSION_ATR"]["sin_ventaja_bruta"] == 1
    assert causas["OOS"]["por_familia"]["REVERSION_ATR"]["sin_ventaja_por_coste"] == 1


def test_resumir_causas_no_rompe_con_registros_sin_pf_bruto_w26():
    """Regresión directa contra el registro W2.6 pre-existente (sin campo "pf_bruto"): sigue
    contando en "sin_ventaja" exactamente igual, y el desglose nuevo se queda en 0 (no se
    inventa una clasificación que el registro no puede sustentar, ni revienta con KeyError)."""
    telemetria = [
        {"strategy_id": "s2", "etapa": "OOS", "familia": "REVERSION_ATR", "trades": 150, "pf": 0.8},
    ]
    causas = resumir_causas(telemetria)
    assert causas["OOS"]["sin_ventaja"] == 1
    assert causas["OOS"]["sin_ventaja_bruta"] == 0
    assert causas["OOS"]["sin_ventaja_por_coste"] == 0


def test_nueva_casilla_causas_trae_las_claves_nuevas_en_cero():
    casilla = _nueva_casilla_causas()
    assert casilla["sin_ventaja_bruta"] == 0
    assert casilla["sin_ventaja_por_coste"] == 0
