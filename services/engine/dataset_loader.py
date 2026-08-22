"""services/engine/dataset_loader.py
Universal Real-Only Dataset Loader & Integrity Verifier (v3.0.0).

DOCTRINA ZERO-MOCKS & ZERO-FALLBACKS:
- Reads exclusively physical verified datasets from disk (JSON / Parquet).
- If the dataset is absent, corrupted, or has invalid OHLC, raises DatasetUnavailableError immediately.
- Never falls back to synthetic or approximate candles.
"""

from __future__ import annotations

import glob
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from contracts.dataset_specification import DatasetSpecification


class DatasetUnavailableError(Exception):
    """Error fatal cuando un dataset requerido no existe físicamente en disco."""
    pass


class DatasetIntegrityError(Exception):
    """Error fatal cuando un dataset físico está corrupto o alterado."""
    pass


class UniversalDataLoader:
    """Cargador y verificador criptográfico de datos históricos en disco."""

    def __init__(self, data_root_dir: str = "/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/normalized") -> None:
        self.data_root = Path(data_root_dir)

    def find_dataset_file(self, symbol: str, timeframe: str) -> Optional[Path]:
        """Busca el archivo físico correspondiente a un símbolo y timeframe."""
        norm_sym = symbol.upper().replace("-", "").replace("/", "").replace("_", "").lower()
        norm_tf = timeframe.lower()

        # Buscar coincidencia exacta en data/normalized
        candidates = list(self.data_root.glob(f"*{norm_sym}*{norm_tf}*.json"))
        # Excluir archivos _manifest.json
        data_files = [p for p in candidates if not p.name.endswith("_manifest.json")]

        if data_files:
            # Retornar el archivo más reciente o más completo
            return max(data_files, key=lambda p: p.stat().st_size)
        return None

    def load_dataset(self, symbol: str, timeframe: str, explicit_filepath: Optional[str] = None) -> tuple[DatasetSpecification, List[Dict[str, Any]]]:
        """Carga y valida criptográficamente el dataset. Si no existe, bloquea inmediatamente."""
        target_path: Optional[Path] = Path(explicit_filepath) if explicit_filepath else self.find_dataset_file(symbol, timeframe)

        if not target_path or not target_path.exists():
            raise DatasetUnavailableError(
                f"DATASET_UNAVAILABLE: No se encontró ningún archivo físico para '{symbol}' ({timeframe}) "
                f"en {self.data_root}. Prohibido continuar sin datos reales verificados."
            )

        spec = DatasetSpecification.from_disk_file(str(target_path), symbol=symbol, timeframe=timeframe)
        if not spec.quality_report.is_valid_ohlc or not spec.quality_report.is_strictly_chronological:
            raise DatasetIntegrityError(
                f"DATASET_CORRUPTED: El archivo {target_path} no superó la auditoría de integridad "
                f"(OHLC válido: {spec.quality_report.is_valid_ohlc}, Cronología: {spec.quality_report.is_strictly_chronological})."
            )

        candles = spec.load_raw_candles()
        return spec, candles
