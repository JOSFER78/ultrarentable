"""Typed Grammar Generator for DSL v1.0.0 AST Trees."""
from __future__ import annotations

import random
from typing import Any


INDICATORS = ["SMA", "EMA", "RSI", "ATR", "HIGHEST", "LOWEST", "ROC", "STDDEV", "VOLUME_RATIO"]
SERIES = ["OPEN", "HIGH", "LOW", "CLOSE", "VOLUME"]
PRICE_SERIES = ["OPEN", "HIGH", "LOW", "CLOSE"]
PRICE_INDICATORS = ["SMA", "EMA", "HIGHEST", "LOWEST"]
PRICE_DELTA_INDICATORS = ["ATR", "STDDEV"]
VOLUME_INDICATORS = ["SMA", "EMA", "HIGHEST", "LOWEST"]
COMPARISON_OPS = ["GT", "GTE", "LT", "LTE", "CROSS_ABOVE", "CROSS_BELOW"]
LOGIC_OPS = ["ALL", "ANY"]
FAMILIES = ["breakout", "mean_reversion", "trend_following", "momentum", "volatility", "statistical_arbitrage"]


class TypedGrammar:
    """Generates structurally valid DSL v1.0.0 strategy dicts by construction."""

    def __init__(self, rng: random.Random | None = None, available_series: list[str] | None = None):
        self.rng = rng or random.Random()
        self.series = available_series or SERIES

    def random_series_node(self, series: list[str] | None = None) -> dict[str, Any]:
        choices = series or self.series
        return {
            "type": "SERIES",
            "series": self.rng.choice(choices),
            "offset": self.rng.choice([0, 0, 0, 1, 2]),
        }

    def random_constant_node(self, values: list[float] | None = None) -> dict[str, Any]:
        choices = values or [10, 20, 30, 50, 70, 80, 100, 200, 0.5, 1.5, 2.0]
        return {"type": "CONSTANT", "value": float(self.rng.choice(choices))}

    def random_indicator_node(
        self,
        indicators: list[str],
        source_series: list[str],
    ) -> dict[str, Any]:
        return {
            "type": "INDICATOR",
            "indicator": self.rng.choice(indicators),
            "source": self.random_series_node(source_series),
            "params": {"period": self.rng.choice([5, 10, 14, 20, 50, 100, 200])},
            "offset": 0,
        }

    def random_value_node(self, max_depth: int = 2) -> dict[str, Any]:
        # Kept for callers that need a single value; price is the safest default.
        if max_depth <= 0 or self.rng.random() < 0.4:
            return self.random_series_node(PRICE_SERIES)
        return self.random_indicator_node(PRICE_INDICATORS, PRICE_SERIES)

    def random_comparison_node(self) -> dict[str, Any]:
        kind = self.rng.choice([
            "price_series_indicator",
            "price_indicators",
            "price_deltas",
            "rsi_threshold",
            "roc_threshold",
            "volume_series_indicator",
            "volume_delta_threshold",
            "volume_ratio_threshold",
        ])
        if kind == "price_series_indicator":
            left = self.random_series_node(PRICE_SERIES)
            right = self.random_indicator_node(PRICE_INDICATORS, PRICE_SERIES)
        elif kind == "price_indicators":
            left = self.random_indicator_node(PRICE_INDICATORS, PRICE_SERIES)
            right = self.random_indicator_node(PRICE_INDICATORS, PRICE_SERIES)
        elif kind == "price_deltas":
            left = self.random_indicator_node(PRICE_DELTA_INDICATORS, PRICE_SERIES)
            right = self.random_indicator_node(PRICE_DELTA_INDICATORS, PRICE_SERIES)
        elif kind == "rsi_threshold":
            left = self.random_indicator_node(["RSI"], PRICE_SERIES)
            right = self.random_constant_node([20, 30, 40, 50, 60, 70, 80])
        elif kind == "roc_threshold":
            left = self.random_indicator_node(["ROC"], PRICE_SERIES)
            right = self.random_constant_node([-10, -5, -2, -1, 0, 1, 2, 5, 10])
        elif kind == "volume_series_indicator":
            left = self.random_series_node(["VOLUME"])
            right = self.random_indicator_node(VOLUME_INDICATORS, ["VOLUME"])
        elif kind == "volume_delta_threshold":
            left = self.random_indicator_node(["STDDEV"], ["VOLUME"])
            right = self.random_constant_node([10, 50, 100, 500, 1_000])
        else:
            left = self.random_indicator_node(["VOLUME_RATIO"], ["VOLUME"])
            right = self.random_constant_node([0.5, 0.8, 1.0, 1.2, 1.5, 2.0])
        if left == right:
            # Preserve units while ensuring the predicate is not self-comparison.
            right["offset"] = (int(right.get("offset", 0)) + 1) % 3
        return {
            "nodeType": "COMPARISON",
            "op": self.rng.choice(COMPARISON_OPS),
            "left": left,
            "right": right,
        }

    def random_signal_node(self, depth: int = 1) -> dict[str, Any]:
        if depth <= 0 or self.rng.random() < 0.7:
            return self.random_comparison_node()
        op = self.rng.choice(LOGIC_OPS)
        n_children = self.rng.randint(2, 3)
        return {
            "nodeType": "LOGIC",
            "op": op,
            "children": [self.random_comparison_node() for _ in range(n_children)],
        }

    def generate_strategy(
        self,
        *,
        name: str | None = None,
        symbol: str = "ETH-USDT",
        timeframe: str = "1h",
        family: str | None = None,
        leverage: int | None = None,
        max_leverage: int = 20,
    ) -> dict[str, Any]:
        fam = family or self.rng.choice(FAMILIES)
        strat_name = name or f"Auto_{fam.capitalize()}_{self.rng.randint(1000, 9999)}"
        leverage_cap = min(500, max(1, int(max_leverage)))
        lev = int(leverage) if leverage is not None else self.rng.randint(1, leverage_cap)
        if not 1 <= lev <= leverage_cap:
            raise ValueError(f"leverage must be between 1 and {leverage_cap}")

        return {
            "dslVersion": "1.0.0",
            "metadata": {
                "name": strat_name,
                "family": fam,
                "parents": [],
                "origin": "MUTATION",
            },
            "market": {
                "venue": "BINGX",
                "symbol": symbol,
                "timeframe": timeframe,
            },
            "signals": {
                "longEntry": self.random_signal_node(),
                "shortEntry": self.random_signal_node(),
                "longExit": self.random_signal_node(),
                "shortExit": self.random_signal_node(),
            },
            "position": {
                # CROSS stays out of the executable search domain until the
                # portfolio-wide margin model is implemented and verified.
                "marginMode": "ISOLATED",
                "leverage": lev,
                "allocationPct": float(self.rng.choice([25.0, 50.0, 100.0])),
                "compound": self.rng.choice([True, False]),
                "pyramiding": {"enabled": False, "maxEntries": 1},
                "riskManagement": {
                    "stopLossPct": float(self.rng.choice([0.5, 1.0, 1.5, 2.0, 3.0, 5.0])),
                    "takeProfitPct": float(self.rng.choice([1.0, 2.0, 3.0, 5.0, 8.0, 12.0])),
                    "trailingStopPct": self.rng.choice([None, 0.5, 1.0, 1.5, 2.0, 3.0]),
                    "maxHoldingBars": self.rng.choice([12, 24, 48, 96, 200, 400]),
                },
            },
            "execution": {
                # LIMIT orders require an explicit price/fill model, which DSL
                # v1 does not yet provide. Generated strategies therefore use
                # executable market orders only.
                "entryOrderType": "MARKET",
                "exitOrderType": "MARKET",
                "signalTiming": "BAR_CLOSE_EXECUTE_NEXT_OPEN",
            },
        }
