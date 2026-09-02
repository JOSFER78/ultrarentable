"""services/meta/ensamblado.py
Asignación estática determinista de pesos para meta-estrategias (M4 / D9 / W6.0).
REAL-ONLY · ZERO-MOCKS · FAIL-CLOSED

Métodos cuantitativos:
----------------------
1. Mínima Varianza (`pesos_min_varianza`):
   Optimiza los pesos minimizando la varianza conjunta w^T Sigma w, sujeto a sum(w) = 1
   y w_i >= 0 (long-only por defecto). Resuelto analíticamente o mediante gradiente
   proyectado sobre el simplex de forma 100% determinista.
2. Hierarchical Risk Parity (`pesos_hrp`):
   Implementación completa en tres etapas (López de Prado, 2016):
   (a) Distancia y agrupamiento jerárquico determinista (Single Linkage);
   (b) Cuasi-diagonalización de la matriz;
   (c) Bisección recursiva por varianza de clústeres.
   Nunca invierte la matriz de covarianza completa.

Determinismo y pureza:
----------------------
- Cero generadores estocásticos. Retornos y pesos 100% reproducibles.
- Fail-closed: ante matrices no definidas positivas, NaNs/Infs, dimensiones insuficientes
  o datos faltantes, devuelve pesos=None con motivo explícito.
"""

from __future__ import annotations

from typing import Any, Dict, List, NamedTuple, Optional


class ResultadoEnsamblado(NamedTuple):
    pesos: Optional[List[float]]
    motivo: str


def _proyectar_simplex(v: Any, z: float = 1.0) -> Any:
    """Proyecta un vector v sobre el simplex euclídeo: sum(w) = z, w >= 0."""
    import numpy as np

    n = len(v)
    u = np.sort(v)[::-1]
    cssv = np.cumsum(u) - z
    ind = np.arange(1, n + 1)
    cond = u - cssv / ind > 0
    if not np.any(cond):
        return np.ones(n, dtype=np.float64) / n
    rho = ind[cond][-1]
    theta = cssv[cond][-1] / float(rho)
    w = np.maximum(v - theta, 0.0)
    s = np.sum(w)
    if s <= 0:
        return np.ones(n, dtype=np.float64) / n
    return w / s


def pesos_min_varianza(
    matriz_cov: Any,
    restricciones: Optional[Dict[str, Any]] = None,
) -> ResultadoEnsamblado:
    """Calcula la asignación de pesos de mínima varianza sobre una matriz de covarianza.

    Args:
        matriz_cov: Matriz de covarianza (N x N) convertible a numpy float64.
        restricciones: Diccionario opcional de restricciones (p.ej. {"allow_short": False}).

    Returns:
        ResultadoEnsamblado(pesos, motivo)
        Si la matriz no es definida positiva o contiene datos inválidos, devuelve pesos=None.
    """
    import numpy as np

    if matriz_cov is None:
        return ResultadoEnsamblado(pesos=None, motivo="NO_EVALUABLE: matriz de covarianza ausente")
    try:
        cov = np.asarray(matriz_cov, dtype=np.float64)
    except Exception:
        return ResultadoEnsamblado(pesos=None, motivo="NO_EVALUABLE: no se pudo convertir la matriz a numpy float64")

    if cov.ndim != 2 or cov.shape[0] != cov.shape[1] or cov.shape[0] < 1:
        return ResultadoEnsamblado(pesos=None, motivo="NO_EVALUABLE: dimensiones inválidas en matriz de covarianza")

    if np.isnan(cov).any() or np.isinf(cov).any():
        return ResultadoEnsamblado(pesos=None, motivo="NO_EVALUABLE: valores no finitos (NaN/Inf) en matriz de covarianza")

    n = cov.shape[0]
    if n == 1:
        if cov[0, 0] <= 0:
            return ResultadoEnsamblado(pesos=None, motivo="NO_EVALUABLE: varianza no positiva en componente único")
        return ResultadoEnsamblado(pesos=[1.0], motivo="OK")

    cov_sym = 0.5 * (cov + cov.T)
    eigvals = np.linalg.eigvalsh(cov_sym)

    if np.any(eigvals <= 1e-8):
        return ResultadoEnsamblado(pesos=None, motivo="NO_EVALUABLE: matriz de covarianza no es estrictamente definida positiva")

    allow_short = False
    if isinstance(restricciones, dict):
        allow_short = bool(restricciones.get("allow_short", False))

    ones = np.ones(n, dtype=np.float64)
    try:
        w_unconstrained = np.linalg.solve(cov_sym, ones)
        sum_w = np.sum(w_unconstrained)
        if abs(sum_w) <= 1e-12:
            return ResultadoEnsamblado(pesos=None, motivo="NO_EVALUABLE: suma de pesos nula en solución analítica")
        w_analytic = w_unconstrained / sum_w
    except np.linalg.LinAlgError:
        return ResultadoEnsamblado(pesos=None, motivo="NO_EVALUABLE: error algebraico resolviendo sistema lineal")

    if allow_short or np.all(w_analytic >= -1e-7):
        w_final = np.maximum(w_analytic, 0.0) if not allow_short else w_analytic
        w_final = w_final / np.sum(w_final)
        return ResultadoEnsamblado(
            pesos=[round(float(x), 6) for x in w_final],
            motivo="OK",
        )

    # Optimización determinista por gradiente proyectado sobre el simplex (long-only)
    w = ones / n
    step_size = 1.0 / float(np.max(eigvals))
    for _ in range(300):
        grad = cov_sym @ w
        w = _proyectar_simplex(w - step_size * grad)

    w = w / np.sum(w)
    return ResultadoEnsamblado(
        pesos=[round(float(x), 6) for x in w],
        motivo="OK",
    )


def pesos_hrp(
    matriz_corr: Any,
    matriz_cov: Optional[Any] = None,
) -> ResultadoEnsamblado:
    """Calcula pesos mediante Hierarchical Risk Parity (HRP) determinista en tres etapas.

    Args:
        matriz_corr: Matriz de correlación (N x N).
        matriz_cov: Matriz de covarianza (N x N) opcional. Si es None, se utiliza matriz_corr.

    Returns:
        ResultadoEnsamblado(pesos, motivo)
        Si la matriz de correlación no es definida positiva o es inválida, devuelve pesos=None.
    """
    import numpy as np

    if matriz_corr is None:
        return ResultadoEnsamblado(pesos=None, motivo="NO_EVALUABLE: matriz de correlación ausente")
    try:
        corr = np.asarray(matriz_corr, dtype=np.float64)
    except Exception:
        return ResultadoEnsamblado(pesos=None, motivo="NO_EVALUABLE: no se pudo convertir matriz de correlación a numpy")

    if corr.ndim != 2 or corr.shape[0] != corr.shape[1] or corr.shape[0] < 1:
        return ResultadoEnsamblado(pesos=None, motivo="NO_EVALUABLE: dimensiones inválidas en matriz de correlación")

    if np.isnan(corr).any() or np.isinf(corr).any():
        return ResultadoEnsamblado(pesos=None, motivo="NO_EVALUABLE: valores no finitos en matriz de correlación")

    n = corr.shape[0]
    if n == 1:
        return ResultadoEnsamblado(pesos=[1.0], motivo="OK")

    corr_sym = 0.5 * (corr + corr.T)
    np.fill_diagonal(corr_sym, 1.0)

    if np.any(corr_sym < -1.0001) or np.any(corr_sym > 1.0001):
        return ResultadoEnsamblado(pesos=None, motivo="NO_EVALUABLE: coeficientes de correlación fuera de [-1, 1]")

    eigvals = np.linalg.eigvalsh(corr_sym)
    if np.any(eigvals <= 1e-8):
        return ResultadoEnsamblado(pesos=None, motivo="NO_EVALUABLE: matriz de correlación no es estrictamente definida positiva")

    if matriz_cov is not None:
        try:
            cov = np.asarray(matriz_cov, dtype=np.float64)
        except Exception:
            return ResultadoEnsamblado(pesos=None, motivo="NO_EVALUABLE: matriz de covarianza incompatible")
        if cov.shape != (n, n) or np.isnan(cov).any() or np.isinf(cov).any():
            return ResultadoEnsamblado(pesos=None, motivo="NO_EVALUABLE: matriz de covarianza incompatible o con valores no finitos")
        cov_sym = 0.5 * (cov + cov.T)
        cov_eigs = np.linalg.eigvalsh(cov_sym)
        if np.any(cov_eigs <= 1e-8):
            return ResultadoEnsamblado(pesos=None, motivo="NO_EVALUABLE: matriz de covarianza no es definida positiva")
    else:
        cov_sym = corr_sym.copy()

    # 1. Distancia de correlación
    dist = np.sqrt(np.maximum(0.0, 0.5 * (1.0 - corr_sym)))
    np.fill_diagonal(dist, 0.0)

    # 2. Agrupamiento jerárquico determinista (Single Linkage)
    class _NodoCluster:
        def __init__(self, elementos: List[int], izq=None, der=None):
            self.elementos = elementos
            self.izq = izq
            self.der = der

    clusters: List[_NodoCluster] = [_NodoCluster([i]) for i in range(n)]

    while len(clusters) > 1:
        min_d = float("inf")
        best_pair = (0, 1)
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                c_i = clusters[i].elementos
                c_j = clusters[j].elementos
                sub_d = dist[np.ix_(c_i, c_j)]
                d_ij = float(np.min(sub_d))
                if d_ij < min_d:
                    min_d = d_ij
                    best_pair = (i, j)
        idx_a, idx_b = best_pair
        nuevo = _NodoCluster(
            elementos=clusters[idx_a].elementos + clusters[idx_b].elementos,
            izq=clusters[idx_a],
            der=clusters[idx_b],
        )
        for idx in sorted([idx_a, idx_b], reverse=True):
            clusters.pop(idx)
        clusters.append(nuevo)

    raiz = clusters[0]

    def _cuasi_diagonalizar(nodo: _NodoCluster) -> List[int]:
        if nodo.izq is None and nodo.der is None:
            return nodo.elementos
        out: List[int] = []
        if nodo.izq is not None:
            out.extend(_cuasi_diagonalizar(nodo.izq))
        if nodo.der is not None:
            out.extend(_cuasi_diagonalizar(nodo.der))
        return out

    ordenados = _cuasi_diagonalizar(raiz)

    # 3. Bisección recursiva
    def _varianza_cluster(indices: List[int]) -> float:
        cov_sub = cov_sym[np.ix_(indices, indices)]
        diag_inv = 1.0 / np.maximum(1e-12, np.diag(cov_sub))
        w_sub = diag_inv / np.sum(diag_inv)
        return float(w_sub @ cov_sub @ w_sub)

    pesos_dict: Dict[int, float] = {i: 1.0 for i in range(n)}
    cola_biseccion: List[List[int]] = [ordenados]

    while cola_biseccion:
        actual = cola_biseccion.pop(0)
        if len(actual) <= 1:
            continue
        corte = len(actual) // 2
        c1 = actual[:corte]
        c2 = actual[corte:]
        v1 = _varianza_cluster(c1)
        v2 = _varianza_cluster(c2)
        total_v = v1 + v2
        if total_v <= 1e-14:
            alfa1 = 0.5
        else:
            alfa1 = v2 / total_v
        alfa2 = 1.0 - alfa1
        for idx in c1:
            pesos_dict[idx] *= alfa1
        for idx in c2:
            pesos_dict[idx] *= alfa2
        if len(c1) > 1:
            cola_biseccion.append(c1)
        if len(c2) > 1:
            cola_biseccion.append(c2)

    pesos_vec = np.array([pesos_dict[i] for i in range(n)], dtype=np.float64)
    pesos_vec = pesos_vec / np.sum(pesos_vec)

    return ResultadoEnsamblado(
        pesos=[round(float(x), 6) for x in pesos_vec],
        motivo="OK",
    )
