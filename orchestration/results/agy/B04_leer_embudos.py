#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
M2 - Lector de embudos para B04 (GO_B04.md, pasos 1-4).

SOLO LECTURA: no toca codigo, no toca data/, no relanza el motor, no escribe nada salvo
su propia salida por stdout. Lee 5 JSON de telemetria ya generados (E1 5m/15m reversion,
E2 5m/15m arquetipos, re-ejecucion de determinismo de 3 configs) y:

  1. Imprime metadatos de cada embudo, recomputa coberturas y buckets desde 'telemetria',
     y lista anomalias estructurales (campos que faltan, sumas que no cuadran, ids
     duplicados, registros IS con 'is_pf', pf != pf_neto, coste_pct None con ganancias
     brutas).
  2. Recalcula bucket/sub-bucket por registro con los umbrales propios del JSON y cuenta
     discrepancias frente a 'causas_por_etapa'.
  3. Compara campo a campo los 3 registros de la re-ejecucion (185231Z) contra los mismos
     strategy_id del E1 15m (105236Z): determinismo. Comprueba si algun registro trae un
     ledger de operaciones para recalcular pf_bruto a mano; si no, NO DATA.
  4. Sensibilidad: por embudo y familia, cuantas configs tienen pf_bruto>=1.00,
     pf_bruto>=1.05, pf>=1.00, pf>=1.05.

Termina imprimiendo 'ANOMALIAS=<n>' y sale con rc=0 siempre (las anomalias son hallazgos,
no fallos del script).
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

RAIZ = Path(__file__).resolve().parents[3]
TELEMETRIA_DIR = RAIZ / "orchestration" / "results" / "telemetria"

EMBUDOS = [
    ("E1_5m_reversion", TELEMETRIA_DIR / "embudo_FONDEO_ES_5m_reversion_20260902T104704Z.json"),
    ("E1_15m_reversion", TELEMETRIA_DIR / "embudo_FONDEO_ES_15m_reversion_20260902T105236Z.json"),
    ("E2_5m_arquetipos", TELEMETRIA_DIR / "embudo_FONDEO_ES_5m_arquetipos_20260902T180821Z.json"),
    ("E2_15m_arquetipos", TELEMETRIA_DIR / "embudo_FONDEO_ES_15m_arquetipos_20260902T182722Z.json"),
    ("RERUN_15m_reversion_determinismo", TELEMETRIA_DIR / "embudo_FONDEO_ES_15m_reversion_20260902T185231Z.json"),
]

CAMPOS_REQUERIDOS = [
    "strategy_id", "etapa", "familia", "pf", "pf_bruto", "pf_neto",
    "coste_pct_del_bruto", "trades",
]

FAMILIAS_ARQUETIPOS_6 = {
    "REVERSION_ATR", "SQUEEZE_BREAKOUT", "SESSION_MOMENTUM", "STREAK_EDGE",
    "OPENING_RANGE_BREAKOUT", "VWAP_REVERSION",
}

CAMPOS_DETERMINISMO = ["trades", "pf", "pf_bruto", "pf_neto", "coste_total_usd", "coste_pct_del_bruto"]

anomalias: List[str] = []


def anom(msg: str) -> None:
    anomalias.append(msg)
    print(f"  ANOMALIA: {msg}")


def cargar(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        anom(f"fichero no existe: {path}")
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def clasificar(reg: Dict[str, Any], umbrales: Dict[str, Any]):
    """Reproduce la logica de resumir_causas() de scripts/mine.py (lineas ~823-848)."""
    etapa = reg.get("etapa", "?")
    umbral = umbrales.get(etapa)
    trades = reg.get("trades")
    pf = reg.get("pf")
    pf_bruto = reg.get("pf_bruto")
    if umbral is None or trades is None or pf is None:
        return "otro", None
    pocas = trades < umbral["trades_min"]
    floja = pf < umbral["pf_min"]
    if pocas and floja:
        bucket = "ambas"
    elif pocas:
        bucket = "pocas_operaciones"
    elif floja:
        bucket = "sin_ventaja"
    else:
        bucket = "otro"
    sub = None
    if bucket == "sin_ventaja" and isinstance(pf_bruto, (int, float)):
        sub = "sin_ventaja_bruta" if pf_bruto < umbral["pf_min"] else "sin_ventaja_por_coste"
    return bucket, sub


def seccion(titulo: str) -> None:
    print()
    print(f"--- {titulo} ---")


# ---------------------------------------------------------------------------------------
# PASOS 1 y 2: por cada embudo
# ---------------------------------------------------------------------------------------
datos_por_embudo: Dict[str, Dict[str, Any]] = {}

for nombre, path in EMBUDOS:
    print("=" * 100)
    print(f"EMBUDO: {nombre}  ({path.name})")
    print("=" * 100)
    d = cargar(path)
    if d is None:
        continue
    datos_por_embudo[nombre] = d

    ctx = d.get("contexto", {}) or {}
    umbrales = d.get("umbrales", {}) or {}
    telemetria = d.get("telemetria", []) or []
    cobertura = d.get("cobertura_familias", {}) or {}
    causas = d.get("causas_por_etapa", {}) or {}

    print(f"generado_utc={d.get('generado_utc')}  engine_version={d.get('engine_version')}")
    print(f"track/symbol/tf/profile = {ctx.get('track')}/{ctx.get('symbol')}/{ctx.get('timeframe')}/{ctx.get('profile')}")
    print(f"dataset_source={ctx.get('dataset_source')}  dataset_file={ctx.get('dataset_file')}")
    print(f"max_candidates={ctx.get('max_candidates')}  espacio_total={ctx.get('espacio_total')}  "
          f"configuraciones_evaluadas={ctx.get('configuraciones_evaluadas')}  truncado={ctx.get('truncado')}")
    print(f"barras_is={ctx.get('barras_is')}  barras_val={ctx.get('barras_val')}  barras_oos={ctx.get('barras_oos')}")
    print(f"umbrales(JSON)={umbrales}")
    print(f"len(telemetria)={len(telemetria)}")

    # --- conteo por familia: JSON vs recomputado desde telemetria ---
    conteo_familia_recomp = Counter(str(r.get("familia") or "?") for r in telemetria)
    seccion("cobertura por familia: JSON vs recomputado desde telemetria")
    print(f"  cobertura_familias (JSON)      = {dict(cobertura)}")
    print(f"  conteo_familia (recomputado)   = {dict(conteo_familia_recomp)}")
    if dict(conteo_familia_recomp) != dict(cobertura):
        anom(f"[{nombre}] cobertura_familias del JSON != recomputado desde telemetria "
             f"(JSON={dict(cobertura)} recomputado={dict(conteo_familia_recomp)})")
    if ctx.get("profile") == "arquetipos":
        faltan_6 = FAMILIAS_ARQUETIPOS_6 - set(cobertura.keys())
        if faltan_6:
            anom(f"[{nombre}] perfil arquetipos sin las 6 familias esperadas; faltan: {sorted(faltan_6)}")
        else:
            print(f"  perfil arquetipos: 6/6 familias representadas -> {sorted(cobertura.keys())}")

    # --- conteo por bucket y sub-bucket: JSON (causas_por_etapa) vs recomputado ---
    seccion("conteo por bucket/sub-bucket: JSON (causas_por_etapa) vs recomputado")
    recomp_etapa: Dict[str, Counter] = {}
    recomp_familia: Dict[str, Dict[str, Counter]] = {}
    for r in telemetria:
        etapa = r.get("etapa", "?")
        familia = str(r.get("familia") or "?")
        bucket, sub = clasificar(r, umbrales)
        c = recomp_etapa.setdefault(etapa, Counter())
        c["total"] += 1
        c[bucket] += 1
        if sub:
            c[sub] += 1
        cf = recomp_familia.setdefault(etapa, {}).setdefault(familia, Counter())
        cf["total"] += 1
        cf[bucket] += 1
        if sub:
            cf[sub] += 1

    discrepancias_bucket = 0
    for etapa, c_json in causas.items():
        c_rec = recomp_etapa.get(etapa, Counter())
        print(f"  etapa={etapa}")
        for clave in ("total", "pocas_operaciones", "sin_ventaja", "ambas", "otro",
                      "sin_ventaja_bruta", "sin_ventaja_por_coste"):
            v_json = c_json.get(clave)
            v_rec = c_rec.get(clave, 0)
            marca = "OK" if v_json == v_rec else "DISCREPANCIA"
            if v_json is not None and v_json != v_rec:
                discrepancias_bucket += 1
                anom(f"[{nombre}] etapa={etapa} bucket={clave}: JSON={v_json} recomputado={v_rec}")
            print(f"    {clave}: JSON={v_json} recomputado={v_rec} [{marca}]")

        # por_familia: JSON vs recomputado
        fam_json = c_json.get("por_familia", {}) or {}
        fam_rec = recomp_familia.get(etapa, {})
        familias_union = set(fam_json.keys()) | set(fam_rec.keys())
        for fam in sorted(familias_union):
            if fam not in fam_json:
                anom(f"[{nombre}] etapa={etapa} familia={fam}: presente en recomputo pero ausente en "
                     f"causas_por_etapa.por_familia del JSON")
                continue
            if fam not in fam_rec:
                anom(f"[{nombre}] etapa={etapa} familia={fam}: presente en causas_por_etapa.por_familia "
                     f"del JSON pero ausente en telemetria recomputada")
                continue
            for clave in ("total", "pocas_operaciones", "sin_ventaja", "ambas", "otro",
                          "sin_ventaja_bruta", "sin_ventaja_por_coste"):
                v_json = fam_json[fam].get(clave)
                v_rec = fam_rec[fam].get(clave, 0)
                if v_json is not None and v_json != v_rec:
                    discrepancias_bucket += 1
                    anom(f"[{nombre}] etapa={etapa} familia={fam} bucket={clave}: "
                         f"JSON={v_json} recomputado={v_rec}")
    print(f"  discrepancias de bucket/sub-bucket (JSON vs recomputado) = {discrepancias_bucket}")

    # --- consistencia interna de causas_por_etapa (sumas que deben cuadrar dentro del propio JSON) ---
    seccion("consistencia interna de causas_por_etapa (sumas dentro del propio JSON)")
    for etapa, c_json in causas.items():
        total = c_json.get("total")
        suma_buckets = sum(c_json.get(k, 0) for k in ("pocas_operaciones", "sin_ventaja", "ambas", "otro"))
        if total is not None and total != suma_buckets:
            anom(f"[{nombre}] etapa={etapa}: total={total} != suma(pocas+sin_ventaja+ambas+otro)={suma_buckets}")
        else:
            print(f"  etapa={etapa}: total={total} == suma(pocas+sin_ventaja+ambas+otro)={suma_buckets} [OK]")

        if "sin_ventaja_bruta" in c_json and "sin_ventaja_por_coste" in c_json:
            sv = c_json.get("sin_ventaja")
            suma_sub = c_json.get("sin_ventaja_bruta", 0) + c_json.get("sin_ventaja_por_coste", 0)
            if sv is not None and sv != suma_sub:
                anom(f"[{nombre}] etapa={etapa}: sin_ventaja={sv} != sin_ventaja_bruta+sin_ventaja_por_coste={suma_sub}")
            else:
                print(f"  etapa={etapa}: sin_ventaja={sv} == bruta+por_coste={suma_sub} [OK]")

        fam_json = c_json.get("por_familia")
        if fam_json:
            for clave in ("total", "pocas_operaciones", "sin_ventaja", "ambas", "otro"):
                suma_fam = sum(f.get(clave, 0) for f in fam_json.values())
                v = c_json.get(clave)
                if v is not None and v != suma_fam:
                    anom(f"[{nombre}] etapa={etapa}: {clave}={v} != suma por_familia({clave})={suma_fam}")
            print(f"  etapa={etapa}: suma por_familia de total = {sum(f.get('total', 0) for f in fam_json.values())} "
                  f"(total etapa={c_json.get('total')})")

    # --- ids duplicados ---
    ids = [r.get("strategy_id") for r in telemetria]
    dup = [i for i, n in Counter(ids).items() if n > 1]
    if dup:
        anom(f"[{nombre}] strategy_id duplicados: {dup}")
    else:
        print(f"  ids duplicados: ninguno (total ids={len(ids)}, unicos={len(set(ids))})")

    # --- comprobacion campo a campo de cada registro ---
    seccion("comprobacion de campos por registro")
    faltantes = 0
    is_con_is_pf = 0
    pf_distinto_neto = 0
    coste_none_con_ganancias = 0
    ledger_encontrado = 0
    for r in telemetria:
        for campo in CAMPOS_REQUERIDOS:
            if campo not in r or r.get(campo) is None:
                # coste_pct_del_bruto puede ser legitimamente None (sin ganancias brutas);
                # el resto de campos requeridos no deberian faltar nunca.
                if campo == "coste_pct_del_bruto":
                    continue
                faltantes += 1
                anom(f"[{nombre}] registro {r.get('strategy_id')} sin campo requerido '{campo}'")
        if r.get("etapa") == "IS" and "is_pf" in r:
            is_con_is_pf += 1
            anom(f"[{nombre}] registro IS {r.get('strategy_id')} lleva 'is_pf' (W2.8 dice que IS no lo lleva)")
        if r.get("pf") is not None and r.get("pf_neto") is not None and r.get("pf") != r.get("pf_neto"):
            pf_distinto_neto += 1
            anom(f"[{nombre}] registro {r.get('strategy_id')}: pf={r.get('pf')} != pf_neto={r.get('pf_neto')}")
        pf_bruto = r.get("pf_bruto")
        if isinstance(pf_bruto, (int, float)) and pf_bruto > 0.0 and r.get("coste_pct_del_bruto") is None:
            # segun _pf_bruto_y_coste() de mine.py, coste_pct_del_bruto solo es None cuando
            # ganancias_brutas<=0, lo que solo ocurre si pf_bruto==0.0. pf_bruto>0 implica
            # ganancias_brutas>0 (ver docstring de _pf_bruto_y_coste, scripts/mine.py L753-758).
            coste_none_con_ganancias += 1
            anom(f"[{nombre}] registro {r.get('strategy_id')}: pf_bruto={pf_bruto} (>0, implica ganancias "
                 f"brutas) pero coste_pct_del_bruto=None")
        for clave_ledger in ("trades_list", "operaciones", "ledger", "trade_ledger", "operations"):
            if clave_ledger in r:
                ledger_encontrado += 1
    print(f"  registros con campo requerido faltante: {faltantes}")
    print(f"  registros IS con 'is_pf' (no deberia haber): {is_con_is_pf}")
    print(f"  registros con pf != pf_neto: {pf_distinto_neto}")
    print(f"  registros con coste_pct_del_bruto=None pese a pf_bruto>0: {coste_none_con_ganancias}")
    print(f"  registros con alguna clave de ledger de operaciones embebida: {ledger_encontrado}")
    if ledger_encontrado == 0:
        print("  NO DATA: ningun registro de telemetria trae la lista de operaciones (ledger) del motor; "
              "solo trae los agregados strategy_id/etapa/familia/motivo/trades/pf/pf_bruto/pf_neto/"
              "coste_total_usd/coste_pct_del_bruto. No se puede recalcular pf_bruto 'a mano desde el "
              "ledger' con estos JSON: solo se puede reconciliar con la formula de _pf_bruto_y_coste() "
              "usando los propios agregados ya persistidos (ver seccion determinismo).")

print()
print("=" * 100)
print("PASO 3: DETERMINISMO (rerun 185231Z vs E1_15m_reversion 105236Z)")
print("=" * 100)
print("Contexto de ejecucion: E1_15m_reversion (105236Z) corrio en el PC (Windows); el rerun")
print("(185231Z, paso 3 de GO_B04, --max-candidates 3) corrio en el VPS (Linux), bajo gobernanza_recursos.")

d_e1 = datos_por_embudo.get("E1_15m_reversion")
d_rerun = datos_por_embudo.get("RERUN_15m_reversion_determinismo")
if d_e1 is None or d_rerun is None:
    anom("no se pudo cargar E1_15m_reversion o el rerun; determinismo no comprobado")
else:
    e1_por_id = {r.get("strategy_id"): r for r in d_e1.get("telemetria", [])}
    rerun_regs = d_rerun.get("telemetria", [])
    print(f"registros en rerun: {len(rerun_regs)}  (esperado: 3, --max-candidates 3)")
    identicos = 0
    difieren = 0
    for r in rerun_regs:
        sid = r.get("strategy_id")
        base = e1_por_id.get(sid)
        if base is None:
            anom(f"[determinismo] strategy_id={sid} del rerun no existe en E1_15m_reversion (105236Z)")
            print(f"  {sid}: SIN PAREJA en E1 (105236Z)")
            continue
        diffs = []
        for campo in CAMPOS_DETERMINISMO:
            if r.get(campo) != base.get(campo):
                diffs.append(f"{campo}: E1={base.get(campo)!r} rerun={r.get(campo)!r}")
        if diffs:
            difieren += 1
            print(f"  {sid}: DIFIERE -> " + " | ".join(diffs))
            anom(f"[determinismo] {sid} DIFIERE entre E1 (PC) y rerun (VPS): " + " | ".join(diffs))
        else:
            identicos += 1
            print(f"  {sid}: IDENTICO en {CAMPOS_DETERMINISMO} "
                  f"(trades={r.get('trades')} pf={r.get('pf')} pf_bruto={r.get('pf_bruto')} "
                  f"pf_neto={r.get('pf_neto')} coste_total_usd={r.get('coste_total_usd')} "
                  f"coste_pct_del_bruto={r.get('coste_pct_del_bruto')})")
    print(f"resumen determinismo: identicos={identicos} difieren={difieren} de {len(rerun_regs)} comparados")

print()
print("=" * 100)
print("PASO 4: SENSIBILIDAD (analisis; no cambia ningun umbral en codigo)")
print("=" * 100)
for nombre, d in datos_por_embudo.items():
    telemetria = d.get("telemetria", []) or []
    print(f"-- {nombre} (n={len(telemetria)}) --")
    por_familia: Dict[str, Dict[str, int]] = {}
    tot = {"pf_bruto>=1.00": 0, "pf_bruto>=1.05": 0, "pf>=1.00": 0, "pf>=1.05": 0}
    for r in telemetria:
        fam = str(r.get("familia") or "?")
        casilla = por_familia.setdefault(fam, {"n": 0, "pf_bruto>=1.00": 0, "pf_bruto>=1.05": 0,
                                                 "pf>=1.00": 0, "pf>=1.05": 0})
        casilla["n"] += 1
        pf_bruto = r.get("pf_bruto")
        pf = r.get("pf")
        if isinstance(pf_bruto, (int, float)):
            if pf_bruto >= 1.00:
                casilla["pf_bruto>=1.00"] += 1
                tot["pf_bruto>=1.00"] += 1
            if pf_bruto >= 1.05:
                casilla["pf_bruto>=1.05"] += 1
                tot["pf_bruto>=1.05"] += 1
        if isinstance(pf, (int, float)):
            if pf >= 1.00:
                casilla["pf>=1.00"] += 1
                tot["pf>=1.00"] += 1
            if pf >= 1.05:
                casilla["pf>=1.05"] += 1
                tot["pf>=1.05"] += 1
    for fam in sorted(por_familia):
        c = por_familia[fam]
        print(f"    familia={fam:28s} n={c['n']:4d}  pf_bruto>=1.00={c['pf_bruto>=1.00']:4d}  "
              f"pf_bruto>=1.05={c['pf_bruto>=1.05']:4d}  pf>=1.00={c['pf>=1.00']:4d}  pf>=1.05={c['pf>=1.05']:4d}")
    print(f"    TOTAL n={len(telemetria):4d}  pf_bruto>=1.00={tot['pf_bruto>=1.00']:4d}  "
          f"pf_bruto>=1.05={tot['pf_bruto>=1.05']:4d}  pf>=1.00={tot['pf>=1.00']:4d}  pf>=1.05={tot['pf>=1.05']:4d}")

print()
print("=" * 100)
print(f"ANOMALIAS={len(anomalias)}")
print("=" * 100)
if anomalias:
    print("Listado completo de anomalias:")
    for i, a in enumerate(anomalias, 1):
        print(f"  {i}. {a}")

sys.exit(0)
