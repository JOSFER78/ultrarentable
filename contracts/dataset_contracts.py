"""contracts/dataset_contracts.py
Contratos Canónicos para la Cadena de Custodia e Inmutabilidad de Datasets (Fase 01 Rework P01-003).
ZERO-MOCKS · REAL-ONLY · PROVENANCE-LOCKED · NO-SYNTHETIC-DEFAULTS
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
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
    start_time_utc_ms: int = Field(..., gt=0, description="Timestamp UTC ms de la primera vela de la partición")
    end_time_utc_ms: int = Field(..., gt=0, description="Timestamp UTC ms de la última vela de la partición")
    coverage_start: str = Field(..., description="Timestamp ISO 8601 UTC inicio")
    coverage_end: str = Field(..., description="Timestamp ISO 8601 UTC fin")
    record_count: int = Field(..., ge=0, description="Conteo físico de velas en la partición")
    partition_sha256: str = Field(..., min_length=64, max_length=64, description="Hash SHA-256 de los bytes canónicos de la partición")

    @classmethod
    def compute_slice_sha256(cls, slice_candles: List[Dict[str, Any]]) -> str:
        """Calcula el hash SHA-256 sobre la representación JSON canónica de las velas de la partición."""
        raw = json.dumps(slice_candles, separators=(",", ":"), sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()


class DatasetManifest(BaseModel):
    """Manifiesto SSOT de custodia de un dataset físico normalizado sin defaults inventados."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    # Identidad canónica
    data_snapshot_id: str = Field(..., description="ID inmutable del snapshot")
    data_version: Optional[str] = Field(default=None, description="Versión semántica del dataset si está documentada")
    source_id: str = Field(..., description="Proveedor e.g. YAHOO_CME, BINANCE_PERP, BINGX_SWAP o UNVERIFIED")
    instrument_id: str = Field(..., description="Símbolo canónico e.g. NQ, BTCUSDT, EURUSD")
    timeframe_id: str = Field(..., description="Timeframe canónico e.g. 1m, 5m, 15m, 1h, 4h, 1d")
    schema_version: Optional[str] = Field(default=None, description="Versión del esquema si está documentada")
    normalization_version: Optional[str] = Field(default=None, description="Versión del pipeline de normalización")
    
    # Cobertura temporal y conteo físico
    coverage_start: str = Field(..., description="ISO 8601 UTC de la primera vela")
    coverage_end: str = Field(..., description="ISO 8601 UTC de la última vela")
    start_time_utc_ms: int = Field(..., gt=0)
    end_time_utc_ms: int = Field(..., gt=0)
    record_count: int = Field(..., gt=0, description="Número de velas físicas en el dataset")
    data_sha256: str = Field(..., min_length=64, max_length=64, description="Hash SHA-256 de los bytes físicos")
    
    # Métricas de integridad física real
    gap_count: int = Field(default=0, ge=0)
    duplicate_count: int = Field(default=0, ge=0)
    out_of_order_count: int = Field(default=0, ge=0)
    coverage_pct: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    is_valid: bool = Field(default=True)
    
    # Particiones segregadas con hashes físicos reales
    partitions: Dict[str, DatasetPartition] = Field(default_factory=dict)
    
    # Ruta física relativa
    relative_path: Optional[str] = None
    created_at_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def compute_sha256(cls, content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()
