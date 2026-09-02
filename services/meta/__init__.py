"""services/meta/
Módulo canónico de Meta-Estrategias y Ensamblado Cuantitativo (M4 / W6.0).
REAL-ONLY · ZERO-MOCKS · FAIL-CLOSED
"""

from __future__ import annotations

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

__all__ = [
    "CERTIFIED_STATUSES",
    "es_certificada",
    "ResultadoCorrelacion",
    "correlacion_honesta",
    "matriz_correlacion",
    "ResultadoEnsamblado",
    "pesos_min_varianza",
    "pesos_hrp",
]
