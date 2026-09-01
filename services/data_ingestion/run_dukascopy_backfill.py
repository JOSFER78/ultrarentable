"""Runner de backfill Dukascopy por trimestres, priorizado y reanudable.

Motivacion (diagnostico 2026-08-31): el cuello de botella medido en la descarga es la
latencia del propio servidor de Dukascopy (~15s por peticion exitosa, confirmado con
curl -w) mas backoff exponencial en los 503 intermitentes del feed gratuito bajo carga.
`dukascopy_feed.ingest()` ya soporta `concurrency>1` (I/O-bound, thread pool acotado)
para paliar eso, pero sigue teniendo un problema estructural distinto: NO persiste nada
hasta que TERMINA el rango completo pedido, y para un simbolo x 2023-01-01..2026-08-30
(~32.000 horas) eso significa acumular en RAM todos los ticks de ~3.5 anios antes de
escribir el primer dataset normalizado. En un VPS con el swap ya lleno, un solo reinicio
o OOM-kill a mitad de camino tira TODO el progreso normalizado de ese simbolo (aunque el
cache crudo .bi5 sobrevive, ver `download_hour`).

Este runner NO toca la logica de descarga/decodificacion (Regla #26: esto es ingesta de
datos, no el motor). Se limita a invocar `ingest()` en trozos trimestrales, marcando en
un fichero de estado JSON que trimestre esta ya persistido (checkpoint), de modo que:
  - un crash pierde como mucho el trimestre en curso (no el simbolo entero);
  - el cache crudo .bi5 hace que reintentar un trimestre truncado sea barato (las horas
    ya bajadas no se vuelven a pedir, ver `download_hour`);
  - los simbolos se procesan en orden de prioridad para FONDEO: los 3 indices primero
    (ES/NQ/YM via sus proxies CFD), luego metales/energia, luego forex.

Uso:
    python3 -m services.data_ingestion.run_dukascopy_backfill \
        --start 2023-01-01 --end 2026-08-30 --concurrency 3
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from services.data_ingestion.dukascopy_feed import SYMBOLS, ingest  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
PROGRESS_PATH = REPO_ROOT / "data" / "dukascopy_backfill_progress.json"

# Prioridad explicita para FONDEO: los 3 indices (proxies CME) primero. El resto sigue
# el orden natural del registro canonico (metales/energia, luego forex).
PRIORITY_ORDER: List[str] = [
    "USA500IDXUSD", "USATECHIDXUSD", "USA30IDXUSD",
] + [s for s in SYMBOLS if s not in ("USA500IDXUSD", "USATECHIDXUSD", "USA30IDXUSD")]


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
    args = parser.parse_args(argv)

    start = datetime.strptime(args.start, "%Y-%m-%d")
    end = datetime.strptime(args.end, "%Y-%m-%d")
    tfs = [t.strip() for t in args.timeframes.split(",") if t.strip()]
    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()] or PRIORITY_ORDER

    chunks = _quarter_chunks(start, end)
    progress = _load_progress()

    print(f"=== runner dukascopy: {len(symbols)} simbolos x {len(chunks)} trimestres, concurrency={args.concurrency} ===", flush=True)
    print(f"orden: {symbols}", flush=True)

    for symbol in symbols:
        if symbol not in SYMBOLS:
            print(f"AVISO: '{symbol}' no esta en el registro canonico, se omite.", file=sys.stderr, flush=True)
            continue
        done = set(progress.get(symbol, []))
        for key, c_start, c_end in chunks:
            if key in done:
                continue
            c_end_full = c_end.replace(hour=23)
            t0 = time.time()
            print(f"\n--- {symbol} {key} [{c_start.date()} -> {c_end.date()}] ---", flush=True)
            try:
                report = ingest(symbol, c_start, c_end_full, tfs, verbose=True, concurrency=args.concurrency)
            except Exception as exc:  # noqa: BLE001 - se registra, no se enmascara; el chunk NO se marca hecho
                print(f"ERROR {symbol} {key}: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
                continue
            elapsed = time.time() - t0
            print(
                f"  {symbol} {key}: status={report.get('status')} "
                f"horas_pedidas={report.get('hours_requested')} vacias={report.get('hours_empty')} "
                f"fallidas={report.get('hours_failed')} ticks={report.get('ticks_total')} "
                f"elapsed_s={elapsed:.1f}",
                flush=True,
            )
            # Un trimestre sin ni un tick (NO DATA) o con datos reales se considera
            # completado igualmente: el chunk se proceso integro (huecos legitimos
            # incluidos). Solo un ERROR (excepcion) de arriba deja el chunk pendiente.
            done.add(key)
            progress[symbol] = sorted(done)
            _save_progress(progress)

    print("\n=== runner dukascopy: backfill priorizado completo ===", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
