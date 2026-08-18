"""Seed Factory for generating initial strategy populations."""
from __future__ import annotations

import random
from typing import Any

from services.api.app.factory.grammar import TypedGrammar


QUANTITATIVE_TEMPLATES = [
    {
        "name": "EMA Crossover Trend Template",
        "family": "trend_following",
        "longEntry_fast": 10,
        "longEntry_slow": 30,
        "exit_slow": 50,
    },
    {
        "name": "RSI Mean Reversion Template",
        "family": "mean_reversion",
        "rsi_period": 14,
        "oversold": 30.0,
        "overbought": 70.0,
    },
    {
        "name": "Donchian Breakout Momentum Template",
        "family": "breakout",
        "donchian_period": 20,
    },
    {
        "name": "Ultra Hyperscale Asymmetric Burst",
        "family": "hyperscale",
        "fast_ema": 9,
        "slow_ema": 21,
        "atr_period": 14,
    },
    {
        "name": "Prop Firm Conservative Session Trend",
        "family": "fondeo_preservation",
        "fast_ema": 20,
        "slow_ema": 50,
        "donchian_period": 30,
    },
]


class SeedFactory:
    """Generates initial populations for autonomous search campaigns."""

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self.grammar = TypedGrammar(rng=self.rng)

    def _determine_venue(self, symbol: str) -> str:
        s = symbol.upper()
        if any(f in s for f in ("NQ", "ES", "YM", "RTY", "CL", "GC", "MES", "MNQ")):
            return "CME"
        elif "USDT" in s or s in ("BTC", "ETH", "SOL", "DOGE", "AVAX"):
            return "BINGX"
        return "UNIVERSAL"

    def create_template_strategy(
        self, template_index: int, symbol: str = "NQ", timeframe: str = "1h"
    ) -> dict[str, Any]:
        tmpl = QUANTITATIVE_TEMPLATES[template_index % len(QUANTITATIVE_TEMPLATES)]
        venue = self._determine_venue(symbol)
        if tmpl["family"] == "trend_following":
            fast_p = tmpl.get("longEntry_fast", 10)
            slow_p = tmpl.get("longEntry_slow", 30)
            exit_p = tmpl.get("exit_slow", 50)
            return {
                "dslVersion": "1.0.0",
                "metadata": {"name": tmpl["name"], "family": "trend_following", "parents": [], "origin": "MANUAL"},
                "market": {"venue": venue, "symbol": symbol, "timeframe": timeframe},
                "signals": {
                    "longEntry": {
                        "nodeType": "COMPARISON",
                        "op": "CROSS_ABOVE",
                        "left": {
                            "type": "INDICATOR",
                            "indicator": "EMA",
                            "source": {"type": "SERIES", "series": "CLOSE", "offset": 0},
                            "params": {"period": fast_p},
                            "offset": 0,
                        },
                        "right": {
                            "type": "INDICATOR",
                            "indicator": "EMA",
                            "source": {"type": "SERIES", "series": "CLOSE", "offset": 0},
                            "params": {"period": slow_p},
                            "offset": 0,
                        },
                    },
                    "shortEntry": {
                        "nodeType": "COMPARISON",
                        "op": "CROSS_BELOW",
                        "left": {
                            "type": "INDICATOR",
                            "indicator": "EMA",
                            "source": {"type": "SERIES", "series": "CLOSE", "offset": 0},
                            "params": {"period": fast_p},
                            "offset": 0,
                        },
                        "right": {
                            "type": "INDICATOR",
                            "indicator": "EMA",
                            "source": {"type": "SERIES", "series": "CLOSE", "offset": 0},
                            "params": {"period": slow_p},
                            "offset": 0,
                        },
                    },
                    "longExit": {
                        "nodeType": "COMPARISON",
                        "op": "CROSS_BELOW",
                        "left": {"type": "SERIES", "series": "CLOSE", "offset": 0},
                        "right": {
                            "type": "INDICATOR",
                            "indicator": "SMA",
                            "source": {"type": "SERIES", "series": "CLOSE", "offset": 0},
                            "params": {"period": exit_p},
                            "offset": 0,
                        },
                    },
                    "shortExit": {
                        "nodeType": "COMPARISON",
                        "op": "CROSS_ABOVE",
                        "left": {"type": "SERIES", "series": "CLOSE", "offset": 0},
                        "right": {
                            "type": "INDICATOR",
                            "indicator": "SMA",
                            "source": {"type": "SERIES", "series": "CLOSE", "offset": 0},
                            "params": {"period": exit_p},
                            "offset": 0,
                        },
                    },
                },
                "position": {"marginMode": "ISOLATED", "leverage": 1, "allocationPct": 25.0, "compound": True, "pyramiding": {"enabled": False, "maxEntries": 1}, "riskManagement": {"stopLossPct": 2.0, "takeProfitPct": 4.0, "trailingStopPct": 1.5, "maxHoldingBars": 200}},
                "execution": {"entryOrderType": "MARKET", "exitOrderType": "MARKET", "signalTiming": "BAR_CLOSE_EXECUTE_NEXT_OPEN"},
            }
        strategy = self.create_template_strategy(0, symbol=symbol, timeframe=timeframe)
        strategy["metadata"] = {
            "name": tmpl["name"],
            "family": tmpl["family"],
            "parents": [],
            "origin": "MANUAL",
        }
        close = {"type": "SERIES", "series": "CLOSE", "offset": 0}

        if tmpl["family"] == "mean_reversion":
            period = int(tmpl["rsi_period"])

            def rsi() -> dict[str, Any]:
                return {
                    "type": "INDICATOR",
                    "indicator": "RSI",
                    "source": dict(close),
                    "params": {"period": period},
                    "offset": 0,
                }

            def threshold(op: str, value: float) -> dict[str, Any]:
                return {
                    "nodeType": "COMPARISON",
                    "op": op,
                    "left": rsi(),
                    "right": {"type": "CONSTANT", "value": float(value)},
                }

            strategy["signals"] = {
                "longEntry": threshold("CROSS_BELOW", float(tmpl["oversold"])),
                "shortEntry": threshold("CROSS_ABOVE", float(tmpl["overbought"])),
                "longExit": threshold("CROSS_ABOVE", 50.0),
                "shortExit": threshold("CROSS_BELOW", 50.0),
            }
            return strategy

        if tmpl["family"] == "hyperscale":
            fast_p = int(tmpl.get("fast_ema", 9))
            slow_p = int(tmpl.get("slow_ema", 21))
            strategy["signals"] = {
                "longEntry": {
                    "nodeType": "COMPARISON",
                    "op": "CROSS_ABOVE",
                    "left": {"type": "INDICATOR", "indicator": "EMA", "source": dict(close), "params": {"period": fast_p}, "offset": 0},
                    "right": {"type": "INDICATOR", "indicator": "EMA", "source": dict(close), "params": {"period": slow_p}, "offset": 0},
                },
                "shortEntry": {
                    "nodeType": "COMPARISON",
                    "op": "CROSS_BELOW",
                    "left": {"type": "INDICATOR", "indicator": "EMA", "source": dict(close), "params": {"period": fast_p}, "offset": 0},
                    "right": {"type": "INDICATOR", "indicator": "EMA", "source": dict(close), "params": {"period": slow_p}, "offset": 0},
                },
                "longExit": {
                    "nodeType": "COMPARISON",
                    "op": "CROSS_BELOW",
                    "left": dict(close),
                    "right": {"type": "INDICATOR", "indicator": "EMA", "source": dict(close), "params": {"period": slow_p}, "offset": 0},
                },
                "shortExit": {
                    "nodeType": "COMPARISON",
                    "op": "CROSS_ABOVE",
                    "left": dict(close),
                    "right": {"type": "INDICATOR", "indicator": "EMA", "source": dict(close), "params": {"period": slow_p}, "offset": 0},
                },
            }
            strategy["position"] = {"marginMode": "ISOLATED", "leverage": 50, "allocationPct": 50.0, "compound": True, "pyramiding": {"enabled": True, "maxEntries": 3}, "riskManagement": {"stopLossPct": 1.5, "takeProfitPct": 15.0, "trailingStopPct": 2.0, "maxHoldingBars": 150}}
            return strategy

        period = int(tmpl.get("donchian_period", 20))

        def channel(indicator: str, series: str) -> dict[str, Any]:
            return {
                "type": "INDICATOR",
                "indicator": indicator,
                "source": {"type": "SERIES", "series": series, "offset": 0},
                "params": {"period": period},
                "offset": 1,
            }

        def ema_exit(op: str) -> dict[str, Any]:
            return {
                "nodeType": "COMPARISON",
                "op": op,
                "left": dict(close),
                "right": {
                    "type": "INDICATOR",
                    "indicator": "EMA",
                    "source": dict(close),
                    "params": {"period": 10},
                    "offset": 0,
                },
            }

        strategy["signals"] = {
            "longEntry": {
                "nodeType": "COMPARISON",
                "op": "CROSS_ABOVE",
                "left": dict(close),
                "right": channel("HIGHEST", "HIGH"),
            },
            "shortEntry": {
                "nodeType": "COMPARISON",
                "op": "CROSS_BELOW",
                "left": dict(close),
                "right": channel("LOWEST", "LOW"),
            },
            "longExit": ema_exit("CROSS_BELOW"),
            "shortExit": ema_exit("CROSS_ABOVE"),
        }
        return strategy

    def generate_population(
        self,
        population_size: int,
        symbol: str = "ETH-USDT",
        timeframe: str = "1h",
    ) -> list[dict[str, Any]]:
        population: list[dict[str, Any]] = []

        # 1. Add quantitative templates first
        for idx in range(min(len(QUANTITATIVE_TEMPLATES), population_size)):
            population.append(self.create_template_strategy(idx, symbol=symbol, timeframe=timeframe))

        # 2. Fill rest with typed grammar generation
        while len(population) < population_size:
            population.append(self.grammar.generate_strategy(symbol=symbol, timeframe=timeframe))

        return population
