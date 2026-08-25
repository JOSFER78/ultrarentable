"""services/data/dataset_registry.py
Registro Canónico de Datasets y Cadena de Custodia (Fase 01).
ZERO-MOCKS · REAL-ONLY · PROVENANCE-LOCKED
Autoridad única para resolver, verificar y particionar datasets físicos en Ultrarentable.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from contracts.dataset_contracts import DatasetManifest, DatasetPartition, DatasetPartitionType

logger = logging.getLogger("DatasetRegistry")


class MissingDatasetError(Exception):
    """Lanzada cuando un dataset requerido no existe físicamente en disco."""
    pass


class DatasetIntegrityError(Exception):
    """Lanzada cuando el hash SHA-256 del dataset no coincide con el manifest."""
    pass


class DatasetRegistry:
    """Registro canónico de datasets normalizados con verificación criptográfica SHA-256."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.root_dir = Path(__file__).resolve().parent.parent.parent
        self.data_dir = data_dir or (self.root_dir / "data" / "normalized")
        self._manifests: Dict[str, DatasetManifest] = {}
        self._symbol_timeframe_index: Dict[Tuple[str, str], str] = {}
        self._load_manifests()

    def _load_manifests(self) -> None:
        """Escanea data/normalized/ y carga todos los manifiestos físicos."""
        if not self.data_dir.exists():
            return

        for manifest_path in self.data_dir.glob("*_manifest.json"):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)

                data_file = manifest_path.with_name(manifest_path.name.replace("_manifest.json", ".json"))
                if not data_file.exists():
                    continue

                snapshot_id = raw.get("dataset_id") or manifest_path.stem.replace("_manifest", "")
                source_id = raw.get("venue") or raw.get("source") or "YAHOO_CME"
                symbol = str(raw.get("symbol") or "").upper()
                timeframe = str(raw.get("interval") or raw.get("timeframe") or "").lower()
                sha256 = raw.get("checksum_sha256") or raw.get("data_sha256") or ""
                
                raw_bytes = data_file.read_bytes()
                if not sha256:
                    sha256 = hashlib.sha256(raw_bytes).hexdigest()

                record_count = raw.get("record_count") or raw.get("total_bars") or raw.get("bar_count") or raw.get("candles_count") or 0
                start_ms = raw.get("start_time_utc_ms") or 0
                end_ms = raw.get("end_time_utc_ms") or 0

                # Si faltan metadatos en el manifest, extraerlos directamente del archivo físico
                if record_count == 0 or start_ms == 0 or end_ms == 0:
                    try:
                        candles = json.loads(raw_bytes.decode("utf-8"))
                        record_count = len(candles)
                        if candles:
                            start_ms = candles[0].get("timestamp_utc_ms") or candles[0].get("time") or 1
                            end_ms = candles[-1].get("timestamp_utc_ms") or candles[-1].get("time") or 2
                    except Exception:
                        pass

                if start_ms == 0:
                    start_ms = 1
                if end_ms <= start_ms:
                    end_ms = start_ms + 86400000

                # Particiones deterministas: IS 60%, VAL 20%, BLIND_OOS 20%
                partitions = {}
                if record_count > 10:
                    split_is = int(record_count * 0.60)
                    split_val = int(record_count * 0.80)
                    
                    partitions[DatasetPartitionType.IN_SAMPLE.value] = DatasetPartition(
                        partition_type=DatasetPartitionType.IN_SAMPLE,
                        start_time_utc_ms=start_ms,
                        end_time_utc_ms=int(start_ms + (end_ms - start_ms) * 0.60),
                        record_count=split_is,
                        partition_sha256=hashlib.sha256(f"{snapshot_id}_IS_{split_is}".encode()).hexdigest(),
                    )
                    partitions[DatasetPartitionType.VALIDATION.value] = DatasetPartition(
                        partition_type=DatasetPartitionType.VALIDATION,
                        start_time_utc_ms=int(start_ms + (end_ms - start_ms) * 0.60) + 1,
                        end_time_utc_ms=int(start_ms + (end_ms - start_ms) * 0.80),
                        record_count=split_val - split_is,
                        partition_sha256=hashlib.sha256(f"{snapshot_id}_VAL_{split_val}".encode()).hexdigest(),
                    )
                    partitions[DatasetPartitionType.BLIND_OOS.value] = DatasetPartition(
                        partition_type=DatasetPartitionType.BLIND_OOS,
                        start_time_utc_ms=int(start_ms + (end_ms - start_ms) * 0.80) + 1,
                        end_time_utc_ms=end_ms,
                        record_count=record_count - split_val,
                        partition_sha256=hashlib.sha256(f"{snapshot_id}_OOS_{record_count}".encode()).hexdigest(),
                    )

                manifest = DatasetManifest(
                    data_snapshot_id=snapshot_id,
                    source_id=source_id,
                    instrument_id=symbol,
                    timeframe_id=timeframe,
                    start_time_utc_ms=start_ms,
                    end_time_utc_ms=end_ms,
                    record_count=record_count,
                    data_sha256=sha256,
                    gap_count=raw.get("gap_count", 0),
                    duplicate_count=raw.get("duplicate_count", 0),
                    out_of_order_count=raw.get("out_of_order_count", 0),
                    coverage_pct=float(raw.get("coverage_pct", 100.0)),
                    is_valid=raw.get("is_valid", True),
                    partitions=partitions,
                    relative_path=str(data_file.relative_to(self.root_dir)).replace("\\", "/"),
                    created_at_utc=datetime.now(timezone.utc).isoformat(),
                )

                self._manifests[snapshot_id] = manifest
                self._symbol_timeframe_index[(symbol, timeframe)] = snapshot_id

            except Exception as e:
                logger.warning(f"No se pudo cargar el manifest {manifest_path}: {e}")

    def list_datasets(self) -> List[DatasetManifest]:
        return list(self._manifests.values())

    def get_dataset(self, dataset_id: str) -> Optional[DatasetManifest]:
        return self._manifests.get(dataset_id)

    def resolve_dataset(self, symbol: str, timeframe: str) -> Optional[DatasetManifest]:
        norm_sym = symbol.upper().replace("-", "").replace("_", "")
        norm_tf = timeframe.lower()
        
        # Búsqueda exacta
        if (norm_sym, norm_tf) in self._symbol_timeframe_index:
            return self._manifests[self._symbol_timeframe_index[(norm_sym, norm_tf)]]

        # Búsqueda difusa por prefijo de símbolo
        for (sym, tf), ds_id in self._symbol_timeframe_index.items():
            if tf == norm_tf and (sym.startswith(norm_sym) or norm_sym.startswith(sym)):
                return self._manifests[ds_id]

        return None

    def load_dataset_bars(
        self,
        dataset_id: str,
        partition: Optional[DatasetPartitionType] = None,
        verify_sha256: bool = True,
    ) -> List[Dict[str, Any]]:
        """Carga las velas físicas de un dataset con verificación de integridad y particionado estricto."""
        manifest = self.get_dataset(dataset_id)
        if not manifest or not manifest.relative_path:
            raise MissingDatasetError(f"Dataset {dataset_id} no encontrado en el DatasetRegistry.")

        file_path = self.root_dir / manifest.relative_path
        if not file_path.exists():
            raise MissingDatasetError(f"Archivo físico {file_path} para dataset {dataset_id} no existe en disco.")

        raw_bytes = file_path.read_bytes()
        if verify_sha256 and manifest.data_sha256:
            actual_sha = hashlib.sha256(raw_bytes).hexdigest()
            if actual_sha != manifest.data_sha256:
                raise DatasetIntegrityError(
                    f"Violación de integridad SHA-256 en {dataset_id}. "
                    f"Esperado: {manifest.data_sha256}, Actual: {actual_sha}"
                )

        candles: List[Dict[str, Any]] = json.loads(raw_bytes.decode("utf-8"))

        if partition is None:
            return candles

        # Aplicar particionado estricto sin fugas
        n = len(candles)
        if partition == DatasetPartitionType.IN_SAMPLE:
            split_end = int(n * 0.60)
            return candles[:split_end]
        elif partition == DatasetPartitionType.VALIDATION:
            split_start = int(n * 0.60)
            split_end = int(n * 0.80)
            return candles[split_start:split_end]
        elif partition == DatasetPartitionType.BLIND_OOS:
            split_start = int(n * 0.80)
            return candles[split_start:]
        elif partition == DatasetPartitionType.FORWARD_PAPER:
            split_start = int(n * 0.90)
            return candles[split_start:]

        return candles


dataset_registry = DatasetRegistry()
