"""Genetic Operators for Strategy Evolution (Mutations & Crossovers)."""
from __future__ import annotations

import copy
import random
from typing import Any

from services.api.app.factory.grammar import COMPARISON_OPS, TypedGrammar


class GeneticOperators:
    """Genetic mutation and crossover operations for DSL v1.0.0 strategies."""

    def __init__(self, rng: random.Random | None = None, max_leverage: int = 20):
        self.rng = rng or random.Random()
        self.max_leverage = min(500, max(1, int(max_leverage)))
        self.grammar = TypedGrammar(rng=self.rng)

    def mutate(self, strategy_dict: dict[str, Any]) -> dict[str, Any]:
        """Apply random structural or numeric mutation to strategy."""
        mutated = copy.deepcopy(strategy_dict)
        mut_type = self.rng.choice(["mutate_operator", "mutate_period", "mutate_constant", "mutate_subtree", "mutate_position", "mutate_risk"])

        if mut_type == "mutate_operator":
            sig_name = self.rng.choice(["longEntry", "shortEntry", "longExit", "shortExit"])
            node = mutated["signals"][sig_name]
            if node.get("nodeType") == "COMPARISON":
                node["op"] = self.rng.choice(COMPARISON_OPS)

        elif mut_type == "mutate_period":
            # Walk AST and mutate any indicator period
            def _mutate_period_walk(node: Any) -> None:
                if isinstance(node, dict):
                    if node.get("type") == "INDICATOR" and "params" in node and "period" in node["params"]:
                        curr = node["params"]["period"]
                        delta = self.rng.choice([-10, -5, -2, -1, 1, 2, 5, 10])
                        node["params"]["period"] = max(2, curr + delta)
                    for v in node.values():
                        _mutate_period_walk(v)
                elif isinstance(node, list):
                    for item in node:
                        _mutate_period_walk(item)

            sig_name = self.rng.choice(["longEntry", "shortEntry", "longExit", "shortExit"])
            _mutate_period_walk(mutated["signals"][sig_name])

        elif mut_type == "mutate_constant":
            sig_name = self.rng.choice(["longEntry", "shortEntry", "longExit", "shortExit"])

            def _mutate_constant_walk(node: Any) -> None:
                if isinstance(node, dict):
                    if node.get("type") == "CONSTANT" and "value" in node:
                        current = float(node["value"])
                        if current == 0.0:
                            node["value"] = float(self.rng.choice([-2.0, -1.0, 1.0, 2.0]))
                        else:
                            node["value"] = round(
                                current * self.rng.choice([0.75, 0.9, 1.1, 1.25]),
                                6,
                            )
                    for value in node.values():
                        _mutate_constant_walk(value)
                elif isinstance(node, list):
                    for item in node:
                        _mutate_constant_walk(item)

            _mutate_constant_walk(mutated["signals"][sig_name])

        elif mut_type == "mutate_subtree":
            sig_name = self.rng.choice(["longEntry", "shortEntry", "longExit", "shortExit"])
            mutated["signals"][sig_name] = self.grammar.random_signal_node()

        elif mut_type == "mutate_position":
            pos = mutated["position"]
            pos["leverage"] = self.rng.randint(1, self.max_leverage)
            pos["allocationPct"] = float(self.rng.choice([10.0, 25.0, 50.0, 100.0]))

        elif mut_type == "mutate_risk":
            risk = mutated["position"].setdefault("riskManagement", {})
            risk["stopLossPct"] = float(self.rng.choice([0.5, 1.0, 1.5, 2.0, 3.0, 5.0]))
            risk["takeProfitPct"] = float(self.rng.choice([1.0, 2.0, 3.0, 5.0, 8.0, 12.0]))
            risk["trailingStopPct"] = self.rng.choice([None, 0.5, 1.0, 1.5, 2.0, 3.0])
            risk["maxHoldingBars"] = self.rng.choice([12, 24, 48, 96, 200, 400])

        # Numeric mutations can make two formerly distinct indicator nodes
        # identical (for example EMA 20 versus EMA 20). Repair that predicate
        # with a fresh dimensionally typed comparison.
        def _repair_degenerate(node: Any) -> dict[str, Any]:
            if not isinstance(node, dict):
                return node
            if (
                node.get("nodeType") == "COMPARISON"
                and node.get("left") == node.get("right")
            ):
                return self.grammar.random_comparison_node()
            if node.get("nodeType") == "LOGIC":
                node["children"] = [
                    _repair_degenerate(child)
                    for child in node.get("children", [])
                ]
            elif node.get("nodeType") == "NOT" and isinstance(node.get("child"), dict):
                node["child"] = _repair_degenerate(node["child"])
            return node

        for signal_name, signal in mutated["signals"].items():
            mutated["signals"][signal_name] = _repair_degenerate(signal)

        # Update metadata
        parent_name = mutated["metadata"].get("name", "Unknown")
        mutated["metadata"]["origin"] = "MUTATION"
        mutated["metadata"]["parents"] = [parent_name]
        mutated["metadata"]["name"] = f"Mut_{parent_name[:16]}_{self.rng.randint(100, 999)}"

        return mutated

    def crossover(self, parent_a: dict[str, Any], parent_b: dict[str, Any]) -> dict[str, Any]:
        """Crossover entry/exit signals from two parent strategies."""
        child = copy.deepcopy(parent_a)

        # Swap exit signals from parent B
        child["signals"]["longExit"] = copy.deepcopy(parent_b["signals"]["longExit"])
        child["signals"]["shortExit"] = copy.deepcopy(parent_b["signals"]["shortExit"])

        name_a = parent_a["metadata"].get("name", "A")
        name_b = parent_b["metadata"].get("name", "B")
        child["metadata"]["origin"] = "CROSSOVER"
        child["metadata"]["parents"] = [name_a, name_b]
        child["metadata"]["name"] = f"Cross_{name_a[:8]}_{name_b[:8]}_{self.rng.randint(100, 999)}"

        return child
