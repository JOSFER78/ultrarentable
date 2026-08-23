import json
from pathlib import Path
import re

possible_dirs = [
    Path("data/sqx_imports"),
    Path("/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/sqx_imports"),
    Path(__file__).resolve().parents[0] / "data" / "sqx_imports",
    Path(__file__).resolve().parents[1] / "data" / "sqx_imports",
]

sqx_imports_dir = None
for p in possible_dirs:
    if p.exists() and p.is_dir():
        sqx_imports_dir = p.resolve()
        break

print("Resolved SQX Imports Directory:", sqx_imports_dir)
datasets_map = {}
if sqx_imports_dir and sqx_imports_dir.exists():
    for csv_file in sorted(sqx_imports_dir.glob("*.csv")):
        m = re.match(r"([A-Za-z0-9]+)_([0-9]+[A-Za-z]+)\.csv", csv_file.name)
        if not m:
            continue
        sym_raw, tf = m.group(1), m.group(2).lower()
        if "USDT" in sym_raw:
            base = sym_raw.replace("USDT", "")
            display_sym = f"{base}-USDT"
            engine = "BingX / Binance Perps"
            route = "TRACK_ULTRA"
        elif sym_raw in ["NQ", "ES", "YM", "RTY", "GC", "SI", "CL", "NG", "FDAX", "FTSE", "NK225"]:
            display_sym = sym_raw
            engine = "CME Globex Futures"
            route = "TRACK_FONDEO"
        else:
            display_sym = sym_raw
            engine = "Interbank Forex"
            route = "TRACK_FONDEO"

        if display_sym not in datasets_map:
            datasets_map[display_sym] = {
                "symbol": display_sym,
                "timeframes": set(),
                "engine": engine,
                "route": route,
                "bars": 0,
            }
        datasets_map[display_sym]["timeframes"].add(tf)
        try:
            with open(csv_file, "r", encoding="utf-8") as f:
                cnt = max(0, sum(1 for _ in f) - 1)
                if tf == "1h" or datasets_map[display_sym]["bars"] == 0:
                    datasets_map[display_sym]["bars"] = cnt
        except Exception:
            pass

def _asset_sort_key(item):
    sym = item["symbol"]
    route = item["route"]
    if route == "TRACK_ULTRA":
        priority = 0
        crypto_order = ["BTC-USDT", "ETH-USDT", "SOL-USDT", "SUI-USDT", "DOGE-USDT", "AVAX-USDT", "BNB-USDT", "LINK-USDT", "XRP-USDT"]
        sub_prio = crypto_order.index(sym) if sym in crypto_order else 99
    elif "CME" in item["engine"]:
        priority = 1
        cme_order = ["NQ", "ES", "YM", "RTY", "GC", "SI", "CL"]
        sub_prio = cme_order.index(sym) if sym in cme_order else 99
    else:
        priority = 2
        forex_order = ["EURUSD", "GBPUSD", "USDJPY", "USDCAD", "USDCHF", "AUDUSD"]
        sub_prio = forex_order.index(sym) if sym in forex_order else 99
    return (priority, sub_prio, sym)

inventory = []
for d in sorted(datasets_map.values(), key=_asset_sort_key):
    d["timeframes"] = list(d["timeframes"])
    inventory.append(d)

print("TOTAL ASSETS DETECTED IN DISK:", len(inventory))
print(json.dumps(inventory, indent=2))
