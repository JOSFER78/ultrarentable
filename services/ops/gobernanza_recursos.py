"""services/ops/gobernanza_recursos.py

Puerta unica de admision para todo trabajo pesado del proyecto.

Por que existe
--------------
El VPS tiene 4 nucleos (menos el 4-9 % que se lleva el hipervisor de Oracle), ~23 GB de RAM y
4 GB de swap, y ademas sirve la API, la web y StrategyQuantX. Se ha colapsado tres veces. La
causa no fue nunca un proceso concreto: fue que cada proceso decidia por su cuenta cuando
arrancar. Aplicar `nice` a cada uno reparte la CPU, pero no reduce la demanda: en el ultimo
colapso el 56,6 % del tiempo de CPU era ya `nice` y la maquina seguia saturada, con la swap al
100 % y un servicio frenado por el kernel 713.626 veces.

Este modulo sustituye la disciplina caso a caso por un mecanismo: UN solo trabajo pesado a la vez
en toda la maquina, y solo si la maquina esta en condiciones de aceptarlo.

Como se usa
-----------
    from services.ops.gobernanza_recursos import trabajo_pesado

    with trabajo_pesado("campana-fondeo-5m"):
        ...  # mineria, backfill, build de la web, consolidacion, pytest largo

Si otro trabajo pesado ya esta corriendo, este espera (o se rinde con `esperar=False`). Si la
maquina no admite mas carga, se rechaza con el motivo concreto: fallar cerrado y decirlo es
preferible a arrancar y tumbar la maquina, porque un colapso arrastra tambien a la API y a la web.
"""

from __future__ import annotations

import contextlib
import ctypes
import ctypes.wintypes
import errno
import json
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional, Tuple

if os.name == "nt":
    import msvcrt
    fcntl = None  # type: ignore
else:
    import fcntl
    msvcrt = None  # type: ignore


# El candado vive fuera del repositorio: es estado de maquina, no del proyecto, y debe sobrevivir
# a un `git clean` y ser comun a todas las sesiones y usuarios del proyecto.
def get_directorio_estado(custom_dir: Optional[Path | str] = None) -> Path:
    if custom_dir:
        return Path(custom_dir)
    env_dir = os.getenv("GOBERNANZA_LOCK_DIR") or os.getenv("ULTRARENTABLE_RUNTIME_DIR")
    if env_dir:
        return Path(env_dir)
    return Path.home() / ".local/state/ultrarentable"


def get_ruta_candado(custom_dir: Optional[Path | str] = None) -> Path:
    return get_directorio_estado(custom_dir) / "trabajo_pesado.lock"


def get_ruta_titular(custom_dir: Optional[Path | str] = None) -> Path:
    return get_directorio_estado(custom_dir) / "trabajo_pesado.json"


DIRECTORIO_ESTADO = get_directorio_estado()
RUTA_CANDADO = get_ruta_candado()
RUTA_TITULAR = get_ruta_titular()

# Umbrales de admision. Son deliberadamente conservadores: el coste de esperar cinco minutos es
# nulo, el de tumbar la maquina es perder la API, la web y la sesion de trabajo entera.
MIN_SWAP_LIBRE_MB = 256.0
MIN_MEMORIA_DISPONIBLE_MB = 1536.0
FACTOR_CARGA_MAXIMA = 1.5  # load1 maximo admisible = nucleos * este factor


class MaquinaSaturada(RuntimeError):
    """La maquina no admite mas trabajo pesado ahora mismo."""


class RecursoOcupado(RuntimeError):
    """Otro trabajo pesado tiene el turno y no se quiso esperar."""


@dataclass(frozen=True)
class EstadoMaquina:
    nucleos: int
    carga_1m: Optional[float]
    memoria_disponible_mb: Optional[float]
    swap_libre_mb: Optional[float]
    cpu_pct: Optional[float] = None
    ram_pct: Optional[float] = None

    @property
    def carga_relativa(self) -> Optional[float]:
        if self.carga_1m is None:
            return None
        return self.carga_1m / max(1, self.nucleos)


def _bloquear(fh) -> None:
    """Aplica un candado exclusivo no bloqueante."""
    if os.name == "nt":
        fh.seek(0, os.SEEK_END)
        if fh.tell() == 0:
            fh.write("\0")
            fh.flush()
        fh.seek(0)
        msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


def _liberar(fh) -> None:
    """Libera el candado previamente adquirido."""
    if os.name == "nt":
        fh.seek(0)
        msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


# Cache para CPU en Windows (timeout 10s, cache 5s)
_CACHE_CPU_S = 5.0
_ultimo_cpu_medido: Tuple[float, Optional[float]] = (0.0, None)


def _medir_cpu_windows() -> Optional[float]:
    """Mide CPU % promedio en Windows usando Get-CimInstance Win32_Processor."""
    global _ultimo_cpu_medido
    ahora = time.monotonic()
    t_prev, val_prev = _ultimo_cpu_medido
    if val_prev is not None and (ahora - t_prev) < _CACHE_CPU_S:
        return val_prev

    cmd = [
        "powershell",
        "-NoProfile",
        "-Command",
        "(Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average",
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if res.returncode == 0 and res.stdout.strip():
            val = float(res.stdout.strip().replace(",", "."))
            _ultimo_cpu_medido = (ahora, val)
            return val
    except Exception:
        pass
    return None


def _medir_memoria_windows() -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float]]:
    """Devuelve (memoria disponible MB, memoria total MB, ram % usada, swap libre MB)."""
    try:
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.wintypes.DWORD),
                ("dwMemoryLoad", ctypes.wintypes.DWORD),
                ("ullTotalPhys", ctypes.c_uint64),
                ("ullAvailPhys", ctypes.c_uint64),
                ("ullTotalPageFile", ctypes.c_uint64),
                ("ullAvailPageFile", ctypes.c_uint64),
                ("ullTotalVirtual", ctypes.c_uint64),
                ("ullAvailVirtual", ctypes.c_uint64),
                ("ullAvailExtendedVirtual", ctypes.c_uint64),
            ]

        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
            return None, None, None, None

        disponible_mb = stat.ullAvailPhys / (1024.0 * 1024.0)
        total_mb = stat.ullTotalPhys / (1024.0 * 1024.0)
        ram_pct = float(stat.dwMemoryLoad)
        swap_libre_mb = stat.ullAvailPageFile / (1024.0 * 1024.0)
        return disponible_mb, total_mb, ram_pct, swap_libre_mb
    except Exception:
        return None, None, None, None


def _leer_meminfo() -> Tuple[float, float]:
    """Devuelve (memoria disponible MB, swap libre MB) leyendo /proc/meminfo."""
    disponible_kb = 0.0
    swap_total_kb = 0.0
    swap_libre_kb = 0.0
    try:
        with open("/proc/meminfo", "r", encoding="utf-8") as fh:
            for linea in fh:
                campo, _, resto = linea.partition(":")
                valor = resto.strip().split()
                if not valor:
                    continue
                try:
                    numero = float(valor[0])
                except ValueError:
                    continue
                if campo == "MemAvailable":
                    disponible_kb = numero
                elif campo == "SwapTotal":
                    swap_total_kb = numero
                elif campo == "SwapFree":
                    swap_libre_kb = numero
    except OSError as exc:  # pragma: no cover - /proc siempre existe en Linux
        raise MaquinaSaturada(f"No se pudo leer /proc/meminfo: {exc}") from exc
    # Sin swap configurada, su ausencia no debe bloquear nada.
    libre = swap_libre_kb / 1024.0 if swap_total_kb > 0 else float("inf")
    return disponible_kb / 1024.0, libre


def medir() -> EstadoMaquina:
    """Foto instantanea de la maquina."""
    nucleos = os.cpu_count() or 1
    if os.name == "nt":
        cpu_pct = _medir_cpu_windows()
        disponible_mb, _total_mb, ram_pct, swap_libre_mb = _medir_memoria_windows()
        return EstadoMaquina(
            nucleos=nucleos,
            carga_1m=None,
            memoria_disponible_mb=disponible_mb,
            swap_libre_mb=swap_libre_mb,
            cpu_pct=cpu_pct,
            ram_pct=ram_pct,
        )

    disponible_mb, swap_libre_mb = _leer_meminfo()
    carga_1m = os.getloadavg()[0] if hasattr(os, "getloadavg") else None
    return EstadoMaquina(
        nucleos=nucleos,
        carga_1m=carga_1m,
        memoria_disponible_mb=disponible_mb,
        swap_libre_mb=swap_libre_mb,
        cpu_pct=None,
        ram_pct=None,
    )


def admision(estado: Optional[EstadoMaquina] = None) -> Tuple[bool, str]:
    """Decide si la maquina admite un trabajo pesado mas, y explica por que no."""
    e = estado or medir()
    if e.memoria_disponible_mb is None:
        return False, "no se pudo medir memoria disponible (NO DATA)."
    if e.memoria_disponible_mb < MIN_MEMORIA_DISPONIBLE_MB:
        return False, (
            f"memoria disponible insuficiente ({e.memoria_disponible_mb:.0f} MB, minimo "
            f"{MIN_MEMORIA_DISPONIBLE_MB:.0f})."
        )
    if e.swap_libre_mb is not None and e.swap_libre_mb < MIN_SWAP_LIBRE_MB:
        return False, (
            f"swap practicamente agotada ({e.swap_libre_mb:.0f} MB libres, minimo "
            f"{MIN_SWAP_LIBRE_MB:.0f}). Arrancar ahora hace thrashing de disco y arrastra a la API."
        )

    if e.carga_1m is not None:
        limite = e.nucleos * FACTOR_CARGA_MAXIMA
        if e.carga_1m > limite:
            return False, (
                f"carga demasiado alta ({e.carga_1m:.2f} sobre {e.nucleos} nucleos, limite {limite:.2f}). "
                "Hay procesos ajenos ocupando la maquina."
            )
        swap_str = f", swap {e.swap_libre_mb:.0f} MB" if e.swap_libre_mb is not None else ""
        return True, (
            f"admitida: carga {e.carga_1m:.2f}/{e.nucleos}, {e.memoria_disponible_mb:.0f} MB libres{swap_str}"
        )

    if os.name == "nt":
        if e.cpu_pct is None:
            return False, "no se pudo medir CPU (NO DATA)."
        limite_cpu = FACTOR_CARGA_MAXIMA * 100.0
        if e.cpu_pct > limite_cpu:
            return False, (
                f"carga de CPU demasiado alta ({e.cpu_pct:.1f}%, limite {limite_cpu:.1f}%). "
                "Hay procesos ajenos ocupando la maquina."
            )
        ram_str = f" (RAM {e.ram_pct:.1f}%)" if e.ram_pct is not None else ""
        return True, (
            f"admitida: CPU {e.cpu_pct:.1f}%, {e.memoria_disponible_mb:.0f} MB libres{ram_str}"
        )

    return True, f"admitida: {e.memoria_disponible_mb:.0f} MB libres"


def titular_actual(directorio: Optional[Path | str] = None) -> Optional[dict]:
    """Quien tiene el turno ahora mismo, si alguien lo tiene."""
    ruta = get_ruta_titular(directorio)
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _rebajar_prioridad() -> None:
    """Baja la prioridad de CPU y de E/S del proceso actual."""
    if os.name == "nt":
        with contextlib.suppress(Exception):
            ctypes.windll.kernel32.SetPriorityClass(
                ctypes.windll.kernel32.GetCurrentProcess(), 0x00004000  # BELOW_NORMAL_PRIORITY_CLASS
            )
        return

    with contextlib.suppress(Exception):
        if hasattr(os, "nice"):
            os.nice(19 - os.nice(0))
    # ionice best-effort: si no esta disponible, no es motivo para abortar el trabajo.
    with contextlib.suppress(Exception):
        subprocess.run(
            ["ionice", "-c", "3", "-p", str(os.getpid())],
            check=False,
            capture_output=True,
            timeout=5,
        )


@contextlib.contextmanager
def trabajo_pesado(
    nombre: str,
    esperar: bool = True,
    espera_maxima_s: float = 1800.0,
    comprobar_admision: bool = True,
    rebajar_prioridad: bool = True,
    lock_dir: Optional[Path | str] = None,
) -> Iterator[EstadoMaquina]:
    """Toma el turno unico de trabajo pesado de la maquina.

    El candado usa msvcrt.locking en Windows y flock en POSIX, asi que si el proceso muere el kernel
    lo libera solo: no hay candados huerfanos que haya que limpiar a mano, que es como acaban fallando
    estos mecanismos.
    """
    if not nombre or not nombre.strip():
        raise ValueError("todo trabajo pesado debe identificarse con un nombre")

    dir_estado = get_directorio_estado(lock_dir)
    ruta_candado = get_ruta_candado(lock_dir)
    ruta_titular = get_ruta_titular(lock_dir)

    dir_estado.mkdir(parents=True, exist_ok=True)
    inicio_espera = time.monotonic()
    fh = open(ruta_candado, "a+", encoding="utf-8")
    try:
        while True:
            try:
                _bloquear(fh)
                break
            except OSError as exc:
                if exc.errno not in (errno.EAGAIN, errno.EACCES, getattr(errno, "EDEADLK", 36)):
                    raise
                otro = titular_actual(lock_dir) or {}
                descripcion = otro.get("nombre", "otro trabajo")
                if not esperar:
                    raise RecursoOcupado(
                        f"'{descripcion}' (pid {otro.get('pid')}) tiene el turno de trabajo pesado"
                    ) from exc
                if time.monotonic() - inicio_espera > espera_maxima_s:
                    raise RecursoOcupado(
                        f"esperando a '{descripcion}' mas de {espera_maxima_s:.0f}s; se abandona"
                    ) from exc
                time.sleep(1.0 if os.name == "nt" else 5.0)

        estado = medir()
        if comprobar_admision:
            ok, motivo = admision(estado)
            if not ok:
                raise MaquinaSaturada(f"'{nombre}' no arranca: {motivo}")

        if rebajar_prioridad:
            _rebajar_prioridad()

        with contextlib.suppress(OSError):
            carga_inicial = estado.carga_1m if estado.carga_1m is not None else estado.cpu_pct
            ruta_titular.write_text(
                json.dumps(
                    {
                        "nombre": nombre,
                        "pid": os.getpid(),
                        "inicio_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "carga_al_arrancar": carga_inicial,
                        "memoria_disponible_mb": round(estado.memoria_disponible_mb) if estado.memoria_disponible_mb is not None else None,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        yield estado
    finally:
        with contextlib.suppress(OSError):
            t = titular_actual(lock_dir)
            if t and t.get("pid") == os.getpid():
                ruta_titular.unlink(missing_ok=True)
        with contextlib.suppress(OSError):
            _liberar(fh)
        with contextlib.suppress(OSError):
            fh.close()


def _main(argv: Optional[list[str]] = None) -> int:
    import argparse
    import sys

    raw_args = sys.argv[1:] if argv is None else argv

    p = argparse.ArgumentParser(description="Gobernanza de recursos del VPS")
    p.add_argument("accion", choices=["estado", "ejecutar"])
    p.add_argument("--nombre", default=None, help="identificador del trabajo (con 'ejecutar')")
    p.add_argument("--no-esperar", action="store_true")
    p.add_argument("--lock-dir", default=None, help="directorio alternativo para los ficheros de candado y estado")
    p.add_argument("comando", nargs="*", help="comando a ejecutar bajo el turno")

    if "--" in raw_args:
        idx = raw_args.index("--")
        args = p.parse_intermixed_args(raw_args[:idx])
        args.comando = raw_args[idx + 1 :]
    else:
        args = p.parse_intermixed_args(raw_args)

    dir_estado = get_directorio_estado(args.lock_dir)

    if args.accion == "estado":
        e = medir()
        ok, motivo = admision(e)
        print(f"nucleos            : {e.nucleos}")
        if e.carga_1m is not None:
            carga_rel_str = f"  ({e.carga_relativa:.2f} por nucleo)" if e.carga_relativa is not None else ""
            print(f"carga 1m           : {e.carga_1m:.2f}{carga_rel_str}")
        else:
            print("carga 1m           : NO DATA")
        if e.cpu_pct is not None:
            print(f"cpu %              : {e.cpu_pct:.1f}%")
        elif os.name == "nt":
            print("cpu %              : NO DATA")
        if e.memoria_disponible_mb is not None:
            print(f"memoria disponible : {e.memoria_disponible_mb:.0f} MB")
        else:
            print("memoria disponible : NO DATA")
        if e.ram_pct is not None:
            print(f"ram %              : {e.ram_pct:.1f}%")
        if e.swap_libre_mb is not None:
            print(f"swap libre         : {e.swap_libre_mb:.0f} MB")
        else:
            print("swap libre         : NO DATA")
        t = titular_actual(directorio=dir_estado)
        print(f"turno              : {t['nombre'] + ' (pid ' + str(t['pid']) + ')' if t else 'libre'}")
        print(f"admision           : {'SI' if ok else 'NO'} — {motivo}")
        return 0 if ok else 1

    if not args.comando:
        p.error("'ejecutar' necesita un comando")

    nombre = args.nombre or args.comando[0]
    try:
        with trabajo_pesado(nombre, esperar=not args.no_esperar, lock_dir=args.lock_dir):
            return subprocess.run(args.comando, check=False).returncode
    except (MaquinaSaturada, RecursoOcupado) as exc:
        print(f"RECHAZADO: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(_main())
