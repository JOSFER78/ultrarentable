"""Runner de backfill Dukascopy por trimestres, idempotente y priorizado.

Descarga por trimestres en staging temporal; salta chunks con manifiesto
valido, nunca degrada datasets existentes (peores van a cuarentena) y
actualiza progreso con soporte para --force y --dry-run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from services.data_ingestion.dukascopy_feed import (  # noqa: E402
    OUTPUT_DIR,
    SYMBOLS,
    ingest,
    write_dataset_files,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PROGRESS_PATH = REPO_ROOT / "data" / "dukascopy_backfill_progress.json"
QUARANTINE_DIR = REPO_ROOT / "data" / "quarantine"
STAGING_SUBDIR = ".staging_backfill"

# Prioridad explicita para FONDEO: los 3 indices (proxies CME) primero. El resto sigue
# el orden natural del registro canonico (metales/energia, luego forex).
PRIORITY_ORDER: List[str] = [
    "USA500IDXUSD", "USATECHIDXUSD", "USA30IDXUSD",
] + [s for s in SYMBOLS if s not in ("USA500IDXUSD", "USATECHIDXUSD", "USA30IDXUSD")]


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def _ms(dt: datetime) -> int:
    return int(dt.replace(tzinfo=timezone.utc).timestamp() * 1000)


def _find_existing(
    out_dir: Path, symbol: str, tf: str, c_start: datetime, c_end: datetime
) -> Optional[Tuple[Path, Path, Dict[str, object]]]:
    pattern = f"ds_dukascopy_{symbol.lower()}_{tf}_*_manifest.json"
    candidates: List[Tuple[Path, Path, Dict[str, object]]] = []
    min_ms = _ms(c_start)
    max_ms = _ms(c_end + timedelta(days=1)) - 1

    for mf_path in out_dir.glob(pattern):
        if "_consolidated" in mf_path.name:
            continue
        try:
            m = json.loads(mf_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        start_ms = m.get("start_time_utc_ms")
        if start_ms is not None and min_ms <= start_ms <= max_ms:
            data_name = mf_path.name.replace("_manifest.json", ".json")
            data_path = mf_path.with_name(data_name)
            candidates.append((data_path, mf_path, m))

    if not candidates:
        return None

    if len(candidates) > 1:
        candidates.sort(key=lambda item: int(item[2].get("bar_count", 0)), reverse=True)
        best = candidates[0]
        print(
            f"AVISO {symbol} {tf}: multiples manifiestos existentes ({len(candidates)}), "
            f"seleccionando el de mayor bar_count ({best[2].get('bar_count', 0)}) -> {best[1].name}",
            file=sys.stderr,
            flush=True,
        )
        return best

    return candidates[0]


def _estado_existente(
    data_path: Optional[Path],
    manifest_path: Optional[Path],
    manifest: Optional[Dict[str, object]],
) -> str:
    if manifest_path is None or not manifest_path.exists() or manifest is None:
        return "ausente"
    if data_path is None or not data_path.exists():
        return "sin_datos"
    expected_sha = manifest.get("checksum_sha256")
    try:
        actual_sha = _sha256_file(data_path)
    except OSError:
        return "invalido"
    if expected_sha and actual_sha.lower() == str(expected_sha).lower():
        return "valido"
    return "invalido"


def _es_mejor_o_igual(nuevo: Dict[str, object], viejo: Dict[str, object]) -> bool:
    n_hf = int(nuevo.get("hours_failed", 0))
    v_hf = int(viejo.get("hours_failed", 0))
    n_bc = int(nuevo.get("bar_count", 0))
    v_bc = int(viejo.get("bar_count", 0))
    return n_hf <= v_hf and n_bc >= v_bc


def _a_cuarentena(paths: List[Path], quarantine_dir: Path, motivo: str) -> Path:
    quarantine_dir = Path(quarantine_dir)
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y%m%d")
    target_dir = quarantine_dir / f"backfill_{motivo}_{date_str}"
    if target_dir.exists():
        time_str = now.strftime("%Y%m%dT%H%M%S")
        target_dir = quarantine_dir / f"backfill_{motivo}_{date_str}.{time_str}"
        idx = 1
        while target_dir.exists():
            target_dir = quarantine_dir / f"backfill_{motivo}_{date_str}.{time_str}_{idx}"
            idx += 1

    target_dir.mkdir(parents=True, exist_ok=True)
    manifest_txt = target_dir / "MANIFEST_SHA256.txt"
    entries: List[str] = []

    for p in paths:
        if p and p.exists():
            sha = _sha256_file(p)
            dest = target_dir / p.name
            if dest.exists():
                dest.unlink()
            shutil.move(str(p), str(dest))
            entries.append(f"{p.name} | {sha}\n")

    if entries:
        with open(manifest_txt, "a", encoding="utf-8") as f:
            for entry in entries:
                f.write(entry)

    return target_dir


def process_chunk(
    symbol: str,
    key: str,
    c_start: datetime,
    c_end: datetime,
    tfs: List[str],
    *,
    force: bool = False,
    dry_run: bool = False,
    concurrency: int = 3,
    ingest_fn=ingest,
    out_dir: Path = OUTPUT_DIR,
    quarantine_dir: Path = QUARANTINE_DIR,
) -> Dict[str, object]:
    out_dir = Path(out_dir)
    quarantine_dir = Path(quarantine_dir)

    estados: Dict[str, str] = {}
    pendientes: List[Tuple[str, str, str, Optional[Tuple[Path, Path, Dict[str, object]]]]] = []

    # (a) Evaluar cada timeframe
    for tf in tfs:
        existing = _find_existing(out_dir, symbol, tf, c_start, c_end)
        if existing is not None:
            data_path, manifest_path, manifest = existing
            estado = _estado_existente(data_path, manifest_path, manifest)
        else:
            data_path, manifest_path, manifest = None, None, None
            estado = "ausente"

        if estado == "valido" and not force:
            dataset_id = manifest.get("dataset_id", "")
            bar_count = manifest.get("bar_count", 0)
            hours_failed = manifest.get("hours_failed", 0)
            print(
                f"SKIP {symbol} {key} {tf}: manifiesto valido ({dataset_id}, {bar_count} barras, {hours_failed} horas fallidas)",
                flush=True,
            )
            estados[tf] = "saltado"
        else:
            if force:
                motivo = "--force"
            elif estado == "ausente":
                motivo = "sin manifiesto"
            elif estado == "sin_datos":
                motivo = f"manifiesto sin fichero de datos ({manifest_path.name})"
            elif estado == "invalido":
                motivo = f"manifiesto invalido: sha256 no coincide con el contenido ({manifest_path.name})"
            else:
                motivo = "desconocido"
            pendientes.append((tf, motivo, estado, existing))
            estados[tf] = "pendiente"

    # (b) Si no hay pendientes o dry_run
    if not pendientes:
        return {"estados": estados, "hours_failed": None}

    if dry_run:
        for tf, motivo, _estado, _existing in pendientes:
            print(f"PENDIENTE {symbol} {key} {tf}: {motivo}", flush=True)
        return {"estados": estados, "hours_failed": None}

    # (c) Avisos y descarga en staging
    for tf, motivo, estado, _existing in pendientes:
        if estado in ("sin_datos", "invalido"):
            print(f"AVISO {symbol} {key} {tf}: {motivo}, se trata como inexistente", flush=True)

    tfs_pendientes = [tf for tf, _, _, _ in pendientes]
    staging = out_dir / STAGING_SUBDIR / f"{symbol}_{key}"
    staging.mkdir(parents=True, exist_ok=True)
    print(f"DESCARGA {symbol} {key}: tfs pendientes={tfs_pendientes}", flush=True)

    c_end_full = c_end.replace(hour=23)
    try:
        report = ingest_fn(
            symbol,
            c_start,
            c_end_full,
            tfs_pendientes,
            verbose=True,
            concurrency=concurrency,
            output_dir=staging,
        )
    except Exception as exc:
        print(f"ERROR {symbol} {key}: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        for tf in tfs_pendientes:
            estados[tf] = "error"
        return {"estados": estados, "hours_failed": None}

    hours_failed = report.get("hours_failed")

    # (d) Evaluar descargas y aplicar cuarentena / sustitución
    datasets = report.get("datasets", {})
    for tf, _motivo, estado_viejo, existing in pendientes:
        ds = datasets.get(tf)
        if not ds or not isinstance(ds, dict) or not ds.get("dataset_id"):
            estados[tf] = "no_data"
            continue

        dataset_id = str(ds["dataset_id"])
        staged_manifest_path = staging / f"{dataset_id}_manifest.json"
        staged_data_path = staging / f"{dataset_id}.json"

        if not staged_manifest_path.exists() or not staged_data_path.exists():
            estados[tf] = "no_data"
            continue

        try:
            staged_manifest = json.loads(staged_manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            estados[tf] = "error"
            continue

        # Si el existente era valido (solo con force) y NO es mejor o igual:
        if estado_viejo == "valido" and existing is not None:
            _old_data, _old_mf_path, old_manifest = existing
            if not _es_mejor_o_igual(staged_manifest, old_manifest):
                q_dir = _a_cuarentena([staged_data_path, staged_manifest_path], quarantine_dir, "rechazado")
                v_bars = old_manifest.get("bar_count", 0)
                n_bars = staged_manifest.get("bar_count", 0)
                v_hf = old_manifest.get("hours_failed", 0)
                n_hf = staged_manifest.get("hours_failed", 0)
                print(
                    f"RECHAZADO {symbol} {key} {tf}: peor que el existente "
                    f"(barras {v_bars}->{n_bars}, horas fallidas {v_hf}->{n_hf}) -> {q_dir}",
                    flush=True,
                )
                estados[tf] = "rechazado"
                continue

        # En otro caso: si existe par viejo con NOMBRE distinto -> cuarentena sustituido
        if existing is not None:
            old_data_path, old_manifest_path, _old_m = existing
            if old_manifest_path.name != staged_manifest_path.name:
                old_files = [p for p in (old_data_path, old_manifest_path) if p is not None and p.exists()]
                if old_files:
                    _a_cuarentena(old_files, quarantine_dir, "sustituido")

        # Mover staged a out_dir (mismo nombre = sobrescribe)
        target_data = out_dir / staged_data_path.name
        target_manifest = out_dir / staged_manifest_path.name
        if target_data.exists():
            target_data.unlink()
        shutil.move(str(staged_data_path), str(target_data))
        if target_manifest.exists():
            target_manifest.unlink()
        shutil.move(str(staged_manifest_path), str(target_manifest))

        n_bars = staged_manifest.get("bar_count", len(staged_manifest.get("bars", [])))
        hf = staged_manifest.get("hours_failed", 0)
        sha = str(staged_manifest.get("checksum_sha256", ""))
        sha_16 = sha[:16] if sha else ""
        print(
            f"ESCRITO {symbol} {key} {tf}: {dataset_id} ({n_bars} barras, {hf} horas fallidas, sha256 {sha_16}...)",
            flush=True,
        )
        estados[tf] = "escrito"

    try:
        staging.rmdir()
    except OSError:
        pass
    try:
        (out_dir / STAGING_SUBDIR).rmdir()
    except OSError:
        pass

    return {"estados": estados, "hours_failed": hours_failed}


def _quarter_chunks(start: datetime, end: datetime) -> List[Tuple[str, datetime, datetime]]:
    """Trocea [start, end] en trimestres calendario. Devuelve (clave, inicio, fin_incl)."""
    chunks: List[Tuple[str, datetime, datetime]] = []
    cur = start.replace(hour=0, minute=0, second=0, microsecond=0)
    while cur <= end:
        q = (cur.month - 1) // 3
        q_start_month = q * 3 + 1
        next_q_month = q_start_month + 3
        if next_q_month > 12:
            chunk_end = datetime(cur.year, 12, 31)
        else:
            chunk_end = datetime(cur.year, next_q_month, 1) - timedelta(days=1)
        chunk_end = min(chunk_end, end)
        key = f"{cur.year}-Q{q + 1}"
        chunks.append((key, cur, chunk_end))
        cur = chunk_end + timedelta(days=1)
    return chunks


def _load_progress() -> dict:
    if PROGRESS_PATH.exists():
        try:
            return json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_progress(progress: dict) -> None:
    PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = PROGRESS_PATH.with_suffix(".json.part")
    tmp.write_text(json.dumps(progress, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(PROGRESS_PATH)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", default="2023-01-01")
    parser.add_argument("--end", default="2026-08-30")
    parser.add_argument("--concurrency", type=int, default=3)
    parser.add_argument("--timeframes", default="1m,5m,15m,1h,4h")
    parser.add_argument("--symbols", default="", help="lista separada por comas para acotar; vacio = todos, en orden de prioridad")
    parser.add_argument("--force", action="store_true", help="fuerza la descarga aunque el manifiesto sea valido")
    parser.add_argument("--dry-run", action="store_true", help="muestra que chunks estan pendientes sin descargar ni escribir nada")
    args = parser.parse_args(argv)

    start = datetime.strptime(args.start, "%Y-%m-%d")
    end = datetime.strptime(args.end, "%Y-%m-%d")
    tfs = [t.strip() for t in args.timeframes.split(",") if t.strip()]
    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()] or PRIORITY_ORDER

    chunks = _quarter_chunks(start, end)
    progress = _load_progress() if not args.dry_run else {}

    print(f"=== runner dukascopy: {len(symbols)} simbolos x {len(chunks)} trimestres, concurrency={args.concurrency} ===", flush=True)
    print(f"orden: {symbols}", flush=True)

    if "_resumen" not in progress:
        progress["_resumen"] = {}

    for symbol in symbols:
        if symbol not in SYMBOLS:
            print(f"AVISO: '{symbol}' no esta en el registro canonico, se omite.", file=sys.stderr, flush=True)
            continue

        if symbol not in progress["_resumen"]:
            progress["_resumen"][symbol] = {
                tf: {"saltados": 0, "escritos": 0, "rechazados": 0, "con_horas_fallidas": 0}
                for tf in tfs
            }

        done_chunks = set(progress.get(symbol, []))
        for key, c_start, c_end in chunks:
            res = process_chunk(
                symbol,
                key,
                c_start,
                c_end,
                tfs,
                force=args.force,
                dry_run=args.dry_run,
                concurrency=args.concurrency,
            )
            estados = res["estados"]
            hours_failed = res["hours_failed"]

            if not args.dry_run:
                for tf, st in estados.items():
                    if tf not in progress["_resumen"][symbol]:
                        progress["_resumen"][symbol][tf] = {
                            "saltados": 0, "escritos": 0, "rechazados": 0, "con_horas_fallidas": 0
                        }
                    resumen_tf = progress["_resumen"][symbol][tf]
                    if st == "saltado":
                        resumen_tf["saltados"] += 1
                    elif st == "escrito":
                        resumen_tf["escritos"] += 1
                        if hours_failed is not None and hours_failed > 0:
                            resumen_tf["con_horas_fallidas"] += 1
                    elif st == "rechazado":
                        resumen_tf["rechazados"] += 1

                all_done = all(st in ("saltado", "escrito", "rechazado", "no_data") for st in estados.values())
                if all_done:
                    done_chunks.add(key)
                progress[symbol] = sorted(done_chunks)
                _save_progress(progress)

    if not args.dry_run:
        print("\n=== RESUMEN BACKFILL DUKASCOPY ===", flush=True)
        for sym in symbols:
            if sym in progress.get("_resumen", {}):
                print(f"[{sym}]", flush=True)
                for tf in tfs:
                    stats = progress["_resumen"][sym].get(tf, {})
                    s = stats.get("saltados", 0)
                    e = stats.get("escritos", 0)
                    r = stats.get("rechazados", 0)
                    hf = stats.get("con_horas_fallidas", 0)
                    print(f"  {tf:>4s}: {s} saltados, {e} escritos ({hf} con horas fallidas), {r} rechazados", flush=True)

    print("\n=== runner dukascopy: backfill priorizado completo ===", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

