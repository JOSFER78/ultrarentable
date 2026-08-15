"""Directed Repairer for Failed Strategy ASTs."""
from __future__ import annotations

import copy
import random
from typing import Any

from services.api.app.factory.grammar import COMPARISON_OPS, TypedGrammar


class DirectedRepairer:
    """Modifies failed strategy ASTs based on specific failure codes to restore viability."""

    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()
        self.grammar = TypedGrammar(rng=self.rng)

    def repair(self, strategy_dict: dict[str, Any], failure_code: str) -> dict[str, Any]:
        repaired = copy.deepcopy(strategy_dict)
        pos = repaired["position"]
        signals = repaired["signals"]

        if failure_code in ("LIQUIDATED", "NEGATIVE_EQUITY", "INSUFFICIENT_MARGIN"):
            # Lower leverage, switch to ISOLATED margin, reduce allocation
            pos["leverage"] = max(1, pos["leverage"] // 2)
            pos["marginMode"] = "ISOLATED"
            pos["allocationPct"] = min(pos["allocationPct"], 50.0)

        elif failure_code in ("NO_TRADES", "TOO_FEW_TRADES"):
            # Relax entry condition by generating simpler comparison or lowering indicator periods
            signals["longEntry"] = self.grammar.random_comparison_node()
            signals["shortEntry"] = self.grammar.random_comparison_node()

        elif failure_code == "FEES_DOMINATE":
            # Reduce trading frequency by requiring longer indicator periods
            def _scale_periods(node: Any) -> None:
                if isinstance(node, dict):
                    if node.get("type") == "INDICATOR" and "params" in node and "period" in node["params"]:
                        node["params"]["period"] = int(node["params"]["period"] * 1.5)
                    for v in node.values():
                        _scale_periods(v)
                elif isinstance(node, list):
                    for item in node:
                        _scale_periods(item)

            _scale_periods(signals)

        elif failure_code in ("MISSING_SERIES", "MISSING_FUNDING_SERIES"):
            # Replace missing series nodes with CLOSE series
            def _replace_missing_series(node: Any) -> None:
                if isinstance(node, dict):
                    if node.get("type") == "SERIES" and node.get("series") not in ("OPEN", "HIGH", "LOW", "CLOSE", "VOLUME"):
                        node["series"] = "CLOSE"
                    for v in node.values():
                        _replace_missing_series(v)
                elif isinstance(node, list):
                    for item in node:
                        _replace_missing_series(item)

            _replace_missing_series(signals)

        # Update metadata
        parent_name = repaired["metadata"].get("name", "Unknown")
        repaired["metadata"]["origin"] = "MUTATION"
        repaired["metadata"]["parents"] = [parent_name]
        repaired["metadata"]["name"] = f"Rep_{failure_code[:6]}_{parent_name[:12]}"

        return repaired
