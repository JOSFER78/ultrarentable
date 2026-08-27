"""Semantic strategy evolution engine.

Turns validated strategy hypotheses into auditable child hypotheses. The engine never
claims profitability: it only proposes deterministic, traceable mutations that must
be evaluated again by the canonical backtest and validation pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence


@dataclass(frozen=True)
class EvolutionProposal:
    parent_strategy_id: str
    mutation_id: str
    mutation_type: str
    rationale: str
    parameters: Dict[str, Any]
    expected_effect: str


class StrategyEvolutionEngine:
    """Deterministic semantic mutation generator for adaptive research."""

    MUTATIONS: Sequence[str] = (
        "RELAX_CONFIRMATION",
        "TIGHTEN_CONFIRMATION",
        "SHIFT_FAST_REACTION",
        "SHIFT_SLOW_ANCHOR",
        "SWAP_SIGNAL_FAMILY",
        "ADD_VOLATILITY_FILTER",
        "REMOVE_VOLATILITY_FILTER",
        "ADD_VOLUME_CONFIRMATION",
        "ADD_BREAKOUT_CONFIRMATION",
        "CHANGE_EXIT_FAMILY",
        "WIDEN_STOP",
        "TIGHTEN_STOP",
        "WIDEN_TARGET",
        "TIGHTEN_TARGET",
        "CHANGE_SESSION",
        "REDUCE_COMPLEXITY",
        "INCREASE_COMPLEXITY",
    )

    SIGNAL_FAMILIES: Sequence[str] = (
        "TREND",
        "MOMENTUM",
        "MEAN_REVERSION",
        "BREAKOUT",
        "VOLATILITY_EXPANSION",
        "VOLATILITY_COMPRESSION",
        "VOLUME_FLOW",
        "PRICE_ACTION",
        "HYBRID_REGIME",
    )
    EXIT_FAMILIES: Sequence[str] = (
        "ATR_DYNAMIC",
        "RR_DYNAMIC",
        "VOLATILITY_ADAPTIVE",
        "TIME_DECAY",
        "STRUCTURE_EXIT",
        "TRAILING_PROFIT",
    )

    def propose(
        self,
        parent_strategy_id: str,
        parameters: Dict[str, Any],
        archetype: Optional[str] = None,
        limit: int = 16,
    ) -> List[EvolutionProposal]:
        """Return bounded, reproducible semantic mutations of a parent hypothesis.

        Every semantic key added here must be consumed by a downstream SQX/export
        compiler before it can reach a canonical backtest. We intentionally do not
        pretend that an ignored parameter changes a strategy.
        """
        base = dict(parameters)
        result: List[EvolutionProposal] = []

        def add(mutation_type: str, changes: Dict[str, Any], rationale: str, effect: str) -> None:
            if len(result) >= limit:
                return
            next_params = {**base, **changes}
            mutation_id = f"{parent_strategy_id}:{mutation_type}:{len(result)+1:02d}"
            result.append(EvolutionProposal(parent_strategy_id, mutation_id, mutation_type, rationale, next_params, effect))

        fast = int(base.get("ema_fast", 20))
        slow = int(base.get("ema_slow", 50))
        sl = float(base.get("sl_atr_mult", 2.0))
        tp = float(base.get("tp_atr_mult", 6.0))
        rsi = int(base.get("rsi_period", 14))
        rsi_long = float(base.get("rsi_threshold_long", 52.0))
        rsi_short = float(base.get("rsi_threshold_short", 48.0))
        signal_family = str(base.get("signal_family") or archetype or "TREND").upper()
        exit_family = str(base.get("exit_family") or "ATR_DYNAMIC").upper()
        complexity = int(base.get("complexity", 2))

        add("RELAX_CONFIRMATION", {"rsi_threshold_long": max(50.0, rsi_long - 3.0), "rsi_threshold_short": min(50.0, rsi_short + 3.0)},
            "Test whether confirmation filters suppress too many valid opportunities.", "Increase opportunity while retaining the parent semantic family.")
        add("TIGHTEN_CONFIRMATION", {"rsi_threshold_long": min(70.0, rsi_long + 3.0), "rsi_threshold_short": max(30.0, rsi_short - 3.0)},
            "Test whether stronger confirmation improves conditional expectancy.", "Trade less frequently with stricter confirmation.")
        add("SHIFT_FAST_REACTION", {"ema_fast": max(2, fast - 2)},
            "Test earlier response to regime changes.", "Potentially improve timing in fast regimes.")
        add("SHIFT_SLOW_ANCHOR", {"ema_slow": max(fast + 2, slow + 10)},
            "Test a slower regime anchor.", "Potentially reduce noise at the cost of delay.")

        family_index = self.SIGNAL_FAMILIES.index(signal_family) if signal_family in self.SIGNAL_FAMILIES else 0
        next_family = self.SIGNAL_FAMILIES[(family_index + 1) % len(self.SIGNAL_FAMILIES)]
        add("SWAP_SIGNAL_FAMILY", {"signal_family": next_family, "archetype": next_family},
            "Challenge the parent market hypothesis instead of only tuning parameters.", f"Explore semantic family {next_family}.")

        add("ADD_VOLATILITY_FILTER", {"volatility_filter": "ATR_REGIME", "volatility_percentile_min": 40.0},
            "Test whether the strategy benefits from explicitly conditioning on volatility.", "Avoid low-information regimes or focus on expansion depending on family.")
        add("REMOVE_VOLATILITY_FILTER", {"volatility_filter": None},
            "Test whether volatility conditioning is overfitting the parent.", "Return to a simpler regime-neutral hypothesis.")
        add("ADD_VOLUME_CONFIRMATION", {"volume_confirmation": "RELATIVE_VOLUME", "relative_volume_min": 1.2},
            "Test whether participation confirmation separates stronger moves.", "Require materially higher activity before entry.")
        add("ADD_BREAKOUT_CONFIRMATION", {"breakout_confirmation": True, "breakout_lookback": 20},
            "Test whether structural price breaks improve entry timing.", "Add a causal price-structure gate rather than another oscillator.")

        next_exit_index = (self.EXIT_FAMILIES.index(exit_family) + 1) % len(self.EXIT_FAMILIES) if exit_family in self.EXIT_FAMILIES else 0
        next_exit = self.EXIT_FAMILIES[next_exit_index]
        add("CHANGE_EXIT_FAMILY", {"exit_family": next_exit},
            "Test whether the edge is being lost in exits rather than entries.", f"Use exit family {next_exit}.")

        add("WIDEN_STOP", {"sl_atr_mult": sl + 0.5},
            "Test whether normal volatility is causing premature stop-outs.", "Allow more room only if the signal remains robust.")
        add("TIGHTEN_STOP", {"sl_atr_mult": max(0.5, sl - 0.5)},
            "Test whether the loss tail can be reduced.", "Reduce adverse excursion at the cost of sensitivity.")
        add("WIDEN_TARGET", {"tp_atr_mult": tp + 1.0},
            "Test whether winners are being cut too early.", "Increase payoff asymmetry if trends persist.")
        add("TIGHTEN_TARGET", {"tp_atr_mult": max(1.0, tp - 1.0)},
            "Test whether the target is too ambitious.", "Increase hit rate if the edge remains after costs.")

        add("CHANGE_SESSION", {"session_profile": "LIQUIDITY_CORE"},
            "Test whether the strategy depends on a particular market session.", "Restrict discovery to a liquid market window; the exact hours must be supplied by the dataset/exchange contract.")
        add("REDUCE_COMPLEXITY", {"complexity": max(1, complexity - 1), "optional_filters": []},
            "Fight overfitting by simplifying the rule set.", "Remove one layer of optional conditions.")
        add("INCREASE_COMPLEXITY", {"complexity": min(5, complexity + 1), "optional_filters": ["ONE_ADDITIONAL_FILTER"]},
            "Test whether a controlled extra condition improves stability rather than IS only.", "Permit exactly one additional semantic filter.")

        return result[: max(0, int(limit))]
