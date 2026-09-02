"""services/meta/correlacion.py
Cálculo honesto y reproducible de correlaciones entre estrategias (M4 / W4.5 / W6.0).
REAL-ONLY · ZERO-MOCKS · FAIL-CLOSED

Doctrina cuantitativa:
----------------------
1. Alineación temporal estricta por timestamp:
   Nunca se correlaciona por índice secuencial de trade ni sobre curvas de nivel de equity
   acumulado (ambos son errores estadísticos que introducen correlaciones espurias).
   Se correlaciona sobre retorno / PnL por período común real (día, hora o marca temporal observada).
2. Solape temporal mínimo:
   Exige un mínimo de observaciones coincidentes (`min_solape`, por defecto 30).
   Con solape insuficiente (<=2 pasos o < min_solape), devuelve `NO_EVALUABLE` explícito.
   Queda terminantemente prohibido fabricar 0.15, matriz identidad o silenciar NaN -> 0.0.
3. Fail-closed ante falta de varianza o valores no finitos:
   Si una serie tiene varianza cero o el cálculo genera NaN/Inf, se devuelve `NO_EVALUABLE`.
"""

from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List, NamedTuple, Optional, Sequence, Tuple, Union


class ResultadoCorrelacion(NamedTuple):
    coef: Optional[float]
    n_solape: int
    motivo: str


def _normalizar_serie_temporal(serie: Any) -> Dict[Any, float]:
    """Convierte entradas heterogéneas a un diccionario timestamp -> valor numérico."""
    if serie is None:
        return {}
    if isinstance(serie, dict):
        out: Dict[Any, float] = {}
        for k, v in serie.items():
            try:
                out[k] = float(v)
            except (TypeError, ValueError):
                continue
        return out
    if isinstance(serie, (list, tuple, set)):
        out = {}
        for item in serie:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                ts, val = item[0], item[1]
                try:
                    out[ts] = float(val)
                except (TypeError, ValueError):
                    continue
        return out
    return {}


def correlacion_honesta(
    serie_a: Any,
    serie_b: Any,
    min_solape: int = 30,
) -> ResultadoCorrelacion:
    """Calcula el coeficiente de correlación de Pearson sobre el solape temporal real de dos series.

    Args:
        serie_a: Secuencia de tuplas `(timestamp, valor)` o diccionario `{timestamp: valor}`.
        serie_b: Secuencia de tuplas `(timestamp, valor)` o diccionario `{timestamp: valor}`.
        min_solape: Umbral mínimo de observaciones pareadas requeridas (por defecto 30).

    Returns:
        ResultadoCorrelacion(coef, n_solape, motivo)
        Si `n_solape < min_solape`, `coef` es None y `motivo` inicia con "NO_EVALUABLE".
    """
    map_a = _normalizar_serie_temporal(serie_a)
    map_b = _normalizar_serie_temporal(serie_b)

    if not map_a or not map_b:
        return ResultadoCorrelacion(
            coef=None,
            n_solape=0,
            motivo="NO_EVALUABLE: serie de retornos ausente o vacía",
        )

    common_keys = sorted(set(map_a.keys()) & set(map_b.keys()))
    n_solape = len(common_keys)

    if n_solape < min_solape:
        return ResultadoCorrelacion(
            coef=None,
            n_solape=n_solape,
            motivo=f"NO_EVALUABLE: solape temporal insuficiente ({n_solape} < {min_solape})",
        )

    vals_a = [map_a[k] for k in common_keys]
    vals_b = [map_b[k] for k in common_keys]

    mean_a = sum(vals_a) / n_solape
    mean_b = sum(vals_b) / n_solape

    var_a = sum((x - mean_a) ** 2 for x in vals_a) / (n_solape - 1)
    var_b = sum((y - mean_b) ** 2 for y in vals_b) / (n_solape - 1)

    if var_a <= 1e-14 or var_b <= 1e-14:
        return ResultadoCorrelacion(
            coef=None,
            n_solape=n_solape,
            motivo="NO_EVALUABLE: varianza nula o casi nula en al menos una serie",
        )

    std_a = math.sqrt(var_a)
    std_b = math.sqrt(var_b)

    cov = sum((vals_a[i] - mean_a) * (vals_b[i] - mean_b) for i in range(n_solape)) / (n_solape - 1)
    raw_coef = cov / (std_a * std_b)

    if math.isnan(raw_coef) or math.isinf(raw_coef):
        return ResultadoCorrelacion(
            coef=None,
            n_solape=n_solape,
            motivo="NO_EVALUABLE: cálculo de correlación produjo valor no finito (NaN/Inf)",
        )

    clamped_coef = max(-1.0, min(1.0, float(raw_coef)))
    return ResultadoCorrelacion(
        coef=round(clamped_coef, 6),
        n_solape=n_solape,
        motivo="OK",
    )


def matriz_correlacion(
    series: Dict[str, Any],
    min_solape: int = 30,
) -> Tuple[Optional[List[List[float]]], Dict[str, str]]:
    """Calcula la matriz completa de correlación sobre un diccionario de series temporales.

    Args:
        series: Diccionario `{identificador_estrategia: serie_temporal}`.
        min_solape: Umbral mínimo de observaciones pareadas exigido a cada par.

    Returns:
        (matriz, motivos)
        Si cualquier par fuera de la diagonal no es evaluable, devuelve (None, motivos) (fail-closed).
    """
    if not series or not isinstance(series, dict):
        return None, {"error": "NO_EVALUABLE: diccionario de series vacío o inválido"}

    keys = list(series.keys())
    n = len(keys)

    if n < 2:
        return None, {"error": f"NO_EVALUABLE: se requieren al menos 2 series (recibidas {n})"}

    motivos: Dict[str, str] = {}
    matrix: List[List[float]] = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    all_ok = True

    for i in range(n):
        for j in range(i + 1, n):
            key_i = keys[i]
            key_j = keys[j]
            pair_key = f"{key_i}__{key_j}"
            res = correlacion_honesta(series[key_i], series[key_j], min_solape=min_solape)
            if res.coef is None:
                all_ok = False
                motivos[pair_key] = res.motivo
            else:
                matrix[i][j] = res.coef
                matrix[j][i] = res.coef
                motivos[pair_key] = "OK"

    if not all_ok:
        return None, motivos

    return matrix, {"status": "OK"}
