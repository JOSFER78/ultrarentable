#!/usr/bin/env python3
"""scripts/meta.py — Ensamblado y validación honesta de meta-estrategias.

Toma las candidatas REALES certificadas 11/11 de la base canónica, ensambla meta-portafolios
sobre activos ortogonales y los valida walk-forward: el multiplicador de riesgo se elige SOLO
con la primera mitad de la serie y se aplica a ciegas a la segunda.

REAL-ONLY: si una candidata no aporta `oos_returns` reales, se descarta y se dice. Jamás se
fabrica una curva de equity.

Dos lecciones aprendidas el 2026-08-31 y codificadas aquí:

1. NO se dimensiona al drawdown máximo admisible. La k que roza el 70 % en el pasado se sale al
   72 % en el futuro. Se dimensiona a una FRACCIÓN del presupuesto (`--fraccion`, 0.5 por defecto).
2. Una envolvente de riesgo AMPLIFICA lo que haya. Si la esperanza fuera de muestra es negativa,
   amplifica pérdidas: por eso se reporta el resultado a ciegas, no el optimizado.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.portfolio.meta_strategy_engine import MetaStrategyEngine  # noqa: E402

# Presupuesto de drawdown por track (decisión sellada #6 del usuario).
PRESUPUESTO_DD = {"ULTRA": 70.0, "FONDEO": 4.0}
CAPITAL_BASE = {"ULTRA": 1000.0, "FONDEO": 50000.0}


def serie_portafolio(cands: List[Dict[str, Any]], capital: float) -> np.ndarray:
    """Serie de retornos fraccionales del portafolio, ponderado por volatilidad inversa."""
    series, vols = [], []
    for c in cands:
        cap0 = float(c.get("initial_capital_usd") or capital)
        r = np.array(c["oos_returns"], dtype=float) / cap0
        series.append(r)
        vols.append(max(1e-6, float(np.std(r))))
    n = max(len(s) for s in series)
    matriz = np.zeros((len(series), n))
    for i, s in enumerate(series):
        matriz[i, : len(s)] = s  # periodo sin operación = 0, no se rellena
    inv = np.array([1.0 / v for v in vols])
    pesos = inv / inv.sum()
    return (pesos[:, None] * matriz).sum(axis=0)


def simular(retornos: np.ndarray, k: float) -> Tuple[float, float, bool]:
    """Compone la serie con multiplicador k. Devuelve (retorno %, DD máx %, ¿ruina?)."""
    eq = peak = 1.0
    maxdd = 0.0
    for x in retornos:
        eq *= 1.0 + k * x
        if eq <= 0:
            return -100.0, 100.0, True
        peak = max(peak, eq)
        maxdd = max(maxdd, (peak - eq) / peak * 100.0)
    return (eq - 1.0) * 100.0, maxdd, False


def k_maxima(retornos: np.ndarray, dd_budget: float, k_max: int = 1000) -> int:
    """Mayor k que respeta el presupuesto de DD en esta serie."""
    mejor = 0
    for k in range(1, k_max + 1):
        _, dd, ruina = simular(retornos, float(k))
        if not ruina and dd <= dd_budget:
            mejor = k
    return mejor


def seleccionar_ortogonales(cands: List[Dict[str, Any]], min_trades: int) -> List[Dict[str, Any]]:
    """Un activo, una estrategia: la de más operaciones. Diversificación real, no repetida."""
    vistos: Dict[str, Dict[str, Any]] = {}
    for c in sorted(cands, key=lambda z: -int(z.get("trades_oos") or 0)):
        if int(c.get("trades_oos") or 0) < min_trades:
            continue
        sym = str(c.get("symbol"))
        if sym not in vistos:
            vistos[sym] = c
    return list(vistos.values())


def evaluar(route: str, min_trades: int, fraccion: float, solo_nuevas: bool) -> Optional[Dict[str, Any]]:
    engine = MetaStrategyEngine()
    cands = engine.load_candidates_from_db(route=route)
    if solo_nuevas:
        # Solo lo certificado por el pipeline ya corregido (a partir del 2026-08-31 05:00 UTC).
        cands = [c for c in cands if str(c.get("created_at", "")) >= "2026-08-31T05:00"]

    sel = seleccionar_ortogonales(cands, min_trades)
    print(f"\n{'='*74}\n{route} — {len(cands)} candidatas con retornos reales, "
          f"{len(sel)} activos ortogonales (mín. {min_trades} operaciones)\n{'='*74}")
    for c in sel:
        print(f"  {str(c.get('name'))[:34]:<34} {str(c.get('symbol')):<10} "
              f"{str(c.get('timeframe')):<4} ops={c.get('trades_oos')} pf={c.get('profit_factor_oos')}")

    if len(sel) < 2:
        print(f"  >>> NO DATA: hacen falta al menos 2 activos distintos. La campaña de "
              f"descubrimiento aún no ha producido suficientes candidatas para {route}.")
        return None

    capital = CAPITAL_BASE[route]
    dd_budget = PRESUPUESTO_DD[route]

    # --- Meta-portafolio con el motor canónico (persiste con hash SHA-256) ---
    pid = f"META_{route}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}"
    meta = engine.assemble_meta_portfolio(
        portfolio_id=pid, route=route, strategies=sel, allocation_method="RISK_PARITY"
    )
    print(f"\n  Meta-portafolio {pid}")
    for k in ("average_cross_correlation", "drawdown_reduction_pct", "combined_sharpe_ratio",
              "combined_profit_factor", "combined_net_profit_pct", "combined_max_drawdown_pct"):
        if k in meta:
            print(f"    {k:<28} {meta[k]}")

    # --- Validación walk-forward del multiplicador de riesgo ---
    r = serie_portafolio(sel, capital)
    mitad = len(r) // 2
    if mitad < 5:
        print(f"\n  >>> NO_EVIDENCE: solo {len(r)} periodos. Insuficiente para partir en dos "
              f"y validar a ciegas. No se emite veredicto.")
        return {"portfolio_id": pid, "meta": meta, "veredicto": "NO_EVIDENCE"}

    entreno, validacion = r[:mitad], r[mitad:]
    k_tope = k_maxima(entreno, dd_budget)
    k_usada = max(1, int(k_tope * fraccion))
    ret_v, dd_v, ruina = simular(validacion, float(k_usada))
    ret_e, dd_e, _ = simular(entreno, float(k_usada))

    print(f"\n  Validación walk-forward ({mitad} periodos de entreno / {len(validacion)} ciegos)")
    print(f"    k máxima que respeta el {dd_budget}% en entreno : {k_tope}")
    print(f"    k aplicada (fracción {fraccion})                : {k_usada}")
    print(f"    en entreno    : {ret_e:+.1f}%  DD {dd_e:.2f}%")
    print(f"    A CIEGAS      : {ret_v:+.1f}%  DD {dd_v:.2f}%")

    if ruina:
        veredicto = "RUINA"
    elif dd_v > dd_budget:
        veredicto = "EXCEDE_PRESUPUESTO"
    elif ret_v <= 0:
        veredicto = "SIN_EDGE_PERSISTENTE"
    else:
        veredicto = "VALIDA"
    print(f"    VEREDICTO     : {veredicto}")
    if veredicto == "SIN_EDGE_PERSISTENTE":
        print("      El edge no persiste fuera de muestra. Una envolvente amplifica lo que haya:")
        print("      si la esperanza es negativa, amplifica pérdidas. No se despliega.")

    return {"portfolio_id": pid, "meta": meta, "k_tope": k_tope, "k_usada": k_usada,
            "retorno_ciego_pct": round(ret_v, 2), "dd_ciego_pct": round(dd_v, 2),
            "veredicto": veredicto, "activos": [c.get("symbol") for c in sel]}


def main() -> int:
    ap = argparse.ArgumentParser(description="Ensamblado y validación de meta-estrategias.")
    ap.add_argument("--route", choices=["ULTRA", "FONDEO", "AMBOS"], default="AMBOS")
    ap.add_argument("--min-trades", type=int, default=20,
                    help="operaciones OOS mínimas por candidata (por defecto 20)")
    ap.add_argument("--fraccion", type=float, default=0.5,
                    help="fracción del presupuesto de DD que se usa (por defecto 0.5)")
    ap.add_argument("--solo-nuevas", action="store_true",
                    help="usar solo lo certificado por el pipeline corregido")
    ap.add_argument("--salida", default="orchestration/results/meta_resultados.json")
    args = ap.parse_args()

    rutas = ["ULTRA", "FONDEO"] if args.route == "AMBOS" else [args.route]
    out = {}
    for route in rutas:
        out[route] = evaluar(route, args.min_trades, args.fraccion, args.solo_nuevas)

    destino = ROOT / args.salida
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(out, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"\nResultados en {destino}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
