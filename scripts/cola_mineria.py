#!/usr/bin/env python3
"""F03.2 — Cola de minería gobernada para 4 cores (plan v4).

Reutiliza la infraestructura durable existente (services/queue/durable_job_queue.py, SQLite WAL,
watchdog) en vez de inventar otra cola. Cada trabajo MINE_CELL es una celda
(track, symbol, tf, profile) que se ejecuta como subproceso `nice -n 15 ionice -c 3` de
scripts/mine.py, con concurrencia limitada (2 por defecto) para no ahogar API + web + SQX.

Reanudable: la cola persiste en la BD canónica; las celdas COMPLETED no se re-encolan y un
worker caído deja trabajos IN_PROGRESS que se recuperan con --recuperar.

Uso:
    python scripts/cola_mineria.py encolar               # encola el universo de campana (dry: --ver)
    python scripts/cola_mineria.py trabajar               # worker con 2 celdas concurrentes
    python scripts/cola_mineria.py estado                 # censo de la cola y últimos resultados
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from contracts.queue_contracts import JobStatus, JobType  # noqa: E402
from services.queue.durable_job_queue import DurableJobQueue  # noqa: E402

RESULTADOS = REPO_ROOT / "orchestration" / "results" / "cola_mineria.jsonl"
CAMPANA02 = REPO_ROOT / "orchestration" / "results" / "campana_02_amplia.jsonl"

# Universo de la campana.
# AVISO 2026-08-31 (evidencia: orchestration/results/desbloqueo_tradfi_calidad_datos.md):
# el TF "4h" de TRADFI esta CONTAMINADO -- no se descarga, se remuestrea de 1h sin comprobar
# que la barra este completa (data_downloader.py:266). En ES, 750 de 3.714 barras 4h (20,2 %)
# se construyen con menos de 4 velas horarias y 145 con UNA sola: una barra de 1 hora
# etiquetada como barra de 4 horas, que corrompe cualquier indicador de rango/ATR.
# Para TRADFI/FONDEO usar SIEMPRE `--tfs 1h` (13.701 barras en ES, contiguidad real 95,45 %,
# solo 31 huecos anomalos que ademas son festivos de mercado). El default de abajo se conserva
# por compatibilidad con las campanas de cripto ya registradas.
CRIPTO = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "AVAXUSDT", "BNBUSDT", "LINKUSDT", "DOGEUSDT", "SUIUSDT"]
TRADFI = ["ES", "NQ", "YM", "RTY", "GC", "CL", "SI", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF"]
TRADFI_FONDEO = [s for s in TRADFI if s != "SI"]  # FONDEO solo micros verificados
TFS = ["4h"]
PERFIL = "amplio"

PRIORIDAD = {"fondeo": 7, "ultra": 5}  # FONDEO primero: 4x mas rapido y desbloquea meta-FONDEO


def celdas_universo(perfil: str, tfs: list[str] | None = None, solo_cripto: bool = False,
                     dataset_source: str = "auto") -> list[dict]:
    # solo_cripto: mandato del censo F03.1 (2026-08-31) — los datasets Yahoo de TRADFI tienen
    # 64-73% de cobertura y minar sobre ellos viola REAL-ONLY; TRADFI espera al backfill
    # Dukascopy verificado. Cripto Binance 1h/4h esta al 100% de cobertura.
    # dataset_source (Tarea B, 2026-09-01): se persiste en el payload del job y viaja hasta
    # mine.py via _lanzar(); ver DatasetSourceError/resolve_dataset_file en scripts/mine.py.
    celdas = []
    for track, universo in (("fondeo", TRADFI_FONDEO), ("ultra", CRIPTO + TRADFI)):
        if solo_cripto and track == "fondeo":
            continue
        for sym in universo:
            if solo_cripto and sym not in CRIPTO:
                continue
            for tf in (tfs or TFS):
                celdas.append({"track": track, "symbol": sym, "tf": tf, "profile": perfil,
                                "dataset_source": dataset_source})
    return celdas


def clave(payload: dict) -> tuple:
    return (payload.get("track"), payload.get("symbol"), payload.get("tf"), payload.get("profile"))


def celdas_ya_encoladas(q: DurableJobQueue) -> set[tuple]:
    ya = set()
    for status in (JobStatus.PENDING, JobStatus.IN_PROGRESS, JobStatus.COMPLETED, JobStatus.RETRYING):
        for job in q.list_jobs(status=status, limit=2000):
            if job.job_type == JobType.MINE_CELL:
                ya.add(clave(job.payload))
    return ya


def celdas_hechas_campana02() -> set[tuple]:
    hechas = set()
    if CAMPANA02.exists():
        for linea in CAMPANA02.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(linea)
                if r.get("estado") == "OK":
                    hechas.add((r["track"], r["symbol"], r["tf"], PERFIL))
            except (json.JSONDecodeError, KeyError):
                continue
    return hechas


def cmd_encolar(args) -> int:
    q = DurableJobQueue()
    ya = celdas_ya_encoladas(q)
    hechas = celdas_hechas_campana02() if args.respetar_campana02 else set()
    nuevas, omitidas = [], 0
    tfs = [t.strip() for t in args.tfs.split(",") if t.strip()] if args.tfs else None
    for c in celdas_universo(args.perfil, tfs=tfs, solo_cripto=args.solo_cripto,
                              dataset_source=args.dataset_source):
        if args.solo_track and c["track"] != args.solo_track:
            continue
        if clave(c) in ya or clave(c) in hechas:
            omitidas += 1
            continue
        nuevas.append(c)

    print(f"Celdas nuevas a encolar: {len(nuevas)} (omitidas por duplicado/hechas: {omitidas})")
    for c in nuevas:
        print(f"  {c['track']:>6} {c['symbol']:>9} {c['tf']:>4} perfil={c['profile']}")
    if args.ver:
        print("\n--ver: no se ha encolado nada.")
        return 0
    for c in nuevas:
        q.enqueue(JobType.MINE_CELL, c, priority=PRIORIDAD[c["track"]], max_attempts=2)
    print(f"Encoladas {len(nuevas)} celdas en durable_job_queue (BD canónica).")
    return 0


def _comando_mine(payload: dict, max_candidates: int = 2000) -> list[str]:
    """Construye el comando exacto de mine.py para una celda.

    Factorizado fuera de _lanzar() para poder trazarlo (tests/verificación) sin lanzar el
    subproceso real. payload.get(..., default) en vez de indexación directa: los jobs ya
    encolados antes de la Tarea B (2026-09-01) no tienen "dataset_source" en su payload y
    deben seguir comportándose como "auto" (comportamiento histórico, sin cambios).
    """
    return [
        "nice", "-n", "15", "ionice", "-c", "3",
        sys.executable, str(REPO_ROOT / "scripts" / "mine.py"),
        "--track", payload["track"], "--symbol", payload["symbol"],
        "--tf", payload["tf"], "--profile", payload["profile"],
        "--max-candidates", str(int(payload.get("max_candidates") or max_candidates)),
        "--dataset-source", str(payload.get("dataset_source") or "auto"),
    ]


def _lanzar(payload: dict, max_candidates: int = 2000) -> subprocess.Popen:
    cmd = _comando_mine(payload, max_candidates)
    return subprocess.Popen(
        cmd, cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )


def cmd_trabajar(args) -> int:
    q = DurableJobQueue()
    if args.recuperar:
        rep = q.recover_orphaned_jobs(max_in_progress_seconds=args.huerfano_seg)
        if getattr(rep, "recovered_jobs", None):
            print(f"Recuperados {len(rep.recovered_jobs)} trabajos huérfanos -> RETRYING")

    RESULTADOS.parent.mkdir(parents=True, exist_ok=True)
    activos: dict[str, dict] = {}  # job_id -> {proc, payload, t0}
    procesadas = 0
    print(f"Worker de minería: concurrencia={args.concurrencia}, nice=15, ionice=idle. Ctrl-C para parar.")

    try:
        while True:
            # 0) Heartbeat: sin esto, el watchdog externo (umbral 300s) marca RETRYING los
            #    trabajos vivos de minería y provoca duplicados (incidente 2026-08-31 14:08).
            if activos:
                q.heartbeat(list(activos.keys()))

            # 1) Cosechar terminados
            for job_id in list(activos):
                info = activos[job_id]
                rc = info["proc"].poll()
                if rc is None:
                    continue
                salida = (info["proc"].stdout.read() or "").strip().splitlines()
                cola_salida = " | ".join(salida[-3:])[:500] if salida else "(sin salida)"
                seg = round(time.time() - info["t0"], 1)
                reg = {
                    "ts": datetime.now(timezone.utc).isoformat(), "job_id": job_id,
                    **info["payload"], "rc": rc, "segundos": seg, "cola_salida": cola_salida,
                }
                with RESULTADOS.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(reg, ensure_ascii=False) + "\n")
                if rc == 0:
                    q.complete_job(job_id, outcome_summary=cola_salida[:200])
                    print(f"OK   {info['payload']['track']:>6} {info['payload']['symbol']:>9} "
                          f"{info['payload']['tf']:>4} ({seg}s)")
                else:
                    q.fail_job(job_id, error_message=f"rc={rc}: {cola_salida[:300]}")
                    print(f"FAIL {info['payload']['track']:>6} {info['payload']['symbol']:>9} "
                          f"{info['payload']['tf']:>4} rc={rc} ({seg}s)")
                del activos[job_id]
                procesadas += 1

            if args.max_celdas and procesadas >= args.max_celdas:
                print(f"Límite --max-celdas={args.max_celdas} alcanzado.")
                break

            # 2) Rellenar huecos de concurrencia
            while len(activos) < args.concurrencia:
                job = q.fetch_next_job()
                if job is None:
                    break
                if job.job_type != JobType.MINE_CELL:
                    q.fail_job(job.job_id, error_message="Worker de minería: job_type no soportado")
                    continue
                # Guardia anti-duplicado: si un watchdog externo re-encoló una celda que este
                # worker YA está minando, no se lanza un segundo proceso sobre la misma celda.
                if clave(job.payload) in {clave(i["payload"]) for i in activos.values()}:
                    print(f"..   celda ya activa, se ignora duplicado (job {job.job_id})")
                    continue
                activos[job.job_id] = {"proc": _lanzar(job.payload, args.max_candidates), "payload": job.payload, "t0": time.time()}
                print(f"->   {job.payload['track']:>6} {job.payload['symbol']:>9} "
                      f"{job.payload['tf']:>4} (job {job.job_id})")

            if not activos:
                print("Cola vacía: worker terminado.")
                break
            time.sleep(10)
    except KeyboardInterrupt:
        print("\nInterrumpido. Los trabajos en curso quedan IN_PROGRESS; "
              "reanuda con `trabajar --recuperar` (los subprocesos siguen o mueren con el TTY).")
        for info in activos.values():
            info["proc"].terminate()
        return 130
    return 0


def cmd_estado(args) -> int:
    q = DurableJobQueue()
    print("Cola durable (MINE_CELL):")
    for status in JobStatus:
        jobs = [j for j in q.list_jobs(status=status, limit=2000) if j.job_type == JobType.MINE_CELL]
        if jobs:
            print(f"  {status.value:>12}: {len(jobs)}")
    if RESULTADOS.exists():
        lineas = RESULTADOS.read_text(encoding="utf-8").splitlines()
        print(f"\nÚltimos resultados ({RESULTADOS.name}, {len(lineas)} total):")
        for linea in lineas[-5:]:
            try:
                r = json.loads(linea)
                print(f"  {r.get('track'):>6} {r.get('symbol'):>9} {r.get('tf'):>4} "
                      f"rc={r.get('rc')} {r.get('segundos')}s")
            except json.JSONDecodeError:
                continue
    return 0


def cmd_cancelar(args) -> int:
    import sqlite3 as _sq
    from services.api.app.config import STATE_DB_PATH
    from datetime import datetime as _dt, timezone as _tz
    conn = _sq.connect(str(STATE_DB_PATH), timeout=15.0)
    try:
        with conn:
            cur = conn.execute(
                "UPDATE durable_job_queue SET status='CANCELLED', error_message=?, updated_at_utc=? "
                "WHERE job_type='MINE_CELL' AND status IN ('PENDING','RETRYING','IN_PROGRESS')",
                (f"Cancelado por orquestador: {args.motivo}"[:400],
                 _dt.now(_tz.utc).isoformat()),
            )
            print(f"Cancelados {cur.rowcount} trabajos MINE_CELL (motivo registrado).")
        return 0
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_enc = sub.add_parser("encolar", help="Encola las celdas del universo de campana")
    # 5.14.0 (F03.3): "arquetipos" mina SOLO las 4 familias nuevas (mine.py::build_candidate_
    # search_configs). Sin este choice la re-campana de arquetipos no se podia encolar.
    p_enc.add_argument("--perfil", default=PERFIL, choices=["default", "amplio", "champions", "arquetipos"])
    p_enc.add_argument("--solo-track", choices=["ultra", "fondeo"], default=None)
    p_enc.add_argument("--ver", action="store_true", help="Muestra qué se encolaría, sin encolar")
    p_enc.add_argument("--respetar-campana02", action=argparse.BooleanOptionalAction, default=True,
                       help="Omite celdas ya OK en campana_02_amplia.jsonl")
    p_enc.add_argument("--tfs", default=None, help="TFs separados por coma (p.ej. '4h,1h'); por defecto los del universo")
    p_enc.add_argument("--solo-cripto", action="store_true",
                       help="Solo celdas cripto (mandato censo F03.1: TRADFI bloqueado hasta backfill Dukascopy)")
    p_enc.add_argument("--dataset-source", dest="dataset_source", default="auto",
                       choices=["auto", "dukascopy"],
                       help=(
                           "Fuente de dataset a propagar a mine.py --dataset-source por celda "
                           "(Tarea B, 2026-09-01). 'auto' (default): sin cambios de comportamiento. "
                           "'dukascopy': activa el proxy CFD Dukascopy para FONDEO (ES->USA500IDXUSD, "
                           "etc.); ver FONDEO_DUKASCOPY_PROXY en scripts/mine.py."
                       ))
    p_enc.set_defaults(fn=cmd_encolar)

    p_tra = sub.add_parser("trabajar", help="Worker: ejecuta celdas de la cola")
    p_tra.add_argument("--concurrencia", type=int, default=2)
    p_tra.add_argument("--max-candidates", type=int, default=2000,
                       help="Configuraciones máximas por celda (default 2000, como campana_02)")
    p_tra.add_argument("--max-celdas", type=int, default=0, help="0 = sin límite")
    p_tra.add_argument("--recuperar", action=argparse.BooleanOptionalAction, default=True)
    p_tra.add_argument("--huerfano-seg", type=int, default=4 * 3600,
                       help="Umbral para considerar huérfano un IN_PROGRESS")
    p_tra.set_defaults(fn=cmd_trabajar)

    p_est = sub.add_parser("estado", help="Censo de la cola y últimos resultados")
    p_est.set_defaults(fn=cmd_estado)

    p_can = sub.add_parser("cancelar", help="Cancela trabajos MINE_CELL pendientes/en reintento")
    p_can.add_argument("--motivo", required=True, help="Razón de la cancelación (queda en error_message)")
    p_can.set_defaults(fn=cmd_cancelar)

    args = parser.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
