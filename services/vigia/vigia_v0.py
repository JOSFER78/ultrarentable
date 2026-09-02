"""services/vigia/vigia_v0.py

Vigia V0: Centinela determinista de solo lectura para monitorizacion diaria.

MANDATO ESTRICTO:
- SOLO LECTURA (Zero-Mocks, Real-Only).
- Prohibido modificar estado de base de datos o emitir ordenes a brokers.
- Prohibidas peticiones a internet; unicamentee inspeccion local (localhost y ficheros en disco).
- Si una fuente no esta disponible o no contiene datos, reporta explicitamente
  estado='NO DATA' junto con el motivo detallado (cero silencios complacientes o valores sinteticos).
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import socket
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

VIGIA_VERSION = "0.1.0"
DEFAULT_OUT_DIR = Path("orchestration/results/vigia")


def _obtener_repo_root() -> Path:
    """Calcula la raiz del repositorio de forma determinista."""
    try:
        actual = Path(__file__).resolve()
    except OSError:
        actual = Path(__file__).absolute()
    for parent in [actual, *actual.parents]:
        if (parent / "REAL_ONLY_START_HERE.md").exists() or (parent / "pyproject.toml").exists():
            return parent
    return Path.cwd()


def _resolver_ruta_bd_default() -> Path:
    """Resuelve la ruta a la base de datos sqlite canonica."""
    try:
        from services.api.app.config import STATE_DB_PATH
        return Path(STATE_DB_PATH)
    except Exception:
        db_env = os.getenv("STATE_DB_PATH") or os.getenv("ULTRARENTABLE_DB_PATH")
        if db_env:
            return Path(db_env)
        user_canonical = Path.home() / ".local/state/ultrarentable/ultrarentable.sqlite3"
        if user_canonical.exists():
            return user_canonical
        return _obtener_repo_root() / "data/state/ultrarentable.sqlite3"


# ─────────────────────────────────────────────────────────────────────────────
# 1. FUENTE: API LOCAL (:8000)
# ─────────────────────────────────────────────────────────────────────────────

def obtener_estado_api(host: str = "127.0.0.1", port: int = 8000, timeout: float = 2.0) -> Dict[str, Any]:
    """Inspecciona la salud de la API local en localhost:port."""
    url = f"http://{host}:{port}/"
    t0 = time.perf_counter()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": f"Ultrarentable-Vigia/{VIGIA_VERSION}"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
            codigo = resp.status
            body = resp.read()
            try:
                data = json.loads(body.decode("utf-8"))
            except Exception:
                data = {}
            return {
                "estado": "ONLINE",
                "codigo_http": codigo,
                "latencia_ms": elapsed_ms,
                "url": url,
                "version_api": data.get("version", "NO DATA"),
                "engine_version": data.get("engine_version", "NO DATA"),
                "runtime_mode": data.get("runtime_mode", "NO DATA"),
                "autonomous_runtime_enabled": data.get("autonomous_runtime_enabled", False),
            }
    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        return {
            "estado": "NO DATA",
            "motivo": f"No se pudo conectar a la API local en {url} ({exc})",
            "latencia_ms": elapsed_ms,
            "url": url,
        }


# ─────────────────────────────────────────────────────────────────────────────
# 2. FUENTE: SERVICIOS SYSTEMD
# ─────────────────────────────────────────────────────────────────────────────

SERVICIOS_OBJETIVO = [
    "ultrarentable-api.service",
    "ultrarentable-discovery.service",
    "sqx.service",
    "ultrarentable-vigia.service",
]


def obtener_estado_systemd(servicios: Optional[List[str]] = None) -> Dict[str, Any]:
    """Inspecciona el estado de los servicios systemd en host Linux."""
    targets = servicios or SERVICIOS_OBJETIVO
    systemctl_path = shutil.which("systemctl")
    if not systemctl_path:
        return {
            "estado": "NO DATA",
            "motivo": "systemctl no disponible en este entorno (sistema no-Linux o sin systemd)",
            "servicios": {svc: {"estado": "NO DATA", "motivo": "systemctl no disponible"} for svc in targets},
        }

    resultados_servicios: Dict[str, Any] = {}
    for svc in targets:
        try:
            cmd = [
                systemctl_path,
                "show",
                svc,
                "--property=Id,ActiveState,SubState,UnitFileState,MainPID,ExecMainStatus,ExecMainCode,Description",
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=3.0, check=False)
            if proc.returncode == 0 and proc.stdout.strip():
                props: Dict[str, str] = {}
                for line in proc.stdout.splitlines():
                    if "=" in line:
                        k, v = line.split("=", 1)
                        props[k.strip()] = v.strip()
                active_state = props.get("ActiveState", "unknown")
                sub_state = props.get("SubState", "unknown")
                unit_file_state = props.get("UnitFileState", "unknown")
                main_pid = props.get("MainPID", "0")
                description = props.get("Description", "")

                is_active = active_state == "active"
                resultados_servicios[svc] = {
                    "estado": "ACTIVO" if is_active else "INACTIVO",
                    "active_state": active_state,
                    "sub_state": sub_state,
                    "unit_file_state": unit_file_state,
                    "main_pid": int(main_pid) if main_pid.isdigit() else main_pid,
                    "descripcion": description,
                }
            else:
                resultados_servicios[svc] = {
                    "estado": "NO DATA",
                    "motivo": f"systemctl show retorno codigo {proc.returncode}: {proc.stderr.strip() or 'sin salida'}",
                }
        except Exception as exc:
            resultados_servicios[svc] = {
                "estado": "NO DATA",
                "motivo": f"Error ejecutando consulta systemctl: {exc}",
            }

    servicios_activos = sum(1 for s in resultados_servicios.values() if s.get("estado") == "ACTIVO")
    return {
        "estado": "DISPONIBLE",
        "servicios_consultados": len(targets),
        "servicios_activos": servicios_activos,
        "servicios": resultados_servicios,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3. FUENTE: RECURSOS DEL SISTEMA (CPU / RAM / SWAP / GOBERNANZA)
# ─────────────────────────────────────────────────────────────────────────────

def obtener_estado_recursos() -> Dict[str, Any]:
    """Lee el estado de carga, RAM, swap y gobernanza de recursos."""
    try:
        from services.ops.gobernanza_recursos import medir, admision, titular_actual
        estado_m = medir()
        ok_adm, motivo_adm = admision(estado_m)
        titular = titular_actual()

        carga_1m_val = round(estado_m.carga_1m, 2) if estado_m.carga_1m is not None else "NO DATA"
        mem_disp_val = round(estado_m.memoria_disponible_mb, 1) if estado_m.memoria_disponible_mb is not None else "NO DATA"
        swap_libre_val = round(estado_m.swap_libre_mb, 1) if estado_m.swap_libre_mb is not None else "NO DATA"
        cpu_pct_val = round(estado_m.cpu_pct, 1) if estado_m.cpu_pct is not None else "NO DATA"
        ram_pct_val = round(estado_m.ram_pct, 1) if estado_m.ram_pct is not None else "NO DATA"

        return {
            "estado": "DISPONIBLE",
            "nucleos": estado_m.nucleos,
            "carga_1m": carga_1m_val,
            "carga_relativa": round(estado_m.carga_relativa, 2) if estado_m.carga_relativa is not None else "NO DATA",
            "memoria_disponible_mb": mem_disp_val,
            "swap_libre_mb": swap_libre_val,
            "cpu_pct": cpu_pct_val,
            "ram_pct": ram_pct_val,
            "admision_trabajo_pesado": {
                "admitido": ok_adm,
                "motivo": motivo_adm,
            },
            "turno_trabajo_pesado": titular if titular else "libre",
        }
    except Exception as exc:
        nucleos = os.cpu_count() or 1
        return {
            "estado": "NO DATA",
            "motivo": f"Fallo al medir gobernanza de recursos: {exc}",
            "nucleos": nucleos,
            "carga_1m": "NO DATA",
            "memoria_disponible_mb": "NO DATA",
            "swap_libre_mb": "NO DATA",
            "cpu_pct": "NO DATA",
            "ram_pct": "NO DATA",
            "admision_trabajo_pesado": {
                "admitido": False,
                "motivo": f"Error: {exc}",
            },
            "turno_trabajo_pesado": "NO DATA",
        }


# ─────────────────────────────────────────────────────────────────────────────
# 4. FUENTE: DISCOVERY CGROUP MEMORY.EVENTS
# ─────────────────────────────────────────────────────────────────────────────

RUTAS_CGROUP_CANDIDATAS = [
    Path("/sys/fs/cgroup/system.slice/ultrarentable-discovery.service/memory.events"),
    Path("/sys/fs/cgroup/memory/system.slice/ultrarentable-discovery.service/memory.events"),
]


def obtener_estado_discovery(cgroup_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """Lee el archivo memory.events del cgroup de ultrarentable-discovery si existe."""
    rutas = [Path(cgroup_path)] if cgroup_path else RUTAS_CGROUP_CANDIDATAS
    ruta_encontrada: Optional[Path] = None
    for r in rutas:
        if r.exists() and r.is_file():
            ruta_encontrada = r
            break

    if not ruta_encontrada:
        return {
            "estado": "NO DATA",
            "motivo": "fichero cgroup memory.events no existe en rutas del sistema (/sys/fs/cgroup/...). Discovery inactivo o entorno sin cgroup v2.",
            "eventos": {},
            "alerta_thrashing": False,
        }

    try:
        contenido = ruta_encontrada.read_text(encoding="utf-8")
        eventos: Dict[str, int] = {}
        for linea in contenido.splitlines():
            linea = linea.strip()
            if not linea:
                continue
            partes = linea.split()
            if len(partes) == 2:
                clave, valor = partes
                try:
                    eventos[clave] = int(valor)
                except ValueError:
                    pass

        high_count = eventos.get("high", 0)
        max_count = eventos.get("max", 0)
        oom_count = eventos.get("oom", 0)
        oom_kill = eventos.get("oom_kill", 0)
        alerta_thrashing = high_count > 100000

        return {
            "estado": "DISPONIBLE",
            "ruta": str(ruta_encontrada),
            "eventos": eventos,
            "frenazos_high": high_count,
            "limite_max": max_count,
            "oom_count": oom_count,
            "oom_kills": oom_kill,
            "alerta_thrashing": alerta_thrashing,
            "diagnostico": (
                f"ALERTA CRITICA: {high_count} frenazos de memoria en cgroup (thrashing activo)"
                if alerta_thrashing
                else "Normal (sin thrashing descontrolado)"
            ),
        }
    except Exception as exc:
        return {
            "estado": "NO DATA",
            "motivo": f"Error leyendo {ruta_encontrada}: {exc}",
            "eventos": {},
            "alerta_thrashing": False,
        }


# ─────────────────────────────────────────────────────────────────────────────
# 5. FUENTE: BASE DE DATOS CANONICA (SQLITE SOLO LECTURA)
# ─────────────────────────────────────────────────────────────────────────────

TABLAS_MONITORIZADAS = [
    "strategies",
    "candidates",
    "backtests",
    "execution_sessions",
    "audit_events",
    "datasets",
    "portfolios",
    "provider_rule_sets",
]


def obtener_estado_bd(db_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """Consulta la base de datos canonica en modo estricto de SOLO LECTURA."""
    target_path = Path(db_path) if db_path else _resolver_ruta_bd_default()
    if not target_path.exists() or not target_path.is_file():
        return {
            "estado": "NO DATA",
            "motivo": f"Fichero de base de datos no existe en la ruta {target_path}",
            "db_path": str(target_path),
            "size_bytes": 0,
            "wal_active": False,
            "conteos_tablas": {},
            "ultimos_trades": "NO DATA",
            "ultimos_examenes": "NO DATA",
        }

    size_bytes = target_path.stat().st_size
    wal_path = Path(f"{target_path}-wal")
    wal_active = wal_path.exists() and wal_path.stat().st_size > 0

    # Conexion URI modo read-only
    uri_path = f"file:{target_path.resolve().as_posix()}?mode=ro"
    conteos: Dict[str, Any] = {}
    ultimos_trades: Any = []
    ultimos_examenes: Any = []

    try:
        conn = sqlite3.connect(uri_path, uri=True, timeout=5.0)
        conn.execute("PRAGMA query_only = ON;")
        cursor = conn.cursor()

        # Comprobar tablas existentes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tablas_existentes = {row[0] for row in cursor.fetchall()}

        for tbl in TABLAS_MONITORIZADAS:
            if tbl in tablas_existentes:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {tbl};")  # noqa: S608
                    row = cursor.fetchone()
                    conteos[tbl] = row[0] if row else 0
                except Exception as e_tbl:
                    conteos[tbl] = f"error: {e_tbl}"
            else:
                conteos[tbl] = "NO DATA (tabla no existe)"

        # Ultimas sesiones de ejecucion / trades
        if "execution_sessions" in tablas_existentes:
            try:
                cursor.execute(
                    """
                    SELECT session_id, route, environment, symbol, status,
                           current_pnl_usd, daily_pnl_usd, current_drawdown_pct, created_at
                    FROM execution_sessions
                    ORDER BY created_at DESC
                    LIMIT 5;
                    """
                )
                filas_exec = cursor.fetchall()
                if filas_exec:
                    ultimos_trades = [
                        {
                            "session_id": f[0],
                            "route": f[1],
                            "environment": f[2],
                            "symbol": f[3],
                            "status": f[4],
                            "current_pnl_usd": f[5],
                            "daily_pnl_usd": f[6],
                            "current_drawdown_pct": f[7],
                            "created_at": str(f[8]),
                        }
                        for f in filas_exec
                    ]
                else:
                    ultimos_trades = "sin_registros"
            except Exception as e_tr:
                ultimos_trades = f"NO DATA ({e_tr})"
        elif "backtests" in tablas_existentes:
            try:
                cursor.execute(
                    """
                    SELECT backtest_id, strategy_id, dataset_id, engine_type,
                           net_return_pct, max_drawdown_pct, trades_count, status, created_at
                    FROM backtests
                    ORDER BY created_at DESC
                    LIMIT 5;
                    """
                )
                filas_bt = cursor.fetchall()
                if filas_bt:
                    ultimos_trades = [
                        {
                            "backtest_id": f[0],
                            "strategy_id": f[1],
                            "dataset_id": f[2],
                            "engine_type": f[3],
                            "net_return_pct": f[4],
                            "max_drawdown_pct": f[5],
                            "trades_count": f[6],
                            "status": f[7],
                            "created_at": str(f[8]),
                        }
                        for f in filas_bt
                    ]
                else:
                    ultimos_trades = "sin_registros"
            except Exception as e_bt:
                ultimos_trades = f"NO DATA ({e_bt})"
        else:
            ultimos_trades = "NO DATA (sin tabla de ejecuciones o backtests)"

        # Ultimos examenes / candidatas
        if "candidates" in tablas_existentes:
            try:
                cursor.execute(
                    """
                    SELECT candidate_id, name, route, symbol, status,
                           status_reason, net_profit_is, profit_factor_is,
                           net_profit_oos, profit_factor_oos, max_dd_oos_pct, created_at
                    FROM candidates
                    ORDER BY created_at DESC
                    LIMIT 5;
                    """
                )
                filas_cand = cursor.fetchall()
                if filas_cand:
                    ultimos_examenes = [
                        {
                            "candidate_id": f[0],
                            "name": f[1],
                            "route": f[2],
                            "symbol": f[3],
                            "status": f[4],
                            "status_reason": f[5],
                            "net_profit_is": f[6],
                            "profit_factor_is": f[7],
                            "net_profit_oos": f[8],
                            "profit_factor_oos": f[9],
                            "max_dd_oos_pct": f[10],
                            "created_at": str(f[11]),
                        }
                        for f in filas_cand
                    ]
                else:
                    ultimos_examenes = "sin_registros"
            except Exception as e_cd:
                ultimos_examenes = f"NO DATA ({e_cd})"
        else:
            ultimos_examenes = "NO DATA (tabla candidates no existe)"

        conn.close()

        return {
            "estado": "DISPONIBLE",
            "db_path": str(target_path),
            "size_bytes": size_bytes,
            "size_mb": round(size_bytes / (1024 * 1024), 2),
            "wal_active": wal_active,
            "conteos_tablas": conteos,
            "ultimos_trades": ultimos_trades,
            "ultimos_examenes": ultimos_examenes,
        }
    except Exception as exc:
        return {
            "estado": "NO DATA",
            "motivo": f"Fallo al abrir o consultar base de datos en modo solo lectura: {exc}",
            "db_path": str(target_path),
            "size_bytes": size_bytes,
            "wal_active": wal_active,
            "conteos_tablas": {},
            "ultimos_trades": "NO DATA",
            "ultimos_examenes": "NO DATA",
        }


# ─────────────────────────────────────────────────────────────────────────────
# 6. GENERADOR DE INFORME INTEGRAL (JSON + MARKDOWN)
# ─────────────────────────────────────────────────────────────────────────────

def generar_informe(
    api_host: str = "127.0.0.1",
    api_port: int = 8000,
    db_path: Optional[Union[str, Path]] = None,
    cgroup_path: Optional[Union[str, Path]] = None,
    servicios: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Recopila todas las fuentes y devuelve el diccionario estructurado del informe."""
    ahora_utc = datetime.now(timezone.utc)
    timestamp_iso = ahora_utc.isoformat()
    fecha_str = ahora_utc.strftime("%Y-%m-%d")
    hostname = socket.gethostname()
    plataforma = sys.platform

    res_api = obtener_estado_api(host=api_host, port=api_port)
    res_systemd = obtener_estado_systemd(servicios=servicios)
    res_recursos = obtener_estado_recursos()
    res_discovery = obtener_estado_discovery(cgroup_path=cgroup_path)
    res_bd = obtener_estado_bd(db_path=db_path)

    alertas: List[str] = []
    if res_discovery.get("alerta_thrashing"):
        frenazos = res_discovery.get("frenazos_high", 0)
        alertas.append(f"Cgroup Discovery en thrashing severo: {frenazos} frenazos registrados.")

    if res_recursos.get("estado") == "DISPONIBLE":
        adm = res_recursos.get("admision_trabajo_pesado", {})
        if not adm.get("admitido", True):
            alertas.append(f"Admision de recursos denegada: {adm.get('motivo')}")

    if res_bd.get("estado") == "NO DATA":
        alertas.append(f"Base de datos no accesible: {res_bd.get('motivo')}")

    informe = {
        "vigia_version": VIGIA_VERSION,
        "timestamp_utc": timestamp_iso,
        "fecha": fecha_str,
        "host": hostname,
        "plataforma": plataforma,
        "fuentes": {
            "api": res_api,
            "systemd": res_systemd,
            "recursos": res_recursos,
            "discovery": res_discovery,
            "bd": res_bd,
        },
        "resumen": {
            "alerta_critica": len(alertas) > 0,
            "total_alertas": len(alertas),
            "motivos_alerta": alertas,
        },
    }
    return informe


def generar_markdown(informe: Dict[str, Any]) -> str:
    """Genera la representacion en Markdown estructurado del informe diario."""
    ts = informe.get("timestamp_utc", "UNKNOWN")
    fecha = informe.get("fecha", "UNKNOWN")
    host = informe.get("host", "UNKNOWN")
    plat = informe.get("plataforma", "UNKNOWN")
    version = informe.get("vigia_version", VIGIA_VERSION)
    resumen = informe.get("resumen", {})
    fuentes = informe.get("fuentes", {})

    api = fuentes.get("api", {})
    sysd = fuentes.get("systemd", {})
    rec = fuentes.get("recursos", {})
    disc = fuentes.get("discovery", {})
    bd = fuentes.get("bd", {})

    alerta_md = "[ALERTA] ALERTAS ACTIVAS" if resumen.get("alerta_critica") else "[OK] SISTEMA EN ORDEN"

    lineas = [
        f"# INFORME DIARIO VIGIA V0 -- {fecha}",
        "",
        f"> **Timestamp UTC:** `{ts}` | **Host:** `{host}` | **Plataforma:** `{plat}` | **Vigia Version:** `v{version}`",
        f"> **Estado General:** {alerta_md}",
        "",
    ]

    if resumen.get("motivos_alerta"):
        lineas.append("### [ALERTA] Alertas Registradas")
        for m in resumen["motivos_alerta"]:
            lineas.append(f"- **ALERTA:** {m}")
        lineas.append("")

    # 1. API
    lineas.append("## 1. Estado de API Local (:8000)")
    if api.get("estado") == "ONLINE":
        lineas.append("| Propiedad | Valor |")
        lineas.append("| :--- | :--- |")
        lineas.append(f"| Estado | `ONLINE` (HTTP {api.get('codigo_http')}) |")
        lineas.append(f"| Latencia | `{api.get('latencia_ms')} ms` |")
        lineas.append(f"| Version API | `{api.get('version_api')}` |")
        lineas.append(f"| Engine Version | `{api.get('engine_version')}` |")
        lineas.append(f"| Runtime Mode | `{api.get('runtime_mode')}` |")
    else:
        lineas.append(f"- **Estado:** `NO DATA`")
        lineas.append(f"- **Motivo:** {api.get('motivo', 'Desconocido')}")
    lineas.append("")

    # 2. Systemd
    lineas.append("## 2. Servicios Systemd")
    if sysd.get("estado") == "DISPONIBLE":
        lineas.append("| Servicio | Estado | Active State | Sub State | PID |")
        lineas.append("| :--- | :--- | :--- | :--- | :--- |")
        for s_nombre, s_info in sysd.get("servicios", {}).items():
            if s_info.get("estado") == "NO DATA":
                lineas.append(f"| `{s_nombre}` | `NO DATA` | - | - | {s_info.get('motivo')} |")
            else:
                lineas.append(
                    f"| `{s_nombre}` | `{s_info.get('estado')}` | `{s_info.get('active_state')}` | `{s_info.get('sub_state')}` | `{s_info.get('main_pid')}` |"
                )
    else:
        lineas.append(f"- **Estado:** `NO DATA`")
        lineas.append(f"- **Motivo:** {sysd.get('motivo', 'Desconocido')}")
    lineas.append("")

    # 3. Recursos
    lineas.append("## 3. Recursos y Gobernanza")
    if rec.get("estado") == "DISPONIBLE":
        adm = rec.get("admision_trabajo_pesado", {})
        turno = rec.get("turno_trabajo_pesado")
        turno_str = turno if isinstance(turno, str) else json.dumps(turno, ensure_ascii=False)
        lineas.append("| Metrica | Valor |")
        lineas.append("| :--- | :--- |")
        lineas.append(f"| Nucleos CPU | `{rec.get('nucleos')}` |")
        lineas.append(f"| Carga 1m / Relativa | `{rec.get('carga_1m')}` (rel: `{rec.get('carga_relativa')}`) |")
        lineas.append(f"| CPU % | `{rec.get('cpu_pct')}%` |")
        lineas.append(f"| Memoria Disponible | `{rec.get('memoria_disponible_mb')} MB` (RAM {rec.get('ram_pct')}%) |")
        lineas.append(f"| Swap Libre | `{rec.get('swap_libre_mb')} MB` |")
        lineas.append(f"| Admision Trabajo Pesado | `{'SI' if adm.get('admitido') else 'NO'}` -- {adm.get('motivo')} |")
        lineas.append(f"| Turno Actual | `{turno_str}` |")
    else:
        lineas.append(f"- **Estado:** `NO DATA`")
        lineas.append(f"- **Motivo:** {rec.get('motivo', 'Desconocido')}")
    lineas.append("")

    # 4. Discovery Cgroup
    lineas.append("## 4. Cgroup Discovery (memory.events)")
    if disc.get("estado") == "DISPONIBLE":
        evs = disc.get("eventos", {})
        lineas.append(f"- **Ruta:** `{disc.get('ruta')}`")
        lineas.append(f"- **Diagnostico:** {disc.get('diagnostico')}")
        lineas.append("| Evento | Contador |")
        lineas.append("| :--- | :--- |")
        for ek, ev in evs.items():
            lineas.append(f"| `{ek}` | `{ev}` |")
    else:
        lineas.append(f"- **Estado:** `NO DATA`")
        lineas.append(f"- **Motivo:** {disc.get('motivo', 'Desconocido')}")
    lineas.append("")

    # 5. Base de Datos
    lineas.append("## 5. Base de Datos Canonica (SQLite)")
    if bd.get("estado") == "DISPONIBLE":
        lineas.append(f"- **Ruta:** `{bd.get('db_path')}` (`{bd.get('size_mb')} MB` | WAL activo: `{bd.get('wal_active')}`)")
        lineas.append("")
        lineas.append("### Conteos de Tablas")
        lineas.append("| Tabla | Registros |")
        lineas.append("| :--- | :--- |")
        for tk, tv in bd.get("conteos_tablas", {}).items():
            lineas.append(f"| `{tk}` | `{tv}` |")
        lineas.append("")

        lineas.append("### Ultimos Examenes / Candidatas")
        examenes = bd.get("ultimos_examenes")
        if isinstance(examenes, list) and examenes:
            lineas.append("| Candidata | Ruta | Simbolo | Estado | Ret IS | PF IS | Ret OOS | PF OOS | Max DD OOS |")
            lineas.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
            for ex in examenes:
                lineas.append(
                    f"| `{ex.get('candidate_id')}` | `{ex.get('route')}` | `{ex.get('symbol')}` | `{ex.get('status')}` | "
                    f"`{ex.get('net_profit_is')}` | `{ex.get('profit_factor_is')}` | `{ex.get('net_profit_oos')}` | "
                    f"`{ex.get('profit_factor_oos')}` | `{ex.get('max_dd_oos_pct')}%` |"
                )
        else:
            lineas.append(f"- `{examenes}`")
        lineas.append("")

        lineas.append("### Ultimas Sesiones / Trades")
        trades = bd.get("ultimos_trades")
        if isinstance(trades, list) and trades:
            lineas.append("| ID | Ruta / Entorno | Simbolo | Estado | PnL Total | PnL Diario | DD Actual |")
            lineas.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
            for tr in trades:
                sid = tr.get("session_id") or tr.get("backtest_id")
                r_env = f"{tr.get('route', '')} / {tr.get('environment', tr.get('engine_type', ''))}"
                pnl = tr.get("current_pnl_usd", tr.get("net_return_pct", 0.0))
                pnl_d = tr.get("daily_pnl_usd", "-")
                dd = tr.get("current_drawdown_pct", tr.get("max_drawdown_pct", 0.0))
                lineas.append(
                    f"| `{sid}` | `{r_env}` | `{tr.get('symbol', tr.get('dataset_id', ''))}` | `{tr.get('status')}` | `{pnl}` | `{pnl_d}` | `{dd}%` |"
                )
        else:
            lineas.append(f"- `{trades}`")
    else:
        lineas.append(f"- **Estado:** `NO DATA`")
        lineas.append(f"- **Motivo:** {bd.get('motivo', 'Desconocido')}")

    lineas.append("")
    lineas.append("---")
    lineas.append("*Informe generado automaticamente por Vigia V0 (proceso de solo lectura, sin efectos colaterales).*")
    lineas.append("")
    return "\n".join(lineas)


def guardar_informe(informe: Dict[str, Any], out_dir: Union[str, Path] = DEFAULT_OUT_DIR) -> Tuple[Path, Path]:
    """Guarda atomicamente el informe en formato JSON y Markdown."""
    destino = Path(out_dir)
    destino.mkdir(parents=True, exist_ok=True)
    fecha = informe.get("fecha", datetime.now(timezone.utc).strftime("%Y-%m-%d"))

    json_path = destino / f"{fecha}.json"
    md_path = destino / f"{fecha}.md"

    json_str = json.dumps(informe, indent=2, ensure_ascii=False)
    md_str = generar_markdown(informe)

    # Escritura atomica
    tmp_json = json_path.with_suffix(".json.tmp")
    tmp_md = md_path.with_suffix(".md.tmp")

    tmp_json.write_text(json_str, encoding="utf-8")
    tmp_md.write_text(md_str, encoding="utf-8")

    tmp_json.replace(json_path)
    tmp_md.replace(md_path)

    return json_path, md_path


# ─────────────────────────────────────────────────────────────────────────────
# 7. PUNTO DE ENTRADA CLI
# ─────────────────────────────────────────────────────────────────────────────

def main(argv: Optional[List[str]] = None) -> int:
    """Ejecuta la captura del vigia y persiste o imprime el informe."""
    parser = argparse.ArgumentParser(
        description="Vigia V0: Monitor de solo lectura y generador de informe diario del sistema."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Si se activa, no escribe ningun fichero en disco; emite el informe por stdout.",
    )
    parser.add_argument(
        "--out-dir",
        default=str(DEFAULT_OUT_DIR),
        help="Directorio donde guardar los informes diarios (por defecto orchestration/results/vigia).",
    )
    parser.add_argument(
        "--api-host",
        default="127.0.0.1",
        help="Host de la API local a inspeccionar.",
    )
    parser.add_argument(
        "--api-port",
        type=int,
        default=8000,
        help="Puerto de la API local a inspeccionar.",
    )
    parser.add_argument(
        "--db-path",
        default=None,
        help="Ruta explicita a la base de datos sqlite a inspeccionar.",
    )
    parser.add_argument(
        "--cgroup-path",
        default=None,
        help="Ruta explicita al fichero memory.events de cgroup.",
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Emite unicamentee el JSON estructurado por stdout.",
    )

    args = parser.parse_args(argv)

    informe = generar_informe(
        api_host=args.api_host,
        api_port=args.api_port,
        db_path=args.db_path,
        cgroup_path=args.cgroup_path,
    )

    if args.dry_run:
        if args.json_only:
            print(json.dumps(informe, indent=2, ensure_ascii=False))
        else:
            md = generar_markdown(informe)
            try:
                print(md)
            except UnicodeEncodeError:
                # Fallback seguro para consolas legacy
                sys.stdout.buffer.write(md.encode("utf-8", errors="replace"))
                sys.stdout.buffer.write(b"\n")
        return 0

    json_path, md_path = guardar_informe(informe, out_dir=args.out_dir)
    if args.json_only:
        print(json.dumps(informe, indent=2, ensure_ascii=False))
    else:
        print("Informe Vigia V0 generado exitosamente:")
        print(f"  JSON : {json_path}")
        print(f"  MD   : {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
