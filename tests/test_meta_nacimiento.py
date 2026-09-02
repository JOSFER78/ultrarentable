"""tests/test_meta_nacimiento.py
Suite de validación canónica para el nacimiento de `services/meta/` (M4 / W6.0).
Demuestra con series y datos REALES del repositorio:
1. Unificación y fail-closed de estados de certificación (`estados.py`).
2. Correlación honesta por solape temporal real, sin fabricaciones (`correlacion.py`).
3. Asignación estática determinista de mínima varianza y HRP (`ensamblado.py`).
4. Pureza de AST: ausencia absoluta del módulo/subcadena random y cero generadores sintéticos.

REAL-ONLY · ZERO-MOCKS · FAIL-CLOSED
"""

from __future__ import annotations

import ast
import json
import math
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pytest

from services.meta.estados import CERTIFIED_STATUSES, es_certificada
from services.meta.correlacion import (
    ResultadoCorrelacion,
    correlacion_honesta,
    matriz_correlacion,
)
from services.meta.ensamblado import (
    ResultadoEnsamblado,
    pesos_min_varianza,
    pesos_hrp,
)


def _cargar_series_friccion_reales() -> Dict[str, List[Tuple[int, float]]]:
    """Extrae series temporales reales de retornos desde data/bingx/friccion_2026-08-31/."""
    base_dir = Path("data/bingx/friccion_2026-08-31")
    simbolos = ["BTC-USDT", "ETH-USDT", "SOL-USDT"]
    series_dict: Dict[str, List[Tuple[int, float]]] = {}

    for sym in simbolos:
        fpath = base_dir / f"{sym}.json"
        if not fpath.exists():
            continue
        data = json.loads(fpath.read_text(encoding="utf-8"))
        history = data.get("funding_history", [])
        # Ordenar cronológicamente por fundingTime (marca temporal real de 8h)
        sorted_history = sorted(history, key=lambda x: x["fundingTime"])
        # Construir serie de retornos reales entre marcas consecutivas
        ret_serie: List[Tuple[int, float]] = []
        for i in range(1, len(sorted_history)):
            prev_p = float(sorted_history[i - 1]["markPrice"])
            curr_p = float(sorted_history[i]["markPrice"])
            ts = int(sorted_history[i]["fundingTime"])
            if prev_p > 0:
                ret = (curr_p - prev_p) / prev_p
                ret_serie.append((ts, ret))
        if ret_serie:
            series_dict[sym] = ret_serie

    return series_dict


# ======================================================================================
# 1. Tests de Estados de Certificación (`estados.py`)
# ======================================================================================

def test_es_certificada_acepta_certificadas_vigentes():
    """Verifica que es_certificada acepta exactamente los estados canónicos vigentes."""
    assert es_certificada("APPROVED_CURRENT_ENGINE") is True
    assert es_certificada("CERTIFIED_CURRENT") is True
    assert es_certificada("  approved_current_engine  ") is True
    assert es_certificada("certified_current") is True
    assert "APPROVED_CURRENT_ENGINE" in CERTIFIED_STATUSES
    assert "CERTIFIED_CURRENT" in CERTIFIED_STATUSES


def test_es_certificada_rechaza_no_certificadas_legacy_y_fallbacks():
    """Verifica que es_certificada rechaza fail-closed cualquier estado no vigente o legacy."""
    # Rechazos explícitos
    assert es_certificada("REJECTED_GATES") is False
    assert es_certificada("REJECTED_OOS") is False
    assert es_certificada("REJECTED_OVERFITTING") is False

    # Estados obsoletos de motor (Regla #26)
    assert es_certificada("LEGACY_5_4_0") is False
    assert es_certificada("LEGACY_MOTOR_OBSOLETO") is False

    # Estados de falta de evidencia
    assert es_certificada("BLOCKED_NO_EVIDENCE") is False
    assert es_certificada("NO_EVIDENCE") is False

    # Estados legacy de meta_ensemble_service no anclados a versión
    assert es_certificada("APPROVED") is False
    assert es_certificada("ULTRA_CERTIFIED") is False
    assert es_certificada("FUNDING_CERTIFIED") is False
    assert es_certificada("CERTIFIED_PASS") is False
    assert es_certificada("CERTIFICADA_TIER_1") is False

    # Casos nulos o vacíos
    assert es_certificada(None) is False
    assert es_certificada("") is False
    assert es_certificada("   ") is False
    assert es_certificada("UNKNOWN_STATUS") is False


# ======================================================================================
# 2. Tests de Correlación Honesta (`correlacion.py`)
# ======================================================================================

def test_correlacion_honesta_con_series_reales_solape_suficiente():
    """Calcula correlación real entre series de BTC y ETH con solape >= 30."""
    series = _cargar_series_friccion_reales()
    assert "BTC-USDT" in series, "Falta serie real de BTC-USDT en data/bingx/friccion_2026-08-31/"
    assert "ETH-USDT" in series, "Falta serie real de ETH-USDT en data/bingx/friccion_2026-08-31/"

    serie_btc = series["BTC-USDT"]
    serie_eth = series["ETH-USDT"]

    res = correlacion_honesta(serie_btc, serie_eth, min_solape=30)
    assert res.coef is not None
    assert isinstance(res.coef, float)
    assert -1.0 <= res.coef <= 1.0
    assert res.n_solape >= 30
    assert res.motivo == "OK"


def test_correlacion_honesta_falla_cerrado_con_solape_corto_o_insuficiente():
    """Verifica que con <=2 pasos o solape < min_solape devuelve NO_EVALUABLE, nunca 0.15."""
    # Caso canónico de aceptación: 2 pasos
    res_2pasos = correlacion_honesta([(1, 0.1), (2, 0.2)], [(1, 0.1), (2, 0.3)], min_solape=30)
    assert res_2pasos.coef is None
    assert res_2pasos.n_solape == 2
    assert "NO_EVALUABLE" in res_2pasos.motivo

    # Caso con 10 pasos (< 30)
    serie_a = [(i, 0.01 * (i % 3)) for i in range(10)]
    serie_b = [(i, 0.02 * (i % 4)) for i in range(10)]
    res_10pasos = correlacion_honesta(serie_a, serie_b, min_solape=30)
    assert res_10pasos.coef is None
    assert res_10pasos.n_solape == 10
    assert "NO_EVALUABLE" in res_10pasos.motivo

    # Cero solape temporal (marcas disjuntas)
    serie_disj_a = [(100 + i, 0.01) for i in range(50)]
    serie_disj_b = [(200 + i, 0.02) for i in range(50)]
    res_disj = correlacion_honesta(serie_disj_a, serie_disj_b, min_solape=30)
    assert res_disj.coef is None
    assert res_disj.n_solape == 0
    assert "NO_EVALUABLE" in res_disj.motivo


def test_correlacion_honesta_rechaza_varianza_nula_y_datos_invalidos():
    """Verifica fail-closed ante series constantes o vacías."""
    serie_cte = [(i, 5.0) for i in range(40)]
    serie_var = [(i, float(i)) for i in range(40)]

    res_cte = correlacion_honesta(serie_cte, serie_var, min_solape=30)
    assert res_cte.coef is None
    assert "NO_EVALUABLE" in res_cte.motivo
    assert "varianza" in res_cte.motivo.lower()

    assert correlacion_honesta([], serie_var).coef is None
    assert correlacion_honesta(None, serie_var).coef is None


def test_matriz_correlacion_sobre_series_reales_multi_activo():
    """Calcula la matriz completa de correlación sobre 3 activos reales (BTC, ETH, SOL)."""
    series = _cargar_series_friccion_reales()
    assert len(series) >= 3, "Se requieren al menos 3 series reales (BTC, ETH, SOL)"

    mat, motivos = matriz_correlacion(series, min_solape=30)
    assert mat is not None
    assert motivos == {"status": "OK"}
    assert len(mat) == 3
    assert all(len(row) == 3 for row in mat)

    # Diagonal unitaria
    for i in range(3):
        assert mat[i][i] == 1.0

    # Simetría exacta y rango [-1, 1]
    for i in range(3):
        for j in range(3):
            assert mat[i][j] == mat[j][i]
            assert -1.0 <= mat[i][j] <= 1.0


def test_matriz_correlacion_fail_closed_si_falla_un_par():
    """Verifica que si un par tiene solape insuficiente, la matriz completa devuelve None."""
    series = _cargar_series_friccion_reales()
    series_con_corta = dict(series)
    series_con_corta["SHORT_TEST"] = [(1, 0.01), (2, 0.02)]

    mat, motivos = matriz_correlacion(series_con_corta, min_solape=30)
    assert mat is None
    assert any("NO_EVALUABLE" in mot for mot in motivos.values())


# ======================================================================================
# 3. Tests de Ensamblado Determinista (`ensamblado.py`)
# ======================================================================================

def test_ensamblado_min_varianza_y_hrp_sobre_3_series_reales():
    """Calcula pesos de mínima varianza y HRP sobre series reales de 3 activos."""
    series = _cargar_series_friccion_reales()
    keys = sorted(series.keys())
    assert len(keys) >= 3

    # Extraer marcas comunes para matriz de covarianza y correlación
    common_ts = sorted(set.intersection(*(set(dict(series[k]).keys()) for k in keys)))
    assert len(common_ts) >= 30

    ret_matrix = np.array([[dict(series[k])[ts] for ts in common_ts] for k in keys])
    cov_matrix = np.cov(ret_matrix)
    corr_matrix = np.corrcoef(ret_matrix)

    # 1. Mínima varianza (long-only)
    res_mv = pesos_min_varianza(cov_matrix)
    assert res_mv.pesos is not None
    assert res_mv.motivo == "OK"
    assert len(res_mv.pesos) == 3
    assert abs(sum(res_mv.pesos) - 1.0) < 1e-4
    assert all(w >= 0.0 for w in res_mv.pesos)

    # 2. Hierarchical Risk Parity (HRP)
    res_hrp = pesos_hrp(corr_matrix, cov_matrix)
    assert res_hrp.pesos is not None
    assert res_hrp.motivo == "OK"
    assert len(res_hrp.pesos) == 3
    assert abs(sum(res_hrp.pesos) - 1.0) < 1e-4
    assert all(w >= 0.0 for w in res_hrp.pesos)

    # 3. Reproducibilidad determinista bit a bit en dos pasadas consecutivas
    res_mv_2 = pesos_min_varianza(cov_matrix)
    res_hrp_2 = pesos_hrp(corr_matrix, cov_matrix)
    assert res_mv.pesos == res_mv_2.pesos
    assert res_hrp.pesos == res_hrp_2.pesos


def test_ensamblado_fail_closed_ante_matrices_no_definidas_positivas_o_invalidas():
    """Verifica que tanto min_varianza como HRP rechazan matrices singulares, NaNs o nulas."""
    # Matriz singular (rango 1, no definida positiva)
    mat_singular = [[1.0, 1.0], [1.0, 1.0]]
    res_mv_sing = pesos_min_varianza(mat_singular)
    assert res_mv_sing.pesos is None
    assert "NO_EVALUABLE" in res_mv_sing.motivo

    res_hrp_sing = pesos_hrp(mat_singular)
    assert res_hrp_sing.pesos is None
    assert "NO_EVALUABLE" in res_hrp_sing.motivo

    # Matriz con NaN
    mat_nan = [[1.0, float("nan")], [float("nan"), 1.0]]
    assert pesos_min_varianza(mat_nan).pesos is None
    assert pesos_hrp(mat_nan).pesos is None

    # Entradas nulas o de dimensión incorrecta
    assert pesos_min_varianza(None).pesos is None
    assert pesos_hrp(None).pesos is None
    assert pesos_min_varianza([[1.0, 0.2]]).pesos is None


# ======================================================================================
# 4. Auditoría Estática de Pureza (Zero Random)
# ======================================================================================

def test_pureza_ast_y_cero_random_en_ensamblado():
    """Comprueba formalmente que ensamblado.py no importa ni contiene la subcadena random."""
    ensamblado_path = Path("services/meta/ensamblado.py")
    assert ensamblado_path.exists(), "El archivo services/meta/ensamblado.py debe existir"

    src = ensamblado_path.read_text(encoding="utf-8")
    assert "random" not in src, "Prohibido el uso o mención de 'random' en services/meta/ensamblado.py"

    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name != "random", "Import prohibido de 'random'"
        elif isinstance(node, ast.ImportFrom):
            assert node.module != "random", "ImportFrom prohibido de 'random'"
