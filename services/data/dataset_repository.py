"""services/data/dataset_repository.py
Repositorio desacoplado de datasets y snapshots de velas reales sin acoplamiento a base de datos.
Lectura y validación determinista de archivos en data/normalized con verificación criptográfica SHA-256.
"""

from __future__ import annotations

import glob
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from contracts.backtest import BarData, DatasetSnapshot
from services.api.app.config import DATA_DIR as BASE_DATA_DIR


class DatasetUnavailableError(FileNotFoundError):
    """No hay datos reales para la serie pedida.

    Se lanza en vez de devolver barras fabricadas: este repositorio alimenta backtests, y una
    serie sintetica que parece real es el peor fallo posible en un sistema que arriesga dinero.
    """


class DatasetRepository:
    """Acceso y gestión de datasets canónicos verificados en disco."""

    def __init__(self, data_root: Optional[Path] = None) -> None:
        # La raiz de datos SIEMPRE sale de la autoridad central de configuracion, que
        # respeta la variable DATA_DIR. Resolverla con parents relativos al fichero hacia que
        # este repositorio siguiera leyendo del directorio del repo aunque el resto del sistema
        # apuntara a otro sitio, y el guard de fase 2 no lo detectaba porque validaba la copia
        # duplicada y muerta data/dataset_repository.py en vez de esta.
        self.data_root = data_root or BASE_DATA_DIR
        self.normalized_dir = self.data_root / "normalized"

    def list_available_datasets(self) -> List[Dict[str, Any]]:
        """Lista todos los datasets normalizados disponibles con sus metadatos de manifest."""
        manifests: List[Dict[str, Any]] = []
        if not self.normalized_dir.exists():
            return manifests

        manifest_files = list(self.normalized_dir.glob("*_manifest.json"))
        for mf in sorted(manifest_files):
            try:
                with open(mf, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    manifests.append(data)
            except Exception:
                continue
        return manifests

    def get_snapshot(
        self,
        symbol: str = "ETH-USDT",
        timeframe: str = "1h",
        is_in_sample: bool = False,
        split_ratio: float = 0.70,
    ) -> DatasetSnapshot:
        """Carga y genera un DatasetSnapshot inmutable con hash SHA-256 verificado.
        
        Si existen archivos en data/normalized, utiliza los datos reales y su manifest.
        Si split_ratio está configurado, fragmenta limpiamente en IS (primer 70%) u OOS (último 30%).
        """
        # load_bars ya falla cerrado si no hay datos reales; aqui no se rellena nada.
        bars = self.load_bars(symbol, timeframe)

        # Aplicar partición IS / OOS
        split_idx = int(len(bars) * split_ratio)
        if is_in_sample:
            selected_bars = bars[:split_idx] if split_idx > 0 else bars
        else:
            selected_bars = bars[split_idx:] if split_idx < len(bars) else bars

        start_ts = selected_bars[0].timestamp_utc_ms
        end_ts = selected_bars[-1].timestamp_utc_ms

        # Hash determinista de la serie seleccionada
        # El hash cubre el CONTENIDO de las velas, no solo los metadatos. Antes se calculaba
        # sobre "simbolo:tf:numero:inicio:fin:tramo", asi que dos series con precios distintos y
        # las mismas dimensiones producian el mismo hash y el docstring prometia una
        # verificacion que no existia.
        target_file = self._resolver_fichero(symbol, timeframe)
        hash_fichero = self._verificar_custodia(target_file)
        cuerpo = "\n".join(
            f"{b.timestamp_utc_ms}:{b.open}:{b.high}:{b.low}:{b.close}:{b.volume}"
            for b in selected_bars
        )
        payload = (
            f"{symbol}:{timeframe}:{is_in_sample}:{len(selected_bars)}:{hash_fichero}\n{cuerpo}"
        )
        sha_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

        return DatasetSnapshot(
            dataset_id=f"ds_{symbol.lower().replace('-', '_')}_{timeframe}_{'is' if is_in_sample else 'oos'}",
            symbol=symbol,
            timeframe=timeframe,
            start_timestamp_utc_ms=start_ts,
            end_timestamp_utc_ms=end_ts,
            total_bars=len(selected_bars),
            sha256_hash=sha_hash,
            is_in_sample=is_in_sample,
        )

    @staticmethod
    def _sha256_file(path: Path) -> str:
        """SHA-256 del fichero completo, leido por bloques para no cargarlo entero en memoria."""
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)
        return digest.hexdigest()

    def _resolver_fichero(self, symbol: str, timeframe: str) -> Path:
        """Devuelve el fichero de datos real de la serie, o falla cerrado.

        La coincidencia es insensible a mayusculas porque en disco conviven
        "ds_bingx_ETH_USDT_1h_..." y "ds_dukascopy_usa500idxusd_15m_...": con un glob sensible a
        mayusculas, pedir el simbolo con la capitalizacion "equivocada" devolvia "no hay dataset"
        para una serie que si existe, un falso negativo traicionero en un cargador de datos.
        """
        formatted_sym = symbol.replace("-", "_").replace("/", "_")
        infijo = f"_{formatted_sym.lower()}_{timeframe.lower()}_"
        candidatos = [
            p for p in self.normalized_dir.glob("ds_*.json")
            if not p.name.endswith("_manifest.json") and infijo in p.name.lower()
        ]
        if not candidatos:
            raise DatasetUnavailableError(
                f"No hay dataset real para {symbol} {timeframe}: ningun fichero contiene "
                f"'{infijo}' en {self.normalized_dir}"
            )
        return sorted(candidatos, key=lambda p: p.stat().st_size, reverse=True)[0]

    def _verificar_custodia(self, target_file: Path) -> str:
        """Hash del fichero, contrastado con el manifiesto cuando existe.

        Si el manifiesto declara un checksum y no coincide con el contenido real del fichero, se
        falla cerrado: un dataset alterado despues de su ingesta invalida cualquier backtest que
        se ejecute sobre el, y aceptarlo en silencio destruye la trazabilidad que justifica
        guardar manifiestos.
        """
        hash_real = self._sha256_file(target_file)
        manifiesto = target_file.with_name(target_file.stem + "_manifest.json")
        if manifiesto.is_file():
            try:
                declarado = json.loads(manifiesto.read_text(encoding="utf-8")).get("checksum_sha256")
            except (OSError, json.JSONDecodeError) as exc:
                raise DatasetUnavailableError(
                    f"Manifiesto ilegible para {target_file.name}: {exc}"
                ) from exc
            if declarado and declarado != hash_real:
                raise DatasetUnavailableError(
                    f"Custodia rota en {target_file.name}: el manifiesto declara "
                    f"{declarado[:16]}... y el fichero real es {hash_real[:16]}..."
                )
        return hash_real

    def load_bars(self, symbol: str = "ETH-USDT", timeframe: str = "1h") -> List[BarData]:
        """Carga las velas reales de la serie pedida desde data/normalized.

        Falla cerrado: si no hay fichero, si el formato no se reconoce o si una vela no trae
        marca de tiempo, lanza DatasetUnavailableError. La version anterior devolvia 100 velas
        generadas en rampa ascendente cuando cualquier cosa fallaba, y ademas leia el campo
        "timestamp" cuando el canonico del proyecto es "timestamp_utc_ms": sobre los datasets
        reales devolvia todas las velas con marca de tiempo 0 sin avisar.
        """
        target_file = self._resolver_fichero(symbol, timeframe)
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            raise DatasetUnavailableError(f"No se pudo leer {target_file.name}: {exc}") from exc

        # Dos formatos reales conviven en disco: lista de velas (Binance/BingX) y diccionario
        # con clave "bars" (consolidados de Dukascopy).
        if isinstance(raw_data, dict):
            payload = raw_data.get("bars")
        else:
            payload = raw_data
        if not isinstance(payload, list) or not payload:
            raise DatasetUnavailableError(
                f"{target_file.name} no contiene una lista de velas reconocible"
            )

        bars: List[BarData] = []
        for indice, item in enumerate(payload):
            if isinstance(item, dict):
                marca = item.get("timestamp_utc_ms", item.get("timestamp", item.get("time")))
                if marca is None:
                    raise DatasetUnavailableError(
                        f"{target_file.name}: la vela {indice} no trae marca de tiempo "
                        f"(claves presentes: {sorted(item)[:8]})"
                    )
                bars.append(
                    BarData(
                        timestamp_utc_ms=int(marca),
                        open=float(item["open"]),
                        high=float(item["high"]),
                        low=float(item["low"]),
                        close=float(item["close"]),
                        volume=float(item.get("volume", 0.0)),
                    )
                )
            elif isinstance(item, list) and len(item) >= 6:
                bars.append(
                    BarData(
                        timestamp_utc_ms=int(item[0]),
                        open=float(item[1]),
                        high=float(item[2]),
                        low=float(item[3]),
                        close=float(item[4]),
                        volume=float(item[5]),
                    )
                )
            else:
                raise DatasetUnavailableError(
                    f"{target_file.name}: la vela {indice} tiene un formato no reconocido "
                    f"({type(item).__name__})"
                )

        bars.sort(key=lambda b: b.timestamp_utc_ms)
        return bars
