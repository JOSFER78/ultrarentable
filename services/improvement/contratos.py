"""services/improvement/contratos.py
Contratos canónicos inmutables para el loop de mejora continua de estrategias (M2).
DOCTRINA ZERO-MOCKS & REAL-ONLY:
- Multiplicidad upstream obligatoria (trials_tested_upstream > 0).
- Prohibición de defaults sintéticos que maquillen métricas.
- Máquina de estados determinista (CERTIFICADA, EN_MEJORA, AGOTADA, SIN_MEJORA).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class EstadoMejora(str, Enum):
    """Estados del ciclo de mejora cuantitativa en M2."""
    CERTIFICADA = "CERTIFICADA"
    EN_MEJORA = "EN_MEJORA"
    AGOTADA = "AGOTADA"
    SIN_MEJORA = "SIN_MEJORA"


@dataclass(frozen=True)
class EntradaMejora:
    """Contrato inmutable de entrada al loop de mejora M2.
    
    Exige la multiplicidad declarada del proceso upstream (M1/campañas) para evitar
    la fuga de penalización en Gate 8 (Deflated Sharpe Ratio).
    """
    strategy_hash: str
    snapshot: Any
    trials_tested_upstream: int
    presupuesto_iteraciones: int
    holdout_blind: Any

    def __post_init__(self) -> None:
        if not self.strategy_hash or not isinstance(self.strategy_hash, str) or not self.strategy_hash.strip():
            raise ValueError("strategy_hash debe ser un str no vacío")

        if not isinstance(self.trials_tested_upstream, int) or self.trials_tested_upstream <= 0:
            raise ValueError(
                f"trials_tested_upstream debe ser un entero > 0 (recibido {self.trials_tested_upstream}). "
                "DOCTRINA REAL-ONLY: sin multiplicidad upstream declarada no hay mejora honesta."
            )

        if not isinstance(self.presupuesto_iteraciones, int) or self.presupuesto_iteraciones <= 0:
            raise ValueError(
                f"presupuesto_iteraciones debe ser un entero > 0 (recibido {self.presupuesto_iteraciones})."
            )


@dataclass(frozen=True)
class IteracionMejora:
    """Registro inmutable de una iteración dentro del bucle de mejora."""
    iteracion: int
    snapshot_propuesto: Any
    metricas_is_val: Dict[str, Any]
    supera_is_val: bool = False
    hipotesis: Optional[str] = None
    detalles: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ResultadoMejora:
    """Resultado final inmutable tras la ejecución del loop de mejora."""
    estado: EstadoMejora
    strategy_hash_inicial: str
    snapshot_final: Any
    iteraciones_realizadas: int
    trials_tested_total: int
    historial: List[IteracionMejora] = field(default_factory=list)
    resultado_registro: Optional[Any] = None
    motivo: str = ""
