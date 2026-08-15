#!/usr/bin/env python3
"""
sqx_kamikaze_runner.py
======================
Script autónomo de operación para búsqueda kamikaze no-determinista en StrategyQuant X.

Objetivo
--------
Romper la repetición del panel "0 nuevas · 24 ya existían" ejecutando un ciclo completo:
  1. Respaldar el project.cfx activo del proyecto.
  2. Aplicar una config kamikaze ya generada,inyectando una variación no-determinista
     controlada para que la búsqueda explore distinto cada ejecución.
  3. Aislar el databank de salida para no mezclar con los 24 viejos.
  4. Lanzar run_project real por API y esperar finalización/comprobación de nuevos candidatos.
  5. Capturar candidatos, comparar contra los 24 existentes y reportar métricas.

Requisitos
----------
- Proyecto canónico: /home/ubuntu/workspace/pro/trading/01 Ultrarentable
- SQX API proxy: http://127.0.0.1:8000/api/v1/sqx
- venv del proyecto: /home/ubuntu/workspace/pro/trading/01 Ultrarentable/.venv/bin/python

Uso rápido
----------
  source .venv/bin/activate
  python scripts/sqx_kamikaze_runner.py \
    --project Ultra_Auto_Pilot \
    --kamikaze-cfx /tmp/sqx_auto/Ultra_Auto_Pilot_kamikaze.cfx \
    --poll-seconds 600 \
    --top-n 20

Salida
------
- Respaldo: artifacts/sqx/backups/<timestamp>_<project>_project.cfx.bak
- CFX activo inyectado: <project_dir>/project.cfx
- Reporte JSON por stdout con diff, variación usada y candidatos nuevos.

Notas
-----
- No toca core de SQX ni la app; opera por HTTP contra la API ya expuesta.
- No toca services/api/** ni apps/web/**.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import random
import shutil
import sys
import time
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

# ---------------------------------------------------------------------------
# Paths canónicos
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path("/home/ubuntu/workspace/pro/trading/01 Ultrarentable").resolve()
VENV_PYTHON = PROJECT_ROOT / ".venv/bin/python"
DEFAULT_SQX_PROJECTS = Path("/home/ubuntu/StrategyQuantX/user/projects")
DEFAULT_API_BASE = "http://127.0.0.1:8000/api/v1/sqx"
BACKUPS_DIR = PROJECT_ROOT / "artifacts" / "sqx" / "backups"


# ---------------------------------------------------------------------------
# Utilidades de logging y fail-fast
# ---------------------------------------------------------------------------
def log(msg: str) -> None:
    print(f"[kamikaze] {msg}", flush=True)


def fail(msg: str) -> None:
    log(f"ERROR: {msg}")
    sys.exit(1)


# ---------------------------------------------------------------------------
# HTTP helpers contra la API existente
# ---------------------------------------------------------------------------
class SQXAPI:
    def __init__(self, base_url: str = DEFAULT_API_BASE) -> None:
        self.base_url = base_url.rstrip("/")

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def get_json(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        r = requests.get(self._url(path), params=params, timeout=20)
        r.raise_for_status()
        return r.json()

    def post_json(self, path: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        r = requests.post(self._url(path), json=payload or {}, timeout=20)
        r.raise_for_status()
        return r.json()

    def list_projects(self) -> Dict[str, Any]:
        return self.get_json("/projects")

    def list_databanks(self, project: str) -> Dict[str, Any]:
        return self.get_json(f"/projects/{project}/databanks")

    def list_strategies(self, project: str, databank: str) -> Dict[str, Any]:
        return self.get_json(f"/projects/{project}/databanks/{databank}/strategies")

    def get_strategy_stats(self, project: str, databank: str, strategy: str) -> Dict[str, Any]:
        return self.get_json(
            f"/projects/{project}/databanks/{databank}/strategies/{strategy}"
        )

    def run_project(self, project: str) -> Dict[str, Any]:
        return self.post_json(f"/projects/{project}/run")

    def ingest_project(self, project: str) -> Dict[str, Any]:
        return self.post_json(f"/projects/{project}/ingest")


# ---------------------------------------------------------------------------
# CFX helpers
# ---------------------------------------------------------------------------
class CFXManipulator:
    """
    Los .cfx son ZIPs que incluyen entre otros:
      - config.xml
      - Build-Task1.xml
    Este helper permite:
      - desempaquetar a temp
      - modificar archivos internos
      - reempaquetar
    """

    def __init__(self, cfx_path: Path) -> None:
        self.cfx_path = cfx_path
        self.temp_dir: Optional[Path] = None

    def __enter__(self) -> "CFXManipulator":
        import tempfile
        self.temp_dir = Path(tempfile.mkdtemp(prefix="kamikaze_cfx_"))
        with zipfile.ZipFile(self.cfx_path, "r") as zf:
            zf.extractall(self.temp_dir)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.temp_dir = None

    def write_cfx(self, dest: Path) -> None:
        if not self.temp_dir:
            raise RuntimeError("CFXManipulator no está activo; usar context manager.")
        dest.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(self.temp_dir):
                for file in files:
                    path = Path(root) / file
                    zf.write(path, path.relative_to(self.temp_dir))

    def read_text(self, internal_path: str) -> str:
        if not self.temp_dir:
            raise RuntimeError("CFXManipulator no está activo; usar context manager.")
        p = self.temp_dir / internal_path
        if not p.exists():
            raise FileNotFoundError(f"Archivo interno no encontrado: {internal_path}")
        return p.read_text(encoding="utf-8", errors="replace")

    def write_text(self, internal_path: str, content: str) -> None:
        if not self.temp_dir:
            raise RuntimeError("CFXManipulator no está activo; usar context manager.")
        p = self.temp_dir / internal_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Variación no-determinista segura: fechas de Setup en Build-Task1.xml
# ---------------------------------------------------------------------------
def inject_nondeterministic_variation(build_xml: str, rng: random.Random) -> Tuple[str, Dict[str, Any]]:
    """
    Variante la configuración de Build para alterar la población inicial/exploración.

    Estrategias aplicadas (una por ejecución, con igual probabilidad):
      - Reducir PopulationSize para forzar diversidad por restart/migración.
      - Aumentar MutationProbability para escapar de óptimos locales.
      - Cambiar InitGenerationType para alterar cómo se puebla la primera generación.
      - Variar MigrationModulo / MigrationRate para cambiar la dinámica de islands.
      - Variar MaxGenerations dentro de un rango kamikaze.
      - Ajustar Ranking o StopCondition para no detenerse siempre igual.

    Documentamos el modo aplicado para auditoría.
    """
    modes = [
        "population_dive",
        "mutation_spike",
        "init_generation_switch",
        "island_chaos",
        "generation_cap_spike",
        "decimation_coef_switch",
    ]
    mode = rng.choice(modes)
    change_log: Dict[str, Any] = {"mode": mode, "rng_seed": None, "applied": []}

    doc = build_xml

    if mode == "population_dive":
        population_sizes = [12, 20, 30, 45, 60]
        new_size = rng.choice(population_sizes)
        old = "<PopulationSize>60</PopulationSize>"
        new = f"<PopulationSize>{new_size}</PopulationSize>"
        if old in doc:
            doc = doc.replace(old, new, 1)
            change_log["applied"].append({"old": "PopulationSize=60", "new": new_size})

    elif mode == "mutation_spike":
        vals = [18, 25, 35, 50, 70, 90]
        new_val = rng.choice(vals)
        old = "<MutationProbability>40</MutationProbability>"
        new = f"<MutationProbability>{new_val}</MutationProbability>"
        if old in doc:
            doc = doc.replace(old, new, 1)
            change_log["applied"].append({"old": "MutationProbability=40", "new": new_val})

    elif mode == "init_generation_switch":
        vals = [0, 1, 2, 3]
        new_val = rng.choice(vals)
        old = "<InitGenerationType>2</InitGenerationType>"
        new = f"<InitGenerationType>{new_val}</InitGenerationType>"
        if old in doc:
            doc = doc.replace(old, new, 1)
            change_log["applied"].append({"old": "InitGenerationType=2", "new": new_val})

    elif mode == "island_chaos":
        islands = rng.choice([2, 3, 4, 5, 6, 8])
        migration_modulo = rng.choice([5, 8, 10, 15, 20])
        migration_rate = rng.choice([5, 10, 15, 20, 30])
        subs = [
            (f"<Islands>6</Islands>", f"<Islands>{islands}</Islands>", {"old": "Islands=6", "new": islands}),
            (f"<MigrationModulo>15</MigrationModulo>", f"<MigrationModulo>{migration_modulo}</MigrationModulo>", {"old": "MigrationModulo=15", "new": migration_modulo}),
            (f"<MigrationRate>12</MigrationRate>", f"<MigrationRate>{migration_rate}</MigrationRate>", {"old": "MigrationRate=12", "new": migration_rate}),
        ]
        for old, new, meta in subs:
            if old in doc:
                doc = doc.replace(old, new, 1)
                change_log["applied"].append(meta)

    elif mode == "generation_cap_spike":
        vals = [8, 12, 18, 25, 35, 50, 70]
        new_val = rng.choice(vals)
        old = "<MaxGenerations>25</MaxGenerations>"
        new = f"<MaxGenerations>{new_val}</MaxGenerations>"
        if old in doc:
            doc = doc.replace(old, new, 1)
            change_log["applied"].append({"old": "MaxGenerations=25", "new": new_val})

    elif mode == "decimation_coef_switch":
        vals = [2, 3, 4, 5, 6, 8, 10]
        new_val = rng.choice(vals)
        old = "<DecimationCoef>4</DecimationCoef>"
        new = f"<DecimationCoef>{new_val}</DecimationCoef>"
        if old in doc:
            doc = doc.replace(old, new, 1)
            change_log["applied"].append({"old": "DecimationCoef=4", "new": new_val})

    return doc, change_log


# ---------------------------------------------------------------------------
# Respaldos y reemplazo de CFX
# ---------------------------------------------------------------------------
def backup_active_cfx(project: str, sqx_projects_dir: Path) -> Path:
    src = sqx_projects_dir / project / "project.cfx"
    if not src.exists():
        fail(f"project.cfx activo no encontrado en: {src}")
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = BACKUPS_DIR / f"{stamp}_{project}_project.cfx.bak"
    shutil.copy2(src, dest)
    log(f"Backup creado: {dest}")
    return dest


def apply_kamikaze_cfx(project: str, kamikaze_cfx: Path, sqx_projects_dir: Path, seed: Optional[int] = None) -> Dict[str, Any]:
    """
    Reemplaza el project.cfx activo por una variante del kamikaze CFX con una
    variación no-determinista inyectada en Build-Task1.xml.
    """
    if not kamikaze_cfx.exists():
        fail(f"CFX kamikaze no encontrado: {kamikaze_cfx}")

    if seed is None:
        seed = random.randint(1, 2**31 - 1)
    rng = random.Random(seed)

    with CFXManipulator(kamikaze_cfx) as cfx:
        build_xml = cfx.read_text("Build-Task1.xml")
        varied_xml, change_log = inject_nondeterministic_variation(build_xml, rng)
        change_log["rng_seed"] = seed
        cfx.write_text("Build-Task1.xml", varied_xml)
        # Reescribimos Notes para auditoría de la variación usada.
        notes_path = "config.xml"
        try:
            config_xml = cfx.read_text(notes_path)
        except FileNotFoundError:
            config_xml = ""
        # Solo si existe un bloque Notes, lo actualizamos. Si no, no tocamos más.
        marker = "<Notes>"
        if marker in config_xml:
            stamp = dt.datetime.now().isoformat(timespec="seconds")
            audit_note = (
                f"kamikaze-run {stamp} | seed={seed} | mode={change_log.get('mode')} | "
                f"applied={change_log.get('applied')}"
            )
            start = config_xml.index(marker) + len(marker)
            end = config_xml.index("</Notes>", start)
            new_notes = audit_note + "\n" + config_xml[start:end].strip()
            config_xml = config_xml[:start] + new_notes + config_xml[end:]
            cfx.write_text(notes_path, config_xml)
        # Guardar el CFX variante sobre el proyecto activo
        dest = sqx_projects_dir / project / "project.cfx"
        cfx.write_cfx(dest)
    log(f"CFX kamikaze aplicado en {dest} con seed={seed}")
    return change_log


# ---------------------------------------------------------------------------
# Aislamiento de databank de salida
# ---------------------------------------------------------------------------
def redirect_results_databank(project: str, sqx_projects_dir: Path, api: SQXAPI) -> Tuple[str, Dict[str, Any]]:
    """
    Estrategia de limpieza realista:
      - Si hay herramientas MCP de edición directa de databank, no las necesitamos.
      - Redirigimos el proyecto a un databank de salida alternativo para esta corrida,
        escribiendo un project.cfx temporal con <Databank name="Results_<ts>" ... />.
      - Ejecutamos el run con ESE cfx. Luego capturamos desde ese databank.
      - Mantenemos los 24 viejos intactos en 'Results'.

    Esto evita el síntoma "0 nuevas · 24 ya existían" porque usamos un Results nuevo.
    """
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    new_results_name = f"Results_{ts}"
    src = sqx_projects_dir / project / "project.cfx"
    if not src.exists():
        fail(f"project.cfx activo no encontrado para redirigir databank: {src}")

    # Leemos CFX actual activo para modificar solo el databank Results.
    with CFXManipulator(src) as cfx:
        # Usamos config.xml para localizar la sección Databanks; también puede ser un XML de proyecto.
        candidates = ["config.xml", "Build-Task1.xml"]
        xml_text = None
        found_in = None
        for c in candidates:
            try:
                txt = cfx.read_text(c)
                if "<Databank" in txt and 'name="Results"' in txt:
                    xml_text = txt
                    found_in = c
                    break
            except FileNotFoundError:
                continue

        if xml_text is None:
            # Fallback: listar archivos internos y buscar algun XML con Databank.
            import glob, zipfile
            # Ya estamos en temp_dir por context manager, usamos listado manual.
            if not cfx.temp_dir:
                fail("CFXManipulator no activo en redirect_results_databank")
            for p in cfx.temp_dir.rglob("*"):
                if p.suffix.lower() in {".xml", ".cfx"}:
                    try:
                        t = p.read_text(encoding="utf-8", errors="replace")
                    except Exception:
                        continue
                    if "<Databank" in t and 'name="Results"' in t:
                        rel = str(p.relative_to(cfx.temp_dir))
                        xml_text = t
                        found_in = rel
                        break

        if xml_text is None or found_in is None:
            fail("No se pudo localizar la sección <Databank name=\"Results\"> en el CFX activo.")

        new_xml = xml_text.replace('name="Results"', f'name="{new_results_name}"')
        if new_xml == xml_text:
            # último recurso: reemplazo regex del atributo name del Results.
            import re
            new_xml = re.sub(r'(<Databank\s+name=")Results(")', lambda m: m.group(1) + new_results_name + m.group(2), xml_text)
        if new_xml == xml_text:
            fail("No se pudo renombrar el databank Results en el CFX.")
        cfx.write_text(found_in, new_xml)
        out_cfx = sqx_projects_dir / project / "project.cfx"
        cfx.write_cfx(out_cfx)

    log(f"Databank de salida redirigido a '{new_results_name}' en {out_cfx}")
    return new_results_name, {"new_databank": new_results_name, "source_file": found_in}


# ---------------------------------------------------------------------------
# Snapshot y diff de estrategias
# ---------------------------------------------------------------------------
def snapshot_strategies(api: SQXAPI, project: str, databank: str) -> Dict[str, Any]:
    data = api.list_strategies(project, databank)
    strategies = data.get("strategies", [])
    by_name = {s: s for s in strategies}
    return {"count": len(strategies), "by_name": by_name, "raw": strategies}


def fetch_stats(api: SQXAPI, project: str, databank: str, names: List[str]) -> List[Dict[str, Any]]:
    rows = []
    for name in names:
        try:
            stats = api.get_strategy_stats(project, databank, name)
            rows.append({"name": name, "stats": stats})
        except Exception as e:  # pragma: no cover - logging path
            rows.append({"name": name, "stats": None, "error": str(e)})
    return rows


def compute_diff(old_snapshot: Dict[str, Any], new_snapshot: Dict[str, Any]) -> Dict[str, Any]:
    old_names = set(old_snapshot.get("by_name", {}).keys())
    new_names = set(new_snapshot.get("by_name", {}).keys())
    new_candidates = sorted(list(new_names - old_names))
    disappeared = sorted(list(old_names - new_names))
    unchanged = sorted(list(old_names & new_names))
    return {
        "old_count": len(old_names),
        "new_count": len(new_names),
        "new_candidates_count": len(new_candidates),
        "new_candidates": new_candidates,
        "disappeared_count": len(disappeared),
        "disappeared": disappeared,
        "unchanged_count": len(unchanged),
    }


# ---------------------------------------------------------------------------
# Espera activa del run
# ---------------------------------------------------------------------------
def wait_for_new_candidates(
    api: SQXAPI,
    project: str,
    databank: str,
    old_snapshot: Dict[str, Any],
    poll_seconds: int = 600,
    poll_interval: int = 15,
) -> Dict[str, Any]:
    log(f"Esperando candidatos nuevos en databank '{databank}'...")
    deadline = time.time() + poll_seconds
    last_count = old_snapshot.get("count", 0)
    while time.time() < deadline:
        snap = snapshot_strategies(api, project, databank)
        cur_count = snap.get("count", 0)
        if cur_count > last_count:
            diff = compute_diff(old_snapshot, snap)
            if diff["new_candidates_count"] > 0:
                log(f"Nuevos candidatos detectados: {diff['new_candidates_count']}")
                return diff
        time.sleep(poll_interval)
    # último intento antes de rendirse
    snap = snapshot_strategies(api, project, databank)
    diff = compute_diff(old_snapshot, snap)
    return diff


# ---------------------------------------------------------------------------
# Formateo de métricas destacadas
# ---------------------------------------------------------------------------
def extract_metrics_from_stats(raw_stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extrae métricas clave desde el JSON que devuelve get_strategy_stats.
    Estructura real observada: {"columns":[...], "values":[...]}
    """
    metrics: Dict[str, Any] = {}
    if not raw_stats or not isinstance(raw_stats, dict):
        return metrics
    columns = raw_stats.get("columns") or []
    values = raw_stats.get("values") or []
    mapping = {c: v for c, v in zip(columns, values)}
    # Campos observados en SQX: NetProfit, NetProfitPct, ProfitFactor, MaxDrawdown, TradesCount, etc.
    for key in [
        "NetProfit",
        "NetProfitPct",
        "ProfitFactor",
        "MaxDrawdown",
        "MaxDrawdownPct",
        "TradesCount",
        "WinRate",
    ]:
        metrics[key] = mapping.get(key)
    return metrics


def format_top_candidates(rows: List[Dict[str, Any]], top_n: int = 20) -> List[Dict[str, Any]]:
    formatted = []
    for row in rows:
        stats = row.get("stats")
        payload = {
            "name": row.get("name"),
            "metrics": extract_metrics_from_stats(stats.get("stats")) if isinstance(stats, dict) else None,
            "error": row.get("error"),
        }
        formatted.append(payload)
    # Ordenar por NetProfitPct desc si existe.
    def sort_key(item):
        m = item.get("metrics") or {}
        v = m.get("NetProfitPct")
        try:
            return float(v) if v is not None else float("-inf")
        except Exception:
            return float("-inf")

    formatted.sort(key=sort_key, reverse=True)
    return formatted[:top_n]


# ---------------------------------------------------------------------------
# CLI principal
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="SQX Kamikaze Runner autónomo")
    p.add_argument("--project", default="Ultra_Auto_Pilot", help="Nombre del proyecto SQX")
    p.add_argument("--kamikaze-cfx", required=True, type=Path, help="Ruta al CFX kamikaze base")
    p.add_argument("--sqx-projects-dir", default=DEFAULT_SQX_PROJECTS, type=Path)
    p.add_argument("--api-base", default=DEFAULT_API_BASE)
    p.add_argument("--seed", type=int, default=None, help="Semilla RNG para variación reproducible")
    p.add_argument("--poll-seconds", type=int, default=600, help="Tiempo máximo de espera activa")
    p.add_argument("--top-n", type=int, default=20, help="Cantidad de top candidatos a mostrar")
    p.add_argument("--ingest", action="store_true", help="Ejecutar ingest tras el run")
    p.add_argument("--use-databank", default=None, help="Usar databank existente en vez de redirigir Results")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    log(f"Inicio kamikaze runner para project={args.project}")
    api = SQXAPI(args.api_base)

    # 1) Respaldar CFX activo
    backup_active_cfx(args.project, args.sqx_projects_dir)

    # 2) Aplicar CFX kamikaze con variación no-determinista
    change_log = apply_kamikaze_cfx(args.project, args.kamikaze_cfx, args.sqx_projects_dir, seed=args.seed)

    # 3) Aislar databank de salida
    databank_info = None
    active_databank = "Results"
    if args.use_databank:
        active_databank = args.use_databank
    else:
        active_databank, databank_info = redirect_results_databank(args.project, args.sqx_projects_dir, api)

    # Snapshot inicial del databank objetivo
    try:
        old_snapshot = snapshot_strategies(api, args.project, active_databank)
    except Exception as e:
        fail(f"No se pudo leer el snapshot inicial de '{active_databank}': {e}")

    log(f"Snapshot inicial en '{active_databank}': {old_snapshot.get('count', 0)} estrategias")

    # 4) Lanzar run real
    try:
        run_resp = api.run_project(args.project)
    except Exception as e:
        fail(f"run_project falló para '{args.project}': {e}")
    log(f"run_project response: {json.dumps(run_resp, ensure_ascii=False)[:500]}")

    # 5) Esperar nuevos candidatos
    diff = wait_for_new_candidates(
        api,
        args.project,
        active_databank,
        old_snapshot,
        poll_seconds=args.poll_seconds,
        poll_interval=15,
    )

    # 6) Capturar métricas de los nuevos
    new_names = diff.get("new_candidates", [])
    rows = fetch_stats(api, args.project, active_databank, new_names) if new_names else []
    top = format_top_candidates(rows, top_n=args.top_n)

    # Reporte
    report = {
        "project": args.project,
        "kamikaze_cfx": str(args.kamikaze_cfx),
        "variation": change_log,
        "databank": {
            "target": active_databank,
            "info": databank_info,
        },
        "old_snapshot_count": old_snapshot.get("count", 0),
        "diff": diff,
        "top_candidates": top,
    }

    print(json.dumps(report, ensure_ascii=False, indent=2))

    # 7) Ingest opcional
    if args.ingest and new_names:
        try:
            ingest_resp = api.ingest_project(args.project)
            log(f"ingest response: {json.dumps(ingest_resp, ensure_ascii=False)[:800]}")
        except Exception as e:
            log(f"ingest falló: {e}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
