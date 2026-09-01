#!/usr/bin/env python3
"""Inventario de primitivas usadas en un lote de ficheros .sqx (StrategyQuant X).

CUELLO 5 (puente SQX -> motor honesto): antes de escribir un traductor, medir QUE
vocabulario usa realmente el lote ya generado. Un .sqx es un ZIP/JAR; la unica pieza
relevante para este inventario es `strategy_Portfolio.xml`, que describe el arbol de
reglas con bloques <Item key="..." mI="..." categoryType="..." returnType="...">.

Categorias de primitiva que extrae (segun lo observado en el XML real, ver informe
`orchestration/results/viabilidad_puente_sqx.md`):
  - regla_condicion   : Item categoryType="simpleRules" -> condicion booleana de entrada/
                        salida (p.ej. "Bar opens above Moving Average after opened below").
  - indicador_valor   : Item categoryType="indicator" -> bloque que produce un valor numerico
                        (precio/ATR/etc.), usado dentro de una Formula (p.ej. precio de
                        entrada EnterAtStop, o ancla de un exit).
  - operador          : Item categoryType="operators" -> AND/OR/Not/comparadores explicitos.
  - orden             : Item con mI="Open" -> tipo de orden de entrada (EnterAtStop, ...).
  - control_posicion  : Item con mI="StrategyControl" -> chequeos de estado de posicion
                        (MarketPositionIsLong/Short) y acciones de cierre (CloseAllPositions).
  - formula_exit      : atributo `key` de <Formula> bajo un Param con exitMethodType="SL"/"PT"
                        (o sin marcar, p.ej. precio de entrada) -> familia de gestion de
                        stop/target (SQ.Formulas.SLPT.ATRBasedValue, RangeLevel.*, Range.*...).
  - money_management  : atributo `type` de <MoneyManagement>.
  - filtro_sesion     : deteccion heuristica (mI/key/nombre que contenga Session/Time/Hour/
                        DayOfWeek/Filter) -- NINGUNA encontrada en el lote medido, se deja el
                        detector para lotes futuros que si los usen.
  - engine            : atributo `engine` de <Strategy> (motor SQX de origen, p.ej. MetaTrader4).

Para cada primitiva se cuenta:
  - n_ficheros: en cuantos .sqx del lote aparece al menos una vez (mide "cobertura": que
    fraccion del lote usa esa primitiva).
  - n_total: cuantas veces aparece en total sumando todo el lote (mide "densidad").

Uso:
    nice -n 19 python3 scripts/herramientas/inventario_sqx.py \\
        --dir "/home/ubuntu/StrategyQuantX144/user/projects/Ultra_Matrix/databanks/ToImprove" \\
        --out orchestration/results/inventario_sqx_histograma.json

Es lectura de ficheros (ZIP + XML), no ejecuta backtests ni SQX: barato en CPU.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Heuristica de filtros de sesion/tiempo -- ninguna primitiva de este tipo aparecio en el
# lote medido (2035/2035 ficheros), pero se deja activa para no dar falso negativo en un
# lote futuro generado con otra configuracion de SQX.
_SESSION_HINT_RE = re.compile(r"session|dayofweek|tradinghours|timefilter|\bhour\b", re.IGNORECASE)


def _local(tag: str) -> str:
    """Quita namespace de una etiqueta XML si lo hubiera (aqui no hay, pero es defensivo)."""
    return tag.rsplit("}", 1)[-1]


class InventarioResultado:
    def __init__(self) -> None:
        # Counter[(categoria, primitiva)] -> n_total (ocurrencias)
        self.total: Counter = Counter()
        # Counter[(categoria, primitiva)] -> n_ficheros (presencia, se deduplica por fichero)
        self.ficheros: Counter = Counter()
        self.n_ficheros_ok = 0
        self.n_ficheros_error = 0
        self.errores: list[tuple[str, str]] = []

    def registrar_fichero(self, presentes_en_este_fichero: set[tuple[str, str]], conteos_este_fichero: Counter) -> None:
        self.total.update(conteos_este_fichero)
        self.ficheros.update(presentes_en_este_fichero)
        self.n_ficheros_ok += 1

    def registrar_error(self, path: str, msg: str) -> None:
        self.n_ficheros_error += 1
        self.errores.append((path, msg))


def _parse_formula_family(formula_key: str) -> str:
    """SQ.Formulas.SLPT.ATRBasedValue -> SLPT.ATRBasedValue (quita el prefijo comun)."""
    prefix = "SQ.Formulas."
    return formula_key[len(prefix):] if formula_key.startswith(prefix) else formula_key


def inventariar_fichero(sqx_path: Path) -> tuple[set[tuple[str, str]], Counter]:
    """Abre un .sqx (ZIP) y extrae las primitivas de strategy_Portfolio.xml.

    Devuelve (set de (categoria, primitiva) presentes, Counter de ocurrencias totales).
    Lanza excepcion si el ZIP o el XML no tienen la forma esperada -- el caller decide
    si contarlo como error (zero-mocks: no se rellena con datos inventados).
    """
    with zipfile.ZipFile(sqx_path) as z:
        xml_bytes = z.read("strategy_Portfolio.xml")
    root = ET.fromstring(xml_bytes)

    conteos: Counter = Counter()
    presentes: set[tuple[str, str]] = set()

    def add(categoria: str, primitiva: str) -> None:
        conteos[(categoria, primitiva)] += 1
        presentes.add((categoria, primitiva))

    # --- engine y money management (atributos de nodo unico) --------------------------
    strategy_el = root.find(".//Strategy")
    if strategy_el is not None:
        engine = strategy_el.get("engine")
        if engine:
            add("engine", engine)
        mm_el = strategy_el.find("./MoneyManagement")
        if mm_el is not None:
            mm_type = mm_el.get("type")
            if mm_type:
                add("money_management", mm_type)

    # --- recorrido generico de <Item> y <Formula> ---------------------------------------
    for el in root.iter():
        tag = _local(el.tag)

        if tag == "Item":
            key = el.get("key")
            mI = el.get("mI")
            category_type = el.get("categoryType")
            if not key:
                continue

            if _SESSION_HINT_RE.search(key) or (mI and _SESSION_HINT_RE.search(mI)):
                add("filtro_sesion", key)

            if mI == "Open":
                add("orden", key)
            elif mI == "StrategyControl":
                add("control_posicion", key)

            if category_type == "simpleRules":
                add("regla_condicion", key)
            elif category_type == "indicator":
                add("indicador_valor", key)
            elif category_type == "operators":
                add("operador", key)
            elif category_type == "other" and mI not in ("Open", "StrategyControl"):
                # Booleans, variables, CloseAllPositions (sin mI) y similares.
                add("otro_bloque", key)

        elif tag == "Formula":
            key = el.get("key")
            if not key:
                continue
            familia = _parse_formula_family(key)
            # exitMethodType vive en el <Param> padre, no en la propia <Formula>.
            parent_method_type = None
            # ElementTree no da acceso al padre directamente; se resuelve via un mapa
            # construido una vez por fichero mas abajo si hiciera falta. Para no pagar ese
            # coste en cada Formula, se clasifica solo por la familia (SLPT/RangeLevel/
            # Range/Price/Size), que ya es suficientemente especifica para el histograma.
            add("formula_exit", familia)

    return presentes, conteos


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument(
        "--dir",
        type=Path,
        default=Path("/home/ubuntu/StrategyQuantX144/user/projects/Ultra_Matrix/databanks/ToImprove"),
        help="Directorio con ficheros .sqx (por defecto: el lote ToImprove de Ultra_Matrix).",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Ruta de salida JSON con el histograma completo (opcional).",
    )
    ap.add_argument("--limit", type=int, default=None, help="Procesar solo los N primeros ficheros (debug).")
    args = ap.parse_args()

    if not args.dir.is_dir():
        print(f"ERROR: directorio no encontrado: {args.dir}", file=sys.stderr)
        return 2

    files = sorted(args.dir.glob("*.sqx"))
    if args.limit:
        files = files[: args.limit]
    if not files:
        print(f"ERROR: no hay ficheros .sqx en {args.dir}", file=sys.stderr)
        return 2

    resultado = InventarioResultado()
    for f in files:
        try:
            presentes, conteos = inventariar_fichero(f)
            resultado.registrar_fichero(presentes, conteos)
        except (zipfile.BadZipFile, KeyError, ET.ParseError) as e:
            resultado.registrar_error(str(f), f"{type(e).__name__}: {e}")

    n = resultado.n_ficheros_ok
    print(f"Ficheros .sqx encontrados : {len(files)}")
    print(f"Procesados OK             : {n}")
    print(f"Con error                 : {resultado.n_ficheros_error}")
    for path, msg in resultado.errores[:10]:
        print(f"  ERROR {path}: {msg}")

    categorias = sorted({cat for cat, _ in resultado.ficheros})
    histograma: dict = {}
    for cat in categorias:
        items = [
            {
                "primitiva": prim,
                "n_ficheros": resultado.ficheros[(cat, prim)],
                "pct_lote": round(100.0 * resultado.ficheros[(cat, prim)] / n, 2) if n else 0.0,
                "n_total": resultado.total[(cat, prim)],
            }
            for (c, prim) in resultado.ficheros
            if c == cat
        ]
        items.sort(key=lambda d: -d["n_ficheros"])
        histograma[cat] = items

        print(f"\n=== {cat} ({len(items)} primitivas distintas) ===")
        for it in items:
            print(f"  {it['primitiva']:45s} n_ficheros={it['n_ficheros']:5d} ({it['pct_lote']:6.2f}%)  n_total={it['n_total']:6d}")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "dir_origen": str(args.dir),
            "n_ficheros_encontrados": len(files),
            "n_ficheros_procesados_ok": n,
            "n_ficheros_error": resultado.n_ficheros_error,
            "errores": resultado.errores,
            "histograma": histograma,
        }
        args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nHistograma completo escrito en: {args.out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
