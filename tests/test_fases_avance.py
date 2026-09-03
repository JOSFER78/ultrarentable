"""
tests/test_fases_avance.py

Tests unitarios para la lógica pura de cálculo de avance y estado de fases (A40).
Utiliza exclusivamente casos sintéticos inventados para probar la máquina de estados
sin depender de los ficheros reales del tablero que cambian en cada ciclo.
"""

import pytest
from services.api.app.core.fases_avance import (
    calcular_avance_fase,
    calcular_fases_avance,
    ESTADOS_FASE,
)


def test_fase_con_devolucion_es_con_correcciones_pendientes():
    tareas = [
        {"id": "A01", "estado": "VERIFICADO"},
        {"id": "A02", "estado": "DEVUELTO", "motivo": "Falta parámetro X"},
        {"id": "A03", "estado": "EN_CURSO"},
    ]
    res = calcular_avance_fase(
        fase_id="F03",
        titulo="Descubrimiento",
        depende_de=[],
        verificacion_global="Criterio de prueba",
        cerrada=False,
        tareas=tareas,
    )
    assert res["estado_calculado"] == "con correcciones pendientes"
    assert res["devueltas"] == 1
    assert res["verificadas"] == 1
    assert res["total_tareas"] == 3
    assert res["avance_label"] == "1 de 3"


def test_fase_en_marcha_con_en_curso_o_entregado():
    tareas = [
        {"id": "A10", "estado": "VERIFICADO"},
        {"id": "A11", "estado": "EN_CURSO"},
        {"id": "A12", "estado": "PENDIENTE"},
    ]
    res = calcular_avance_fase(
        fase_id="F03",
        titulo="Descubrimiento",
        depende_de=[],
        verificacion_global="Criterio",
        cerrada=False,
        tareas=tareas,
    )
    assert res["estado_calculado"] == "en marcha"
    assert res["avance_label"] == "1 de 3"


def test_todas_verificadas_es_lista_para_auditar_no_cerrada():
    """
    Regla crítica de A40: 'todas verificadas' NUNCA es 'cerrada'.
    Pasa a 'lista para auditar'.
    """
    tareas = [
        {"id": "A20", "estado": "VERIFICADO"},
        {"id": "A21", "estado": "VERIFICADO"},
        {"id": "A22", "estado": "VERIFICADO"},
    ]
    res = calcular_avance_fase(
        fase_id="F02",
        titulo="Motor realista",
        depende_de=["F01"],
        verificacion_global="13 partes publicados",
        cerrada=False,  # El orquestador no ha puesto cerrada: true
        tareas=tareas,
    )
    assert res["estado_calculado"] == "lista para auditar"
    assert res["estado_calculado"] != "cerrada"
    assert res["avance_label"] == "3 de 3"
    assert res["progreso_pct"] == 100.0


def test_fase_formalmente_cerrada_con_flag():
    tareas = [
        {"id": "A20", "estado": "VERIFICADO"},
        {"id": "A21", "estado": "VERIFICADO"},
    ]
    res = calcular_avance_fase(
        fase_id="F01",
        titulo="Censo catálogo",
        depende_de=["F00"],
        verificacion_global="Censo completo",
        cerrada=True,  # Auditada y sellada por el orquestador
        tareas=tareas,
    )
    assert res["estado_calculado"] == "cerrada"


def test_esperando_turno_si_dependencias_abiertas_y_sin_empezar():
    tareas = [
        {"id": "A50", "estado": "PENDIENTE"},
        {"id": "A51", "estado": "PENDIENTE"},
    ]
    res = calcular_avance_fase(
        fase_id="F07",
        titulo="Fondeo exámenes",
        depende_de=["F03"],
        verificacion_global="Exámenes reales",
        cerrada=False,
        tareas=tareas,
        fases_cerradas={"F01", "F02"},  # F03 aún no cerrada
    )
    assert res["estado_calculado"] == "esperando turno"
    assert res["avance_label"] == "0 de 2"
    assert res["progreso_pct"] == 0.0


def test_calculo_conjunto_de_fases_y_fase_activa():
    fases_raw = [
        {"id": "F01", "titulo": "Censo", "depende_de": [], "cerrada": True},
        {"id": "F02", "titulo": "Motor", "depende_de": ["F01"], "cerrada": True},
        {"id": "F03", "titulo": "Descubrimiento masivo", "depende_de": ["F01", "F02"], "cerrada": False},
        {"id": "F10", "titulo": "Operaciones e Infra", "depende_de": [], "cerrada": False},
    ]
    tareas_por_fase = {
        "F01": [{"id": "A01", "estado": "VERIFICADO"}],
        "F02": [{"id": "A02", "estado": "VERIFICADO"}],
        "F03": [
            {"id": "A31", "estado": "VERIFICADO"},
            {"id": "A32", "estado": "VERIFICADO"},
            {"id": "A33", "estado": "DEVUELTO"},
            {"id": "A35", "estado": "DEVUELTO"},
            {"id": "A36", "estado": "EN_CURSO"},
            {"id": "A39", "estado": "PENDIENTE"},
            {"id": "E01", "estado": "PENDIENTE"},
            {"id": "A21", "estado": "VERIFICADO"},
            {"id": "A22", "estado": "VERIFICADO"},
            {"id": "A23", "estado": "VERIFICADO"},
            {"id": "A24", "estado": "VERIFICADO"},
            {"id": "A25", "estado": "VERIFICADO"},
            {"id": "A26", "estado": "VERIFICADO"},
        ],
        "F10": [{"id": "A37", "estado": "ENTREGADO"}],
    }

    resultado = calcular_fases_avance(fases_raw, tareas_por_fase)

    # F03 debe ser la fase activa destacada con 8 de 13
    f03 = next(f for f in resultado if f["id"] == "F03")
    assert f03["es_activa"] is True
    assert f03["total_tareas"] == 13
    assert f03["verificadas"] == 8
    assert f03["avance_label"] == "8 de 13"
    assert f03["estado_calculado"] == "con correcciones pendientes"

    # F10 es carril de apoyo
    f10 = next(f for f in resultado if f["id"] == "F10")
    assert f10["es_carril_apoyo"] is True
    assert f10["es_activa"] is False
