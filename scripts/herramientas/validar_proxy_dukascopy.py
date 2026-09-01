#!/usr/bin/env python3
"""scripts/herramientas/validar_proxy_dukascopy.py

Tarea B (preparatoria FONDEO, 2026-09-01): valida si el CFD Dukascopy (p.ej. USA500IDXUSD)
es un sustituto aceptable del futuro CME real (dataset Yahoo, p.ej. ES=F) para MINAR y
CERTIFICAR estrategias FONDEO.

Doctrina: el backfill de Dukascopy da ~18x mas barras que Yahoo para el mismo simbolo, pero
mas barras NO es automaticamente mas fiel. Certificar sobre un CFD para despues operar el
futuro real seria un autoengaño caro si las dos series se comportan distinto. Esta herramienta
compara las series REALES en el tramo temporal donde solapan y devuelve un veredicto explicito
respaldado por numeros -- nunca una opinion, y nunca un veredicto forzado si no hay datos
suficientes para sostenerlo.

Compara:
  - correlacion de RETORNOS (no de precios: dos series con tendencia correlacionan alto de
    todos modos y eso no dice nada) en el timeframe comun, global y por sub-periodos (para ver
    si la relacion es estable o se rompe en alguna ventana);
  - diferencias de volatilidad: ATR% medio y desviacion estandar de retornos, cada fuente por
    separado y su ratio;
  - desajustes de horario de sesion: barras que existen en una fuente y no en la otra al mismo
    timestamp UTC, con desglose por hora del dia;
  - gaps de apertura diarios (open de hoy vs close de ayer) y su magnitud comparada;
  - un veredicto explicito APTO / APTO_CON_RESERVAS / NO_APTO / PENDIENTE_DATOS_INSUFICIENTES,
    con el criterio numerico exacto que lo justifica.

REAL-ONLY: opera sobre los datasets fisicos ya descargados en data/normalized/ (Yahoo vía
resolve_dataset_file data_source='auto', Dukascopy vía data_source='dukascopy' -- Tarea A,
mismo SSOT de mapeo). No descarga nada, no interpola, no inventa barras. Si el solape temporal
es insuficiente (p.ej. mientras el backfill de Dukascopy no alcanza el rango de Yahoo), lo dice
explicitamente con status SIN_SOLAPE o SOLAPE_INSUFICIENTE y el veredicto queda en
PENDIENTE_DATOS_INSUFICIENTES -- nunca se fuerza APTO/NO_APTO sobre datos escasos.

Uso:
    .venv/bin/python scripts/herramientas/validar_proxy_dukascopy.py --symbol ES --tf 1h
    .venv/bin/python scripts/herramientas/validar_proxy_dukascopy.py --symbol ES --tf 5m \
        --json-out orchestration/results/validacion_proxy_es_5m.json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import numpy as np
import pandas as pd

from scripts.mine import (
    DatasetSourceError,
    compute_file_sha256,
    infer_dataset_source_label,
    load_candles_from_file,
    resolve_dataset_file,
)

# --------------------------------------------------------------------------------------------
# Umbrales del veredicto: propuestos de ingenieria, documentados y explicitos aqui mismo.
# NO son un criterio sellado como el 1.1 (ese lo fija REGLAS_INVARIANTES.md) -- son el punto de
# partida transparente que esta herramienta necesita para no devolver solo numeros sueltos sin
# interpretacion. Quedan pendientes de ratificacion doctrinal antes de usarse para bloquear o
# aprobar una certificacion FONDEO sobre datos Dukascopy.
# --------------------------------------------------------------------------------------------
MIN_BARRAS_SOLAPADAS = 200  # por debajo de esto ninguna correlacion es estadisticamente fiable
N_SUBPERIODOS = 4  # ventanas para medir si la correlacion es estable o se rompe en alguna

UMBRAL_CORR_APTO = 0.90
UMBRAL_CORR_APTO_PEOR_SUBPERIODO = 0.80
UMBRAL_CORR_RESERVAS = 0.75

UMBRAL_COBERTURA_HORARIA_APTO = 0.90  # fraccion de barras Yahoo con contrapartida Dukascopy
UMBRAL_COBERTURA_HORARIA_RESERVAS = 0.70

RATIO_VOL_APTO = (0.70, 1.30)  # ATR%_dukascopy / ATR%_yahoo
RATIO_VOL_RESERVAS = (0.50, 2.00)

ATR_WINDOW = 14


def _load_series(path: Path) -> pd.DataFrame:
    """Carga un dataset fisico (JSON list o dict-con-bars, ambos formatos ya soportados por
    scripts/mine.py::load_candles_from_file) como DataFrame OHLC indexado por timestamp_ms."""
    candles = load_candles_from_file(path)
    df = pd.DataFrame(candles)
    if df.empty:
        return df
    df["timestamp_ms"] = df["timestamp_ms"].astype(np.int64)
    df = df.drop_duplicates(subset="timestamp_ms").sort_values("timestamp_ms")
    df = df.set_index("timestamp_ms")
    return df[["open", "high", "low", "close"]].astype(float)


def _iso(ts_ms: int) -> str:
    return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).isoformat()


def _atr_pct(df: pd.DataFrame, window: int = ATR_WINDOW) -> pd.Series:
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    atr = tr.rolling(window, min_periods=window).mean()
    return (atr / df["close"]) * 100.0


def _daily_open_gaps_pct(df: pd.DataFrame) -> pd.Series:
    """Gap% diario: (open del primer bar del dia - close del ultimo bar del dia previo) /
    close_previo * 100. Indexado por fecha UTC (date), para poder comparar dia-a-dia entre
    fuentes con `.index.intersection`."""
    dt = pd.to_datetime(df.index, unit="ms", utc=True)
    tmp = df.copy()
    tmp["day"] = dt.date
    daily_open = tmp.groupby("day")["open"].first()
    daily_close = tmp.groupby("day")["close"].last()
    prev_close = daily_close.shift(1)
    gap_pct = (daily_open - prev_close) / prev_close * 100.0
    return gap_pct.dropna()


def _hour_histogram(idx: pd.Index) -> Dict[int, int]:
    if len(idx) == 0:
        return {}
    hrs = pd.to_datetime(idx, unit="ms", utc=True).hour
    counts = pd.Series(hrs).value_counts().sort_index()
    return {int(h): int(c) for h, c in counts.items()}


def _sub_period_correlations(joined: pd.DataFrame, n: int) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    idx = joined.index
    n_eff = n if len(idx) >= n else 1
    bounds = np.linspace(0, len(idx), n_eff + 1, dtype=int)
    for i in range(n_eff):
        lo, hi = bounds[i], bounds[i + 1]
        if hi - lo < 3:
            continue
        chunk = joined.iloc[lo:hi]
        corr = chunk["ret_yahoo"].corr(chunk["ret_dukascopy"])
        out.append(
            {
                "desde_utc": _iso(int(chunk.index[0])),
                "hasta_utc": _iso(int(chunk.index[-1])),
                "n_barras": int(len(chunk)),
                "correlacion_retornos": None if pd.isna(corr) else round(float(corr), 4),
            }
        )
    return out


def validar(symbol: str, timeframe: str) -> Dict[str, Any]:
    symbol_u = symbol.upper()
    reporte: Dict[str, Any] = {
        "symbol": symbol_u,
        "timeframe": timeframe,
        "generado_utc": datetime.now(timezone.utc).isoformat(),
    }

    # --- Resolver los dos datasets fisicos (misma SSOT de mapeo que Tarea A) ---
    yahoo_file, yahoo_manifest = resolve_dataset_file(symbol_u, timeframe, data_source="auto")
    if yahoo_file is None:
        reporte["status"] = "ERROR"
        reporte["mensaje"] = (
            f"No hay dataset Yahoo/futuro para '{symbol_u}' {timeframe} en data/normalized/."
        )
        return reporte

    try:
        duka_file, duka_manifest = resolve_dataset_file(
            symbol_u, timeframe, data_source="dukascopy"
        )
    except DatasetSourceError as e:
        reporte["status"] = "ERROR"
        reporte["mensaje"] = f"No se puede validar la fuente Dukascopy: {e}"
        return reporte

    reporte["dataset_yahoo"] = {
        "archivo": yahoo_file.name,
        "fuente": infer_dataset_source_label(yahoo_file, yahoo_manifest),
        "sha256": compute_file_sha256(yahoo_file),
    }
    reporte["dataset_dukascopy"] = {
        "archivo": duka_file.name,
        "fuente": infer_dataset_source_label(duka_file, duka_manifest),
        "sha256": compute_file_sha256(duka_file),
    }

    df_yahoo = _load_series(yahoo_file)
    df_duka = _load_series(duka_file)
    if df_yahoo.empty or df_duka.empty:
        reporte["status"] = "ERROR"
        reporte["mensaje"] = "Uno de los dos datasets cargó 0 barras validas."
        return reporte

    reporte["rango_yahoo_utc"] = [_iso(int(df_yahoo.index.min())), _iso(int(df_yahoo.index.max()))]
    reporte["rango_dukascopy_utc"] = [_iso(int(df_duka.index.min())), _iso(int(df_duka.index.max()))]
    reporte["n_barras_yahoo"] = int(len(df_yahoo))
    reporte["n_barras_dukascopy"] = int(len(df_duka))

    # --- Solape temporal ---
    overlap_start = int(max(df_yahoo.index.min(), df_duka.index.min()))
    overlap_end = int(min(df_yahoo.index.max(), df_duka.index.max()))
    if overlap_start >= overlap_end:
        reporte["status"] = "SIN_SOLAPE"
        reporte["veredicto"] = "PENDIENTE_DATOS_INSUFICIENTES"
        reporte["mensaje"] = (
            "Los rangos temporales de Yahoo y Dukascopy NO se solapan en absoluto: "
            f"Yahoo [{reporte['rango_yahoo_utc'][0]} .. {reporte['rango_yahoo_utc'][1]}], "
            f"Dukascopy [{reporte['rango_dukascopy_utc'][0]} .. {reporte['rango_dukascopy_utc'][1]}]. "
            "Validacion PENDIENTE: falta que el backfill de Dukascopy avance hasta alcanzar el "
            "inicio de los futuros Yahoo. NO se emite veredicto APTO/NO_APTO sin datos que lo "
            "sostengan."
        )
        return reporte

    y_win = df_yahoo[(df_yahoo.index >= overlap_start) & (df_yahoo.index <= overlap_end)]
    d_win = df_duka[(df_duka.index >= overlap_start) & (df_duka.index <= overlap_end)]

    reporte["ventana_solape_utc"] = [_iso(overlap_start), _iso(overlap_end)]
    reporte["n_barras_yahoo_en_ventana"] = int(len(y_win))
    reporte["n_barras_dukascopy_en_ventana"] = int(len(d_win))

    joined = y_win[["close"]].join(
        d_win[["close"]], how="inner", lsuffix="_yahoo", rsuffix="_dukascopy"
    )
    n_matched = len(joined)
    reporte["n_barras_coincidentes_mismo_timestamp"] = int(n_matched)

    solo_yahoo_idx = y_win.index.difference(d_win.index)
    solo_duka_idx = d_win.index.difference(y_win.index)
    reporte["barras_solo_en_yahoo"] = int(len(solo_yahoo_idx))
    reporte["barras_solo_en_dukascopy"] = int(len(solo_duka_idx))
    reporte["horas_utc_solo_en_yahoo_histograma"] = _hour_histogram(solo_yahoo_idx)
    reporte["horas_utc_solo_en_dukascopy_histograma"] = _hour_histogram(solo_duka_idx)

    cobertura_horaria = (n_matched / len(y_win)) if len(y_win) else 0.0
    reporte["cobertura_horaria_dukascopy_sobre_yahoo"] = round(float(cobertura_horaria), 4)

    if n_matched < MIN_BARRAS_SOLAPADAS:
        reporte["status"] = "SOLAPE_INSUFICIENTE"
        reporte["veredicto"] = "PENDIENTE_DATOS_INSUFICIENTES"
        reporte["mensaje"] = (
            f"Hay solape temporal pero solo {n_matched} barras coinciden en el mismo "
            f"timestamp UTC (minimo exigido: {MIN_BARRAS_SOLAPADAS}). Validacion PENDIENTE de "
            "que el backfill produzca mas barras solapadas. NO se emite veredicto."
        )
        return reporte

    # --- Correlacion de RETORNOS (no de precios) ---
    joined["ret_yahoo"] = joined["close_yahoo"].pct_change()
    joined["ret_dukascopy"] = joined["close_dukascopy"].pct_change()
    joined = joined.dropna(subset=["ret_yahoo", "ret_dukascopy"])

    corr_global = joined["ret_yahoo"].corr(joined["ret_dukascopy"])
    corr_global_val = None if pd.isna(corr_global) else round(float(corr_global), 4)
    reporte["correlacion_retornos_global"] = corr_global_val

    subperiodos = _sub_period_correlations(joined, N_SUBPERIODOS)
    reporte["correlacion_retornos_por_subperiodo"] = subperiodos
    corrs_sub = [
        s["correlacion_retornos"] for s in subperiodos if s["correlacion_retornos"] is not None
    ]
    corr_min_sub = min(corrs_sub) if corrs_sub else None
    reporte["correlacion_retornos_peor_subperiodo"] = corr_min_sub

    # --- Volatilidad: ATR% y desviacion estandar de retornos ---
    atr_yahoo = _atr_pct(y_win).dropna()
    atr_duka = _atr_pct(d_win).dropna()
    atr_yahoo_mean = float(atr_yahoo.mean()) if len(atr_yahoo) else None
    atr_duka_mean = float(atr_duka.mean()) if len(atr_duka) else None
    reporte["atr_pct_medio_yahoo"] = None if atr_yahoo_mean is None else round(atr_yahoo_mean, 4)
    reporte["atr_pct_medio_dukascopy"] = None if atr_duka_mean is None else round(atr_duka_mean, 4)
    ratio_vol = (
        (atr_duka_mean / atr_yahoo_mean) if (atr_yahoo_mean and atr_duka_mean) else None
    )
    reporte["ratio_atr_dukascopy_sobre_yahoo"] = None if ratio_vol is None else round(ratio_vol, 4)

    std_yahoo = float(joined["ret_yahoo"].std())
    std_duka = float(joined["ret_dukascopy"].std())
    reporte["std_retornos_yahoo"] = round(std_yahoo, 6)
    reporte["std_retornos_dukascopy"] = round(std_duka, 6)
    reporte["ratio_std_retornos_dukascopy_sobre_yahoo"] = (
        round(std_duka / std_yahoo, 4) if std_yahoo else None
    )

    # --- Gaps de apertura diarios ---
    gaps_yahoo = _daily_open_gaps_pct(y_win)
    gaps_duka = _daily_open_gaps_pct(d_win)
    common_days = gaps_yahoo.index.intersection(gaps_duka.index)
    reporte["n_dias_con_gap_comparable"] = int(len(common_days))
    if len(common_days):
        gy = gaps_yahoo.loc[common_days].abs()
        gd = gaps_duka.loc[common_days].abs()
        reporte["gap_pct_medio_abs_yahoo"] = round(float(gy.mean()), 4)
        reporte["gap_pct_medio_abs_dukascopy"] = round(float(gd.mean()), 4)
        reporte["gap_pct_max_abs_yahoo"] = round(float(gy.max()), 4)
        reporte["gap_pct_max_abs_dukascopy"] = round(float(gd.max()), 4)
    else:
        reporte["gap_pct_medio_abs_yahoo"] = None
        reporte["gap_pct_medio_abs_dukascopy"] = None

    # --- Veredicto explicito, con el criterio numerico que lo justifica ---
    criterios: List[Dict[str, Any]] = []

    def check(nombre: str, ok: bool, detalle: str) -> bool:
        criterios.append({"criterio": nombre, "cumple": bool(ok), "detalle": detalle})
        return ok

    ok_n = check(
        "barras_minimas", n_matched >= MIN_BARRAS_SOLAPADAS,
        f"{n_matched} >= {MIN_BARRAS_SOLAPADAS}",
    )
    corr_v = corr_global_val or 0.0
    ok_corr_apto = check(
        "correlacion_global_apto", corr_v >= UMBRAL_CORR_APTO, f"{corr_v} >= {UMBRAL_CORR_APTO}"
    )
    ok_corr_reservas = check(
        "correlacion_global_reservas", corr_v >= UMBRAL_CORR_RESERVAS,
        f"{corr_v} >= {UMBRAL_CORR_RESERVAS}",
    )
    ok_sub = check(
        "correlacion_estable_subperiodos",
        (corr_min_sub is not None) and (corr_min_sub >= UMBRAL_CORR_APTO_PEOR_SUBPERIODO),
        f"peor subperiodo {corr_min_sub} >= {UMBRAL_CORR_APTO_PEOR_SUBPERIODO}",
    )
    ok_cobertura_apto = check(
        "cobertura_horaria_apto", cobertura_horaria >= UMBRAL_COBERTURA_HORARIA_APTO,
        f"{round(cobertura_horaria, 4)} >= {UMBRAL_COBERTURA_HORARIA_APTO}",
    )
    ok_cobertura_reservas = check(
        "cobertura_horaria_reservas", cobertura_horaria >= UMBRAL_COBERTURA_HORARIA_RESERVAS,
        f"{round(cobertura_horaria, 4)} >= {UMBRAL_COBERTURA_HORARIA_RESERVAS}",
    )
    ok_vol_apto = check(
        "ratio_volatilidad_apto",
        ratio_vol is not None and RATIO_VOL_APTO[0] <= ratio_vol <= RATIO_VOL_APTO[1],
        f"ratio={ratio_vol} en [{RATIO_VOL_APTO[0]}, {RATIO_VOL_APTO[1]}]",
    )
    ok_vol_reservas = check(
        "ratio_volatilidad_reservas",
        ratio_vol is not None and RATIO_VOL_RESERVAS[0] <= ratio_vol <= RATIO_VOL_RESERVAS[1],
        f"ratio={ratio_vol} en [{RATIO_VOL_RESERVAS[0]}, {RATIO_VOL_RESERVAS[1]}]",
    )

    if ok_n and ok_corr_apto and ok_sub and ok_cobertura_apto and ok_vol_apto:
        veredicto = "APTO"
    elif ok_n and ok_corr_reservas and ok_cobertura_reservas and ok_vol_reservas:
        veredicto = "APTO_CON_RESERVAS"
    else:
        veredicto = "NO_APTO"

    reporte["status"] = "OK"
    reporte["criterios"] = criterios
    reporte["umbrales_usados"] = {
        "min_barras_solapadas": MIN_BARRAS_SOLAPADAS,
        "correlacion_global_apto": UMBRAL_CORR_APTO,
        "correlacion_global_reservas": UMBRAL_CORR_RESERVAS,
        "correlacion_peor_subperiodo_apto": UMBRAL_CORR_APTO_PEOR_SUBPERIODO,
        "cobertura_horaria_apto": UMBRAL_COBERTURA_HORARIA_APTO,
        "cobertura_horaria_reservas": UMBRAL_COBERTURA_HORARIA_RESERVAS,
        "ratio_volatilidad_apto": list(RATIO_VOL_APTO),
        "ratio_volatilidad_reservas": list(RATIO_VOL_RESERVAS),
    }
    reporte["veredicto"] = veredicto
    reporte["veredicto_nota"] = (
        "Umbrales de ingenieria propuestos por esta herramienta (ver 'umbrales_usados'), NO son "
        "un criterio sellado como el 1.1 de REGLAS_INVARIANTES.md: requieren ratificacion "
        "doctrinal de Emilio antes de usarse para bloquear o aprobar una certificacion FONDEO "
        "sobre datos Dukascopy."
    )
    return reporte


def _print_reporte(r: Dict[str, Any]) -> None:
    print(f"\n=== Validacion proxy Dukascopy vs futuro Yahoo: {r['symbol']} {r['timeframe']} ===")
    print(f"generado: {r['generado_utc']}")
    if "dataset_yahoo" in r:
        dy = r["dataset_yahoo"]
        print(f"  Yahoo:      {dy['archivo']}  [{dy['fuente']}]  sha256={dy['sha256'][:12]}...")
    if "dataset_dukascopy" in r:
        dd = r["dataset_dukascopy"]
        print(f"  Dukascopy:  {dd['archivo']}  [{dd['fuente']}]  sha256={dd['sha256'][:12]}...")
    if "rango_yahoo_utc" in r:
        print(f"  Rango Yahoo:     {r['rango_yahoo_utc'][0]} .. {r['rango_yahoo_utc'][1]} ({r['n_barras_yahoo']} barras)")
    if "rango_dukascopy_utc" in r:
        print(f"  Rango Dukascopy: {r['rango_dukascopy_utc'][0]} .. {r['rango_dukascopy_utc'][1]} ({r['n_barras_dukascopy']} barras)")

    print(f"\nstatus: {r['status']}")
    if r.get("mensaje"):
        print(f"mensaje: {r['mensaje']}")

    if r["status"] == "OK":
        print(f"\nventana de solape: {r['ventana_solape_utc'][0]} .. {r['ventana_solape_utc'][1]}")
        print(f"barras coincidentes (mismo timestamp UTC): {r['n_barras_coincidentes_mismo_timestamp']}")
        print(f"cobertura horaria Dukascopy/Yahoo: {r['cobertura_horaria_dukascopy_sobre_yahoo']*100:.2f}%")
        print(f"barras solo en Yahoo: {r['barras_solo_en_yahoo']} | solo en Dukascopy: {r['barras_solo_en_dukascopy']}")
        if r["horas_utc_solo_en_yahoo_histograma"]:
            print(f"  horas UTC exclusivas de Yahoo (histograma): {r['horas_utc_solo_en_yahoo_histograma']}")
        if r["horas_utc_solo_en_dukascopy_histograma"]:
            print(f"  horas UTC exclusivas de Dukascopy (histograma): {r['horas_utc_solo_en_dukascopy_histograma']}")

        print(f"\ncorrelacion de retornos global: {r['correlacion_retornos_global']}")
        print(f"correlacion de retornos, peor subperiodo: {r['correlacion_retornos_peor_subperiodo']}")
        for sp in r["correlacion_retornos_por_subperiodo"]:
            print(f"    [{sp['desde_utc']} .. {sp['hasta_utc']}] n={sp['n_barras']}  corr={sp['correlacion_retornos']}")

        print(f"\nATR% medio  Yahoo={r['atr_pct_medio_yahoo']}  Dukascopy={r['atr_pct_medio_dukascopy']}  ratio={r['ratio_atr_dukascopy_sobre_yahoo']}")
        print(f"std retornos  Yahoo={r['std_retornos_yahoo']}  Dukascopy={r['std_retornos_dukascopy']}  ratio={r['ratio_std_retornos_dukascopy_sobre_yahoo']}")

        print(f"\ngaps apertura diarios (dias comparables={r['n_dias_con_gap_comparable']}):")
        print(f"    |gap%| medio  Yahoo={r['gap_pct_medio_abs_yahoo']}  Dukascopy={r['gap_pct_medio_abs_dukascopy']}")
        print(f"    |gap%| max    Yahoo={r['gap_pct_max_abs_yahoo']}  Dukascopy={r['gap_pct_max_abs_dukascopy']}")

        print("\ncriterios evaluados:")
        for c in r["criterios"]:
            marca = "OK " if c["cumple"] else "NO "
            print(f"    [{marca}] {c['criterio']}: {c['detalle']}")

    if r.get("veredicto"):
        print(f"\nVEREDICTO: {r['veredicto']}")
        if r.get("veredicto_nota"):
            print(f"  nota: {r['veredicto_nota']}")


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--symbol", required=True,
        help="Simbolo FONDEO: ES, NQ, YM, GC, SI, CL (RTY no tiene proxy Dukascopy registrado)",
    )
    ap.add_argument("--tf", default="1h", choices=["1m", "5m", "15m", "1h", "4h"])
    ap.add_argument(
        "--json-out", default=None,
        help="Ruta para volcar el reporte completo en JSON (opcional; NO escribe nada por defecto)",
    )
    args = ap.parse_args()

    reporte = validar(args.symbol, args.tf)
    _print_reporte(reporte)

    if args.json_out:
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(reporte, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nReporte JSON escrito en: {out_path}")

    return 0 if reporte.get("status") != "ERROR" else 1


if __name__ == "__main__":
    sys.exit(main())
