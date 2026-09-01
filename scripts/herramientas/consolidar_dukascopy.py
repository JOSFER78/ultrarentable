"""Consolida los chunks trimestrales de Dukascopy en UN dataset por simbolo+TF.

PROBLEMA que resuelve: `services/data_ingestion/run_dukascopy_backfill.py` genera un fichero
`ds_dukascopy_<symbol>_<tf>_<first_ts>_<last_ts>.json` por CADA TRIMESTRE procesado. Como
`scripts/mine.py::resolve_dataset_file` elige "el fichero mas grande que casa el patron", la
mineria solo ve UN trimestre suelto (p.ej. 5.835 barras de 83.543 disponibles en 15m de
USA500IDXUSD) y con eso es matematicamente imposible alcanzar el criterio 1.1 SELLADO
(>=200 trades OOS: con Blind OOS=20% de un solo trimestre no hay ni barras para intentarlo).

Este script une TODOS los chunks de un simbolo+TF en un unico fichero, deduplicando por
timestamp y clasificando cada hueco con criterio de SESION (no de calendario 24/7 -- ver
`orchestration/results/desbloqueo_tradfi_calidad_datos.md`, que documenta el error de medir
cobertura contra un calendario continuo).

REAL-ONLY: no rellena ni un hueco, no inventa ni un dato. `gaps_filled` queda SIEMPRE en
`false` en el manifiesto de salida. Los chunks originales NUNCA se tocan ni se borran (regla
del proyecto: nunca `rm`); este script solo LEE data/normalized/ y escribe UN fichero nuevo
(mas su manifiesto) que no colisiona con ningun nombre de chunk existente.

USO:
    nice -n 19 ionice -c 3 .venv/bin/python scripts/herramientas/consolidar_dukascopy.py \
        --symbol usa500idxusd --tf 15m

    # Solo analizar y mostrar el informe, sin escribir nada en disco:
    nice -n 19 ionice -c 3 .venv/bin/python scripts/herramientas/consolidar_dukascopy.py \
        --symbol usa500idxusd --tf 5m --dry-run

    # Todos los TF intradia de un simbolo de una tacada:
    nice -n 19 ionice -c 3 .venv/bin/python scripts/herramientas/consolidar_dukascopy.py \
        --symbol usa500idxusd --tf all

COMO FUNCIONA (memoria acotada, streaming por chunk):
    1. Localiza `ds_dukascopy_<symbol>_<tf>_*.json` en --data-dir (excluye el propio
       consolidado de una ejecucion anterior: lleva el marcador `_consolidated` en el nombre,
       asi que jamas se relee a si mismo como si fuera un chunk de entrada).
    2. Procesa los chunks DE UNO EN UNO: abre, parsea sus `bars`, los vuelca en un diccionario
       {timestamp_utc_ms: (bar, ingested_at_utc_del_chunk)} y libera el JSON del chunk antes de
       abrir el siguiente. El pico de memoria es ~ el tamano del symbol+TF consolidado (para
       1m, unos cientos de MB), nunca la suma de "todos los TF a la vez" -- cada TF se procesa
       de forma independiente y secuencial, incluso con `--tf all`.
    3. Deduplica por `timestamp_utc_ms` (los chunks se solapan en los bordes: verificado que el
       chunk mas reciente de un backfill en curso puede repetir el rango final del chunk
       trimestral que lo contiene). Si dos chunks dan el MISMO timestamp con bars DISTINTAS
       -- no deberia pasar con una fuente real inmutable, pero no se asume -- se conserva la
       version del chunk cuyo manifiesto declara `ingested_at_utc` mas reciente y se registra
       el conflicto explicitamente en el informe y el manifiesto (nunca se promedia ni se
       elige en silencio).
    4. Ordena por timestamp y verifica que el resultado es estrictamente creciente (aborta si
       no lo es en vez de "arreglarlo").
    5. Clasifica cada hueco (delta entre barras consecutivas > paso nominal del TF) en:
         - fin_de_semana: el hueco empieza jue/vie/sab y termina sab/dom/lun, 40h-60h -- el
           cierre semanal tipico (viernes tarde UTC -> domingo tarde UTC).
         - pausa_diaria: hueco corto (<=3.5h) que NO tiene forma de fin de semana -- la pausa
           de mantenimiento diaria del venue.
         - anomalo: el resto (festivos, fines de semana alargados por un festivo pegado, huecos
           de datos reales). Se listan aparte con fecha/hora y duracion, nunca se ocultan
           dentro de "fin_de_semana" ni de "pausa_diaria".
       Los umbrales estan calibrados empiricamente sobre USA500IDXUSD 15m (ver informe de
       entrega): el hueco dominante en dia laborable mide ~2h (721/970 huecos), el semanal
       ~49-54h (170/970), y todo lo demas (26h, 29h, 74h...) son festivos/anomalias reales.
    6. Escribe el dataset consolidado con el MISMO esquema que produce
       `services/data_ingestion/dukascopy_feed.py::ingest()` (dataset_id/venue/symbol/
       timeframe/proxy_for/bars), serializado exactamente igual (json.dumps con
       separators=(",", ":") y sort_keys=True) para que `checksum_sha256` sea reproducible por
       cualquier verificador que haga sha256 sobre los bytes crudos del fichero (varios scripts
       del repo hacen exactamente eso como fallback si falta el manifest).
    7. Nombre de salida `ds_dukascopy_<symbol>_<tf>_consolidated.json` (+ `_manifest.json`):
       no lleva rango de timestamps, asi que es ESTABLE entre ejecuciones (reescribe siempre el
       mismo fichero -- no acumula versiones viejas) y sigue casando el patron de glob que usa
       `resolve_dataset_file(..., data_source="dukascopy")`
       (`ds_dukascopy_<symbol>_<tf>_*.json`), donde gana "el fichero mas grande". Este script
       verifica esa eleccion de verdad (no la asume): tras escribir, si puede derivar el
       simbolo CME desde `proxy_for`, llama al MISMO `resolve_dataset_file` que usa la mineria
       y reporta si elige el consolidado.
    8. Idempotente: cada ejecucion relee TODOS los chunks originales (nunca el consolidado
       previo) y el resultado es una funcion pura de esos chunks -- volver a ejecutar no
       duplica ni corrompe nada, simplemente regenera el mismo fichero (o uno mayor si el
       backfill produjo chunks nuevos entre medias).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from services.data_ingestion.dukascopy_feed import SYMBOLS, TIMEFRAMES  # noqa: E402

DEFAULT_DATA_DIR = REPO_ROOT / "data" / "normalized"
CONSOLIDATED_MARKER = "_consolidated"

# --- Umbrales de clasificacion de huecos (ver docstring del modulo) --------------------
PAUSA_DIARIA_MAX_HOURS = 3.5
WEEKEND_MIN_HOURS = 40.0
WEEKEND_MAX_HOURS = 60.0
WEEKEND_START_WEEKDAYS = {3, 4, 5}   # jueves, viernes, sabado (Python: lunes=0)
WEEKEND_END_WEEKDAYS = {5, 6, 0}     # sabado, domingo, lunes
MAX_ANOMALOS_DETALLE = 200           # tope de huecos anomalos listados en el manifiesto


class ConsolidationError(RuntimeError):
    """Fallo real de consolidacion (dato inconsistente entre chunks). Falla ruidoso a
    proposito: silenciar una divergencia de price_divisor/proxy_for/ohlc_basis entre
    chunks del MISMO simbolo+TF corromperia el dataset consolidado sin avisar."""


def find_chunks(data_dir: Path, symbol: str, tf: str) -> List[Path]:
    pattern = f"ds_dukascopy_{symbol.lower()}_{tf.lower()}_*.json"
    matches = [
        p for p in data_dir.glob(pattern)
        if not p.name.endswith("_manifest.json") and CONSOLIDATED_MARKER not in p.name
    ]
    return sorted(matches)


def load_manifest(chunk_path: Path) -> Optional[dict]:
    manifest_path = chunk_path.parent / f"{chunk_path.stem}_manifest.json"
    if not manifest_path.exists():
        return None
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def classify_gap(prev_ts_ms: int, next_ts_ms: int) -> Tuple[str, float]:
    """Clasifica un hueco entre dos barras consecutivas. Devuelve (tipo, horas)."""
    delta_ms = next_ts_ms - prev_ts_ms
    hours = delta_ms / 3_600_000.0
    prev_dt = datetime.fromtimestamp(prev_ts_ms / 1000.0, tz=timezone.utc)
    next_dt = datetime.fromtimestamp(next_ts_ms / 1000.0, tz=timezone.utc)
    if (
        hours >= WEEKEND_MIN_HOURS
        and prev_dt.weekday() in WEEKEND_START_WEEKDAYS
        and next_dt.weekday() in WEEKEND_END_WEEKDAYS
    ):
        if hours <= WEEKEND_MAX_HOURS:
            return "fin_de_semana", hours
        return "anomalo", hours  # fin de semana alargado por un festivo pegado
    if hours <= PAUSA_DIARIA_MAX_HOURS:
        return "pausa_diaria", hours
    return "anomalo", hours


def consolidate(symbol: str, tf: str, data_dir: Path, verbose: bool = True) -> dict:
    """Consolida un simbolo+TF. Devuelve un informe completo (dict) SIN escribir nada;
    el llamante decide si persistir con `write_outputs`."""
    t0 = time.monotonic()
    symbol_lower = symbol.lower()
    if tf not in TIMEFRAMES:
        raise ValueError(f"timeframe '{tf}' no es canonico. Validos: {list(TIMEFRAMES)}")
    step_ms = TIMEFRAMES[tf] * 1000

    chunks = find_chunks(data_dir, symbol_lower, tf)
    if not chunks:
        raise FileNotFoundError(
            f"No hay ningun chunk 'ds_dukascopy_{symbol_lower}_{tf}_*.json' en {data_dir}"
        )

    merged: Dict[int, Tuple[dict, str]] = {}
    duplicates_identical = 0
    conflicts: List[dict] = []
    chunk_meta: List[dict] = []
    proxy_for_seen: set = set()
    price_divisor_seen: set = set()
    ohlc_basis_seen: set = set()
    source_url_pattern_seen: set = set()
    canonical_symbol_seen: set = set()

    for chunk_path in chunks:
        manifest = load_manifest(chunk_path)
        ingested_at = str(manifest.get("ingested_at_utc")) if manifest and manifest.get("ingested_at_utc") else ""
        raw = chunk_path.read_text(encoding="utf-8")
        data = json.loads(raw)
        del raw
        bars = data.get("bars", [])
        chunk_meta.append({
            "dataset_id": data.get("dataset_id", chunk_path.stem),
            "file": chunk_path.name,
            "bar_count_raw": len(bars),
            "ingested_at_utc": ingested_at,
        })
        if data.get("proxy_for"):
            proxy_for_seen.add(data["proxy_for"])
        if data.get("symbol"):
            canonical_symbol_seen.add(data["symbol"])
        if manifest:
            if manifest.get("price_divisor") is not None:
                price_divisor_seen.add(manifest["price_divisor"])
            if manifest.get("ohlc_basis"):
                ohlc_basis_seen.add(manifest["ohlc_basis"])
            if manifest.get("source_url_pattern"):
                source_url_pattern_seen.add(manifest["source_url_pattern"])

        for bar in bars:
            ts = int(bar["timestamp_utc_ms"])
            existing = merged.get(ts)
            if existing is None:
                merged[ts] = (bar, ingested_at)
            else:
                existing_bar, existing_ingested = existing
                if existing_bar == bar:
                    duplicates_identical += 1
                else:
                    conflicts.append({
                        "timestamp_utc_ms": ts,
                        "timestamp_iso": datetime.fromtimestamp(ts / 1000.0, tz=timezone.utc).isoformat(),
                        "kept_ingested_at": existing_ingested,
                        "challenger_ingested_at": ingested_at,
                        "resolved_to": "challenger" if ingested_at > existing_ingested else "kept",
                    })
                    if ingested_at > existing_ingested:
                        merged[ts] = (bar, ingested_at)
        del data, bars

    if proxy_for_seen and len(proxy_for_seen) > 1:
        raise ConsolidationError(f"proxy_for inconsistente entre chunks: {proxy_for_seen}")
    if canonical_symbol_seen and len(canonical_symbol_seen) > 1:
        raise ConsolidationError(f"symbol inconsistente entre chunks: {canonical_symbol_seen}")
    if price_divisor_seen and len(price_divisor_seen) > 1:
        raise ConsolidationError(f"price_divisor inconsistente entre chunks: {price_divisor_seen}")
    if ohlc_basis_seen and len(ohlc_basis_seen) > 1:
        raise ConsolidationError(f"ohlc_basis inconsistente entre chunks: {ohlc_basis_seen}")

    canonical_symbol = next(iter(canonical_symbol_seen)) if canonical_symbol_seen else symbol.upper()
    proxy_for = next(iter(proxy_for_seen)) if proxy_for_seen else SYMBOLS.get(canonical_symbol).proxy_for if canonical_symbol in SYMBOLS else None
    price_divisor = next(iter(price_divisor_seen)) if price_divisor_seen else (SYMBOLS[canonical_symbol].price_divisor if canonical_symbol in SYMBOLS else None)
    ohlc_basis = next(iter(ohlc_basis_seen)) if ohlc_basis_seen else "bid"
    source_url_pattern = next(iter(source_url_pattern_seen)) if source_url_pattern_seen else None

    timestamps = sorted(merged.keys())
    for i in range(1, len(timestamps)):
        if timestamps[i] <= timestamps[i - 1]:
            raise ConsolidationError(
                f"Resultado NO estrictamente creciente en indice {i}: "
                f"{timestamps[i-1]} -> {timestamps[i]}"
            )

    bars_sorted = [merged[ts][0] for ts in timestamps]
    has_volume = any(float(b.get("volume", 0.0) or 0.0) > 0.0 for b in bars_sorted)

    gap_counts = {"pausa_diaria": 0, "fin_de_semana": 0, "anomalo": 0}
    anomalos_detalle: List[dict] = []
    contiguous = 0
    for i in range(1, len(timestamps)):
        delta = timestamps[i] - timestamps[i - 1]
        if delta == step_ms:
            contiguous += 1
            continue
        tipo, hours = classify_gap(timestamps[i - 1], timestamps[i])
        gap_counts[tipo] += 1
        if tipo == "anomalo" and len(anomalos_detalle) < MAX_ANOMALOS_DETALLE:
            anomalos_detalle.append({
                "desde_utc": datetime.fromtimestamp(timestamps[i - 1] / 1000.0, tz=timezone.utc).isoformat(),
                "hasta_utc": datetime.fromtimestamp(timestamps[i] / 1000.0, tz=timezone.utc).isoformat(),
                "horas": round(hours, 2),
            })

    elapsed_s = time.monotonic() - t0

    return {
        "symbol": canonical_symbol,
        "timeframe": tf,
        "proxy_for": proxy_for,
        "price_divisor": price_divisor,
        "ohlc_basis": ohlc_basis,
        "source_url_pattern": source_url_pattern,
        "has_volume": has_volume,
        "chunks_found": len(chunks),
        "chunks_meta": chunk_meta,
        "raw_bar_count_sum": sum(c["bar_count_raw"] for c in chunk_meta),
        "duplicates_identical": duplicates_identical,
        "conflicts": conflicts,
        "bar_count": len(bars_sorted),
        "start_time_utc_ms": timestamps[0] if timestamps else None,
        "end_time_utc_ms": timestamps[-1] if timestamps else None,
        "transitions_total": max(0, len(timestamps) - 1),
        "gaps_contiguous": contiguous,
        "gaps_pausa_diaria": gap_counts["pausa_diaria"],
        "gaps_fin_de_semana": gap_counts["fin_de_semana"],
        "gaps_anomalo": gap_counts["anomalo"],
        "gaps_anomalo_detalle": anomalos_detalle,
        "bars": bars_sorted,
        "elapsed_seconds": round(elapsed_s, 2),
    }


def write_outputs(report: dict, symbol: str, tf: str, data_dir: Path) -> Tuple[Path, Path]:
    symbol_lower = symbol.lower()
    dataset_id = f"ds_dukascopy_{symbol_lower}_{tf}{CONSOLIDATED_MARKER}"

    payload = {
        "dataset_id": dataset_id,
        "venue": "dukascopy",
        "symbol": report["symbol"],
        "timeframe": tf,
        "proxy_for": report["proxy_for"],
        "bars": report["bars"],
    }
    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    checksum = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()

    dataset_path = data_dir / f"{dataset_id}.json"
    dataset_path.write_text(payload_json, encoding="utf-8")

    manifest = {
        "dataset_id": dataset_id,
        "venue": "dukascopy",
        "symbol": report["symbol"],
        "timeframe": tf,
        "proxy_for": report["proxy_for"],
        "bar_count": report["bar_count"],
        "start_time_utc_ms": report["start_time_utc_ms"],
        "end_time_utc_ms": report["end_time_utc_ms"],
        "checksum_sha256": checksum,
        "source_url_pattern": report["source_url_pattern"],
        "price_divisor": report["price_divisor"],
        "ohlc_basis": report["ohlc_basis"],
        "has_volume": report["has_volume"],
        "real_only": True,
        "gaps_filled": False,
        "ingested_at_utc": datetime.now(timezone.utc).isoformat(),
        # --- metadata propia de la consolidacion (extension del esquema, no lo rompe) ---
        "consolidated": True,
        "consolidated_at_utc": datetime.now(timezone.utc).isoformat(),
        "consolidated_from_chunks": [c["dataset_id"] for c in report["chunks_meta"]],
        "chunks_count": report["chunks_found"],
        "raw_bar_count_sum_before_dedup": report["raw_bar_count_sum"],
        "duplicates_identical_deduped": report["duplicates_identical"],
        "duplicate_conflicts": report["conflicts"],
        "gap_classification_method": (
            f"session-aware: pausa_diaria<= {PAUSA_DIARIA_MAX_HOURS}h; "
            f"fin_de_semana={WEEKEND_MIN_HOURS}-{WEEKEND_MAX_HOURS}h con inicio jue/vie/sab y "
            f"fin sab/dom/lun; resto=anomalo (incluye festivos y fines de semana alargados)"
        ),
        "gaps_contiguous": report["gaps_contiguous"],
        "gaps_pausa_diaria": report["gaps_pausa_diaria"],
        "gaps_fin_de_semana": report["gaps_fin_de_semana"],
        "gaps_anomalo": report["gaps_anomalo"],
        "gaps_anomalo_detalle": report["gaps_anomalo_detalle"],
    }
    manifest_path = data_dir / f"{dataset_id}_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    return dataset_path, manifest_path


def verify_resolution(symbol: str, tf: str, dataset_path: Path) -> Optional[str]:
    """Confirma (no asume) que `resolve_dataset_file` con data_source='dukascopy' elige el
    consolidado. Devuelve None si no se puede verificar (sin proxy CME conocido)."""
    try:
        from scripts.mine import resolve_dataset_file, FONDEO_DUKASCOPY_PROXY
    except Exception as exc:  # import tardio: no romper el resto del script si falla
        return f"no verificable (fallo importando scripts.mine: {exc})"

    cme_symbol = None
    for cme, duka in FONDEO_DUKASCOPY_PROXY.items():
        if duka.lower() == symbol.lower():
            cme_symbol = cme
            break
    if cme_symbol is None:
        return "no verificable (sin proxy CME mapeado a este simbolo Dukascopy en scripts.mine)"

    chosen, _ = resolve_dataset_file(cme_symbol, tf, data_source="dukascopy")
    if chosen is None:
        return f"resolve_dataset_file no encontro nada para simbolo CME '{cme_symbol}'"
    if chosen.resolve() == dataset_path.resolve():
        return f"OK: resolve_dataset_file('{cme_symbol}', '{tf}', data_source='dukascopy') -> {chosen.name}"
    return f"AVISO: resolve_dataset_file eligio '{chosen.name}', NO el consolidado"


def print_report(report: dict, symbol: str, tf: str, dataset_path: Optional[Path]) -> None:
    r = report
    print(f"\n=== {symbol.upper()} {tf} ===")
    print(f"chunks encontrados: {r['chunks_found']}")
    print(f"barras crudas (suma de chunks, sin deduplicar): {r['raw_bar_count_sum']:,}")
    print(f"duplicados identicos deduplicados: {r['duplicates_identical']:,}")
    print(f"conflictos (mismo timestamp, distinto valor): {len(r['conflicts'])}")
    if r["conflicts"]:
        for c in r["conflicts"][:10]:
            print(f"  ! {c['timestamp_iso']} resuelto a '{c['resolved_to']}'")
    print(f"barras finales (unicas, ordenadas): {r['bar_count']:,}")
    if r["start_time_utc_ms"] is not None:
        start_iso = datetime.fromtimestamp(r["start_time_utc_ms"] / 1000.0, tz=timezone.utc).isoformat()
        end_iso = datetime.fromtimestamp(r["end_time_utc_ms"] / 1000.0, tz=timezone.utc).isoformat()
        print(f"rango: {start_iso} -> {end_iso}")
    total_trans = r["transitions_total"]
    print(f"transiciones entre barras: {total_trans:,}")
    print(f"  contiguas:      {r['gaps_contiguous']:,}")
    print(f"  pausa_diaria:   {r['gaps_pausa_diaria']:,}")
    print(f"  fin_de_semana:  {r['gaps_fin_de_semana']:,}")
    print(f"  anomalo:        {r['gaps_anomalo']:,}")
    if r["gaps_anomalo_detalle"]:
        print(f"  huecos anomalos (hasta {MAX_ANOMALOS_DETALLE}):")
        for g in r["gaps_anomalo_detalle"]:
            print(f"    {g['desde_utc']} -> {g['hasta_utc']}  ({g['horas']}h)")
    print(f"tiempo de proceso: {r['elapsed_seconds']}s")
    if dataset_path is not None:
        size_mb = dataset_path.stat().st_size / (1024 * 1024)
        print(f"escrito: {dataset_path.name} ({size_mb:.2f} MB)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--symbol", required=True, help="simbolo Dukascopy, p.ej. usa500idxusd (case-insensitive)")
    ap.add_argument("--tf", required=True, help="timeframe: 1m,5m,15m,1h,4h o 'all'")
    ap.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR), help="por defecto data/normalized")
    ap.add_argument("--dry-run", action="store_true", help="solo analiza e informa, no escribe nada en disco")
    args = ap.parse_args()

    data_dir = Path(args.data_dir)
    tfs = list(TIMEFRAMES.keys()) if args.tf.lower() == "all" else [args.tf.lower()]

    exit_code = 0
    for tf in tfs:
        try:
            report = consolidate(args.symbol, tf, data_dir)
        except FileNotFoundError as exc:
            print(f"[{args.symbol} {tf}] SIN CHUNKS: {exc}")
            continue
        except ConsolidationError as exc:
            print(f"[{args.symbol} {tf}] ERROR DE CONSISTENCIA (no se escribe nada): {exc}")
            exit_code = 1
            continue

        dataset_path = None
        if not args.dry_run:
            dataset_path, manifest_path = write_outputs(report, args.symbol, tf, data_dir)

        print_report(report, args.symbol, tf, dataset_path)

        if dataset_path is not None:
            verdict = verify_resolution(args.symbol, tf, dataset_path)
            print(f"verificacion resolve_dataset_file: {verdict}")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
