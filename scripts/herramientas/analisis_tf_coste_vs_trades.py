"""Mide ATR(14)% real por TF sobre el tramo BLIND OOS (ultimo 20%) y lo compara con el
coste round-trip real de BingX. REAL-ONLY: datos de data/normalized + data/registry."""
import json, glob, sys
import numpy as np

FR = json.load(open("data/registry/bingx_friction.json"))["resumen"]["pairs"]

def atr_pct(path, frac_oos=0.20, n=14):
    c = json.load(open(path))
    k = int(len(c) * (1 - frac_oos))
    c = c[k:]                      # solo el tramo BLIND OOS
    h = np.fromiter((b["high"] for b in c), float, len(c))
    l = np.fromiter((b["low"] for b in c), float, len(c))
    cl = np.fromiter((b["close"] for b in c), float, len(c))
    pc = np.concatenate(([cl[0]], cl[:-1]))
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    # ATR Wilder aproximado por media movil simple sobre TR (suficiente para dimensionar)
    atr = np.convolve(tr, np.ones(n) / n, mode="valid")
    px = cl[n - 1:]
    return float(np.median(atr / px * 100.0)), len(c)

print(f"{'SIMBOLO':>9} {'TF':>4} {'barrasOOS':>9} {'ATR%med':>8} {'coste%RT':>9} {'coste/ATR':>10} {'TP4ATR neto':>12}")
print("-" * 70)
for sym in ("BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "XRPUSDT"):
    pair = sym.replace("USDT", "-USDT")
    f = FR.get(pair, {})
    spread = float(f.get("spread_median_pct", 0.0))          # ya en %
    taker = float(f.get("taker_fee_rate", 0.0005)) * 100.0   # a %
    coste_rt = spread + 2 * taker                            # 1 spread completo + 2 comisiones
    for tf in ("5m", "15m", "4h"):
        g = [p for p in glob.glob(f"data/normalized/ds_binance_{sym.lower()}_{tf}_*.json")
             if "manifest" not in p]
        if not g:
            continue
        a, nb = atr_pct(g[0])
        ratio = coste_rt / a * 100.0
        neto = (4 * a - coste_rt) / (4 * a) * 100.0   # % del TP de 4 ATR que sobrevive
        print(f"{sym:>9} {tf:>4} {nb:>9} {a:>8.4f} {coste_rt:>9.4f} {ratio:>9.1f}% {neto:>11.1f}%")
