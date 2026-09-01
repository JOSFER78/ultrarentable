#!/usr/bin/env python3
"""Genera un project.cfx NUEVO de StrategyQuant X para el carril FONDEO.

Corrige los dos bugs diagnosticados en `Ultra_Matrix` (ver
`orchestration/results/sqx_reconfiguracion_fondeo.md`):

1. **"Solo el primer Setup"**: el proyecto Ultra_Matrix mete 97 <Setup> dentro
   de un unico <Data><Setups>...</Setups> de un unico Build-Task. La plantilla
   por defecto de SQX (`internal/web/BUILDER/templates/tpl_build.xml`) solo
   trae UN <Setup> por Build-Task -- ese es el contrato real. Con 97, SQX usa
   el primero por orden alfabetico (AUDUSD) y descarta el resto en silencio:
   evidencia en 2.035/2.035 estrategias de `data/sqx_exports/toimprove_2026-08-31.csv`
   con Symbol (IS) == AUDUSD_H1.
   Aqui: **un Build-Task por celda simbolo x TF**, cada uno con un unico <Setup>.

2. **OOS decorativo (0,3 %)**: el <OutOfSample><Range> de Ultra_Matrix es la
   UNION global de fechas de las 97 celdas (min dateFrom / max dateTo de TODAS),
   no un tramo final anidado dentro del <Setup> activo -- rompe la convencion
   del propio template de SQX (donde el Range de OOS es SIEMPRE un subconjunto
   final del rango del Setup). Resultado medido: mediana 1 trade OOS vs
   mediana 326 IS (326/1 ~ ratio 0,27%).
   Aqui: el Range de OOS es el tramo final (>= OOS_FRACTION) DENTRO del rango
   propio de cada Setup.

Fuente de datos: CSVs Dukascopy ya en disco (`data/sqx_imports/dukascopy/`,
SOLO LECTURA) -- proxies CFD de futuros CME para el carril FONDEO:
USA500IDXUSD -> ES, USATECHIDXUSD -> NQ. USA30IDXUSD (proxy de YM) queda
FUERA porque su backfill todavia no existe en disco (ver comprobacion en el
propio script: --check-only lista que celdas tienen CSV y cuales no).

Este script NO toca `Ultra_Matrix` ni ningun fichero de produccion: escribe un
project.cfx NUEVO bajo `artifacts/sqx/import/` (gitignored, igual que
`scripts/create_sqx_improvement_project.py`) mas un manifiesto SHA-256. Los
datos referenciados (USA500IDXUSD/USATECHIDXUSD) todavia NO estan importados
en el data.db interno de SQX -- el proyecto generado no podra construir hasta
que se importen (comando exacto impreso al final, ver tambien el informe).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SQX_ROOT = Path("/home/ubuntu/StrategyQuantX144")
SRC_PROJECT_CFX = SQX_ROOT / "user/projects/Ultra_Matrix/project.cfx"
DUKAS_DIR = REPO_ROOT / "data/sqx_imports/dukascopy"
OUT_DIR = REPO_ROOT / "artifacts/sqx/import"
PROJECT_NAME = "Fondeo_ES_NQ_5m15m"

# label -> (instrumento Dukascopy en disco, TF SQX, comision $/trade)
# Comision heredada de services/... build_ultra_matrix.py FUT_COMM (ES/NQ = 2.4 $/trade,
# convencion PerTrade ya usada y auditada en el proyecto Ultra_Matrix vigente).
CELLS = [
    ("ES_M5", "USA500IDXUSD", "M5", 2.4),
    ("ES_M15", "USA500IDXUSD", "M15", 2.4),
    ("NQ_M5", "USATECHIDXUSD", "M5", 2.4),
    ("NQ_M15", "USATECHIDXUSD", "M15", 2.4),
]
# YM (proxy USA30IDXUSD) queda documentado pero excluido: sin backfill en disco todavia.
PENDING_CELLS = [("YM_M5", "USA30IDXUSD", "M5", 2.4), ("YM_M15", "USA30IDXUSD", "M15", 2.4)]

OOS_FRACTION = 0.20  # tramo final reservado a OOS dentro del rango propio del Setup


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def csv_date_range(instrument: str, tf: str) -> tuple[dt.date, dt.date, int]:
    """Lee dateFrom/dateTo/filas REALES del CSV Dukascopy en disco (sin cargarlo entero)."""
    path = DUKAS_DIR / f"{instrument}_{tf}.csv"
    if not path.is_file():
        raise FileNotFoundError(f"No existe {path} (backfill pendiente)")
    with path.open("rb") as fh:
        header = fh.readline()
        first = fh.readline().decode("utf-8").strip()
        fh.seek(0, 2)
        size = fh.tell()
        block = min(4096, size)
        fh.seek(size - block)
        tail = fh.read().decode("utf-8", errors="ignore").strip().splitlines()
        last = tail[-1]
    n_rows = sum(1 for _ in path.open("rb")) - 1  # menos cabecera
    d_from = dt.datetime.strptime(first.split(",")[0], "%Y.%m.%d %H:%M:%S").date()
    d_to = dt.datetime.strptime(last.split(",")[0], "%Y.%m.%d %H:%M:%S").date()
    return d_from, d_to, n_rows


def iso(d: dt.date) -> str:
    return d.strftime("%Y.%m.%d")


def setup_xml(symbol: str, tf: str, d_from: dt.date, d_to: dt.date, commission: float) -> str:
    return (
        f'      <Setup dateFrom="{iso(d_from)}" dateTo="{iso(d_to)}" testPrecision="1" '
        f'session="No Session" slippage="3" minDist="0" engine="MetaTrader4">\n'
        f'        <Chart symbol="{symbol}" timeframe="{tf}" spread="auto" spreadValue="0" />\n'
        f'        <Commissions>\n'
        f'          <Method type="PerTrade" use="true">\n'
        f'            <Params>\n'
        f'              <Param key="Commission" name="Commission" dataType="2" min="-1000.0" '
        f'max="1000.0" step="0.01" value="{commission}" description="Commission in $ per trade" '
        f'decimals="2" className="PerTrade" category="Default" engine="*" />\n'
        f'            </Params>\n'
        f'          </Method>\n'
        f'        </Commissions>\n'
        f'      </Setup>\n'
    )


def build_task_xml(template: str, setup_block: str, oos_from: dt.date, oos_to: dt.date) -> str:
    """Sustituye <Setups> y <OutOfSample> del template por los de UNA celda, deja el resto igual."""
    start = template.index("    <Setups>")
    end = template.index("    </Setups>") + len("    </Setups>")
    out = template[:start] + "    <Setups>\n" + setup_block + "    </Setups>" + template[end:]

    s = out.index("    <OutOfSample")
    e = out.index("</OutOfSample>") + len("</OutOfSample>")
    oos = (
        '    <OutOfSample showGraph="false">\n'
        f'      <Range dateFrom="{iso(oos_from)}" dateTo="{iso(oos_to)}" />\n'
        "    </OutOfSample>"
    )
    return out[:s] + oos + out[e:]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true", help="Solo audita CSVs disponibles, no genera nada")
    parser.add_argument("--out", type=Path, default=OUT_DIR / f"{PROJECT_NAME}.cfx")
    args = parser.parse_args()

    print(f"Fuente CSV (solo lectura): {DUKAS_DIR}")
    print(f"Plantilla base (solo lectura): {SRC_PROJECT_CFX}")

    ranges: dict[str, tuple[dt.date, dt.date, int]] = {}
    for label, instrument, tf, _comm in CELLS:
        d_from, d_to, rows = csv_date_range(instrument, tf)
        ranges[label] = (d_from, d_to, rows)
        span_days = (d_to - d_from).days
        print(f"  OK   {label:10s} {instrument}_{tf}: {iso(d_from)} -> {iso(d_to)}  ({rows} filas, {span_days} dias)")

    for label, instrument, tf, _comm in PENDING_CELLS:
        path = DUKAS_DIR / f"{instrument}_{tf}.csv"
        print(f"  SKIP {label:10s} {instrument}_{tf}: sin CSV en disco ({path}) -- backfill pendiente")

    if args.check_only:
        return 0

    if not SRC_PROJECT_CFX.is_file():
        raise SystemExit(f"No se encuentra la plantilla fuente: {SRC_PROJECT_CFX}")

    with zipfile.ZipFile(SRC_PROJECT_CFX) as z:
        build_template = z.read("Build-Task1.xml").decode("utf-8")
        config_template = z.read("config.xml").decode("utf-8")

    tasks_xml = []
    task_files: dict[str, str] = {}
    for i, (label, instrument, tf, comm) in enumerate(CELLS, start=1):
        d_from, d_to, _rows = ranges[label]
        symbol = f"{instrument}_{tf}"
        setup = setup_xml(symbol, tf, d_from, d_to, comm)

        span_days = (d_to - d_from).days
        oos_days = max(1, round(span_days * OOS_FRACTION))
        oos_from = d_to - dt.timedelta(days=oos_days)
        actual_oos_pct = oos_days / span_days * 100

        task_xml = build_task_xml(build_template, setup, oos_from, d_to)
        fname = f"Build-Task{i}.xml"
        task_files[fname] = task_xml
        tasks_xml.append(
            f'    <Task type="Build" name="{label}" showSettingsOverview="false" '
            f'sampleName="Custom" active="true" taskXMLFile="{fname}" />'
        )
        print(
            f"  Setup {label}: IS {iso(d_from)}->{iso(oos_from)} | "
            f"OOS {iso(oos_from)}->{iso(d_to)} ({actual_oos_pct:.1f}% del rango, {oos_days} dias)"
        )

    config = config_template
    # Nombre del proyecto (atributo name del nodo raiz <Project name="...">)
    config = config.replace('name="Ultra_Matrix"', f'name="{PROJECT_NAME}"', 1)
    # Reemplazar el bloque <Tasks>...</Tasks> completo por las N tareas Build (sin Improve: fuera de alcance)
    t_start = config.index("  <Tasks>")
    t_end = config.index("  </Tasks>") + len("  </Tasks>")
    config = config[:t_start] + "  <Tasks>\n" + "\n".join(tasks_xml) + "\n  </Tasks>" + config[t_end:]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    if args.out.exists():
        raise SystemExit(f"Me niego a sobrescribir un artefacto existente: {args.out}")
    with zipfile.ZipFile(args.out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("config.xml", config)
        for fname, xml in task_files.items():
            z.writestr(fname, xml)

    manifest = {
        "schema": "ultrarentable.sqx.fondeo_config.v1",
        "createdAt": dt.datetime.now(dt.UTC).isoformat(),
        "project": PROJECT_NAME,
        "sourceTemplate": str(SRC_PROJECT_CFX),
        "sourceTemplateSha256": sha256(SRC_PROJECT_CFX),
        "outputArtifact": str(args.out.resolve()),
        "outputArtifactSha256": sha256(args.out),
        "cells": [
            {
                "label": label,
                "symbol": f"{instrument}_{tf}",
                "dateFrom": iso(ranges[label][0]),
                "dateTo": iso(ranges[label][1]),
                "rows": ranges[label][2],
                "oosFraction": OOS_FRACTION,
            }
            for label, instrument, tf, _c in CELLS
        ],
        "pendingCells": [f"{instrument}_{tf}" for _l, instrument, tf, _c in PENDING_CELLS],
        "notImportedIntoSqxDataDb": True,
        "status": "CONFIG_READY_DATA_NOT_IMPORTED",
    }
    manifest_path = args.out.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"\nEscrito: {args.out}")
    print(f"Manifiesto: {manifest_path}")
    print(f"SHA-256 artefacto: {manifest['outputArtifactSha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
