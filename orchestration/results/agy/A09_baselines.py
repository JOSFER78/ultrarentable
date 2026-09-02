"""orchestration/results/agy/A09_baselines.py
Comparacion de baselines de verificacion_f02: 5.17.0 vs 5.18.0.
Verifica que las 9 celdas ULTRA son 100% identicas (sin sesion) y que las 6 celdas FONDEO
reflejan las sesiones conscientes de DST y flat obligatorio.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Configurar stdout para UTF-8 en Windows si es necesario
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parents[3]
F17_PATH = REPO_ROOT / "orchestration" / "results" / "verificacion_f02_5.17.0.json"
F18_PATH = REPO_ROOT / "orchestration" / "results" / "verificacion_f02_5.18.0.json"


def main() -> int:
    if not F17_PATH.exists():
        print(f"ERROR: No existe {F17_PATH}", file=sys.stderr)
        return 1
    if not F18_PATH.exists():
        print(f"ERROR: No existe {F18_PATH}", file=sys.stderr)
        return 1

    f17 = json.loads(F17_PATH.read_text(encoding="utf-8"))
    f18 = json.loads(F18_PATH.read_text(encoding="utf-8"))

    celdas_17 = {(c["track"], c["symbol"], c["tf"], c["config"]): c for c in f17["celdas"]}
    celdas_18 = {(c["track"], c["symbol"], c["tf"], c["config"]): c for c in f18["celdas"]}

    print("| Track | Simbolo | TF | Cfg | Arquetipo | Trades (5.17 -> 5.18) | Net PnL (5.17 -> 5.18) | PF (5.17 -> 5.18) | Ledger SHA Igual? |")
    print("| :--- | :--- | :--- | :---: | :--- | :---: | :---: | :---: | :---: |")

    ultra_identicas = 0
    ultra_total = 0
    fondeo_distintas = 0
    fondeo_total = 0

    for key, c18 in celdas_18.items():
        c17 = celdas_17.get(key)
        if not c17:
            print(f"Falta celda en 5.17: {key}", file=sys.stderr)
            continue

        track, sym, tf, cfg = key
        arch = c18.get("archetype", "")
        t17, t18 = c17.get("trades", 0), c18.get("trades", 0)
        pnl17, pnl18 = c17.get("net_profit_usd", 0.0), c18.get("net_profit_usd", 0.0)
        pf17, pf18 = c17.get("profit_factor", 0.0), c18.get("profit_factor", 0.0)
        sha17, sha18 = c17.get("ledger_sha256", ""), c18.get("ledger_sha256", "")

        sha_igual = (sha17 == sha18)
        sha_str = "SI (identico)" if sha_igual else "NO (cambio)"

        print(f"| {track.upper()} | {sym} | {tf} | {cfg} | {arch} | {t17} -> {t18} | {pnl17:.2f} -> {pnl18:.2f} | {pf17:.2f} -> {pf18:.2f} | {sha_str} |")

        if track == "ultra":
            ultra_total += 1
            if sha_igual and t17 == t18 and pnl17 == pnl18 and pf17 == pf18:
                ultra_identicas += 1
        elif track == "fondeo":
            fondeo_total += 1
            if not sha_igual:
                fondeo_distintas += 1

    print()
    print(f"ULTRA_IDENTICAS={ultra_identicas} FONDEO_DISTINTAS={fondeo_distintas}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
