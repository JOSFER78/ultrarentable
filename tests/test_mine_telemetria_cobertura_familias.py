"""tests/test_mine_telemetria_cobertura_familias.py — W2.6 (AG-C): la telemetría del embudo
de scripts/mine.py debe registrar su propia cobertura por familia de arquetipo.

Motivo (hallazgo del orquestador, verificado en vivo con `--dry-run` en este mismo lote):
`scripts/mine.py::run_mining_pipeline` trunca el espacio de búsqueda con
`search_space[:max_candidates]`, y `--max-candidates` vale 20 por defecto. Como el recorte es
un PREFIJO y el perfil `arquetipos` emite primero las 108 configuraciones de REVERSION_ATR,
una campaña `--track fondeo --symbol ES --tf 4h --profile arquetipos` (por defecto) evalúa
SIEMPRE una sola familia de seis -- confirmado con un dry-run real en este mismo diagnóstico:
`espacio_total=420`, `truncado=True`, `cobertura_familias={"REVERSION_ATR": 20}`. La
telemetría persistida antes de este fix solo decía "20/20 sin_ventaja" sin decir de qué
familia, haciendo indiagnosticable el único embudo persistido.

Este test cubre las dos funciones puras que construyen el bloque de telemetría:
  1. `resumir_causas()` -- debe desglosar cada etapa por familia (clave "por_familia"),
     además del total agregado.
  2. `persistir_telemetria()` -- debe escribir en el JSON, dentro de "contexto": los campos
     nuevos `max_candidates`, `espacio_total` y `truncado`; y en la raíz del payload, un
     bloque nuevo `cobertura_familias` con el histograma real.

No usa datos de mercado: los registros de telemetría y el resultado del pipeline se
construyen explícitamente (test de la función, no un backtest inventado). El fichero que
`persistir_telemetria()` escribe de verdad en `orchestration/results/telemetria/` se limpia
al final del test para no dejar basura en un directorio de resultados reales.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.mine import persistir_telemetria, resumir_causas


def test_resumir_causas_desglosa_cada_etapa_por_familia_ademas_del_total():
    """Dos familias en la misma etapa OOS: el total agregado debe seguir siendo correcto, y
    además debe poder recuperarse cuántas de esas muertes fueron de cada familia."""
    telemetria = [
        {"strategy_id": "s1", "etapa": "OOS", "familia": "REVERSION_ATR", "trades": 3, "pf": 0.9},
        {"strategy_id": "s2", "etapa": "OOS", "familia": "REVERSION_ATR", "trades": 150, "pf": 0.8},
        {"strategy_id": "s3", "etapa": "OOS", "familia": "SQUEEZE_BREAKOUT", "trades": 300, "pf": 1.4},
        {"strategy_id": "s4", "etapa": "IS", "familia": "REVERSION_ATR", "trades": 2, "pf": 0.5},
    ]
    causas = resumir_causas(telemetria)

    # Total agregado de la etapa OOS: 3 registros (comportamiento preexistente, no debe romperse).
    assert causas["OOS"]["total"] == 3
    # Desglose por familia dentro de la etapa OOS.
    assert causas["OOS"]["por_familia"]["REVERSION_ATR"]["total"] == 2
    assert causas["OOS"]["por_familia"]["SQUEEZE_BREAKOUT"]["total"] == 1
    # s1: trades=3 < MIN_OPERACIONES_OOS y pf=0.9 < 1.10 -> "ambas".
    assert causas["OOS"]["por_familia"]["REVERSION_ATR"]["ambas"] == 1
    # s2: trades=150 >= min, pf=0.8 < 1.10 -> "sin_ventaja".
    assert causas["OOS"]["por_familia"]["REVERSION_ATR"]["sin_ventaja"] == 1
    # s3: trades=300, pf=1.4 -> ni pocas ni floja -> "otro".
    assert causas["OOS"]["por_familia"]["SQUEEZE_BREAKOUT"]["otro"] == 1
    # La etapa IS es independiente de OOS.
    assert causas["IS"]["total"] == 1
    assert causas["IS"]["por_familia"]["REVERSION_ATR"]["total"] == 1


def test_resumir_causas_agrupa_bajo_signo_de_interrogacion_si_falta_familia():
    """Fail-visible, no fail-silent: un registro sin "familia" no debe reventar ni
    desaparecer, se agrupa bajo la clave explícita "?" para que sea visible en el JSON."""
    telemetria = [{"strategy_id": "s1", "etapa": "IS", "trades": 1, "pf": 0.5}]
    causas = resumir_causas(telemetria)
    assert causas["IS"]["por_familia"]["?"]["total"] == 1


def test_persistir_telemetria_escribe_contexto_y_cobertura_familias_nuevos(tmp_path):
    """Prueba de la función completa que construye el bloque de telemetría: dado un
    `resultado` de pipeline construido explícitamente (con max_candidates/espacio_total/
    truncado/cobertura_familias, exactamente como los produce ahora run_mining_pipeline),
    el JSON escrito a disco debe traer los campos nuevos en el sitio correcto."""
    resultado = {
        "track": "FONDEO",
        "symbol": "ES",
        "execution_symbol": "MES",
        "timeframe": "4h",
        "profile": "TEST_arquetipos_cobertura",
        "dataset_source": "auto",
        "dataset_file": "ds_test.json",
        "certified_count": 0,
        "configuraciones_evaluadas": 20,
        "max_candidates": 20,
        "espacio_total": 420,
        "truncado": True,
        "cobertura_familias": {"REVERSION_ATR": 20},
        "barras_is": 100,
        "barras_val": 50,
        "barras_oos": 50,
        "embudo": {"OOS": 20},
        "telemetria": [
            {"strategy_id": f"s{i}", "etapa": "OOS", "familia": "REVERSION_ATR",
             "trades": 3, "pf": 0.5}
            for i in range(20)
        ],
    }

    ruta_escrita = persistir_telemetria(resultado)
    assert ruta_escrita is not None, "persistir_telemetria() no devolvió una ruta (fallo silencioso)"
    try:
        payload = json.loads(Path(ruta_escrita).read_text(encoding="utf-8"))

        # Campos nuevos dentro de "contexto".
        assert payload["contexto"]["max_candidates"] == 20
        assert payload["contexto"]["espacio_total"] == 420
        assert payload["contexto"]["truncado"] is True

        # Bloque nuevo "cobertura_familias" en la raíz del payload.
        assert payload["cobertura_familias"] == {"REVERSION_ATR": 20}

        # causas_por_etapa sigue trayendo el desglose por familia (via resumir_causas).
        assert payload["causas_por_etapa"]["OOS"]["por_familia"]["REVERSION_ATR"]["total"] == 20
    finally:
        # No dejar basura en orchestration/results/telemetria/ (directorio de resultados
        # reales del sistema, no un scratch de test).
        Path(ruta_escrita).unlink(missing_ok=True)
