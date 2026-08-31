#!/usr/bin/env python3
"""F02 — Verificación sellada del motor realista (plan v4, bloque F02).

Ejecuta configuraciones "champions" sobre celdas de referencia con el motor ACTUAL y vuelca
métricas + huella del ledger de operaciones a un JSON etiquetado con la versión del motor.
Comparando el JSON de dos versiones se publica la diferencia. Criterio sellado del plan:
"Si el P&L no baja [al añadir fricción], el motor nuevo no está modelando fricción de verdad."

Uso:
    python scripts/verificacion_f02.py            # corre y escribe verificacion_f02_<ver>.json
    python scripts/verificacion_f02.py --comparar 5.6.0 5.7.0   # publica el diff en markdown
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from services.engine_version import CURRENT_ENGINE_VERSION  # noqa: E402

OUT_DIR = REPO_ROOT / "orchestration" / "results"

# Celdas de referencia: cripto ULTRA (datos 100% cobertura) y futuros FONDEO (para el
# point_value y la comision por contrato). La comparacion es RELATIVA entre motores;
# los huecos del dataset Yahoo afectan igual a ambos lados.
CELDAS = [
    ("ultra", "BTCUSDT", "4h"),
    ("ultra", "ETHUSDT", "4h"),
    ("ultra", "LINKUSDT", "1h"),
    ("fondeo", "ES", "4h"),
    ("fondeo", "GC", "4h"),
]
N_CONFIGS = 3  # las 3 curadas del perfil champions


def _cargar_mine():
    spec = importlib.util.spec_from_file_location("mine", REPO_ROOT / "scripts" / "mine.py")
    mine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mine)
    return mine


def correr() -> Path:
    mine = _cargar_mine()
    from services.validation.engine.event_backtest_engine import EventBacktestEngine
    from services.discovery.ultra_discovery import UltraDiscoveryEngine
    from services.discovery.funding_discovery import FundingDiscoveryEngine

    engine = EventBacktestEngine()
    ultra_discovery = UltraDiscoveryEngine()
    funding_discovery = FundingDiscoveryEngine()
    resultados = []

    for track, symbol, tf in CELDAS:
        dataset_file, _ = mine.resolve_dataset_file(symbol, tf)
        if dataset_file is None or not dataset_file.exists():
            resultados.append({"track": track, "symbol": symbol, "tf": tf, "estado": "SIN DATOS"})
            continue
        candles = mine.load_candles_from_file(dataset_file)
        sha = mine.compute_file_sha256(dataset_file)
        dataset_id = dataset_file.stem.replace("_manifest", "")
        exec_symbol = symbol
        if track == "fondeo":
            if symbol in mine.FONDEO_NO_MICRO:
                resultados.append({"track": track, "symbol": symbol, "tf": tf, "estado": "SIN MICRO"})
                continue
            exec_symbol = mine.FONDEO_MICRO_MAP.get(symbol, symbol)

        configs = mine.build_candidate_search_configs(track, symbol, tf, "champions")[:N_CONFIGS]
        for idx, cfg in enumerate(configs, 1):
            sid = f"VERIF_F02_{track.upper()}_{symbol}_{tf.upper()}_c{idx}"
            if track == "ultra":
                snap = ultra_discovery.generate_candidate_blueprint(
                    strategy_id=sid, symbol=symbol, timeframe=tf, dataset_id=dataset_id,
                    dataset_sha256=sha, leverage=5.0, risk_pct=cfg["risk_pct"],
                    sl_atr_mult=cfg["sl_atr_mult"], tp_atr_mult=cfg["tp_atr_mult"],
                    ema_fast=cfg["ema_fast"], ema_slow=cfg["ema_slow"],
                    archetype=cfg["archetype"], pyramiding_tiers=cfg.get("pyramiding_tiers", 0),
                    breakout_lookback=cfg.get("breakout_lookback", 0),
                )
                cap = 1000.0
            else:
                snap = funding_discovery.generate_candidate_blueprint(
                    strategy_id=sid, symbol=exec_symbol, timeframe=tf, dataset_id=dataset_id,
                    dataset_sha256=sha, ema_fast=cfg["ema_fast"], ema_slow=cfg["ema_slow"],
                    sl_atr_mult=cfg["sl_atr_mult"], tp_atr_mult=cfg["tp_atr_mult"],
                    risk_per_trade_pct=cfg["risk_pct"], archetype=cfg["archetype"],
                )
                cap = 50000.0

            bt = engine.run_backtest(snap, candles, initial_capital_usd=cap)
            ledger = [
                (t.entry_bar, t.exit_bar, round(t.entry_price, 6), round(t.exit_price, 6),
                 t.side, round(t.net_pnl_usd, 4), t.exit_reason)
                for t in getattr(bt, "trades", []) or []
            ]
            ledger_sha = hashlib.sha256(json.dumps(ledger, sort_keys=True).encode()).hexdigest()
            resultados.append({
                "track": track, "symbol": symbol, "tf": tf, "config": idx,
                "archetype": cfg["archetype"], "estado": "OK",
                "trades": bt.total_trades,
                "net_profit_usd": round(bt.net_profit_usd, 2),
                "profit_factor": round(bt.profit_factor, 4),
                "max_dd_pct": round(bt.max_drawdown_pct, 2),
                "fees_usd": round(bt.total_fees_usd, 2),
                "slippage_usd": round(bt.total_slippage_usd, 2),
                "ledger_sha256": ledger_sha,
            })

    out = OUT_DIR / f"verificacion_f02_{CURRENT_ENGINE_VERSION}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "engine_version": CURRENT_ENGINE_VERSION,
        "generado": datetime.now(timezone.utc).isoformat(),
        "celdas": resultados,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Baseline motor {CURRENT_ENGINE_VERSION}: {out}")
    for r in resultados:
        if r["estado"] == "OK":
            print(f"  {r['track']:>6} {r['symbol']:>8} {r['tf']:>3} c{r['config']} "
                  f"trades={r['trades']:>4} pnl={r['net_profit_usd']:>12.2f} "
                  f"pf={r['profit_factor']:>7.3f} fees={r['fees_usd']:>10.2f}")
        else:
            print(f"  {r['track']:>6} {r['symbol']:>8} {r['tf']:>3} -> {r['estado']}")
    return out


def comparar(v_old: str, v_new: str) -> int:
    a = json.loads((OUT_DIR / f"verificacion_f02_{v_old}.json").read_text(encoding="utf-8"))
    b = json.loads((OUT_DIR / f"verificacion_f02_{v_new}.json").read_text(encoding="utf-8"))
    idx_a = {(r["track"], r["symbol"], r["tf"], r.get("config")): r for r in a["celdas"] if r["estado"] == "OK"}
    lineas = [
        f"# VERIFICACIÓN F02 — motor {v_old} vs {v_new}",
        "",
        "| Celda | cfg | trades | Δtrades | PnL viejo | PnL nuevo | ΔPnL | PF viejo | PF nuevo | ledger cambió |",
        "| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |",
    ]
    peor = 0
    for r in b["celdas"]:
        if r["estado"] != "OK":
            continue
        k = (r["track"], r["symbol"], r["tf"], r.get("config"))
        o = idx_a.get(k)
        if not o:
            continue
        dpnl = r["net_profit_usd"] - o["net_profit_usd"]
        if dpnl < 0:
            peor += 1
        lineas.append(
            f"| {r['track']} {r['symbol']} {r['tf']} | {r['config']} | {r['trades']} | "
            f"{r['trades'] - o['trades']:+d} | {o['net_profit_usd']:.2f} | {r['net_profit_usd']:.2f} | "
            f"{dpnl:+.2f} | {o['profit_factor']:.3f} | {r['profit_factor']:.3f} | "
            f"{'SÍ' if r['ledger_sha256'] != o['ledger_sha256'] else 'no'} |"
        )
    lineas += [
        "",
        f"Celdas con PnL más bajo en {v_new}: {peor}. Criterio del plan: al añadir fricción el",
        "P&L debe bajar; si no baja, el motor nuevo no modela fricción de verdad.",
    ]
    out = OUT_DIR / f"verificacion_f02_diff_{v_old}_vs_{v_new}.md"
    out.write_text("\n".join(lineas), encoding="utf-8")
    print(f"Diff publicado: {out}")
    print("\n".join(lineas[2:]))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comparar", nargs=2, metavar=("V_VIEJO", "V_NUEVO"))
    args = parser.parse_args()
    if args.comparar:
        return comparar(*args.comparar)
    correr()
    return 0


if __name__ == "__main__":
    sys.exit(main())
