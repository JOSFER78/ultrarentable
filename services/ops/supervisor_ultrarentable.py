#!/usr/bin/env python3
"""Supervisor de Ultrarentable: el sistema se vigila a sí mismo, en el servidor, sin que nadie mire.

Emilio, 2026-09-03: *"en el PC no tiene que vigilar; el propio sistema de Ultrarentable debe
monitorizarlo, su backend o lo que sea"*. Esto es ese backend. Corre bajo systemd
(`ultrarentable-supervisor.service`, Restart=always, enable) en la máquina donde vive
StrategyQuant, y cada minuto:

1. **Comprueba las piezas** y arregla lo que puede arreglar solo:
   - `sqcli`, el modo de comandos de StrategyQuant en el 5051. Es la pieza crítica: si no
     responde, no se genera nada. Se relanza con `systemctl start sqx-headless`.
   - `m1-runner`, el bucle que recorre las 25 celdas, y `m1-estado`, el que publica el estado.
   - La celda que esté construyendo: si lleva `ESTANCADA_MIN` minutos sin que suba el contador de
     estrategias, se para y el bucle pasa a la siguiente en vez de quedarse colgado para siempre.
   - Disco y memoria: si el disco baja del 10 % libre, se avisa (no se borra nada: doctrina).
2. **Escribe `salud.json`** junto al estado de la rejilla, que ya se publica en el 5052 y del que
   tira la API (`/api/v2/m1/salud`). Así la web enseña la verdad medida, no un adorno.
3. **No inventa y no destruye.** Si no puede medir algo, lo deja en `null` con su motivo. Nunca
   borra datos ni mata procesos ajenos: solo reinicia las unidades de systemd que son suyas.

Uso: `python3 supervisor_ultrarentable.py --base /opt/SQX-headless/import/fondeo`
     `python3 supervisor_ultrarentable.py --base ... --informe`   (imprime salud.json y sale)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

SONDEO_SEG = 60
ESTANCADA_MIN = 20          # minutos sin avanzar antes de dar una celda por colgada
UNIDADES = ["sqx-headless", "m1-runner", "m1-estado"]

_parar = False


def _senal(_s, _m):
    global _parar
    _parar = True


def systemctl(*args: str) -> tuple[int, str]:
    try:
        p = subprocess.run(["systemctl", *args], capture_output=True, text=True, timeout=60)
        return p.returncode, (p.stdout + p.stderr).strip()
    except Exception as exc:  # noqa: BLE001
        return 1, f"{type(exc).__name__}: {exc}"


def unidad_existe(nombre: str) -> bool:
    return systemctl("cat", f"{nombre}.service")[0] == 0


def unidad_activa(nombre: str) -> bool:
    return systemctl("is-active", f"{nombre}.service")[1] == "active"


def sqx(base_url: str, cmd: str, timeout: int = 25) -> str | None:
    try:
        url = f"{base_url}/call?cmd=" + cmd.replace(" ", "%20")
        with urllib.request.urlopen(url, timeout=timeout) as r:  # noqa: S310 (loopback)
            return r.read().decode("utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        return None


def generadas_de(texto: str) -> int | None:
    m = re.search(r"Estrategias generadas\s+([\d.]+)", texto)
    return int(m.group(1).replace(".", "")) if m else None


def _escribir(ruta: Path, datos: dict) -> None:
    """Escritura atómica: o está el fichero entero anterior o el nuevo, nunca uno a medias."""
    tmp = ruta.with_suffix(".tmp")
    tmp.write_text(json.dumps(datos, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, ruta)


SIMBOLOS = ["MES", "MNQ", "MYM", "M2K", "MGC", "MCL", "UB", "M6E"]
MARCOS = ["M1", "M5", "M15", "H1", "H4"]
NOMBRES = {
    "MES": ("Micro E-mini S&P 500", "ES"),
    "MNQ": ("Micro E-mini Nasdaq 100", "NQ"),
    "MYM": ("Micro E-mini Dow Jones", "YM"),
    "M2K": ("Micro E-mini Russell 2000", "RTY"),
    "MGC": ("Micro Oro", "GC"),
    "MCL": ("Micro Petróleo WTI", "CL"),
    "UB": ("Bono del Tesoro a 30 años", "ZB"),
    "M6E": ("Micro Euro FX", "6E"),
}
ETIQUETA_TF = {"M1": "1m", "M5": "5m", "M15": "15m", "H1": "1h", "H4": "4h"}


def _parse_status(texto: str) -> dict:
    def entero(patron: str) -> int | None:
        m = re.search(patron, texto)
        return int(m.group(1).replace(".", "")) if m else None

    def cadena(patron: str) -> str | None:
        m = re.search(patron, texto)
        return m.group(1).strip() if m else None

    if entero(r"Estrategias generadas\s+([\d.]+)") is None:
        return {}
    return {
        "generadas": entero(r"Estrategias generadas\s+([\d.]+)"),
        "en_banco": entero(r"En la base de datos\s+([\d.]+)"),
        "por_hora": cadena(r"Estrategias por hora\s+([\d.,]+)"),
        "aceptadas_por_hora": cadena(r"Estrategias aceptadas por hora\s+([\d.,]+)"),
        "aceptado_pct": cadena(r"Aceptado\s+([\d.,]+)\s*%"),
        "tiempo": cadena(r"Tiempo de funcionamiento hasta ahora\s+(.+)"),
    }


def _rejilla(base_url: str, estado: dict, salud: dict, lista_proyectos: str | None, base: Path) -> dict:
    """Las 25 celdas con todo lo que la web necesita, calculado aquí y servido ya masticado."""
    simbolos: dict[str, dict] = {}
    txt = sqx(base_url, "-symbol action=list", timeout=30)
    for linea in (txt or "").splitlines():
        partes = [p.strip().strip('"') for p in linea.strip().split(",")]
        if len(partes) >= 8 and partes[0] in SIMBOLOS:
            try:
                simbolos[partes[0]] = {"tf_base": partes[2], "desde": partes[4], "hasta": partes[5],
                                       "dias": int(partes[6]), "velas_base": int(partes[7])}
            except ValueError:
                continue

    proyectos = {l.strip() for l in (lista_proyectos or "").splitlines() if l.strip().startswith("FONDEO_")}
    celdas_estado = estado.get("celdas", {})
    en_curso = estado.get("celda_en_curso")
    vivo = _parse_status(sqx(base_url, f"-project action=status name={en_curso}", timeout=30) or "") if en_curso else {}

    try:
        manifiesto = json.loads((base / "manifiesto.json").read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        manifiesto = {}
    costes = manifiesto.get("costes_supuestos", {})

    filas = []
    for simbolo in SIMBOLOS:
        nombre, grande = NOMBRES[simbolo]
        d = simbolos.get(simbolo)  # None mientras ese activo no tenga datos cargados
        for tf in MARCOS:
            proyecto = f"FONDEO_{simbolo}_{tf}"
            ce = celdas_estado.get(proyecto, {})
            rondas = ce.get("rondas", [])
            ultima = rondas[-1] if rondas else {}
            corriendo = proyecto == en_curso
            filas.append({
                "celda": f"{simbolo}_{tf}", "simbolo": simbolo, "contrato_grande": grande,
                "nombre": nombre, "tf": tf, "tf_etiqueta": ETIQUETA_TF[tf],
                "proyecto": proyecto, "proyecto_en_sqx": proyecto in proyectos,
                "datos": d,
                "estado": "EN_CURSO" if corriendo else ce.get("estado", "SIN_EMPEZAR"),
                "rondas_hechas": len(rondas),
                "generadas": vivo.get("generadas") if corriendo else ultima.get("generadas"),
                "en_banco": vivo.get("en_banco") if corriendo else ultima.get("en_banco"),
                "por_hora": vivo.get("por_hora") if corriendo else ultima.get("por_hora"),
                "aceptado_pct": vivo.get("aceptado_pct") if corriendo else ultima.get("aceptado_pct"),
                "tiempo": vivo.get("tiempo") if corriendo else ultima.get("tiempo"),
                "csv_filas": ultima.get("csv_filas"),
                "csv_sha256": ultima.get("csv_sha256"),
                "costes": costes.get(simbolo),
            })

    return {
        "schema": "ultrarentable.m1.rejilla.v1",
        "medido": dt.datetime.now(dt.UTC).isoformat(),
        "disponible": bool(simbolos) and bool(proyectos),
        "bucle": {
            "activo": bool(en_curso), "celda_en_curso": en_curso,
            "ronda": estado.get("ronda"), "horas_por_celda": estado.get("horas_por_celda"),
        },
        "resumen": {
            "celdas": len(filas),
            "con_datos": sum(1 for f in filas if f["datos"]),
            "con_proyecto": sum(1 for f in filas if f["proyecto_en_sqx"]),
            "con_al_menos_una_ronda": sum(1 for f in filas if f["rondas_hechas"] > 0),
            "estrategias_en_bancos": sum(f["en_banco"] or 0 for f in filas),
        },
        "aceptacion_sqx": manifiesto.get("aceptacion", {}),
        "salud": {"todo_en_pie": salud.get("todo_en_pie"), "piezas": salud.get("piezas", {})},
        "celdas": filas,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", type=Path, default=Path("/opt/SQX-headless/import/fondeo"))
    ap.add_argument("--cli", default="http://127.0.0.1:5051")
    ap.add_argument("--informe", action="store_true")
    args = ap.parse_args()

    signal.signal(signal.SIGTERM, _senal)
    signal.signal(signal.SIGINT, _senal)
    args.base.mkdir(parents=True, exist_ok=True)
    ruta_salud = args.base / "salud.json"
    ruta_log = args.base / "supervisor.log"

    if args.informe:
        print(ruta_salud.read_text(encoding="utf-8") if ruta_salud.exists() else '{"error":"sin salud.json todavia"}')
        return 0

    def log(msg: str) -> None:
        linea = f"{dt.datetime.now(dt.UTC):%Y-%m-%d %H:%M:%S} UTC  {msg}"
        print(linea, flush=True)
        with ruta_log.open("a", encoding="utf-8") as fh:
            fh.write(linea + "\n")

    log("=== supervisor Ultrarentable arrancado ===")
    ultima_celda: str | None = None
    ultimas_generadas: int | None = None
    sin_avanzar_desde: float | None = None
    acciones: list[dict] = []

    while not _parar:
        ahora = dt.datetime.now(dt.UTC)
        piezas: dict[str, dict] = {}

        # --- 1. StrategyQuant: la pieza crítica ---
        respuesta = sqx(args.cli, "-project action=list", timeout=25)
        sqx_vivo = respuesta is not None
        piezas["strategyquant"] = {
            "descripcion": "Modo de comandos de StrategyQuant X (genera las estrategias)",
            "ok": sqx_vivo,
            "detalle": (f"{len([l for l in respuesta.splitlines() if l.strip().startswith('FONDEO_')])} proyectos FONDEO"
                        if sqx_vivo else "no responde en el 5051"),
        }
        if not sqx_vivo:
            if unidad_existe("sqx-headless"):
                rc, salida = systemctl("restart", "sqx-headless.service")
                log(f"StrategyQuant no responde -> systemctl restart sqx-headless (rc={rc}) {salida[:120]}")
                acciones.append({"cuando": ahora.isoformat(), "que": "reinicio sqx-headless", "rc": rc})
            else:
                log("StrategyQuant no responde y NO existe la unidad sqx-headless: no puedo levantarlo solo")
                acciones.append({"cuando": ahora.isoformat(), "que": "sqx caido sin unidad systemd", "rc": None})

        # --- 2. Las unidades propias ---
        for unidad in ("m1-runner", "m1-estado"):
            existe = unidad_existe(unidad)
            activa = existe and unidad_activa(unidad)
            piezas[unidad] = {
                "descripcion": ("Bucle que recorre las 25 celdas" if unidad == "m1-runner"
                                else "Publica el estado de la rejilla para la web"),
                "ok": activa,
                "detalle": "activa" if activa else ("parada" if existe else "no instalada"),
            }
            if existe and not activa:
                rc, salida = systemctl("restart", f"{unidad}.service")
                log(f"{unidad} parada -> systemctl restart (rc={rc}) {salida[:120]}")
                acciones.append({"cuando": ahora.isoformat(), "que": f"reinicio {unidad}", "rc": rc})

        # --- 3. ¿La celda en curso avanza? ---
        estancada = None
        try:
            estado = json.loads((args.base / "estado.json").read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            estado = {}
        celda = estado.get("celda_en_curso")
        if celda and sqx_vivo:
            txt = sqx(args.cli, f"-project action=status name={celda}", timeout=30) or ""
            generadas = generadas_de(txt)
            if celda != ultima_celda:
                ultima_celda, ultimas_generadas, sin_avanzar_desde = celda, generadas, None
            elif generadas is not None and generadas == ultimas_generadas:
                sin_avanzar_desde = sin_avanzar_desde or time.time()
                minutos = (time.time() - sin_avanzar_desde) / 60
                estancada = round(minutos, 1)
                if minutos >= ESTANCADA_MIN:
                    sqx(args.cli, f"-project action=stop name={celda}", timeout=60)
                    log(f"{celda} llevaba {minutos:.0f} min sin generar ni una estrategia: la paro para que el bucle siga")
                    acciones.append({"cuando": ahora.isoformat(), "que": f"parada de {celda} por estancamiento", "rc": 0})
                    sin_avanzar_desde = None
            else:
                ultimas_generadas, sin_avanzar_desde = generadas, None
        piezas["celda_en_curso"] = {
            "descripcion": "La celda que StrategyQuant está construyendo ahora",
            "ok": bool(celda),
            "detalle": (f"{celda}, minutos sin avanzar: {estancada}" if celda else "ninguna en curso"),
        }

        # --- 4. Disco y memoria ---
        uso = shutil.disk_usage(str(args.base))
        libre_pct = round(uso.free / uso.total * 100, 1)
        piezas["disco"] = {
            "descripcion": "Espacio libre en el servidor",
            "ok": libre_pct >= 10,
            "detalle": f"{libre_pct} % libre ({uso.free // 2**30} GB de {uso.total // 2**30} GB)",
        }
        try:
            campos = dict(re.findall(r"(\w+):\s+(\d+) kB", Path("/proc/meminfo").read_text()))
            libre_mb = int(campos.get("MemAvailable", 0)) // 1024
            piezas["memoria"] = {"descripcion": "Memoria disponible", "ok": libre_mb > 2048,
                                 "detalle": f"{libre_mb} MB disponibles"}
            carga = os.getloadavg()[0]
            piezas["carga"] = {"descripcion": "Carga de la máquina (1 min)", "ok": True,
                               "detalle": f"{carga:.2f} sobre {os.cpu_count()} hilos"}
        except Exception as exc:  # noqa: BLE001
            piezas["memoria"] = {"descripcion": "Memoria disponible", "ok": None, "detalle": f"no medible: {exc}"}

        salud = {
            "schema": "ultrarentable.supervisor.v1",
            "medido": ahora.isoformat(),
            "todo_en_pie": all(p["ok"] for p in piezas.values() if p["ok"] is not None),
            "piezas": piezas,
            "ultimas_acciones": acciones[-20:],
        }
        _escribir(ruta_salud, salud)

        # --- 5. La rejilla completa, calculada aquí y publicada ya lista ---
        # La web no habla con StrategyQuant: lee este fichero por HTTPS. Así el panel dice la
        # verdad aunque el PC esté apagado, y el puerto de comandos no sale nunca de la máquina.
        _escribir(args.base / "rejilla.json",
                  _rejilla(args.cli, estado, salud, respuesta, args.base))

        for _ in range(SONDEO_SEG):
            if _parar:
                break
            time.sleep(1)

    log("supervisor detenido")
    return 0


if __name__ == "__main__":
    sys.exit(main())
