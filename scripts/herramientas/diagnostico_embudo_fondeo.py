"""Diagnostico del embudo de mineria: POR QUE muere cada configuracion.

`scripts/mine.py::run_mining_pipeline` devuelve `telemetria` (una entrada por configuracion
descartada, con `etapa`, `motivo`, `trades` y `pf`), pero la cola solo conserva el recuento
agregado del log. Sin el detalle, una campana con 0 certificadas es ciega: no se sabe si las
estrategias no operan (pocos trades) o si operan y pierden (profit factor bajo). Son dos
diagnosticos opuestos y llevan a decisiones opuestas.

REAL-ONLY: ejecuta el pipeline real sobre los datasets reales; no simula nada.

Uso:
    .venv/bin/python scripts/herramientas/diagnostico_embudo_fondeo.py --symbol GC --tf 1h
"""
from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--track", default="fondeo")
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--tf", default="1h")
    ap.add_argument("--profile", default="arquetipos")
    ap.add_argument("--max-candidates", type=int, default=2000)
    ap.add_argument("--json-out", default=None, help="Ruta para volcar la telemetria completa")
    args = ap.parse_args()

    from scripts.mine import run_mining_pipeline

    res = run_mining_pipeline(
        track=args.track, symbol=args.symbol, timeframe=args.tf,
        profile=args.profile, max_candidates=args.max_candidates,
    )
    tel = res.get("telemetria") or []
    if not tel:
        print("Sin telemetria: el pipeline no evaluo ninguna configuracion.")
        print(json.dumps({k: v for k, v in res.items() if k != "telemetria"}, indent=1)[:800])
        return 1

    print(f"\n=== {args.track.upper()} {args.symbol} {args.tf} perfil={args.profile} ===")
    print(f"configuraciones evaluadas: {len(tel)} · certificadas: {res.get('certified_count')}")
    print(f"embudo: {res.get('embudo')}\n")

    for etapa in ("IS", "VAL", "OOS", "GATES"):
        sub = [r for r in tel if r.get("etapa") == etapa]
        if not sub:
            continue
        trades = [r["trades"] for r in sub if isinstance(r.get("trades"), (int, float))]
        pfs = [r["pf"] for r in sub if isinstance(r.get("pf"), (int, float))]
        print(f"--- etapa {etapa}: {len(sub)} configuraciones ---")
        if trades:
            print(f"    trades  min={min(trades):>5} mediana={st.median(trades):>7.1f} max={max(trades):>5}")
        if pfs:
            print(f"    PF      min={min(pfs):>5.2f} mediana={st.median(pfs):>7.2f} max={max(pfs):>5.2f}")

        # La pregunta que decide todo: dentro de esta etapa, cuantas caen por NO OPERAR
        # (pocos trades) y cuantas por OPERAR MAL (profit factor insuficiente).
        umbral_trades = {"IS": 5, "VAL": 3, "OOS": 100}.get(etapa)
        umbral_pf = {"IS": 1.05, "VAL": 1.0, "OOS": 1.10}.get(etapa)
        if umbral_trades is not None:
            pocos = sum(1 for r in sub if (r.get("trades") or 0) < umbral_trades)
            mal_pf = len(sub) - pocos
            print(f"    causa -> NO OPERAN (trades<{umbral_trades}): {pocos} ({pocos/len(sub)*100:.1f}%)"
                  f" | OPERAN pero PF<{umbral_pf}: {mal_pf} ({mal_pf/len(sub)*100:.1f}%)")
        fams = Counter(r["strategy_id"].split("_")[-2] if "_" in r.get("strategy_id", "") else "?"
                       for r in sub)
        print(f"    por familia (aprox): {dict(fams.most_common(6))}\n")

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(tel, indent=1), encoding="utf-8")
        print(f"telemetria completa -> {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
