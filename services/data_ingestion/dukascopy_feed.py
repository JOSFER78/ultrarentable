"""Ingesta real de ticks Dukascopy (coste 0 EUR) para los proxies CME/FX del universo.

Doctrina REAL-ONLY: este modulo descarga y agrega ticks reales. NO sintetiza barras, NO rellena
huecos y NO repara datos. Una hora sin ticks es un hueco legitimo que se registra como tal.

Fuente verificada fisicamente el 2026-08-31:
    https://datafeed.dukascopy.com/datafeed/{SYM}/{YYYY}/{MM0}/{DD}/{HH}h_ticks.bi5

    MM0 es el mes CERO-INDEXADO (00=enero, 06=julio). Es el error clasico de esta API.

Formato del cuerpo: LZMA -> registros de 20 bytes big-endian '>3I2f':
    (ms_desde_la_hora, ask_escalado, bid_escalado, volumen_ask, volumen_bid)

El divisor de precio depende del instrumento y NO viene en la respuesta. Se declara
explicitamente por simbolo en SYMBOLS y se valida con un rango de cordura: si el precio
resultante cae fuera del rango, se aborta con error en vez de persistir precios erroneos
silenciosamente (un divisor equivocado desplaza el precio x100 sin que nada falle).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import lzma
import struct
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple

import requests
import requests.adapters

BASE_URL = "https://datafeed.dukascopy.com/datafeed"
USER_AGENT = "Ultrarentable/1.0 (real-only market data ingestion)"
TICK_STRUCT = struct.Struct(">3I2f")
TICK_SIZE = TICK_STRUCT.size  # 20 bytes
THROTTLE_SECONDS = 0.35  # cortesia con el feed gratuito; evita los HTTP 503

# Benchmark 2026-09-01 (ver informe): abrir una conexion TCP+TLS nueva por cada hora
# (comportamiento de urllib.request.urlopen sin pooling) cuesta 5-30s por fichero, y a
# veces agota en un timeout de conexion de 60s -- eso, no el "503 del servidor", es la
# causa real de los ~15s/fichero medidos originalmente. Reutilizando una unica conexion
# HTTPS (keep-alive) el mismo fichero baja a ~0.1-0.2s: ~45x mas rapido, medido con
# concurrency=3 sin ningun HTTP 503 en 150 horas reales. La sesion es un singleton de
# proceso (perdura entre los ~14 trimestres que procesa run_dukascopy_backfill) para no
# pagar el coste de conexion mas de una vez por hilo.
_SESSION_LOCK = threading.Lock()
_SESSION: Optional["requests.Session"] = None


def _get_session(pool_size: int = 16) -> "requests.Session":
    global _SESSION
    if _SESSION is None:
        with _SESSION_LOCK:
            if _SESSION is None:
                session = requests.Session()
                adapter = requests.adapters.HTTPAdapter(
                    pool_connections=1, pool_maxsize=pool_size, max_retries=0
                )
                session.mount("https://", adapter)
                session.headers.update({"User-Agent": USER_AGENT})
                _SESSION = session
    return _SESSION


REPO_ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = REPO_ROOT / "data" / "raw" / "dukascopy"
OUTPUT_DIR = REPO_ROOT / "data" / "normalized"
SQX_EXPORT_DIR = REPO_ROOT / "data" / "sqx_imports" / "dukascopy"

# Temporalidades canonicas del proyecto (SOLO INTRADIA, mandato sellado del usuario).
TIMEFRAMES: Dict[str, int] = {
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "1h": 3600,
    "4h": 14400,
}


@dataclass(frozen=True)
class SymbolSpec:
    """Especificacion de un instrumento Dukascopy.

    price_divisor y sanity_range se declaran de forma explicita: fueron determinados
    empiricamente el 2026-08-31 decodificando muestras reales, no asumidos.
    """

    dukascopy: str            # codigo en el datafeed
    canonical: str            # simbolo canonico del proyecto
    price_divisor: float      # escala entera -> precio real
    sanity_min: float         # cota inferior de cordura del precio
    sanity_max: float         # cota superior de cordura del precio
    proxy_for: Optional[str]  # instrumento CME que sustituye (None = es el activo real)
    asset_class: str


# Registro canonico. proxy_for documenta la sustitucion: el descubrimiento se hace sobre el
# proxy CFD y la portabilidad al futuro CME real se valida aparte (correlacion y spread).
SYMBOLS: Dict[str, SymbolSpec] = {
    # --- Indices (proxies CFD de los futuros CME) ---
    "USA500IDXUSD": SymbolSpec("USA500IDXUSD", "USA500IDXUSD", 1e3, 1_000, 30_000, "ES/MES", "index"),
    "USATECHIDXUSD": SymbolSpec("USATECHIDXUSD", "USATECHIDXUSD", 1e3, 3_000, 100_000, "NQ/MNQ", "index"),
    "USA30IDXUSD": SymbolSpec("USA30IDXUSD", "USA30IDXUSD", 1e3, 10_000, 200_000, "YM/MYM", "index"),
    # Anadidos el 2026-09-03 para completar los 8 activos del universo FONDEO que pidio Emilio
    # (8 activos x 5 marcos = 40 celdas). Su existencia en el datafeed esta COMPROBADA desde el
    # servidor Oracle el mismo dia: USSC2000IDXUSD devolvio 52.808 bytes y USTBONDTRUSD 1.065 para
    # la hora 2026-06-15 14h (USA2000IDXUSD, en cambio, da 404: no es ese el codigo).
    # El divisor 1e3 es el mismo de los otros indices; el rango de cordura es DELIBERADAMENTE
    # amplio y el feed aborta si el precio cae fuera, que es justo lo que protege de un divisor
    # equivocado (desplazaria el precio x100 sin que nada fallase).
    "USSC2000IDXUSD": SymbolSpec("USSC2000IDXUSD", "USSC2000IDXUSD", 1e3, 500, 10_000, "RTY/M2K", "index"),
    "USTBONDTRUSD": SymbolSpec("USTBONDTRUSD", "USTBONDTRUSD", 1e3, 40, 300, "ZB/UB", "bond"),
    # --- Metales y energia ---
    "XAUUSD": SymbolSpec("XAUUSD", "XAUUSD", 1e3, 500, 20_000, "GC/MGC", "metal"),
    "XAGUSD": SymbolSpec("XAGUSD", "XAGUSD", 1e3, 5, 500, "SI", "metal"),
    "LIGHTCMDUSD": SymbolSpec("LIGHTCMDUSD", "LIGHTCMDUSD", 1e3, 5, 400, "CL/MCL", "energy"),
    # --- Forex majors (activo real, no proxy) ---
    "EURUSD": SymbolSpec("EURUSD", "EURUSD", 1e5, 0.5, 2.5, None, "forex"),
    "GBPUSD": SymbolSpec("GBPUSD", "GBPUSD", 1e5, 0.8, 3.0, None, "forex"),
    "AUDUSD": SymbolSpec("AUDUSD", "AUDUSD", 1e5, 0.3, 1.5, None, "forex"),
    "USDCHF": SymbolSpec("USDCHF", "USDCHF", 1e5, 0.4, 2.0, None, "forex"),
    "USDCAD": SymbolSpec("USDCAD", "USDCAD", 1e5, 0.8, 2.5, None, "forex"),
    "USDJPY": SymbolSpec("USDJPY", "USDJPY", 1e3, 50, 400, None, "forex"),
}


class DukascopyError(RuntimeError):
    """Fallo irrecuperable de ingesta. Nunca se degrada a datos inventados."""


@dataclass
class HourResult:
    """Resultado de una hora de descarga. Distingue hueco legitimo de fallo."""

    hour_utc: datetime
    ticks: List[Tuple[int, float, float, float]] = field(default_factory=list)
    empty: bool = False       # 0 bytes = mercado cerrado / sin ticks (hueco legitimo)
    failed: bool = False      # error de red tras agotar reintentos
    error: str = ""


# --------------------------------------------------------------------------------------
# Descarga
# --------------------------------------------------------------------------------------

def _hour_url(symbol: str, hour: datetime) -> str:
    """Construye la URL. OJO: el mes va CERO-INDEXADO."""
    return (
        f"{BASE_URL}/{symbol}/{hour.year:04d}/{hour.month - 1:02d}/"
        f"{hour.day:02d}/{hour.hour:02d}h_ticks.bi5"
    )


def _cache_path(symbol: str, hour: datetime) -> Path:
    return (
        CACHE_DIR / symbol / f"{hour.year:04d}" / f"{hour.month:02d}"
        / f"{hour.day:02d}" / f"{hour.hour:02d}h_ticks.bi5"
    )


def download_hour(symbol: str, hour: datetime, retries: int = 6, timeout: int = 60) -> Optional[bytes]:
    """Descarga una hora de ticks. Devuelve bytes, o None si la hora no tiene datos.

    Escritura atomica (.part -> rename) y cache en disco: una hora ya descargada no se
    vuelve a pedir. Lanza DukascopyError si la red falla tras agotar los reintentos: no
    se devuelve un resultado vacio fingiendo que la hora estaba cerrada.
    """
    cached = _cache_path(symbol, hour)
    if cached.exists():
        return cached.read_bytes() or None

    # Estrangulamiento cortes: el feed es gratuito, no se le martillea.
    time.sleep(THROTTLE_SECONDS)

    url = _hour_url(symbol, hour)
    session = _get_session()
    last_error = ""
    for attempt in range(1, retries + 1):
        try:
            resp = session.get(url, timeout=timeout)
            if resp.status_code == 200:
                payload = resp.content
                cached.parent.mkdir(parents=True, exist_ok=True)
                tmp = cached.with_suffix(".part")
                tmp.write_bytes(payload)
                tmp.replace(cached)
                return payload or None
            if resp.status_code == 404:
                # 404 = esa hora no existe en el feed. Hueco legitimo, se cachea vacio.
                cached.parent.mkdir(parents=True, exist_ok=True)
                cached.write_bytes(b"")
                return None
            last_error = f"HTTP {resp.status_code}"
        except requests.exceptions.RequestException as exc:
            last_error = f"{type(exc).__name__}: {exc}"
        if attempt < retries:
            # Backoff exponencial con techo. Dukascopy responde 503 cuando se le aprieta:
            # 3 horas se perdieron asi en la primera prueba real (2026-08-31). Con
            # conexion reutilizada esto ya casi no ocurre (ver benchmark 2026-09-01);
            # el backoff se conserva como red de seguridad ante rafagas de conexion.
            time.sleep(min(2 ** attempt, 30))

    raise DukascopyError(f"{symbol} {hour.isoformat()}: fallo tras {retries} intentos ({last_error}) url={url}")


# --------------------------------------------------------------------------------------
# Decodificacion
# --------------------------------------------------------------------------------------

def decode_ticks(payload: bytes, hour: datetime, spec: SymbolSpec) -> List[Tuple[int, float, float, float]]:
    """Decodifica el .bi5 a (timestamp_ms_utc, bid, ask, volumen).

    Valida el rango de cordura del precio: un divisor equivocado se detecta aqui y aborta,
    en lugar de contaminar el dataset con precios desplazados x100.
    """
    if not payload:
        return []

    try:
        raw = lzma.LZMADecompressor().decompress(payload)
    except lzma.LZMAError as exc:
        raise DukascopyError(f"{spec.dukascopy} {hour.isoformat()}: cuerpo LZMA corrupto ({exc})") from exc

    if len(raw) % TICK_SIZE != 0:
        raise DukascopyError(
            f"{spec.dukascopy} {hour.isoformat()}: longitud {len(raw)} no multiplo de {TICK_SIZE}"
        )

    hour_ms = int(hour.replace(tzinfo=timezone.utc).timestamp() * 1000)
    out: List[Tuple[int, float, float, float]] = []
    div = spec.price_divisor

    for offset in range(0, len(raw), TICK_SIZE):
        ms, ask_i, bid_i, ask_vol, bid_vol = TICK_STRUCT.unpack_from(raw, offset)
        bid = bid_i / div
        ask = ask_i / div
        if not (spec.sanity_min <= bid <= spec.sanity_max):
            raise DukascopyError(
                f"{spec.dukascopy} {hour.isoformat()}: precio {bid} fuera del rango de cordura "
                f"[{spec.sanity_min}, {spec.sanity_max}]. Revisa price_divisor "
                f"(actual {div}). NO se persiste nada."
            )
        out.append((hour_ms + ms, bid, ask, float(ask_vol) + float(bid_vol)))

    return out


# --------------------------------------------------------------------------------------
# Agregacion tick -> OHLCV
# --------------------------------------------------------------------------------------

def aggregate_bars(
    ticks: List[Tuple[int, float, float, float]],
    timeframe: str,
) -> List[Dict[str, float]]:
    """Agrega ticks a barras OHLCV.

    Convencion: OHLC se construye sobre el **BID** (estandar de la industria para datos de
    broker); el spread medio de cada barra se guarda aparte para que el motor lo pueda
    modelar. No se inventan barras para periodos sin ticks: simplemente no existen.
    """
    if timeframe not in TIMEFRAMES:
        raise DukascopyError(f"timeframe '{timeframe}' no es canonico. Validos: {list(TIMEFRAMES)}")

    step_ms = TIMEFRAMES[timeframe] * 1000
    bars: Dict[int, Dict[str, float]] = {}

    for ts, bid, ask, vol in ticks:
        bucket = (ts // step_ms) * step_ms
        bar = bars.get(bucket)
        if bar is None:
            bars[bucket] = {
                "timestamp_utc_ms": bucket,
                "open": bid, "high": bid, "low": bid, "close": bid,
                "volume": vol,
                "_spread_sum": ask - bid,
                "_tick_count": 1,
            }
        else:
            if bid > bar["high"]:
                bar["high"] = bid
            if bid < bar["low"]:
                bar["low"] = bid
            bar["close"] = bid
            bar["volume"] += vol
            bar["_spread_sum"] += ask - bid
            bar["_tick_count"] += 1

    out = []
    for bucket in sorted(bars):
        bar = bars[bucket]
        count = bar.pop("_tick_count")
        spread_sum = bar.pop("_spread_sum")
        bar["spread_mean"] = round(spread_sum / count, 8)
        bar["tick_count"] = count
        out.append(bar)
    return out


# --------------------------------------------------------------------------------------
# Orquestacion de la ingesta
# --------------------------------------------------------------------------------------

def iter_hours(start: datetime, end: datetime) -> Iterator[datetime]:
    cur = start.replace(minute=0, second=0, microsecond=0, tzinfo=None)
    stop = end.replace(minute=0, second=0, microsecond=0, tzinfo=None)
    while cur <= stop:
        yield cur
        cur += timedelta(hours=1)


def write_dataset_files(
    bars: List[Dict[str, object]],
    spec: SymbolSpec,
    tf: str,
    out_dir: Path,
    *,
    hours_empty: int = 0,
    hours_failed: int = 0,
    has_volume: bool = True,
) -> Dict[str, object]:
    """Persiste el dataset normalizado (.json) y su manifiesto (.json).

    Devuelve dict con dataset_id, data_path, manifest_path, bar_count y checksum_sha256.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    first, last = bars[0]["timestamp_utc_ms"], bars[-1]["timestamp_utc_ms"]
    dataset_id = f"ds_dukascopy_{spec.canonical.lower()}_{tf}_{first}_{last}"

    payload_json = json.dumps(
        {
            "dataset_id": dataset_id,
            "venue": "dukascopy",
            "symbol": spec.canonical,
            "timeframe": tf,
            "proxy_for": spec.proxy_for,
            "bars": bars,
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    raw_bytes = payload_json.encode("utf-8")
    checksum = hashlib.sha256(raw_bytes).hexdigest()

    data_path = out_dir / f"{dataset_id}.json"
    manifest_path = out_dir / f"{dataset_id}_manifest.json"

    data_path.write_bytes(raw_bytes)
    manifest_path.write_text(
        json.dumps(
            {
                "dataset_id": dataset_id,
                "venue": "dukascopy",
                "symbol": spec.canonical,
                "timeframe": tf,
                "proxy_for": spec.proxy_for,
                "bar_count": len(bars),
                "start_time_utc_ms": first,
                "end_time_utc_ms": last,
                "checksum_sha256": checksum,
                "source_url_pattern": f"{BASE_URL}/{spec.dukascopy}/YYYY/MM0/DD/HHh_ticks.bi5",
                "price_divisor": spec.price_divisor,
                "ohlc_basis": "bid",
                "has_volume": has_volume,
                "hours_empty": hours_empty,
                "hours_failed": hours_failed,
                "real_only": True,
                "gaps_filled": False,
                "ingested_at_utc": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    return {
        "dataset_id": dataset_id,
        "data_path": data_path,
        "manifest_path": manifest_path,
        "bar_count": len(bars),
        "checksum_sha256": checksum,
    }


def ingest(
    symbol: str,
    start: datetime,
    end: datetime,
    timeframes: Optional[List[str]] = None,
    verbose: bool = True,
    concurrency: int = 1,
    output_dir: Optional[Path] = None,
) -> Dict[str, object]:
    """Descarga el rango completo y persiste un dataset por temporalidad.

    Devuelve un informe con conteos reales y la lista de huecos. Nunca rellena.

    ``concurrency`` acota cuantas horas se piden en paralelo (I/O-bound: el cuello de
    botella medido es la latencia del servidor de Dukascopy, ~15s por peticion, no la
    CPU local ni el THROTTLE_SECONDS propio). Cada hilo respeta su propio throttle y
    backoff via download_hour; no hay estado mutable compartido salvo listas locales
    que solo se tocan desde el hilo principal al recoger cada resultado. El orden de
    llegada no importa: all_ticks se reordena por timestamp al final.
    """
    if symbol not in SYMBOLS:
        raise DukascopyError(f"simbolo '{symbol}' no esta en el registro canonico: {list(SYMBOLS)}")
    spec = SYMBOLS[symbol]
    timeframes = timeframes or list(TIMEFRAMES)

    all_ticks: List[Tuple[int, float, float, float]] = []
    gaps: List[str] = []
    failures: List[str] = []
    hours_total = 0

    def _fetch(hour: datetime) -> Tuple[datetime, Optional[List[Tuple[int, float, float, float]]], Optional[str]]:
        try:
            payload = download_hour(spec.dukascopy, hour)
        except DukascopyError as exc:
            return (hour, None, str(exc))
        if payload is None:
            return (hour, None, None)
        try:
            ticks = decode_ticks(payload, hour, spec)
        except DukascopyError as exc:
            return (hour, None, str(exc))
        return (hour, ticks, "")

    hours = list(iter_hours(start, end))
    workers = max(1, int(concurrency))

    from concurrent.futures import ThreadPoolExecutor, as_completed

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_fetch, hour) for hour in hours]
        for fut in as_completed(futures):
            hour, ticks, err = fut.result()
            hours_total += 1
            if err:
                failures.append(f"{hour.isoformat()}: {err}")
            elif ticks is None:
                gaps.append(hour.isoformat())
            else:
                all_ticks.extend(ticks)
            if verbose and hours_total % 24 == 0:
                print(f"  {spec.dukascopy}: {hours_total}/{len(hours)} horas, {len(all_ticks):,} ticks", flush=True)

    all_ticks.sort(key=lambda t: t[0])

    report: Dict[str, object] = {
        "symbol": spec.canonical,
        "dukascopy_symbol": spec.dukascopy,
        "proxy_for": spec.proxy_for,
        "asset_class": spec.asset_class,
        "source": "dukascopy_datafeed_public",
        "cost_eur": 0.0,
        "range_start_utc": start.isoformat(),
        "range_end_utc": end.isoformat(),
        "hours_requested": hours_total,
        "hours_empty": len(gaps),
        "hours_failed": len(failures),
        "ticks_total": len(all_ticks),
        "price_divisor": spec.price_divisor,
        "datasets": {},
        "gaps_sample": gaps[:50],
        "failures": failures,
    }

    if not all_ticks:
        report["status"] = "NO DATA"
        report["message"] = "El rango no devolvio ni un solo tick real. No se persiste nada."
        return report

    volumes = sum(t[3] for t in all_ticks)
    report["has_volume"] = volumes > 0
    if volumes == 0:
        report["portability_warning"] = (
            "NO_PORTABLE_CME: la fuente entrega volumen 0 para este instrumento. "
            "Toda estrategia que dependa del volumen NO es portable al futuro CME real."
        )

    out_dir = Path(output_dir) if output_dir else OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    SQX_EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    for tf in timeframes:
        bars = aggregate_bars(all_ticks, tf)
        if not bars:
            report["datasets"][tf] = {"status": "NO DATA", "bars": 0}
            continue

        written = write_dataset_files(
            bars,
            spec,
            tf,
            out_dir,
            hours_empty=len(gaps),
            hours_failed=len(failures),
            has_volume=bool(report["has_volume"]),
        )
        dataset_id = str(written["dataset_id"])
        checksum = str(written["checksum_sha256"])

        # CSV plano para importar en SQX (naming canonico <SYM>_<TF>). El nombre no lleva
        # rango de fechas (a diferencia del dataset_id), asi que una llamada a ingest()
        # con un rango parcial DEBE fusionarse con lo ya exportado: sobrescribir sin
        # fusionar borraria barras reales de otros rangos ya persistidos (bug real
        # detectado 2026-08-31 al invocar ingest() con un rango corto de prueba, que
        # trunco el CSV completo de USA500IDXUSD_H1 a solo esas horas).
        tf_sqx = {"1m": "M1", "5m": "M5", "15m": "M15", "1h": "H1", "4h": "H4"}[tf]
        csv_path = SQX_EXPORT_DIR / f"{spec.canonical}_{tf_sqx}.csv"
        merged: Dict[int, Tuple[str, str, str, str, str]] = {}
        if csv_path.exists():
            with csv_path.open("r", encoding="utf-8") as fh:
                next(fh, None)  # cabecera
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    dt_str, o, h, l, c, v = line.split(",")
                    ts_existing = int(
                        datetime.strptime(dt_str, "%Y.%m.%d %H:%M:%S")
                        .replace(tzinfo=timezone.utc).timestamp() * 1000
                    )
                    merged[ts_existing] = (o, h, l, c, v)
        for bar in bars:
            merged[int(bar["timestamp_utc_ms"])] = (
                str(bar["open"]), str(bar["high"]), str(bar["low"]), str(bar["close"]), str(bar["volume"]),
            )
        tmp_csv = csv_path.with_suffix(".part")
        with tmp_csv.open("w", encoding="utf-8") as fh:
            fh.write("DateTime,Open,High,Low,Close,Volume\n")
            for ts in sorted(merged):
                o, h, l, c, v = merged[ts]
                dt = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
                fh.write(f"{dt:%Y.%m.%d %H:%M:%S},{o},{h},{l},{c},{v}\n")
        tmp_csv.replace(csv_path)

        report["datasets"][tf] = {
            "dataset_id": dataset_id,
            "bars": len(bars),
            "checksum_sha256": checksum,
            "csv": str(csv_path.relative_to(REPO_ROOT)),
        }
        if verbose:
            print(f"  -> {tf}: {len(bars):,} barras | sha256 {checksum[:16]}...", flush=True)

    report["status"] = "OK"
    return report


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Ingesta real de ticks Dukascopy (coste 0 EUR).")
    parser.add_argument("--symbol", required=True, help=f"uno de: {', '.join(SYMBOLS)}, o 'ALL'")
    parser.add_argument("--start", required=True, help="fecha inicio UTC YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="fecha fin UTC YYYY-MM-DD (inclusive)")
    parser.add_argument("--timeframes", default="1m,5m,15m,1h,4h")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument(
        "--concurrency", type=int, default=1,
        help="peticiones .bi5 en paralelo (I/O-bound; recomendado 2-3, tope 4 por cortesia con el feed gratuito)",
    )
    args = parser.parse_args(argv)

    start = datetime.strptime(args.start, "%Y-%m-%d")
    end = datetime.strptime(args.end, "%Y-%m-%d").replace(hour=23)
    tfs = [t.strip() for t in args.timeframes.split(",") if t.strip()]
    symbols = list(SYMBOLS) if args.symbol.upper() == "ALL" else [args.symbol]

    exit_code = 0
    for sym in symbols:
        print(f"\n=== {sym} [{args.start} -> {args.end}] ===", flush=True)
        try:
            report = ingest(sym, start, end, tfs, verbose=not args.quiet, concurrency=args.concurrency)
        except DukascopyError as exc:
            print(f"ERROR {sym}: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        print(json.dumps({k: v for k, v in report.items() if k != "gaps_sample"}, indent=2))
        if report.get("status") == "NO DATA":
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
