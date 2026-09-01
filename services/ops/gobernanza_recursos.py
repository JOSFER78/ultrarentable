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
import errno
import fcntl
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional, Tuple

# El candado vive fuera del repositorio: es estado de maquina, no del proyecto, y debe sobrevivir
# a un `git clean` y ser comun a todas las sesiones y usuarios del proyecto.
DIRECTORIO_ESTADO = Path(
    os.getenv("ULTRARENTABLE_RUNTIME_DIR", str(Path.home() / ".local/state/ultrarentable"))
)
RUTA_CANDADO = DIRECTORIO_ESTADO / "trabajo_pesado.lock"
RUTA_TITULAR = DIRECTORIO_ESTADO / "trabajo_pesado.json"

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
    carga_1m: float
    memoria_disponible_mb: float
    swap_libre_mb: float

    @property
    def carga_relativa(self) -> float:
        return self.carga_1m / max(1, self.nucleos)


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
    disponible_mb, swap_libre_mb = _leer_meminfo()
    return EstadoMaquina(
        nucleos=os.cpu_count() or 1,
        carga_1m=os.getloadavg()[0],
        memoria_disponible_mb=disponible_mb,
        swap_libre_mb=swap_libre_mb,
    )


def admision(estado: Optional[EstadoMaquina] = None) -> Tuple[bool, str]:
    """Decide si la maquina admite un trabajo pesado mas, y explica por que no."""
    e = estado or medir()
    if e.swap_libre_mb < MIN_SWAP_LIBRE_MB:
        return False, (
            f"swap practicamente agotada ({e.swap_libre_mb:.0f} MB libres, minimo "
            f"{MIN_SWAP_LIBRE_MB:.0f}). Arrancar ahora hace thrashing de disco y arrastra a la API."
        )
    if e.memoria_disponible_mb < MIN_MEMORIA_DISPONIBLE_MB:
        return False, (
            f"memoria disponible insuficiente ({e.memoria_disponible_mb:.0f} MB, minimo "
            f"{MIN_MEMORIA_DISPONIBLE_MB:.0f})."
        )
    limite = e.nucleos * FACTOR_CARGA_MAXIMA
    if e.carga_1m > limite:
        return False, (
            f"carga demasiado alta ({e.carga_1m:.2f} sobre {e.nucleos} nucleos, limite {limite:.2f}). "
            "Hay procesos ajenos ocupando la maquina."
        )
    return True, (
        f"admitida: carga {e.carga_1m:.2f}/{e.nucleos}, {e.memoria_disponible_mb:.0f} MB libres, "
        f"swap {e.swap_libre_mb:.0f} MB"
    )


def titular_actual() -> Optional[dict]:
    """Quien tiene el turno ahora mismo, si alguien lo tiene."""
    try:
        return json.loads(RUTA_TITULAR.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _rebajar_prioridad() -> None:
    """Baja la prioridad de CPU y de E/S del proceso actual."""
    with contextlib.suppress(OSError):
        os.nice(19 - os.nice(0))
    # ionice best-effort: si no esta disponible, no es motivo para abortar el trabajo.
    with contextlib.suppress(Exception):
        import subprocess

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
) -> Iterator[EstadoMaquina]:
    """Toma el turno unico de trabajo pesado de la maquina.

    El candado usa flock, asi que si el proceso muere el kernel lo libera solo: no hay candados
    huerfanos que haya que limpiar a mano, que es como acaban fallando estos mecanismos.
    """
    if not nombre or not nombre.strip():
        raise ValueError("todo trabajo pesado debe identificarse con un nombre")

    DIRECTORIO_ESTADO.mkdir(parents=True, exist_ok=True)
    inicio_espera = time.monotonic()
    fh = open(RUTA_CANDADO, "a+", encoding="utf-8")
    try:
        while True:
            try:
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as exc:
                if exc.errno not in (errno.EAGAIN, errno.EACCES):
                    raise
                otro = titular_actual() or {}
                descripcion = otro.get("nombre", "otro trabajo")
                if not esperar:
                    raise RecursoOcupado(
                        f"'{descripcion}' (pid {otro.get('pid')}) tiene el turno de trabajo pesado"
                    ) from exc
                if time.monotonic() - inicio_espera > espera_maxima_s:
                    raise RecursoOcupado(
                        f"esperando a '{descripcion}' mas de {espera_maxima_s:.0f}s; se abandona"
                    ) from exc
                time.sleep(5.0)

        estado = medir()
        if comprobar_admision:
            ok, motivo = admision(estado)
            if not ok:
                raise MaquinaSaturada(f"'{nombre}' no arranca: {motivo}")

        if rebajar_prioridad:
            _rebajar_prioridad()

        with contextlib.suppress(OSError):
            RUTA_TITULAR.write_text(
                json.dumps(
                    {
                        "nombre": nombre,
                        "pid": os.getpid(),
                        "inicio_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "carga_al_arrancar": estado.carga_1m,
                        "memoria_disponible_mb": round(estado.memoria_disponible_mb),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        yield estado
    finally:
        with contextlib.suppress(OSError):
            if titular_actual() and titular_actual().get("pid") == os.getpid():
                RUTA_TITULAR.unlink(missing_ok=True)
        with contextlib.suppress(OSError):
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        fh.close()


def _main() -> int:
    import argparse

    p = argparse.ArgumentParser(description="Gobernanza de recursos del VPS")
    p.add_argument("accion", choices=["estado", "ejecutar"])
    p.add_argument("--nombre", default=None, help="identificador del trabajo (con 'ejecutar')")
    p.add_argument("--no-esperar", action="store_true")
    p.add_argument("comando", nargs="*", help="comando a ejecutar bajo el turno")
    args = p.parse_args()

    if args.accion == "estado":
        e = medir()
        ok, motivo = admision(e)
        print(f"nucleos            : {e.nucleos}")
        print(f"carga 1m           : {e.carga_1m:.2f}  ({e.carga_relativa:.2f} por nucleo)")
        print(f"memoria disponible : {e.memoria_disponible_mb:.0f} MB")
        print(f"swap libre         : {e.swap_libre_mb:.0f} MB")
        t = titular_actual()
        print(f"turno              : {t['nombre'] + ' (pid ' + str(t['pid']) + ')' if t else 'libre'}")
        print(f"admision           : {'SI' if ok else 'NO'} — {motivo}")
        return 0 if ok else 1

    if not args.comando:
        p.error("'ejecutar' necesita un comando")
    import subprocess

    nombre = args.nombre or args.comando[0]
    try:
        with trabajo_pesado(nombre, esperar=not args.no_esperar):
            return subprocess.run(args.comando, check=False).returncode
    except (MaquinaSaturada, RecursoOcupado) as exc:
        print(f"RECHAZADO: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(_main())
