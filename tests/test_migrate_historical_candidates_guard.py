"""tests/test_migrate_historical_candidates_guard.py — W4.2 (AG-C): scripts/migrate_historical_candidates.py
ya no puede corromper la BD viva si se ejecuta hoy por error.

El paso 2 de esa migración estampaba `engine_version = '5.4.0'` (hardcodeado) EN TODOS los
candidatos de la BD, sin condición. Es un saneamiento HISTÓRICO puntual del lanzamiento de
motor v5.4.0 (2026-08-25); con el motor vigente hoy en 5.17.0 (services/engine_version.py),
volver a ejecutarlo sobrescribiría el engine_version REAL de cada candidato certificado con
el motor vigente por ese literal viejo, y todo pasaría a descartarse como STALE aguas abajo
(is_version_stale, scripts/gobernanza_regla26.py) -- el mismo bug de fondo que motivó T2,
pero en sentido inverso y sobre datos ya certificados.

Se verifica que `run_migration()` se niega a tocar la base de datos (código de salida
distinto de 0, ningún acceso a sqlite3.connect) mientras el motor vigente no sea exactamente
el ámbito histórico de esa migración ('5.4.0') -- que es siempre, salvo que alguien revierta
el motor. No se usa ninguna base de datos real: se comprueba el fail-closed ANTES de que el
código llegue a abrir conexión alguna.
"""
from __future__ import annotations

import sqlite3

import pytest

from scripts.migrate_historical_candidates import (
    _MIGRACION_ENGINE_VERSION_OBJETIVO,
    run_migration,
)
from services.engine_version import CURRENT_ENGINE_VERSION


def test_motor_vigente_ya_no_es_el_ambito_historico_de_la_migracion():
    """Precondición del propio test: si esto deja de ser cierto (alguien revierte el motor
    a 5.4.0) el resto del test pierde sentido -- se documenta explícitamente."""
    assert CURRENT_ENGINE_VERSION != _MIGRACION_ENGINE_VERSION_OBJETIVO, (
        "El motor vigente coincide con el ámbito histórico de esta migración; el guard de "
        "fail-closed no aplica en este estado y este test debe revisarse."
    )


def test_run_migration_se_niega_a_correr_con_el_motor_vigente_y_no_toca_ninguna_bd(monkeypatch):
    """Con el motor vigente distinto de '5.4.0' (el caso real hoy), run_migration() debe
    abortar con código de salida != 0 SIN llegar a abrir ninguna conexión sqlite3 -- ni
    siquiera a comprobar si el fichero de la BD existe."""
    llamadas_a_connect = []

    def _connect_espia(*args, **kwargs):
        llamadas_a_connect.append((args, kwargs))
        raise AssertionError(
            "run_migration() intentó abrir una conexión sqlite3 pese al motor no coincidir "
            "con el ámbito histórico de la migración -- el guard fail-closed no está "
            "bloqueando antes de tocar datos."
        )

    monkeypatch.setattr(sqlite3, "connect", _connect_espia)

    codigo_salida = run_migration()

    assert codigo_salida != 0, "run_migration() debe devolver código de salida != 0 (aborto)"
    assert llamadas_a_connect == [], "no debe haberse abierto ninguna conexión a la BD"
