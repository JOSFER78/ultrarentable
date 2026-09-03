#!/usr/bin/env python3
"""Bucle M1: recorre las 25 celdas FONDEO en StrategyQuant X, una a una, 24/7 y sin vigilancia.

Vive en el servidor del StrategyQuant automático (Hetzner, `/opt/SQX-headless`) y habla con su modo
de comandos (puerto 5051). Lo arranca systemd (`m1-runner.service`, Restart=always), así que
sobrevive a un fallo del proceso y a un reinicio de la máquina.

Cómo funciona, y por qué así:

- **Una celda a la vez.** StrategyQuant ya usa los 8 hilos de la máquina en una sola construcción
  (medido: carga 7,1 con un proyecto). Dos a la vez no darían el doble, se estorbarían.
- **El tiempo manda.** Cada celda recibe las mismas horas de máquina, así que las estrategias por
  hora son comparables entre celdas. Es la cifra de caudal que M1 tiene que entregar.
- **El estado vive en disco** (`estado.json`), se reescribe de forma atómica después de cada paso.
  Si el proceso muere a mitad, al arrancar retoma exactamente donde estaba y adopta la construcción
  que siguiera viva en StrategyQuant en vez de duplicarla.
- **Rondas.** Cuando las 25 celdas están hechas, empieza otra ronda sobre los mismos proyectos. El
  banco de estrategias acumula, y cada ronda deja su propio CSV con su huella SHA-256.
- **Nunca borra nada.** Solo escribe CSVs nuevos y el estado.

Uso:
  python3 m1_runner_sqx.py --base /opt/SQX-headless/import/fondeo [--horas 1] [--una-ronda]
  python3 m1_runner_sqx.py --base ... --informe     # imprime el estado y sale
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import signal
import sys
import time
import urllib.request
from pathlib import Path

# Orden de prioridad por rendimiento medido (A45):
# H1 y H4 entregan el 98% de las estrategias al banco; M15 intermedio; M5 y M1 al final.
PRIORIDAD_MARCOS = ["H1", "H4", "M15", "M5", "M1"]


def clave_orden_celda(celda: str, prioridad: list[str] = PRIORIDAD_MARCOS) -> tuple[int, str]:
    partes = celda.split("_")
    tf = partes[-1] if len(partes) >= 3 else ""
    sym = partes[1] if len(partes) >= 3 else ""
    try:
        prio_tf = prioridad.index(tf)
    except ValueError:
        prio_tf = 999
    return (prio_tf, sym)


def ordenar_celdas_por_rendimiento(celdas: list[str], prioridad: list[str] = PRIORIDAD_MARCOS) -> list[str]:
    """Ordena las celdas de mayor a menor rendimiento medido preservando todos los elementos."""
    return sorted(celdas, key=lambda c: clave_orden_celda(c, prioridad))


def celdas_del_manifiesto(base: "Path") -> list[str]:
    """La lista de celdas sale del manifiesto que escribe el generador, no de una constante.

    Así, cuando entra un activo nuevo (se descargan sus datos y se regeneran los proyectos), el
    bucle lo recoge en la siguiente vuelta sin tocar este fichero ni perder lo ya hecho.
    Las celdas se ordenan por rendimiento medido (A45): H1 y H4 primero, M5 y M1 al final.
    """
    try:
        m = json.loads((base / "manifiesto.json").read_text(encoding="utf-8"))
        celdas = [p["proyecto"] for p in m.get("proyectos", [])]
        if celdas:
            return ordenar_celdas_por_rendimiento(celdas)
    except Exception:  # noqa: BLE001
        pass
    default_celdas = [f"FONDEO_{s}_{tf}" for s in ["MES", "MNQ", "MYM", "MGC", "MCL"]
                      for tf in ["M1", "M5", "M15", "H1", "H4"]]
    return ordenar_celdas_por_rendimiento(default_celdas)

SONDEO_SEG = 60          # cada cuánto se pregunta el estado
QUIETO_PARA_FIN = 3      # sondeos seguidos con el mismo tiempo de ejecución = terminada
# Margen sobre el tope de horas antes de pararla a la fuerza. Era 25 minutos por si la parada
# propia de StrategyQuant llegaba tarde; medido el 03-09, esa parada **no funciona**: la celda
# FONDEO_MES_M5, configurada con `<StopCondition ... hours="1">`, seguia construyendo a 1 h 14 min.
# Quien para de verdad es este bucle, asi que el margen baja a 3 minutos: son 22 minutos ganados
# por celda, casi 15 horas por ronda de 40.
MARGEN_MIN = 3

_parar = False


def _senal(_signo, _marco):
    global _parar
    _parar = True


class Registro:
    def __init__(self, ruta: Path):
        self.ruta = ruta

    def __call__(self, msg: str) -> None:
        linea = f"{dt.datetime.now(dt.UTC):%Y-%m-%d %H:%M:%S} UTC  {msg}"
        print(linea, flush=True)
        with self.ruta.open("a", encoding="utf-8") as fh:
            fh.write(linea + "\n")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cli(base_url: str, cmd: str, timeout: int = 180) -> str:
    url = f"{base_url}/call?cmd=" + cmd.replace(" ", "%20")
    for intento in range(3):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as r:  # noqa: S310 (localhost)
                return r.read().decode("utf-8", errors="replace")
        except Exception as exc:  # el servidor de comandos puede estar ocupado; se reintenta
            if intento == 2:
                return f"ERROR_CLI: {exc}"
            time.sleep(10)
    return "ERROR_CLI: inalcanzable"


def segundos_de_tiempo(crudo: str) -> int:
    """Convierte el tiempo que escribe StrategyQuant a segundos.

    Acepta las formas que da el programa en espanol y en ingles: "17 min. 58 s.",
    "1 hr. 14 min.", "4 hrs. 29 min.", "2 h. 5 min.", "850 ms.". Las horas cuentan: antes se
    escapaban del patron ("hrs." no casa con "h\\.") y una celda de dos horas se leia como si
    llevara veinte minutos.
    """
    seg = 0
    for valor, unidad in re.findall(r"(\d+)\s*(hrs|hr|h|min|ms|s)\.", crudo):
        seg += int(valor) * {"hrs": 3600, "hr": 3600, "h": 3600, "min": 60, "s": 1, "ms": 0}[unidad]
    return seg


def leer_estado_proyecto(base_url: str, proyecto: str) -> dict:
    """Devuelve {generadas, en_banco, seg_ejecucion, por_hora, aceptadas_por_hora} o {} si no se pudo."""
    txt = cli(base_url, f"-project action=status name={proyecto}", timeout=120)
    if txt.startswith("ERROR_CLI") or "does not exist" in txt:
        return {}
    def num(patron: str) -> float | None:
        m = re.search(patron, txt)
        if not m:
            return None
        return float(m.group(1).replace(".", "").replace(",", ".")) if "," in m.group(1) else float(m.group(1).replace(".", ""))
    out: dict = {}
    m = re.search(r"Estrategias generadas\s+([\d.]+)", txt)
    out["generadas"] = int(m.group(1).replace(".", "")) if m else 0
    m = re.search(r"En la base de datos\s+([\d.]+)", txt)
    out["en_banco"] = int(m.group(1).replace(".", "")) if m else 0
    m = re.search(r"Estrategias por hora\s+([\d.,]+)", txt)
    out["por_hora"] = m.group(1) if m else "0"
    m = re.search(r"Estrategias aceptadas por hora\s+([\d.,]+)", txt)
    out["aceptadas_por_hora"] = m.group(1) if m else "0"
    m = re.search(r"Aceptado\s+([\d.,]+)\s*%", txt)
    out["aceptado_pct"] = m.group(1) if m else "0"
    # "Tiempo de funcionamiento hasta ahora  17 min. 58 s." pero tambien, sin ningun espacio
    # porque StrategyQuant rellena la columna a lo ancho: "...hasta ahora4 hrs. 29 min.".
    # Medido el 03-09 con `cat -A`. Con `\s+` la linea larga no casaba, el tiempo se leia como 0
    # en cada sondeo y el bucle daba la celda por "parada sola" a los 3 minutos dejandola viva:
    # asi se acumularon 29 proyectos construyendo a la vez sobre 8 hilos. Ver #M1-PARADA-FALSA.
    m = re.search(r"Tiempo de funcionamiento hasta ahora\s*(.+)", txt)
    crudo = m.group(1).strip() if m else ""
    out["seg_ejecucion"] = segundos_de_tiempo(crudo)
    out["tiempo_crudo"] = crudo
    return out


def guardar(estado: dict, ruta: Path) -> None:
    tmp = ruta.with_suffix(".tmp")
    tmp.write_text(json.dumps(estado, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, ruta)


def estado_inicial(horas: int, CELDAS: list) -> dict:
    return {
        "schema": "ultrarentable.m1.runner.v1",
        "creado": dt.datetime.now(dt.UTC).isoformat(),
        "horas_por_celda": horas,
        "ronda": 1,
        "celda_en_curso": None,
        "celdas": {c: {"estado": "PENDIENTE", "rondas": []} for c in CELDAS},
    }


def parar_proyecto(base_url: str, proyecto: str, log: Registro) -> bool:
    """Manda parar y comprueba que de verdad paró. Devuelve True si dejó de avanzar.

    Es obligatorio antes de pasar a la celda siguiente: una celda que se abandona sin parar
    sigue construyendo y se lleva su parte de los 8 hilos. El 03-09 asi se juntaron 29
    construcciones a la vez y el caudal por celda cayo de 4.368/h a ~500/h.
    """
    cli(base_url, f"-project action=stop name={proyecto}")
    time.sleep(20)
    a = leer_estado_proyecto(base_url, proyecto)
    time.sleep(SONDEO_SEG)
    b = leer_estado_proyecto(base_url, proyecto)
    if a and b and (a.get("generadas"), a.get("seg_ejecucion")) == (b.get("generadas"), b.get("seg_ejecucion")):
        return True
    log(f"  {proyecto}: AVISO, le he mandado parar y sigue avanzando; lo repito")
    cli(base_url, f"-project action=stop name={proyecto}")
    time.sleep(30)
    c = leer_estado_proyecto(base_url, proyecto)
    quieta = bool(b and c and (b.get("generadas"), b.get("seg_ejecucion")) == (c.get("generadas"), c.get("seg_ejecucion")))
    if not quieta:
        log(f"  {proyecto}: NO PARA. Sigue construyendo y le robara hilos a la siguiente celda.")
    return quieta


def esperar_fin(base_url: str, proyecto: str, tope_seg: int, log: Registro) -> dict:
    """Sondea hasta que la construcción deja de avanzar o se agota el tope. Devuelve el último estado.

    El avance se mide por **dos** señales: el tiempo de funcionamiento y las estrategias
    generadas. El tiempo solo no vale — cuando StrategyQuant lo escribe pegado a la etiqueta se
    lee como 0 y una celda viva parece parada (#M1-PARADA-FALSA, 03-09). Las generadas suben
    siempre que la construccion respira.
    """
    ultimo_avance = (-1, -1)
    quieto = 0
    inicio = time.time()
    ultimo: dict = {}
    while not _parar:
        time.sleep(SONDEO_SEG)
        st = leer_estado_proyecto(base_url, proyecto)
        if not st:
            log(f"  {proyecto}: el modo de comandos no responde; reintento en el siguiente sondeo")
            continue
        ultimo = st
        avance = (st["generadas"], st["seg_ejecucion"])
        if avance == ultimo_avance:
            quieto += 1
            if quieto >= QUIETO_PARA_FIN:
                log(f"  {proyecto}: parada sola tras {st['tiempo_crudo'] or '?'} ({st['generadas']} generadas, {st['en_banco']} en banco)")
                parar_proyecto(base_url, proyecto, log)
                return ultimo
        else:
            if quieto:
                quieto = 0
            ultimo_avance = avance
            transcurrido = int(time.time() - inicio)
            if transcurrido % (SONDEO_SEG * 10) < SONDEO_SEG:
                log(f"  {proyecto}: {st['tiempo_crudo'] or '?'}, {st['generadas']} generadas, {st['en_banco']} en banco, {st['por_hora']}/h")
        if time.time() - inicio > tope_seg:
            log(f"  {proyecto}: alcanzado el tope duro ({tope_seg // 60} min); la paro yo")
            parar_proyecto(base_url, proyecto, log)
            return leer_estado_proyecto(base_url, proyecto) or ultimo
    return ultimo


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", type=Path, default=Path("/opt/SQX-headless/import/fondeo"))
    ap.add_argument("--cli", default="http://127.0.0.1:5051")
    ap.add_argument("--horas", type=int, default=1, help="horas de máquina por celda (solo al crear el estado)")
    ap.add_argument("--una-ronda", action="store_true", help="parar al completar la ronda en curso")
    ap.add_argument("--informe", action="store_true", help="imprimir el estado y salir")
    args = ap.parse_args()

    signal.signal(signal.SIGTERM, _senal)
    signal.signal(signal.SIGINT, _senal)

    args.base.mkdir(parents=True, exist_ok=True)
    (args.base / "resultados").mkdir(exist_ok=True)
    ruta_estado = args.base / "estado.json"
    log = Registro(args.base / "m1_runner.log")

    CELDAS = celdas_del_manifiesto(args.base)
    estado = json.loads(ruta_estado.read_text(encoding="utf-8")) if ruta_estado.exists() else estado_inicial(args.horas, CELDAS)

    # Salvaguarda A51: Si el manifiesto tiene menos celdas que las registradas en estado.json,
    # significa que el manifiesto fue truncado o corrompido accidentalmente.
    # En ese caso, avisar en el log y adoptar el universo completo de estado.json.
    if ruta_estado.exists() and len(CELDAS) < len(estado.get("celdas", {})):
        log(f"AVISO CRÍTICO UNIVERSO: manifiesto.json tiene solo {len(CELDAS)} celdas pero estado.json tiene {len(estado['celdas'])}. Adopto el universo completo de estado.json.")
        CELDAS = ordenar_celdas_por_rendimiento(list(estado["celdas"].keys()))

    # Celdas nuevas (activo recién descargado) entran como PENDIENTE sin tocar lo ya hecho.
    nuevas = [c for c in CELDAS if c not in estado["celdas"]]
    if nuevas:
        for c in nuevas:
            estado["celdas"][c] = {"estado": "PENDIENTE", "rondas": []}
        guardar(estado, ruta_estado)

    if args.informe:
        print(json.dumps({
            "ronda": estado["ronda"],
            "en_curso": estado["celda_en_curso"],
            "celdas": len(estado["celdas"]),
            "hechas": sum(1 for c in estado["celdas"].values() if c["estado"] == "HECHA"),
            "pendientes": sum(1 for c in estado["celdas"].values() if c["estado"] == "PENDIENTE"),
            "celdas": {k: {"estado": v["estado"], "rondas": len(v["rondas"]),
                           "ultimo_banco": (v["rondas"][-1]["en_banco"] if v["rondas"] else None)}
                       for k, v in estado["celdas"].items()},
        }, indent=1, ensure_ascii=False))
        return 0

    horas = estado["horas_por_celda"]
    tope_seg = horas * 3600 + MARGEN_MIN * 60
    log(f"=== runner M1 arrancado · ronda {estado['ronda']} · {len(CELDAS)} celdas · {horas} h por celda · tope duro {tope_seg // 60} min ===")
    if nuevas:
        log(f"celdas nuevas en el universo: {', '.join(nuevas)}")

    # Limpieza de arranque: nadie construye salvo la celda que este bucle tenga en curso.
    # Un proceso que muere (o un fallo como #M1-PARADA-FALSA) deja celdas vivas que siguen
    # comiendo hilos para siempre; al arrancar se paran todas y se empieza con la maquina limpia.
    en_curso = estado.get("celda_en_curso")
    vivas = []
    for c in CELDAS:
        if c == en_curso:
            continue
        st0 = leer_estado_proyecto(args.cli, c)
        if st0 and (st0.get("seg_ejecucion", 0) > 0 or st0.get("generadas", 0) > 0):
            st1 = leer_estado_proyecto(args.cli, c)
            if st1 and (st1.get("generadas"), st1.get("seg_ejecucion")) != (st0.get("generadas"), st0.get("seg_ejecucion")):
                vivas.append(c)
    if vivas:
        log(f"limpieza de arranque: {len(vivas)} celdas seguian construyendo sin permiso: {', '.join(vivas)}")
        for c in vivas:
            parar_proyecto(args.cli, c, log)
        log("limpieza de arranque terminada")

    while not _parar:
        # 1) ¿Había una celda a medias (reinicio del proceso o de la máquina)?
        celda = estado.get("celda_en_curso")
        if celda:
            log(f"retomo {celda}, que quedó a medias")
            st = leer_estado_proyecto(args.cli, celda)
            if st and st["seg_ejecucion"] > 0:
                st_prev = st
                time.sleep(SONDEO_SEG)
                st = leer_estado_proyecto(args.cli, celda)
                if st and (st["generadas"], st["seg_ejecucion"]) != (st_prev["generadas"], st_prev["seg_ejecucion"]):
                    log(f"  {celda} sigue viva en StrategyQuant: la adopto en vez de relanzarla")
                    st = esperar_fin(args.cli, celda, tope_seg, log)
                else:
                    log(f"  {celda} ya no avanza: la doy por terminada")
                    parar_proyecto(args.cli, celda, log)
        else:
            # 2) Siguiente celda pendiente
            pendientes = [c for c in CELDAS if estado["celdas"][c]["estado"] == "PENDIENTE"]
            if not pendientes:
                if args.una_ronda:
                    log(f"ronda {estado['ronda']} completa y --una-ronda: paro")
                    break
                estado["ronda"] += 1
                for c in CELDAS:
                    estado["celdas"][c]["estado"] = "PENDIENTE"
                guardar(estado, ruta_estado)
                log(f"=== las 25 celdas hechas; empieza la ronda {estado['ronda']} ===")
                continue
            celda = pendientes[0]
            estado["celda_en_curso"] = celda
            estado["celdas"][celda]["estado"] = "EN_CURSO"
            guardar(estado, ruta_estado)

            cfx = args.base / f"{celda}.cfx"
            if not cfx.is_file():
                log(f"  {celda}: NO EXISTE {cfx}; la marco IMPOSIBLE y sigo")
                estado["celdas"][celda]["estado"] = "IMPOSIBLE"
                estado["celda_en_curso"] = None
                guardar(estado, ruta_estado)
                continue
            resp = cli(args.cli, f"-project action=loadconfig name={celda} file={cfx}")
            if "Project loaded" not in resp:
                log(f"  {celda}: loadconfig falló -> {resp.strip()[:200]}")
            log(f"--- arranco {celda} (ronda {estado['ronda']})")
            arranque = dt.datetime.now(dt.UTC)
            resp = cli(args.cli, f"-project action=start name={celda}")
            if "segundo plano" not in resp and "background" not in resp:
                log(f"  {celda}: el arranque no confirmó -> {resp.strip()[:200]}")
            st = esperar_fin(args.cli, celda, tope_seg, log)

        # 3) Volcar artefactos .sqx del banco a disco antes de exportar CSV
        dir_artefactos = args.base / "artefactos" / f"{celda}_r{estado['ronda']}"
        dir_artefactos.mkdir(parents=True, exist_ok=True)
        resp_volcado = cli(args.cli, f"-databank action=save project={celda} name=Results folder={dir_artefactos}", timeout=600)
        sqx_contados = len(list(dir_artefactos.glob("*.sqx"))) if dir_artefactos.is_dir() else 0
        log(f"  {celda}: artefactos volcados en {dir_artefactos} ({sqx_contados} ficheros .sqx)")

        # 4) Exportar el banco de esta celda con su huella
        csv = args.base / "resultados" / f"{celda}_r{estado['ronda']}.csv"
        cli(args.cli, f"-databank action=export project={celda} name=Results file={csv}", timeout=300)
        fila = {
            "ronda": estado["ronda"],
            "fin": dt.datetime.now(dt.UTC).isoformat(),
            "generadas": (st or {}).get("generadas"),
            "en_banco": (st or {}).get("en_banco"),
            "por_hora": (st or {}).get("por_hora"),
            "aceptadas_por_hora": (st or {}).get("aceptadas_por_hora"),
            "aceptado_pct": (st or {}).get("aceptado_pct"),
            "tiempo": (st or {}).get("tiempo_crudo"),
            "artefactos_dir": str(dir_artefactos) if sqx_contados > 0 else None,
            "artefactos_contados": sqx_contados,
            "csv": str(csv) if csv.is_file() else None,
            "csv_sha256": sha256(csv) if csv.is_file() else None,
            "csv_filas": (sum(1 for _ in csv.open("rb")) - 1) if csv.is_file() else None,
        }
        estado["celdas"][celda]["rondas"].append(fila)
        estado["celdas"][celda]["estado"] = "HECHA"
        estado["celda_en_curso"] = None
        guardar(estado, ruta_estado)
        hechas = sum(1 for c in estado["celdas"].values() if c["estado"] == "HECHA")
        log(f"=== {celda} HECHA · {fila['en_banco']} en banco · {fila['csv_filas']} filas en CSV · {hechas}/{len(CELDAS)} en esta ronda ===")

    log("runner M1 detenido")
    return 0


if __name__ == "__main__":
    sys.exit(main())
