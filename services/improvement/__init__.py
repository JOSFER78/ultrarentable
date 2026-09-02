"""services/improvement/__init__.py
M2 — Sistema de Mejora Continua y Optimización Paramétrica/Semántica.
Frontera limpia e inyección de dependencias para el loop de mejora de estrategias.
"""

from services.improvement.contratos import (
    EntradaMejora,
    EstadoMejora,
    IteracionMejora,
    ResultadoMejora,
)
from services.improvement.loop import (
    Mejorador,
    ejecutar_loop,
)

__all__ = [
    "EntradaMejora",
    "EstadoMejora",
    "IteracionMejora",
    "ResultadoMejora",
    "Mejorador",
    "ejecutar_loop",
]
