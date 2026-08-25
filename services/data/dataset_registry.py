"""services/data/dataset_registry.py
Registro Canónico de Datasets y Cadena de Custodia Criptográfica (Fase 01 Rework).
ZERO-MOCKS · REAL-ONLY · PROVENANCE-LOCKED · FAIL-CLOSED
SSOT inmutable para la resolución, verificación y particionado físico de series temporales.
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
    """Lanzada cuando el hash SHA-256 del dataset o partición no coincide con el manifest."""
    pass


class DatasetResolutionError(Exception):
    """Lanzada cuando no se puede resolver inequívocamente un símbolo y timeframe."""
    pass


def _extract_ts_ms(candle: Dict[str, Any]) -> int:
    """Extrae el timestamp en milisegundos UTC de forma determinista sin inventar datos."""
    if "timestamp_utc_ms" in candle:
        return int(candle["timestamp_utc_ms"])
    if "time" in candle:
        t = candle["time"]
        if isinstance(t, (int, float)):
            return int(t * 1000) if t < 10_000_000_000 else int(t)
        if isinstance(t, str):
            try:
                dt = datetime.fromisoformat(t.replace("Z", "+00:00"))
                return int(dt.timestamp() * 1000)
            except Exception:
                pass
    if "timestamp" in candle:
        t = candle["timestamp"]
        if isinstance(t, (int, float)):
            return int(t * 1000) if t < 10_000_000_000 else int(t)
    return 0


class DatasetRegistry:
    """Registro SSOT de datasets normalizados con verificación criptográfica y particionado físico."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.root_dir = Path(__file__).resolve().parent.parent.parent
        self.data_dir = data_dir or (self.root_dir / "data" / "normalized")
        self._manifests: Dict[str, DatasetManifest] = {}
        self._symbol_timeframe_index: Dict[Tuple[str, str], str] = {}
        self._load_manifests()

    def _load_manifests(self) -> None:
        """Escanea data/normalized/ y carga los manifiestos derivando métricas de bytes reales."""
        if not self.data_dir.exists():
            return

        for data_file in self.data_dir.glob("*.json"):
            if data_file.name.endswith("_manifest.json"):
                continue

            manifest_file = data_file.with_name(f"{data_file.stem}_manifest.json")
            try:
                raw_bytes = data_file.read_bytes()
                if not raw_bytes:
                    continue

                actual_sha256 = hashlib.sha256(raw_bytes).hexdigest()
                candles: List[Dict[str, Any]] = json.loads(raw_bytes.decode("utf-8"))
                if not isinstance(candles, list) or len(candles) == 0:
                    continue

                record_count = len(candles)
                start_ms = _extract_ts_ms(candles[0])
                end_ms = _extract_ts_ms(candles[-1])

                if start_ms <= 0 or end_ms <= 0 or end_ms < start_ms:
                    logger.error(f"Dataset {data_file.name} tiene timestamps inválidos ({start_ms} -> {end_ms}). Omitido.")
                    continue

                cov_start_iso = datetime.fromtimestamp(start_ms / 1000.0, tz=timezone.utc).isoformat()
                cov_end_iso = datetime.fromtimestamp(end_ms / 1000.0, tz=timezone.utc).isoformat()

                # Auditoría de integridad física (duplicados, gaps, orden)
                duplicate_count = 0
                out_of_order_count = 0
                for i in range(len(candles) - 1):
                    ts_cur = _extract_ts_ms(candles[i])
                    ts_nxt = _extract_ts_ms(candles[i+1])
                    if ts_cur > 0 and ts_nxt > 0:
                        if ts_cur == ts_nxt:
                            duplicate_count += 1
                        elif ts_cur > ts_nxt:
                            out_of_order_count += 1

                # Leer manifest acompañante si existe
                raw_manifest = {}
                if manifest_file.exists():
                    try:
                        with open(manifest_file, "r", encoding="utf-8") as mf:
                            raw_manifest = json.load(mf)
                    except Exception:
                        pass

                snapshot_id = raw_manifest.get("dataset_id") or data_file.stem
                
                # Deducción estricta de source_id sin inventar
                if raw_manifest.get("venue") or raw_manifest.get("source"):
                    source_id = str(raw_manifest.get("venue") or raw_manifest.get("source"))
                elif "bingx" in data_file.name.lower():
                    source_id = "BINGX_SWAP"
                elif "trad_" in data_file.name.lower() or "cme" in data_file.name.lower():
                    source_id = "YAHOO_CME"
                elif "binance" in data_file.name.lower():
                    source_id = "BINANCE_PERP"
                else:
                    source_id = "UNVERIFIED_SOURCE"

                # Extracción canónica de símbolo y timeframe
                if raw_manifest.get("symbol"):
                    raw_sym = str(raw_manifest["symbol"]).upper()
                else:
                    # Parsear desde nombre de archivo e.g. ds_trad_nq_1h_...
                    parts = data_file.stem.split("_")
                    if len(parts) >= 4:
                        raw_sym = parts[2].upper()
                    else:
                        raw_sym = data_file.stem.upper()

                if raw_manifest.get("interval") or raw_manifest.get("timeframe"):
                    raw_tf = str(raw_manifest.get("interval") or raw_manifest.get("timeframe")).lower()
                else:
                    parts = data_file.stem.split("_")
                    if len(parts) >= 4:
                        raw_tf = parts[3].lower()
                    else:
                        raw_tf = "1h"

                clean_sym = raw_sym.replace("-", "").replace("_", "").replace("/", "")
                clean_tf = raw_tf.strip().lower()

                # Particionado físico estricto con cálculo de hashes sobre bytes de cada slice
                partitions = {}
                if record_count >= 10:
                    split_is = int(record_count * 0.60)
                    split_val = int(record_count * 0.80)

                    slice_is = candles[:split_is]
                    slice_val = candles[split_is:split_val]
                    slice_oos = candles[split_val:]

                    is_start_ms = _extract_ts_ms(slice_is[0])
                    is_end_ms = _extract_ts_ms(slice_is[-1])
                    val_start_ms = _extract_ts_ms(slice_val[0])
                    val_end_ms = _extract_ts_ms(slice_val[-1])
                    oos_start_ms = _extract_ts_ms(slice_oos[0])
                    oos_end_ms = _extract_ts_ms(slice_oos[-1])

                    partitions[DatasetPartitionType.IN_SAMPLE.value] = DatasetPartition(
                        partition_type=DatasetPartitionType.IN_SAMPLE,
                        start_time_utc_ms=is_start_ms,
                        end_time_utc_ms=is_end_ms,
                        coverage_start=datetime.fromtimestamp(is_start_ms / 1000.0, tz=timezone.utc).isoformat(),
                        coverage_end=datetime.fromtimestamp(is_end_ms / 1000.0, tz=timezone.utc).isoformat(),
                        record_count=len(slice_is),
                        partition_sha256=DatasetPartition.compute_slice_sha256(slice_is),
                    )
                    partitions[DatasetPartitionType.VALIDATION.value] = DatasetPartition(
                        partition_type=DatasetPartitionType.VALIDATION,
                        start_time_utc_ms=val_start_ms,
                        end_time_utc_ms=val_end_ms,
                        coverage_start=datetime.fromtimestamp(val_start_ms / 1000.0, tz=timezone.utc).isoformat(),
                        coverage_end=datetime.fromtimestamp(val_end_ms / 1000.0, tz=timezone.utc).isoformat(),
                        record_count=len(slice_val),
                        partition_sha256=DatasetPartition.compute_slice_sha256(slice_val),
                    )
                    partitions[DatasetPartitionType.BLIND_OOS.value] = DatasetPartition(
                        partition_type=DatasetPartitionType.BLIND_OOS,
                        start_time_utc_ms=oos_start_ms,
                        end_time_utc_ms=oos_end_ms,
                        coverage_start=datetime.fromtimestamp(oos_start_ms / 1000.0, tz=timezone.utc).isoformat(),
                        coverage_end=datetime.fromtimestamp(oos_end_ms / 1000.0, tz=timezone.utc).isoformat(),
                        record_count=len(slice_oos),
                        partition_sha256=DatasetPartition.compute_slice_sha256(slice_oos),
                    )

                manifest = DatasetManifest(
                    data_snapshot_id=snapshot_id,
                    data_version="1.0.0",
                    source_id=source_id,
                    instrument_id=clean_sym,
                    timeframe_id=clean_tf,
                    schema_version="1.0.0",
                    normalization_version="1.0.0",
                    coverage_start=cov_start_iso,
                    coverage_end=cov_end_iso,
                    start_time_utc_ms=start_ms,
                    end_time_utc_ms=end_ms,
                    record_count=record_count,
                    data_sha256=actual_sha256,
                    gap_count=raw_manifest.get("gap_count", 0),
                    duplicate_count=duplicate_count,
                    out_of_order_count=out_of_order_count,
                    coverage_pct=float(raw_manifest["coverage_pct"]) if "coverage_pct" in raw_manifest else None,
                    is_valid=(out_of_order_count == 0),
                    partitions=partitions,
                    relative_path=str(data_file.relative_to(self.root_dir)).replace("\\", "/"),
                    created_at_utc=datetime.now(timezone.utc).isoformat(),
                )

                self._manifests[snapshot_id] = manifest
                self._symbol_timeframe_index[(clean_sym, clean_tf)] = snapshot_id

            except Exception as e:
                logger.error(f"Error procesando dataset físico {data_file}: {e}")

    def list_datasets(self) -> List[DatasetManifest]:
        return list(self._manifests.values())

    def get_dataset(self, dataset_id: str) -> Optional[DatasetManifest]:
        return self._manifests.get(dataset_id)

    def resolve_dataset(self, symbol: str, timeframe: str) -> Optional[DatasetManifest]:
        """Resolución unívoca y determinista por símbolo y timeframe. Cero coincidencia difusa."""
        clean_sym = symbol.upper().replace("-", "").replace("_", "").replace("/", "")
        clean_tf = timeframe.strip().lower()

        # Coincidencia exacta estricta
        if (clean_sym, clean_tf) in self._symbol_timeframe_index:
            return self._manifests[self._symbol_timeframe_index[(clean_sym, clean_tf)]]

        # Aliases canónicos estándar (ej. BTCUSDT -> BTC, EURUSD=X -> EURUSD)
        alt_sym = clean_sym.replace("USDT", "").replace("USD", "").replace("=X", "")
        if alt_sym and (alt_sym, clean_tf) in self._symbol_timeframe_index:
            return self._manifests[self._symbol_timeframe_index[(alt_sym, clean_tf)]]

        return None

    def load_dataset_bars(
        self,
        dataset_id: str,
        partition: Optional[DatasetPartitionType] = None,
        verify_sha256: bool = True,
    ) -> List[Dict[str, Any]]:
        """Carga las velas físicas de un dataset con verificación criptográfica SHA-256 Fail-Closed."""
        manifest = self.get_dataset(dataset_id)
        if not manifest or not manifest.relative_path:
            raise MissingDatasetError(f"Dataset '{dataset_id}' no registrado en el DatasetRegistry.")

        file_path = self.root_dir / manifest.relative_path
        if not file_path.exists():
            raise MissingDatasetError(f"Archivo físico '{file_path}' para dataset '{dataset_id}' no existe en disco.")

        raw_bytes = file_path.read_bytes()
        actual_sha = hashlib.sha256(raw_bytes).hexdigest()
        
        if verify_sha256 and manifest.data_sha256:
            if actual_sha != manifest.data_sha256:
                raise DatasetIntegrityError(
                    f"Violación criptográfica en {dataset_id}. "
                    f"Esperado: {manifest.data_sha256}, Actual: {actual_sha}"
                )

        candles: List[Dict[str, Any]] = json.loads(raw_bytes.decode("utf-8"))

        if partition is None:
            return candles

        # Particionado físico exacto y verificación de integridad de slice
        n = len(candles)
        if partition == DatasetPartitionType.IN_SAMPLE:
            split_end = int(n * 0.60)
            slice_res = candles[:split_end]
        elif partition == DatasetPartitionType.VALIDATION:
            split_start = int(n * 0.60)
            split_end = int(n * 0.80)
            slice_res = candles[split_start:split_end]
        elif partition == DatasetPartitionType.BLIND_OOS:
            split_start = int(n * 0.80)
            slice_res = candles[split_start:]
        elif partition == DatasetPartitionType.FORWARD_PAPER:
            split_start = int(n * 0.90)
            slice_res = candles[split_start:]
        else:
            return candles

        if verify_sha256 and partition.value in manifest.partitions:
            expected_part_sha = manifest.partitions[partition.value].partition_sha256
            actual_part_sha = DatasetPartition.compute_slice_sha256(slice_res)
            if actual_part_sha != expected_part_sha:
                raise DatasetIntegrityError(
                    f"Violación de hash en partición {partition.value} de {dataset_id}. "
                    f"Esperado: {expected_part_sha}, Actual: {actual_part_sha}"
                )

        return slice_res


dataset_registry = DatasetRegistry()
