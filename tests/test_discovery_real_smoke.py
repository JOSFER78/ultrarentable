from __future__ import annotations

import hashlib
import json
from pathlib import Path

from services.discovery.ultra_discovery import UltraDiscoveryEngine
from services.validation.engine.event_backtest_engine import EventBacktestEngine


def test_real_avx_discovery_produces_trades() -> None:
    """Fails loudly when the real discovery/backtest path produces zero trades on mounted repo data."""
    files = sorted(Path("data/normalized").glob("ds_binance_avaxusdt_1h_*.json"))
    assert files, "No hay dataset AVAXUSDT 1h real montado en data/normalized"
    dataset = files[0]
    candles = json.loads(dataset.read_text(encoding="utf-8"))
    assert len(candles) >= 200, f"Dataset real insuficiente: {len(candles)} velas"

    dataset_sha256 = hashlib.sha256(dataset.read_bytes()).hexdigest()
    engine = UltraDiscoveryEngine()
    backtester = EventBacktestEngine()

    results = []
    for archetype in ("MOMENTUM_BREAKOUT", "TREND_FOLLOWING", "RSI_MOMENTUM", "MEAN_REVERSION"):
        strategy = engine.generate_candidate_blueprint(
            strategy_id=f"SMOKE_{archetype}",
            symbol="AVAX-USDT",
            timeframe="1h",
            dataset_id=dataset.name,
            dataset_sha256=dataset_sha256,
            ema_fast=12,
            ema_slow=50,
            rsi_period=14,
            rsi_threshold_long=52.0,
            rsi_threshold_short=48.0,
            sl_atr_mult=2.0,
            tp_atr_mult=6.0,
            pyramiding_tiers_count=2,
            archetype=archetype,
        )
        result = backtester.run_backtest(strategy, candles, initial_capital_usd=1000.0)
        results.append((archetype, result.total_trades, result.profit_factor, result.net_profit_usd))

    print(f"REAL_DISCOVERY_SMOKE dataset={dataset.name} results={results}")
    assert any(total_trades > 0 for _, total_trades, _, _ in results), (
        f"Discovery/backtest produce 0 trades on real data: {results}"
    )
