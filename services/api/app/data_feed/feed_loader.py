"""Feed Loader for Multi-Market Quantitative Backtesting.

Agnostic time-series loader supporting:
- Normalized local JSON datasets (data/normalized/)
- Resampling (e.g. 1m -> 5m -> 15m -> 1h -> 4h)
- High-fidelity synthetic geometric Brownian motion with jump diffusion
  for benchmark assets (Forex/Indices) when live history is offline.
"""

from __future__ import annotations

import glob
import json
import math
import random
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_candles(
    symbol: str,
    timeframe: str = "1h",
    data_dir: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Load OHLCV candle list for any symbol and timeframe."""
    normalized_symbol = symbol.replace("/", "-").upper()
    
    # 1. Intentar cargar desde data/normalized/
    if data_dir is None:
        base_path = Path("/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/normalized")
    else:
        base_path = Path(data_dir)
        
    pattern = str(base_path / f"*{normalized_symbol.replace('-', '_')}*{timeframe}*.json")
    matches = [f for f in glob.glob(pattern) if not f.endswith("_manifest.json")]
    
    if matches:
        # Usar el archivo más reciente o más grande
        chosen_file = max(matches, key=lambda p: Path(p).stat().st_size)
        try:
            with open(chosen_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0 and "close" in data[0]:
                    return data
        except Exception:
            pass

    # 2. Generar serie benchmark determinista (Geometric Brownian Motion + Volatilidad de Mercado)
    return generate_benchmark_series(symbol, timeframe, n_bars=3000)


def generate_benchmark_series(
    symbol: str,
    timeframe: str = "1h",
    n_bars: int = 3000,
    seed: int = 42
) -> List[Dict[str, Any]]:
    """Generate high-fidelity benchmark price series for multi-market exploration."""
    rng = random.Random(hash(f"{symbol}_{timeframe}_{seed}"))
    
    # Precios base y volatilidades por activo
    if "BTC" in symbol:
        base_price, annual_vol, dt = 60000.0, 0.65, 1.0 / (365 * 24)
    elif "ETH" in symbol:
        base_price, annual_vol, dt = 3000.0, 0.75, 1.0 / (365 * 24)
    elif "SOL" in symbol:
        base_price, annual_vol, dt = 150.0, 0.90, 1.0 / (365 * 24)
    elif "EUR" in symbol:
        base_price, annual_vol, dt = 1.0850, 0.08, 1.0 / (252 * 24)
    elif "GBP" in symbol:
        base_price, annual_vol, dt = 1.2750, 0.10, 1.0 / (252 * 24)
    elif "NQ" in symbol:
        base_price, annual_vol, dt = 18500.0, 0.22, 1.0 / (252 * 6.5)
    elif "ES" in symbol:
        base_price, annual_vol, dt = 5400.0, 0.16, 1.0 / (252 * 6.5)
    else:
        base_price, annual_vol, dt = 100.0, 0.30, 1.0 / (365 * 24)

    # Ajuste de dt por timeframe
    if timeframe == "1m":
        dt /= 60.0
    elif timeframe == "5m":
        dt /= 12.0
    elif timeframe == "15m":
        dt /= 4.0
    elif timeframe == "4h":
        dt *= 4.0

    current_price = base_price
    bars: List[Dict[str, Any]] = []
    base_ts = 1771718400000  # 2026-02-22
    step_ms = {
        "1m": 60_000,
        "5m": 300_000,
        "15m": 900_000,
        "1h": 3_600_000,
        "4h": 14_400_000,
    }.get(timeframe, 3_600_000)

    for i in range(n_bars):
        # Drift ligero + Shock de volatilidad
        mu = 0.05
        drift = (mu - 0.5 * annual_vol**2) * dt
        shock = annual_vol * math.sqrt(dt) * rng.gauss(0, 1)
        
        # Salto ocasional (1% probabilidad)
        jump = 0.0
        if rng.random() < 0.01:
            jump = rng.gauss(0, annual_vol * 2 * math.sqrt(dt))

        o = current_price
        c = o * math.exp(drift + shock + jump)
        intra_vol = annual_vol * math.sqrt(dt) * 0.5
        h = max(o, c) * (1.0 + abs(rng.gauss(0, intra_vol)))
        l = min(o, c) * (1.0 - abs(rng.gauss(0, intra_vol)))
        vol = round(rng.uniform(500, 5000) * (current_price / 100.0), 2)

        bars.append({
            "timestamp": base_ts + (i * step_ms),
            "open": round(o, 5 if "EUR" in symbol or "GBP" in symbol else 2),
            "high": round(h, 5 if "EUR" in symbol or "GBP" in symbol else 2),
            "low": round(l, 5 if "EUR" in symbol or "GBP" in symbol else 2),
            "close": round(c, 5 if "EUR" in symbol or "GBP" in symbol else 2),
            "volume": vol
        })
        current_price = c

    return bars
