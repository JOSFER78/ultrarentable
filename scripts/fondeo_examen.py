#!/usr/bin/env python3
"""scripts/fondeo_examen.py — ¿Cuántos días tarda en pasar el examen, y con qué riesgo de romperlo?

Responde a la pregunta real del track FONDEO: no "cuánto gana", sino
**P(pasar en ≤N días) sujeto a P(violar una regla) < umbral**.

Método: Monte Carlo por remuestreo (bootstrap) de las operaciones REALES del backtest OOS.
Nunca se generan retornos sintéticos: se reordenan y remuestrean operaciones que ocurrieron.
Es la diferencia entre estimar la distribución de un edge real y fabricar uno.

Reglas simuladas (configurables, NO hardcodeadas como verdad universal — cada firma tiene las
suyas y hay que ponerlas):
  - objetivo de beneficio
  - pérdida diaria máxima
  - drawdown total máximo (trailing sobre el pico, que es como matan de verdad las cuentas)
  - días mínimos de operativa
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.portfolio.meta_strategy_engine import MetaStrategyEngine  # noqa: E402


class ReglasExamen:
    """Reglas de una evaluación de prop firm. Por defecto, un perfil tipo 50k bastante común.

    IMPORTANTE: estos valores son un PUNTO DE PARTIDA razonable, no la verdad de ninguna firma
    concreta. Antes de operar de verdad hay que poner los de la firma real.
    """

    def __init__(self, capital: float = 50000.0, objetivo_pct: float = 8.0,
                 perdida_diaria_pct: float = 2.0, dd_total_pct: float = 4.0,
                 dias_minimos: int = 1, trailing: bool = True):
        self.capital = capital
        self.objetivo = capital * objetivo_pct / 100.0
        self.perdida_diaria = capital * perdida_diaria_pct / 100.0
        self.dd_total = capital * dd_total_pct / 100.0
        self.dias_minimos = dias_minimos
        self.trailing = trailing


def simular_examen(trades: np.ndarray, ops_por_dia: float, reglas: ReglasExamen,
                   max_dias: int, rng: np.random.Generator) -> Dict[str, Any]:
    """Un examen completo. Devuelve si pasó, en cuántos días, y si violó alguna regla."""
    equity = reglas.capital
    pico = reglas.capital
    dia = 0
    while dia < max_dias:
        dia += 1
        # Numero de operaciones del dia: Poisson alrededor del ritmo real observado
        n_ops = max(0, int(rng.poisson(ops_por_dia)))
        pnl_dia = 0.0
        for _ in range(n_ops):
            pnl = float(rng.choice(trades))          # remuestreo de una operacion REAL
            equity += pnl
            pnl_dia += pnl
            pico = max(pico, equity)
            # Drawdown total: trailing sobre el pico si la firma lo aplica asi
            referencia = pico if reglas.trailing else reglas.capital
            if referencia - equity >= reglas.dd_total:
                return {"paso": False, "dias": dia, "violacion": "DD_TOTAL",
                        "equity_final": equity}
        if -pnl_dia >= reglas.perdida_diaria:
            return {"paso": False, "dias": dia, "violacion": "PERDIDA_DIARIA",
                    "equity_final": equity}
        if equity - reglas.capital >= reglas.objetivo and dia >= reglas.dias_minimos:
            return {"paso": True, "dias": dia, "violacion": None, "equity_final": equity}
    return {"paso": False, "dias": max_dias, "violacion": "SIN_ALCANZAR_OBJETIVO",
            "equity_final": equity}


def evaluar(trades: np.ndarray, ops_por_dia: float, reglas: ReglasExamen,
            multiplicador: float, iteraciones: int, max_dias: int,
            semilla: int = 7) -> Dict[str, Any]:
    """Distribución completa del examen con las operaciones escaladas por `multiplicador`."""
    rng = np.random.default_rng(semilla)
    escaladas = trades * multiplicador
    resultados = [simular_examen(escaladas, ops_por_dia, reglas, max_dias, rng)
                  for _ in range(iteraciones)]

    pasados = [r for r in resultados if r["paso"]]
    dias = sorted(r["dias"] for r in pasados)
    violaciones: Dict[str, int] = {}
    for r in resultados:
        if r["violacion"]:
            violaciones[r["violacion"]] = violaciones.get(r["violacion"], 0) + 1

    p_pasar = len(pasados) / len(resultados)
    p_romper = sum(v for k, v in violaciones.items() if k != "SIN_ALCANZAR_OBJETIVO") / len(resultados)
    return {
        "multiplicador": multiplicador,
        "p_pasar": round(p_pasar, 4),
        "p_romper_cuenta": round(p_romper, 4),
        "dias_mediana": dias[len(dias) // 2] if dias else None,
        "dias_p90": dias[int(len(dias) * 0.9)] if dias else None,
        "violaciones": violaciones,
    }


class CicloFondeado:
    """El negocio completo: aprobar, sobrevivir y COBRAR.

    Mandato del usuario (2026-08-31): "cuando se aprueba se deben hacer retiros, sin retiros
    no hay negocio". Una cuenta fondeada que nunca paga vale exactamente lo que costo el examen.

    Por eso el ciclo tiene DOS regimenes de riesgo distintos, y esa es la clave del modelo:

      FASE 1 - EXAMEN: agresiva. Hay que alcanzar el objetivo en pocos dias. Romper la cuenta
      cuesta un cartucho (~58 USD) y se dispara otro, asi que el riesgo alto SALE A CUENTA:
      la esperanza es positiva por encima de p_be = C_total/R_avg = 2,91%.

      FASE 2 - FONDEADA: conservadora. Aqui romper ya no cuesta un cartucho, cuesta la cuenta
      entera y todos los payouts futuros. El objetivo deja de ser crecer y pasa a ser
      SOBREVIVIR HASTA EL SIGUIENTE RETIRO, y repetir.

    El valor de una cuenta fondeada no es su beneficio: es la suma de los payouts que llega a
    cobrar antes de romperse.
    """

    def __init__(self, capital: float, umbral_retiro_pct: float = 2.0,
                 dias_entre_retiros: int = 14, reparto_trader: float = 0.90,
                 dd_total_pct: float = 4.0, perdida_diaria_pct: float = 2.0):
        self.capital = capital
        self.umbral_retiro = capital * umbral_retiro_pct / 100.0
        self.dias_entre_retiros = dias_entre_retiros
        self.reparto_trader = reparto_trader
        self.dd_total = capital * dd_total_pct / 100.0
        self.perdida_diaria = capital * perdida_diaria_pct / 100.0


def simular_vida_fondeada(trades: np.ndarray, ops_por_dia: float, ciclo: CicloFondeado,
                          max_dias: int, rng: np.random.Generator) -> Dict[str, Any]:
    """Vida completa de una cuenta ya fondeada: cuanto cobra antes de romperse."""
    equity = ciclo.capital
    pico = ciclo.capital
    cobrado = 0.0
    retiros = 0
    dia = 0
    dias_desde_retiro = 0

    while dia < max_dias:
        dia += 1
        dias_desde_retiro += 1
        pnl_dia = 0.0
        for _ in range(max(0, int(rng.poisson(ops_por_dia)))):
            equity += float(rng.choice(trades))
            pnl_dia += 0.0
            pico = max(pico, equity)
            if pico - equity >= ciclo.dd_total:
                return {"cobrado": cobrado, "retiros": retiros, "dias": dia, "rota": True}
        if ciclo.capital - equity >= ciclo.perdida_diaria and pnl_dia < 0:
            return {"cobrado": cobrado, "retiros": retiros, "dias": dia, "rota": True}

        # Retiro: solo si hay beneficio acumulado suficiente y toca por calendario.
        beneficio = equity - ciclo.capital
        if beneficio >= ciclo.umbral_retiro and dias_desde_retiro >= ciclo.dias_entre_retiros:
            pago = beneficio * ciclo.reparto_trader
            cobrado += pago
            equity -= beneficio          # el beneficio sale de la cuenta
            pico = equity                 # el trailing se recalcula desde el nuevo saldo
            retiros += 1
            dias_desde_retiro = 0

    return {"cobrado": cobrado, "retiros": retiros, "dias": dia, "rota": False}


def evaluar_negocio(trades: np.ndarray, ops_por_dia: float, ciclo: CicloFondeado,
                    mult_fondeada: float, iteraciones: int, dias_horizonte: int,
                    semilla: int = 11) -> Dict[str, Any]:
    """Cuanto dinero devuelve de verdad una cuenta fondeada, en payouts cobrados."""
    rng = np.random.default_rng(semilla)
    escaladas = trades * mult_fondeada
    res = [simular_vida_fondeada(escaladas, ops_por_dia, ciclo, dias_horizonte, rng)
           for _ in range(iteraciones)]
    cobros = sorted(r["cobrado"] for r in res)
    return {
        "mult_fondeada": mult_fondeada,
        "cobrado_medio": round(sum(cobros) / len(cobros), 0),
        "cobrado_mediana": round(cobros[len(cobros) // 2], 0),
        "cobrado_p10": round(cobros[int(len(cobros) * 0.10)], 0),
        "retiros_medios": round(sum(r["retiros"] for r in res) / len(res), 2),
        "p_romper": round(sum(1 for r in res if r["rota"]) / len(res), 4),
        "p_sin_cobrar_nada": round(sum(1 for r in res if r["cobrado"] == 0) / len(res), 4),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Optimizador de paso de examen de fondeo.")
    ap.add_argument("--symbol", help="evaluar una candidata concreta; si se omite, todas las FONDEO")
    ap.add_argument("--capital", type=float, default=50000.0)
    ap.add_argument("--objetivo-pct", type=float, default=8.0)
    ap.add_argument("--perdida-diaria-pct", type=float, default=2.0)
    ap.add_argument("--dd-total-pct", type=float, default=4.0)
    ap.add_argument("--max-dias", type=int, default=8, help="ventana objetivo (usuario: 3-8 dias)")
    ap.add_argument("--iteraciones", type=int, default=4000)
    # --- Economia del negocio de cartuchos (docs/tradesfera/02_MATEMATICA_BANKROLL) ---
    ap.add_argument("--coste-cartucho", type=float, default=58.20,
                    help="C_total = examen + activacion. Ej: Tradeify 50K = 58,20 USD")
    ap.add_argument("--payout-medio", type=float, default=2000.0,
                    help="R_avg: beneficio neto medio retirado por cuenta que llega a cobrar")
    ap.add_argument("--bankroll", type=float, default=3800.0,
                    help="capital destinado al programa de fondeo")
    ap.add_argument("--salida", default="orchestration/results/fondeo_examen.json")
    args = ap.parse_args()

    reglas = ReglasExamen(args.capital, args.objetivo_pct, args.perdida_diaria_pct,
                          args.dd_total_pct)
    engine = MetaStrategyEngine()
    cands = engine.load_candidates_from_db(route="FONDEO")
    if args.symbol:
        cands = [c for c in cands if str(c.get("symbol")) == args.symbol]

    if not cands:
        print("NO DATA: no hay candidatas FONDEO con retornos OOS reales en la base canónica.")
        print("La campaña de descubrimiento aún no ha producido ninguna. No se inventa nada.")
        return 1

    print(f"Reglas del examen: capital {reglas.capital:,.0f} · objetivo {args.objetivo_pct}% "
          f"({reglas.objetivo:,.0f}) · pérdida diaria {args.perdida_diaria_pct}% · "
          f"DD total {args.dd_total_pct}% (trailing) · ventana {args.max_dias} días")
    p_be = args.coste_cartucho / args.payout_medio
    n_intentos = int(args.bankroll // args.coste_cartucho)
    print(f"Método: {args.iteraciones:,} exámenes simulados por remuestreo de operaciones REALES")
    print(f"\nECONOMÍA DEL NEGOCIO (docs/tradesfera/02_MATEMATICA_BANKROLL_Y_CAPITAL_MUNICION.md):")
    print(f"  Coste por cartucho C_total : {args.coste_cartucho:,.2f} USD")
    print(f"  Payout medio R_avg         : {args.payout_medio:,.0f} USD")
    print(f"  Bankroll                   : {args.bankroll:,.0f} USD -> {n_intentos} intentos")
    print(f"  UMBRAL DE RENTABILIDAD     : p_be = C_total/R_avg = {p_be:.2%}")
    print(f"  >>> Por encima de {p_be:.2%} de probabilidad de aprobar, la esperanza YA es positiva.")
    print(f"  >>> Romper una cuenta no es una catastrofe: cuesta un cartucho y se dispara otro.\n")

    resultados = {}
    for c in cands:
        trades = np.array(c["oos_returns"], dtype=float)
        cap0 = float(c.get("initial_capital_usd") or reglas.capital)
        trades = trades / cap0 * reglas.capital      # normalizar al capital del examen
        # Ritmo real observado: no se asume, se deduce de la propia serie.
        ops_por_dia = max(0.5, len(trades) / 60.0)

        nombre = str(c.get("name"))
        print(f"=== {nombre}  ({c.get('symbol')} {c.get('timeframe')}, "
              f"{len(trades)} operaciones reales) ===")
        print(f"{'mult':>6} {'P(pasar)':>10} {'ROI/cartucho':>13} {'EV pool':>12} "
              f"{'días med':>9}  veredicto")

        mejor = None
        for mult in (1, 2, 3, 5, 8, 12, 20, 30, 45):
            r = evaluar(trades, ops_por_dia, reglas, float(mult), args.iteraciones, args.max_dias)
            # ROI unitario = p*R_avg/C_total - 1   (formula 2.4 del dossier Tradesfera)
            roi = (r["p_pasar"] * args.payout_medio / args.coste_cartucho) - 1.0
            ev_pool = n_intentos * (r["p_pasar"] * args.payout_medio - args.coste_cartucho)
            r["roi_cartucho"] = round(roi, 3)
            r["ev_pool_usd"] = round(ev_pool, 0)
            marca = "RENTABLE" if roi > 0 else "pierde dinero"
            print(f"{mult:>6} {r['p_pasar']:>10.1%} {roi:>12.1%} {ev_pool:>11,.0f}$ "
                  f"{str(r['dias_mediana'] or '-'):>9}  {marca}")
            if roi > 0 and (mejor is None or roi > mejor["roi_cartucho"]):
                mejor = r
        if mejor:
            print(f"  -> ÓPTIMO ECONÓMICO: multiplicador {mejor['multiplicador']} · "
                  f"P(pasar)={mejor['p_pasar']:.1%} (umbral {p_be:.2%}) · "
                  f"ROI por cartucho {mejor['roi_cartucho']:.0%} · "
                  f"EV del pool {mejor['ev_pool_usd']:,.0f}$ · mediana {mejor['dias_mediana']} días")
        else:
            print(f"  -> NINGUNA configuración supera el umbral de {p_be:.2%}. Esta estrategia "
                  f"no da dinero ni como negocio de cartuchos. Se reporta tal cual.")
        resultados[nombre] = {"mejor": mejor, "operaciones": len(trades)}
        print()

    destino = ROOT / args.salida
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(resultados, indent=2, ensure_ascii=False, default=str),
                       encoding="utf-8")
    print(f"Resultados en {destino}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
