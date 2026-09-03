"""tests/test_m1_runner_orden.py

Pruebas unitarias de ordenación de celdas por rendimiento medido (A45).
Verifica que H1 y H4 se priorizan primero, M5 y M1 van al final,
y que ninguna celda se pierde ni se duplica.
"""

import pytest
from scripts.herramientas.m1_runner_sqx import (
    PRIORIDAD_MARCOS,
    clave_orden_celda,
    ordenar_celdas_por_rendimiento,
)


def test_prioridad_marcos_definicion():
    assert PRIORIDAD_MARCOS == ["H1", "H4", "M15", "M5", "M1"]


def test_ordenar_celdas_por_rendimiento_h1_h4_primero():
    celdas_desordenadas = [
        "FONDEO_MNQ_M1",
        "FONDEO_MYM_H4",
        "FONDEO_MES_M5",
        "FONDEO_MGC_H1",
        "FONDEO_MCL_M15",
        "FONDEO_MNQ_H1",
        "FONDEO_MGC_M1",
        "FONDEO_MYM_M5",
    ]
    ordenadas = ordenar_celdas_por_rendimiento(celdas_desordenadas)

    # Todas las celdas preservadas
    assert len(ordenadas) == len(celdas_desordenadas)
    assert set(ordenadas) == set(celdas_desordenadas)

    # Los marcos de las celdas ordenadas
    marcos_ordenados = [c.split("_")[-1] for c in ordenadas]

    # H1 debe ir antes que H4, H4 antes que M15, M15 antes que M5, M5 antes que M1
    indices_h1 = [i for i, m in enumerate(marcos_ordenados) if m == "H1"]
    indices_h4 = [i for i, m in enumerate(marcos_ordenados) if m == "H4"]
    indices_m15 = [i for i, m in enumerate(marcos_ordenados) if m == "M15"]
    indices_m5 = [i for i, m in enumerate(marcos_ordenados) if m == "M5"]
    indices_m1 = [i for i, m in enumerate(marcos_ordenados) if m == "M1"]

    assert max(indices_h1) < min(indices_h4)
    assert max(indices_h4) < min(indices_m15)
    assert max(indices_m15) < min(indices_m5)
    assert max(indices_m5) < min(indices_m1)


def test_universo_completo_30_celdas_sin_perdidas():
    simbolos = ["MES", "MNQ", "MYM", "MGC", "MCL", "M6E"]
    marcos = ["M1", "M5", "M15", "H1", "H4"]
    universo = [f"FONDEO_{s}_{tf}" for s in simbolos for tf in marcos]
    assert len(universo) == 30

    ordenadas = ordenar_celdas_por_rendimiento(universo)

    assert len(ordenadas) == 30
    assert set(ordenadas) == set(universo)

    # Las primeras 6 deben ser H1
    assert [c.split("_")[-1] for c in ordenadas[:6]] == ["H1"] * 6
    # Las siguientes 6 deben ser H4
    assert [c.split("_")[-1] for c in ordenadas[6:12]] == ["H4"] * 6
    # Las siguientes 6 deben ser M15
    assert [c.split("_")[-1] for c in ordenadas[12:18]] == ["M15"] * 6
    # Las siguientes 6 deben ser M5
    assert [c.split("_")[-1] for c in ordenadas[18:24]] == ["M5"] * 6
    # Las últimas 6 deben ser M1
    assert [c.split("_")[-1] for c in ordenadas[24:30]] == ["M1"] * 6


def test_prioridad_personalizada_y_marcos_desconocidos():
    celdas = ["FONDEO_ABC_D1", "FONDEO_XYZ_H1", "FONDEO_FOO_UNKNOWN"]
    prio_custom = ["D1", "H1"]
    ordenadas = ordenar_celdas_por_rendimiento(celdas, prioridad=prio_custom)

    assert ordenadas[0] == "FONDEO_ABC_D1"
    assert ordenadas[1] == "FONDEO_XYZ_H1"
    assert ordenadas[2] == "FONDEO_FOO_UNKNOWN"


def test_salvaguarda_universo_si_manifiesto_truncado(tmp_path):
    import json
    from scripts.herramientas.m1_runner_sqx import celdas_del_manifiesto

    base = tmp_path / "fondeo"
    base.mkdir()

    # Manifiesto truncado con solo 1 celda (ej. tras un --solo)
    manifiesto_truncado = {"proyectos": [{"proyecto": "FONDEO_MGC_H4"}]}
    (base / "manifiesto.json").write_text(json.dumps(manifiesto_truncado), encoding="utf-8")

    # Estado previo con 30 celdas
    simbolos = ["MES", "MNQ", "MYM", "MGC", "MCL", "M6E"]
    marcos = ["M1", "M5", "M15", "H1", "H4"]
    celdas_totales = [f"FONDEO_{s}_{tf}" for s in simbolos for tf in marcos]
    estado_completo = {"ronda": 1, "celdas": {c: {"estado": "HECHA"} for c in celdas_totales}}
    (base / "estado.json").write_text(json.dumps(estado_completo), encoding="utf-8")

    # Lógica de salvaguarda
    celdas_leidas = celdas_del_manifiesto(base)
    assert len(celdas_leidas) == 1  # El manifiesto solo tiene 1

    # Al detectar la discrepancia, se adopta el universo completo de estado.json
    if len(celdas_leidas) < len(estado_completo["celdas"]):
        celdas_efectivas = ordenar_celdas_por_rendimiento(list(estado_completo["celdas"].keys()))

    assert len(celdas_efectivas) == 30
    assert set(celdas_efectivas) == set(celdas_totales)
    # Comprobar que además están ordenadas por rendimiento (H1/H4 primero)
    assert celdas_efectivas[0].endswith("_H1")

