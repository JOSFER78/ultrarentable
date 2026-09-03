#!/usr/bin/env python3
"""Genera (y opcionalmente carga) los 25 proyectos FONDEO_<SIMBOLO>_<TF> en StrategyQuant X headless.

Se ejecuta EN EL SERVIDOR donde vive el SQX automático (Hetzner, `/opt/SQX-headless`, modo
comandos en el puerto 5051), con el python3 del sistema. No depende del repo.

Qué hace, y por qué así (medido el 2026-09-03, ver orchestration/tablero/A20.md):

- SQX guarda UNA temporalidad base por símbolo y deriva las demás. Los cinco símbolos micro
  (MES, MNQ, MYM, MGC, MCL) tienen base M1 de 2023.01.02 a 2026.08.30; cada proyecto pide su
  marco temporal (M1/M5/M15/H1/H4) sobre ese mismo símbolo.
- Un proyecto por celda, con UN solo <Setup>. El proyecto antiguo Ultra_Matrix metía 97 Setups en
  una tarea y SQX solo usaba el primero (AUDUSD_H1): eso explicaba 37 ciclos con 0 aceptadas.
- Plantilla: la tarea Build del proyecto de futuros "NQ BREAKOUT FUTURES H1 - Tradestation" (motor
  Tradestation, comisión por contrato, spread y deslizamiento en ticks). Se cambian solo los datos,
  las fechas, el OOS, los costes, la sesión, las condiciones de aceptación y la parada.
- Filtros PERMISIVOS a propósito (orden de Emilio: "no te pongas tan exquisito en SQX; luego
  depuramos en M2/M3"). El criterio 1.1 lo aplica el motor propio en M2, no SQX.
- Costes por contrato y operación completa: SUPUESTOS documentados (tarifa de bolsa + bróker barato)
  hasta que la lista de operaciones del piloto confirme cómo los aplica SQX. Ver COSTES abajo.

Uso (en el servidor):
  python3 generar_proyectos_fondeo_sqx.py --template /opt/SQX-headless/import/NQ_TS.cfx \
      --out /opt/SQX-headless/import/fondeo [--solo MNQ_H1] [--cargar] [--horas 2]

`--cargar` hace `-project action=loadconfig` por cada .cfx generado (crea el proyecto en SQX).
Nunca arranca nada: arrancar es `-project action=start name=FONDEO_MNQ_H1`, a mano y de uno en uno.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
import urllib.request
import zipfile
from pathlib import Path

# Universo FONDEO: 8 activos x 5 marcos = 40 celdas (Emilio, 03-09). Cada símbolo micro se genera
# solo si StrategyQuant ya tiene sus datos cargados; los que no, se saltan avisando.
SIMBOLOS = ["MES", "MNQ", "MYM", "M2K", "MGC", "MCL", "UB", "M6E"]
MARCOS = ["M1", "M5", "M15", "H1", "H4"]

# Costes por símbolo: spread y deslizamiento en TICKS; comisión en USD por contrato y operación
# completa (ida y vuelta), método "SizeBased" de SQX. SUPUESTOS a verificar en el piloto:
#   MES/MNQ/MYM: bolsa CME ~0,60-0,65 USD/lado + bróker ~0,30-0,35 USD/lado -> ~2,00 USD ida y vuelta
#   MGC/MCL:     bolsa ~0,70-0,80 USD/lado + bróker ~0,35 USD/lado          -> ~2,40 USD ida y vuelta
COSTES = {
    "MES": {"spread": 1, "slippage": 2, "comision": 2.00},
    "MNQ": {"spread": 1, "slippage": 2, "comision": 2.00},
    "MYM": {"spread": 1, "slippage": 2, "comision": 2.00},
    "M2K": {"spread": 1, "slippage": 2, "comision": 2.00},
    "MGC": {"spread": 1, "slippage": 2, "comision": 2.40},
    "MCL": {"spread": 1, "slippage": 2, "comision": 2.40},
    "UB": {"spread": 1, "slippage": 2, "comision": 2.60},
    "M6E": {"spread": 1, "slippage": 2, "comision": 2.00},
}

# Condiciones de aceptación DELIBERADAMENTE PERMISIVAS (orden de Emilio: "no te pongas tan exquisito
# con los filtros en SQX, luego depuramos en M2/M3"). El criterio 1.1 lo aplica el motor propio.
#
# Medido el 03-09 con los umbrales anteriores (factor de beneficio 1,2 · retorno/caída 2 · aciertos
# 30 %): en 1 hora StrategyQuant aceptaba el 16 % (Nasdaq 1h, 20.000 en banco), pero en 1 minuto y en
# 5 minutos rechazaba el **100 %** (2.158 y 56 probadas, cero aceptadas). Con la fricción real de un
# micro (1 tick de diferencial, 2 de deslizamiento, ~2 USD por contrato ida y vuelta), los marcos
# rápidos casi no dejan margen bruto. Bajar el listón aquí no relaja nada: solo evita que la celda
# entregue un banco vacío y deja que sea M2, con el criterio sellado, quien decida.
MIN_OPS_MES = {"M1": 20, "M5": 10, "M15": 5, "H1": 2, "H4": 1}
MIN_PF = 1.05
MIN_RET_DD = 0.5
MIN_WIN_PCT = 20

FECHA_DESDE = "2023.01.02"
FECHA_HASTA = "2026.08.30"
OOS_FRACCION = 0.20  # tramo final reservado


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cli(base: str, cmd: str, timeout: int = 180) -> str:
    """Llama al modo de comandos de SQX. Solo los espacios van codificados (%20); el resto, literal."""
    url = f"{base}/call?cmd=" + cmd.replace(" ", "%20")
    with urllib.request.urlopen(url, timeout=timeout) as r:  # noqa: S310 (localhost)
        return r.read().decode("utf-8", errors="replace")


def simbolos_en_sqx(base: str) -> dict[str, tuple[str, str, str]]:
    """{simbolo: (tf_base, desde, hasta)} leído de `-symbol action=list`."""
    out: dict[str, tuple[str, str, str]] = {}
    for line in cli(base, "-symbol action=list").splitlines():
        parts = [p.strip('"') for p in line.strip().split(",")]
        if len(parts) >= 6 and parts[0] in SIMBOLOS:
            out[parts[0]] = (parts[2], parts[4], parts[5])
    return out


def oos_desde(desde: str, hasta: str) -> str:
    d0 = dt.datetime.strptime(desde, "%Y.%m.%d").date()
    d1 = dt.datetime.strptime(hasta, "%Y.%m.%d").date()
    dias = (d1 - d0).days
    return (d1 - dt.timedelta(days=round(dias * OOS_FRACCION))).strftime("%Y.%m.%d")


def sustituir_una_vez(texto: str, patron: str, nuevo: str, etiqueta: str) -> str:
    n = len(re.findall(patron, texto, flags=re.S))
    if n != 1:
        raise SystemExit(f"plantilla inesperada: '{etiqueta}' aparece {n} veces (esperaba 1)")
    return re.sub(patron, nuevo, texto, count=1, flags=re.S)


def condicion(columna: str, valor: str, fmt: str = "Decimal2") -> str:
    return (
        '      <Condition use="true">\n'
        '        <Left-Side valueType="column">\n'
        f'          <Column-Value column="{columna}" columnType="0" format="{fmt}" resultType="main" '
        'direction="0" sampleType="10" plType="10" confidenceLevel="50" market="1" subresult="30" '
        f'pctRatio="0" class="{columna}" />\n'
        "        </Left-Side>\n"
        '        <Comparator value="&gt;" />\n'
        '        <Right-Side valueType="numeric">\n'
        f'          <Numeric-Value value="{valor}" />\n'
        "        </Right-Side>\n"
        "      </Condition>\n"
    )


def build_task(plantilla: str, sym: str, tf: str, desde: str, hasta: str, horas: int) -> str:
    c = COSTES[sym]
    t = plantilla

    # 1) Datos: un único Setup con el símbolo micro, el marco de la celda y los costes.
    setup = (
        f'      <Setup dateFrom="{desde}" dateTo="{hasta}" testPrecision="1" session="No Session" '
        f'slippage="{c["slippage"]}" minDist="0" engine="Tradestation">\n'
        f'        <Chart symbol="{sym}" timeframe="{tf}" spread="{c["spread"]}" />\n'
        "        <Commissions>\n"
        '          <Method type="SizeBased" use="true">\n'
        "            <Params>\n"
        f'              <Param key="Commission" className="SizeBased">{c["comision"]}</Param>\n'
        "            </Params>\n"
        "          </Method>\n"
        "        </Commissions>\n"
        '        <Swap use="false" type="money" long="0" short="0" tripleSwapOn="WEDNESDAY" />\n'
        "      </Setup>\n"
    )
    t = sustituir_una_vez(t, r"<Setups>.*?</Setups>", "<Setups>\n" + setup + "    </Setups>", "Setups de datos")

    # 2) OOS: tramo final dentro del rango de la celda.
    t = sustituir_una_vez(
        t,
        r'<OutOfSample showGraph="false">\s*<Range dateFrom="[0-9.]+" dateTo="[0-9.]+" />\s*</OutOfSample>',
        f'<OutOfSample showGraph="false">\n      <Range dateFrom="{oos_desde(desde, hasta)}" dateTo="{hasta}" />\n    </OutOfSample>',
        "OutOfSample",
    )

    # 3) Sesión: los símbolos micro se importaron sin sesión de bolsa definida.
    t = sustituir_una_vez(t, r'<Param key="Session" className="SessionOption">[^<]*</Param>',
                          '<Param key="Session" className="SessionOption">No Session</Param>', "Session")

    # 4) Condiciones de aceptación permisivas.
    conds = (
        condicion("AvgTradesPerMonth", str(MIN_OPS_MES[tf]))
        + condicion("ProfitFactor", str(MIN_PF))
        + condicion("ReturnDDRatio", str(MIN_RET_DD))
        + condicion("WinningPct", str(MIN_WIN_PCT), "Decimal2Pct")
    )
    t = sustituir_una_vez(t, r"<Conditions>\s*<Condition use=\"true\">.*?</Conditions>\s*<AutomaticDismissal",
                          "<Conditions>\n" + conds + "    </Conditions>\n    <AutomaticDismissal", "Conditions de ranking")

    # 5) Parada: la gobierna EL TIEMPO. El tope de banco se pone deliberadamente alto (100.000) para
    #    que nunca sea él quien pare: así cada celda recibe exactamente las mismas horas de máquina y
    #    el caudal por hora es comparable entre celdas. La evolución se reinicia sola al estancarse
    #    (EvoRestartOnStagnation, ya en la plantilla), que es lo que da variedad dentro de la hora.
    t = sustituir_una_vez(t, r'<StopCondition type="databank-full"[^>]*/>',
                          f'<StopCondition type="databank-full" passedStrategies="100000" restartCount="0" days="0" hours="{horas}" minutes="0" />',
                          "StopCondition")

    # 6) La prueba en mercados adicionales está desactivada, pero que no apunte a un símbolo ajeno.
    t = t.replace('<Chart symbol="@ES" timeframe="M30" spread="0" />', f'<Chart symbol="{sym}" timeframe="{tf}" spread="0" />')

    # 7) Recursos incrustados de la plantilla (@NQ/@ES de otra instalación): fuera. SQX resuelve el
    #    símbolo por nombre en su gestor de datos.
    t = sustituir_una_vez(t, r"<Symbols>.*?</Symbols>", "<Symbols />", "Resources/Symbols")
    return t


def config_xml(plantilla: str, nombre: str) -> str:
    c = sustituir_una_vez(plantilla, r'<Project name="[^"]*"', f'<Project name="{nombre}"', "Project name")
    tareas = ('<Tasks>\n'
              '    <Task type="Build" name="Generar" showSettingsOverview="false" sampleName="Custom" '
              'active="true" taskXMLFile="Build-Task1.xml" />\n'
              '  </Tasks>')
    return sustituir_una_vez(c, r"<Tasks>.*?</Tasks>", tareas, "Tasks")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--template", type=Path, required=True, help="project.cfx de la plantilla de futuros (copia con ruta sin espacios)")
    ap.add_argument("--out", type=Path, required=True, help="carpeta de salida para los .cfx y el manifiesto")
    ap.add_argument("--cli", default="http://127.0.0.1:5051", help="modo de comandos de SQX")
    ap.add_argument("--solo", default="", help="una celda, p. ej. MNQ_H1 (por defecto las 25)")
    ap.add_argument("--horas", type=int, default=2, help="tope de horas por construcción")
    ap.add_argument("--cargar", action="store_true", help="loadconfig de cada .cfx generado (crea el proyecto)")
    args = ap.parse_args()

    with zipfile.ZipFile(args.template) as z:
        # La plantilla viene con finales de línea CRLF: se normaliza antes de tocar nada.
        plantilla_build = z.read("Build-Task1.xml").decode("utf-8").replace("\r\n", "\n")
        plantilla_config = z.read("config.xml").decode("utf-8").replace("\r\n", "\n")

    en_sqx = simbolos_en_sqx(args.cli)
    faltan = [s for s in SIMBOLOS if s not in en_sqx]
    if faltan:
        # No es un error: es el estado real del universo mientras se completan las descargas.
        # Se generan las celdas de los símbolos que SÍ tienen datos y se dice cuáles quedan.
        print(f"AVISO: sin datos en StrategyQuant todavía -> {faltan} ({len(faltan) * 5} celdas pendientes)")
    presentes = [s for s in SIMBOLOS if s in en_sqx]
    if not presentes:
        raise SystemExit("NO DATA: ningún símbolo del universo tiene datos en SQX. No genero nada.")
    for s, (tfb, d0, d1) in ((k, v) for k, v in en_sqx.items() if k in SIMBOLOS):
        if tfb != "M1":
            raise SystemExit(f"{s}: base {tfb}, esperaba M1 (SQX solo deriva marcos superiores a la base)")
        if d0 != FECHA_DESDE or d1 != FECHA_HASTA:
            print(f"AVISO {s}: rango en SQX {d0}->{d1} distinto del esperado {FECHA_DESDE}->{FECHA_HASTA}; uso el de SQX")

    celdas = [(s, tf) for s in presentes for tf in MARCOS]
    if args.solo:
        s, tf = args.solo.split("_")
        celdas = [(s, tf)]

    args.out.mkdir(parents=True, exist_ok=True)
    manifiesto = {
        "schema": "ultrarentable.sqx.fondeo_proyectos.v2",
        "creado": dt.datetime.now(dt.UTC).isoformat(),
        "plantilla": str(args.template),
        "plantilla_sha256": sha256(args.template),
        "costes_supuestos": COSTES,
        "aceptacion": {"min_ops_mes": MIN_OPS_MES, "min_pf": MIN_PF, "min_ret_dd": MIN_RET_DD, "min_win_pct": MIN_WIN_PCT},
        "oos_fraccion": OOS_FRACCION,
        "horas_tope": args.horas,
        "universo": SIMBOLOS,
        "sin_datos_todavia": faltan,
        "proyectos": [],
    }
    for s, tf in celdas:
        nombre = f"FONDEO_{s}_{tf}"
        _, d0, d1 = en_sqx[s]
        destino = args.out / f"{nombre}.cfx"
        with zipfile.ZipFile(destino, "w", compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("config.xml", config_xml(plantilla_config, nombre))
            z.writestr("Build-Task1.xml", build_task(plantilla_build, s, tf, d0, d1, args.horas))
        fila = {"proyecto": nombre, "simbolo": s, "tf": tf, "desde": d0, "hasta": d1,
                "oos_desde": oos_desde(d0, d1), "cfx": str(destino), "sha256": sha256(destino), "cargado": None}
        if args.cargar:
            resp = cli(args.cli, f"-project action=loadconfig name={nombre} file={destino}")
            fila["cargado"] = "Project loaded" in resp
            print(f"{nombre}: {'CARGADO' if fila['cargado'] else 'ERROR -> ' + resp.strip()[:160]}")
        else:
            print(f"{nombre}: generado ({destino.name}, OOS desde {fila['oos_desde']})")
        manifiesto["proyectos"].append(fila)

    (args.out / "manifiesto.json").write_text(json.dumps(manifiesto, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"manifiesto: {args.out / 'manifiesto.json'} ({len(celdas)} proyectos)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
