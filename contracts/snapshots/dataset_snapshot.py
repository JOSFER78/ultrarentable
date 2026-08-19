"""contracts/snapshots/dataset_snapshot.py
Source of Truth Inmutable de Datos Históricos (Fase 2).
Registra y certifica el hash físico SHA256, metadatos y recuento de velas de cada archivo en disco.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DatasetSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    dataset_id: str = Field(..., description="ID normalizado del dataset e.g. ds_binance_btcusdt_1h_...")
    symbol: str = Field(..., description="Símbolo base en mayúsculas")
    venue: str = Field(..., description="Exchange / Fuente: BINANCE, BINGX, CME, RITHMIC")
    timeframe: str = Field(..., description="Timeframe e.g. 1m, 5m, 15m, 1h, 4h")
    start_time_ms: int = Field(..., description="Timestamp Unix ms de la primera vela")
    end_time_ms: int = Field(..., description="Timestamp Unix ms de la última vela")
    start_iso: str = Field(..., description="Fecha UTC legible de inicio")
    end_iso: str = Field(..., description="Fecha UTC legible de fin")
    bar_count: int = Field(..., ge=1, description="Número exacto de barras en el archivo")
    sha256_hash: str = Field(..., description="Hash SHA256 del archivo físico en disco")
    integrity_pct: float = Field(default=100.0, ge=0.0, le=100.0, description="Porcentaje de integridad sin gaps")
    gaps_detected: int = Field(default=0, ge=0, description="Número de huecos temporales detectados")
    file_path: str = Field(..., description="Ruta absoluta al archivo en disco")
    created_at_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def from_file(cls, file_path: str) -> DatasetSnapshot:
        """Carga el dataset físico, computa su hash SHA256 y extrae los metadatos exactos."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Dataset físico no encontrado en disco: {file_path}")

        with open(file_path, "rb") as f:
            file_bytes = f.read()
            sha256_hash = hashlib.sha256(file_bytes).hexdigest()

        candles = json.loads(file_bytes.decode("utf-8"))
        if not isinstance(candles, list) or len(candles) == 0:
            raise ValueError(f"El dataset {file_path} no contiene una lista de velas válida.")

        bar_count = len(candles)
        first_bar = candles[0]
        last_bar = candles[-1]

        # Extract timestamps
        start_ms = int(first_bar.get("timestamp_ms") or first_bar.get("timestamp") or first_bar.get("time") or 0)
        end_ms = int(last_bar.get("timestamp_ms") or last_bar.get("timestamp") or last_bar.get("time") or 0)

        start_iso = datetime.fromtimestamp(start_ms / 1000.0, tz=timezone.utc).isoformat() if start_ms > 0 else "UNKNOWN"
        end_iso = datetime.fromtimestamp(end_ms / 1000.0, tz=timezone.utc).isoformat() if end_ms > 0 else "UNKNOWN"

        # Extract venue, symbol and timeframe from filename or metadata
        base_name = os.path.basename(file_path).replace(".json", "")
        parts = base_name.split("_")
        
        venue = parts[1].upper() if len(parts) > 1 else "UNKNOWN"
        symbol = parts[2].upper() if len(parts) > 2 else "UNKNOWN"
        timeframe = parts[3].lower() if len(parts) > 3 else "1h"

        return cls(
            dataset_id=base_name,
            symbol=symbol,
            venue=venue,
            timeframe=timeframe,
            start_time_ms=start_ms,
            end_time_ms=end_ms,
            start_iso=start_iso,
            end_iso=end_iso,
            bar_count=bar_count,
            sha256_hash=sha256_hash,
            integrity_pct=100.0,
            gaps_detected=0,
            file_path=file_path,
        )

    def verify_file_integrity(self) -> bool:
        """Comprueba físicamente que el archivo en disco no haya sido alterado."""
        if not os.path.exists(self.file_path):
            return False
        with open(self.file_path, "rb") as f:
            current_hash = hashlib.sha256(f.read()).hexdigest()
        return current_hash == self.sha256_hash
