"""Rejilla M1: las 25 celdas de FONDEO tal y como están AHORA en StrategyQuant X.

Sustituye a la tabla escrita a mano que enseñaba la página de Generación (con activos que no están
en el plan y una cobertura histórica inventada).

**El servidor calcula, la web muestra.** El supervisor que corre en la máquina de StrategyQuant
(`services/ops/supervisor_ultrarentable.py`, bajo systemd) escribe cada minuto `rejilla.json` y
`salud.json` con todo masticado, y nginx los publica por HTTPS detrás de la misma contraseña que
el escritorio remoto. Aquí solo se descargan. Ventajas, y son el motivo del diseño:

- El panel dice la verdad aunque el PC se reinicie: no depende de ningún túnel abierto a mano.
- El puerto de comandos de StrategyQuant (5051) **no sale nunca de la máquina**: ejecuta órdenes y
  no tiene contraseña propia. Lo que viaja son ficheros de solo lectura.

Configuración (variables de entorno, nunca en el repositorio):
  M1_ESTADO_URL   base donde están rejilla.json y salud.json
                  (por defecto https://88-99-210-167.sslip.io/m1)
  M1_ESTADO_AUTH  "usuario:contraseña" de la autenticación básica

REAL-ONLY: si no se puede leer, se devuelve `disponible: false` con el motivo. Nunca una celda
inventada ni un número de relleno.
"""
from __future__ import annotations

import base64
import json
import os
import time
import urllib.request
from typing import Any

from fastapi import APIRouter

router = APIRouter()

_BASE_POR_DEFECTO = "https://88-99-210-167.sslip.io/m1"
_CACHE: dict[str, tuple[float, Any]] = {}
_CACHE_SEG = 20  # el supervisor reescribe cada 60 s; refrescar más a menudo no aporta nada


def _base() -> str:
    return (os.getenv("M1_ESTADO_URL") or _BASE_POR_DEFECTO).rstrip("/")


def _credenciales() -> str:
    """"usuario:contraseña" de la autenticación básica, preferentemente desde un fichero.

    `M1_ESTADO_AUTH_FILE` gana a `M1_ESTADO_AUTH` a propósito: una contraseña en la línea de
    comandos se rompe con caracteres como `&` (medido el 03-09: el arranque de la API se cortaba a
    la mitad) y además queda a la vista de cualquiera que liste los procesos. El fichero vive fuera
    del repositorio.
    """
    ruta = os.getenv("M1_ESTADO_AUTH_FILE", "")
    if ruta:
        try:
            with open(ruta, encoding="utf-8") as fh:
                for linea in fh:
                    linea = linea.strip()
                    if linea and not linea.startswith("#") and ":" in linea:
                        return linea
        except OSError:
            return ""
    return os.getenv("M1_ESTADO_AUTH", "")


def _descargar(nombre: str, timeout: int = 20) -> tuple[Any | None, str | None]:
    ahora = time.time()
    guardado = _CACHE.get(nombre)
    if guardado and ahora - guardado[0] < _CACHE_SEG:
        return guardado[1], None
    peticion = urllib.request.Request(f"{_base()}/{nombre}")
    credenciales = _credenciales()
    if credenciales:
        token = base64.b64encode(credenciales.encode("utf-8")).decode("ascii")
        peticion.add_header("Authorization", f"Basic {token}")
    try:
        with urllib.request.urlopen(peticion, timeout=timeout) as r:  # noqa: S310 (URL propia)
            datos = json.loads(r.read().decode("utf-8", errors="replace"))
        _CACHE[nombre] = (ahora, datos)
        return datos, None
    except Exception as exc:  # noqa: BLE001 — el motivo se enseña tal cual
        detalle = f"{type(exc).__name__}: {exc}"
        if "401" in detalle:
            detalle += " (falta o no vale M1_ESTADO_AUTH)"
        return None, detalle


def _vacia(motivo: str) -> dict[str, Any]:
    return {
        "disponible": False,
        "motivo_no_disponible": motivo,
        "origen": _base(),
        "bucle": {"activo": False, "celda_en_curso": None, "ronda": None, "horas_por_celda": None},
        "resumen": {"celdas": 0, "con_datos": 0, "con_proyecto": 0,
                    "con_al_menos_una_ronda": 0, "estrategias_en_bancos": 0},
        "celdas": [],
    }


@router.get("/rejilla")
def rejilla() -> dict[str, Any]:
    """Las 25 celdas de M1 con lo que cada una tiene hoy: datos, proyecto, estado y caudal."""
    datos, error = _descargar("rejilla.json")
    if datos is None:
        return _vacia(f"no se pudo leer rejilla.json del servidor -> {error}")
    datos["origen"] = _base()
    datos.setdefault("motivo_no_disponible", None)
    return datos


@router.get("/salud")
def salud() -> dict[str, Any]:
    """Qué piezas del sistema están en pie, medido por el supervisor del servidor cada minuto."""
    datos, error = _descargar("salud.json")
    if datos is None:
        return {"disponible": False, "motivo_no_disponible": f"no se pudo leer salud.json -> {error}",
                "origen": _base(), "todo_en_pie": None, "piezas": {}}
    datos["disponible"] = True
    datos["origen"] = _base()
    return datos
