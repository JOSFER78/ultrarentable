"""Feed Loader for Real-World Quantitative Backtesting.

Agnostic time-series loader supporting ONLY verified normalized historical datasets from disk:
1. BingX JSON datasets in data/normalized/
2. Local CSV verified datasets in /home/ubuntu/workspace/pro/trading/04 Indicadores Pine/data/

ZERO synthetic or simulated data generation.
"""

from __future__ import annotations

import csv
import glob
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("feed_loader")

CSV_DATA_DIR = Path("/home/ubuntu/workspace/pro/trading/04 Indicadores Pine/data")
NORMALIZED_DATA_DIR = Path("/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/normalized")

# In-memory cache to prevent disk thrashing
_CANDLE_CACHE: Dict[str, List[Dict[str, Any]]] = {}


def _parse_csv_candles(filepath: Path, max_bars: int = 25000) -> List[Dict[str, Any]]:
    """Parse local OHLCV CSV file into standard candle dictionary."""
    candles: List[Dict[str, Any]] = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    c_time = row.get("date") or row.get("timestamp") or row.get("time") or ""
                    o_px = float(row.get("open") or 0.0)
                    h_px = float(row.get("high") or 0.0)
                    l_px = float(row.get("low") or 0.0)
                    c_px = float(row.get("close") or 0.0)
                    vol = float(row.get("volume") or 0.0)
                    if c_px > 0:
                        candles.append({
                            "time": c_time,
                            "open": o_px,
                            "high": h_px,
                            "low": l_px,
                            "close": c_px,
                            "volume": vol
                        })
                except (ValueError, TypeError):
                    continue
        if len(candles) > max_bars:
            # Take the most recent bars
            candles = candles[-max_bars:]
        return candles
    except Exception as e:
        logger.error(f"Error parsing CSV {filepath}: {e}")
        return []


def load_candles(
    symbol: str,
    timeframe: str = "1h",
    data_dir: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Load real OHLCV candle list for a symbol and timeframe from local verified files.
    
    Returns empty list if no real data file exists on disk.
    """
    cache_key = f"{symbol}_{timeframe}"
    if cache_key in _CANDLE_CACHE:
        return _CANDLE_CACHE[cache_key]

    normalized_symbol = symbol.replace("/", "-").replace("_", "-").upper()
    
    # 1. Check normalized JSON files
    base_path = Path(data_dir) if data_dir else NORMALIZED_DATA_DIR
    if base_path.exists():
        symbol_variants = [
            normalized_symbol.replace("-", "_"),
            normalized_symbol,
        ]
        
        matches = []
        for s_var in symbol_variants:
            pattern = str(base_path / f"*{s_var}*{timeframe}*.json")
            found = [f for f in glob.glob(pattern) if not f.endswith("_manifest.json")]
            matches.extend(found)
            
        if matches:
            chosen_file = max(matches, key=lambda p: Path(p).stat().st_size)
            try:
                with open(chosen_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0 and "close" in data[0]:
                        # Limit to last 25,000 candles for ultra-fast evaluations
                        trimmed = data[-25000:] if len(data) > 25000 else data
                        _CANDLE_CACHE[cache_key] = trimmed
                        return trimmed
            except Exception as e:
                logger.error(f"Error loading JSON candle file {chosen_file}: {e}")

    # 2. Check local CSV datasets (BTC, ETH, SOL, NQ/QQQ, ES/SPY, EURUSD, GBPUSD, GLD)
    if CSV_DATA_DIR.exists():
        # Mapping rules
        csv_candidates: List[Path] = []
        
        # Crypto mappings
        if "BTC" in normalized_symbol:
            csv_candidates.extend([
                CSV_DATA_DIR / f"BTCUSDT_{timeframe}.csv",
                CSV_DATA_DIR / "BTCUSDT_1h.csv",
                CSV_DATA_DIR / "BTCUSDT.csv",
                CSV_DATA_DIR / "BTC-USD.csv",
            ])
        elif "ETH" in normalized_symbol:
            csv_candidates.extend([
                CSV_DATA_DIR / f"ETHUSDT_{timeframe}.csv",
                CSV_DATA_DIR / "ETHUSDT_1h.csv",
                CSV_DATA_DIR / "ETHUSDT.csv",
                CSV_DATA_DIR / "ETH-USD.csv",
            ])
        elif "SOL" in normalized_symbol:
            csv_candidates.extend([
                CSV_DATA_DIR / "SOLUSDT.csv",
                CSV_DATA_DIR / "SOL-USD.csv",
            ])
        elif "DOGE" in normalized_symbol:
            csv_candidates.append(CSV_DATA_DIR / "DOGEUSDT.csv")
        # Fondeo / Prop Firm mappings (Only map when appropriate timeframe)
        elif normalized_symbol in ["EURUSD", "EUR-USD"]:
            csv_candidates.append(CSV_DATA_DIR / "EURUSD=X.csv")
        elif normalized_symbol in ["GBPUSD", "GBP-USD"]:
            csv_candidates.append(CSV_DATA_DIR / "GBPUSD=X.csv")
        elif normalized_symbol in ["GLD", "GOLD", "XAUUSD"]:
            csv_candidates.append(CSV_DATA_DIR / "GLD.csv")
        elif normalized_symbol in ["NQ", "MNQ", "NASDAQ"] and timeframe in ["1d", "daily"]:
            csv_candidates.append(CSV_DATA_DIR / "QQQ.csv")
        elif normalized_symbol in ["ES", "MES", "SP500", "SPY"] and timeframe in ["1d", "daily"]:
            csv_candidates.extend([
                CSV_DATA_DIR / "SPY.csv",
                CSV_DATA_DIR / "^GSPC.csv",
            ])

        for candidate_path in csv_candidates:
            if candidate_path.exists():
                candles = _parse_csv_candles(candidate_path)
                if len(candles) >= 100:
                    _CANDLE_CACHE[cache_key] = candles
                    logger.info(f"Loaded {len(candles)} verified real bars for {symbol} ({timeframe}) from {candidate_path.name}")
                    return candles

    # STRICT: Never generate synthetic/mock data.
    logger.info(f"No real historical data found on disk for {symbol} ({timeframe}).")
    return []
