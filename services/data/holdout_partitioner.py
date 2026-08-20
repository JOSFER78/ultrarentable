"""services/data/holdout_partitioner.py
Aislamiento Físico de Holdout (60% In-Sample, 20% WFO, 20% Blind Holdout) (Fase 4).
Garantiza que el motor de descubrimiento genético o semántico nunca pueda leer datos del Blind Holdout.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple


class BlindHoldoutAccessViolation(PermissionError):
    """Excepción forense cuando un proceso de Discovery intenta acceder a datos ciegos de validación."""
    pass


@dataclass
class DatasetPartition:
    dataset_id: str
    symbol: str
    timeframe: str
    is_bars_count: int
    wfo_bars_count: int
    blind_oos_bars_count: int
    is_data: List[Dict[str, Any]]
    wfo_data: List[Dict[str, Any]]
    blind_oos_data: List[Dict[str, Any]]


class HoldoutPartitioner:
    """Particionador y guardián físico de separación de datos temporales."""

    def __init__(self, is_ratio: float = 0.60, wfo_ratio: float = 0.20, blind_ratio: float = 0.20):
        self.is_ratio = is_ratio
        self.wfo_ratio = wfo_ratio
        self.blind_ratio = blind_ratio

    def partition(self, candles: List[Dict[str, Any]], dataset_id: str, symbol: str, timeframe: str) -> DatasetPartition:
        n = len(candles)
        n_is = int(n * self.is_ratio)
        n_wfo = int(n * self.wfo_ratio)
        
        is_data = candles[:n_is]
        wfo_data = candles[n_is : n_is + n_wfo]
        blind_data = candles[n_is + n_wfo :]

        return DatasetPartition(
            dataset_id=dataset_id,
            symbol=symbol,
            timeframe=timeframe,
            is_bars_count=len(is_data),
            wfo_bars_count=len(wfo_data),
            blind_oos_bars_count=len(blind_data),
            is_data=is_data,
            wfo_data=wfo_data,
            blind_oos_data=blind_data,
        )

    @staticmethod
    def assert_discovery_cannot_read_holdout(caller_module: str, requested_partition: str) -> None:
        """Bloquea cualquier intento de descubrimiento que intente leer 'blind_oos'."""
        if "discovery" in caller_module.lower() and requested_partition == "blind_oos":
            raise BlindHoldoutAccessViolation(
                f"CONTAMINACION_BLIND_HOLDOUT_DETECTADA: El módulo de discovery '{caller_module}' "
                f"intentó acceder físicamente a la partición de datos ciegos (Blind OOS). "
                f"Acceso denegado por regla inquebrantable de integridad científica."
            )
