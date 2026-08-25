"""contracts/dataset_contracts.py
Contratos Canónicos para la Cadena de Custodia e Inmutabilidad de Datasets (Fase 01).
ZERO-MOCKS · REAL-ONLY · PROVENANCE-LOCKED
"""

from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DatasetPartitionType(str, Enum):
    IN_SAMPLE = "IN_SAMPLE"
    VALIDATION = "VALIDATION"
    BLIND_OOS = "BLIND_OOS"
    FORWARD_PAPER = "FORWARD_PAPER"


class DatasetPartition(BaseModel):
    """Definición inmutable de partición temporal segregada sin fugas."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    partition_type: DatasetPartitionType
    start_time_utc_ms: int = Field(..., gt=0)
    end_time_utc_ms: int = Field(..., gt=0)
    record_count: int = Field(..., ge=0)
    partition_sha256: str = Field(..., min_length=64, max_length=64)


class DatasetManifest(BaseModel):
    """Manifiesto SSOT de custodia de un dataset físico normalizado."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    data_snapshot_id: str = Field(..., description="ID inmutable del snapshot")
    data_version: str = Field(default="1.0.0")
    source_id: str = Field(..., description="Proveedor e.g. YAHOO_CME, BINANCE_PERP, BINGX_SWAP")
    instrument_id: str = Field(..., description="Símbolo normalizado e.g. NQ, BTCUSDT, EURUSD")
    timeframe_id: str = Field(..., description="Timeframe e.g. 1m, 5m, 15m, 1h, 4h, 1d")
    schema_version: str = Field(default="1.0.0")
    normalization_version: str = Field(default="1.0.0")
    
    start_time_utc_ms: int = Field(..., gt=0)
    end_time_utc_ms: int = Field(..., gt=0)
    record_count: int = Field(..., ge=0)
    data_sha256: str = Field(..., min_length=64, max_length=64)
    
    # Métricas de integridad física
    gap_count: int = Field(default=0, ge=0)
    duplicate_count: int = Field(default=0, ge=0)
    out_of_order_count: int = Field(default=0, ge=0)
    coverage_pct: float = Field(default=100.0, ge=0.0, le=100.0)
    is_valid: bool = Field(default=True)
    
    # Particiones segregadas
    partitions: Dict[str, DatasetPartition] = Field(default_factory=dict)
    
    # Ruta física relativa
    relative_path: Optional[str] = None
    created_at_utc: str = ""

    @classmethod
    def compute_sha256(cls, content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()
