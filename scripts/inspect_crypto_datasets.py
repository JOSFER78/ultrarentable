import glob
import json
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data" / "normalized"

TARGET_SYMBOLS = {"SOL", "SOLUSDT", "XRP", "XRPUSDT", "BNB", "BNBUSDT", "AVAX", "AVAXUSDT", 
                  "LINK", "LINKUSDT", "DOGE", "DOGEUSDT", "BTC", "BTCUSDT", "ETH", "ETHUSDT", "SUI", "SUIUSDT"}
TARGET_TFS = {"1m", "5m", "15m", "1h", "4h"}

manifest_files = sorted(glob.glob(str(DATA_DIR / "*_manifest.json")))
datasets = []

for m_file in manifest_files:
    try:
        with open(m_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        
        raw_sym = manifest.get("symbol", "").upper().replace("-", "").replace("_", "")
        tf = manifest.get("interval", "").lower()
        
        if raw_sym in TARGET_SYMBOLS and tf in TARGET_TFS:
            data_file = m_file.replace("_manifest.json", ".json")
            if os.path.exists(data_file):
                size_mb = os.path.getsize(data_file) / (1024 * 1024)
                datasets.append((raw_sym, tf, data_file, m_file, size_mb, manifest))
    except Exception as e:
        print(f"Error reading {m_file}: {e}")

print(f"Total matching crypto datasets: {len(datasets)}")
by_sym_tf = {}
for sym, tf, df, mf, sz, mdata in datasets:
    by_sym_tf.setdefault(sym, {})[tf] = (df, sz)

for sym in sorted(by_sym_tf.keys()):
    print(f"\nSymbol: {sym}")
    for tf in sorted(by_sym_tf[sym].keys()):
        df, sz = by_sym_tf[sym][tf]
        print(f"  {tf}: {Path(df).name} ({sz:.2f} MB)")
