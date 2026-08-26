"""Semantic strategy evolution engine.

Turns validated strategy hypotheses into auditable child hypotheses. The engine never
claims profitability: it only proposes deterministic, traceable mutations that must
be evaluated again by the canonical backtest and validation pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Dict, Iterable, List, Optional, Sequence


@dataclass(frozen=True)
class EvolutionProposal:
    parent_strategy_id: str
    mutation_id: str
    mutation_type: str
    rationale: str
    parameters: Dict[str, Any]
    expected_effect: str


class StrategyEvolutionEngine:
    """Deterministic proposal generator for semantic strategy research."""

    MUTATIONS: Sequence[str] = (
        "RELAX_RSI",
        "TIGHTEN_RSI",
        "FAST_EMA_SHIFT",
        "SLOW_EMA_SHIFT",
        "WIDEN_STOP",
        "TIGHTEN_STOP",
        "WIDEN_TARGET",
        "TIGHTEN_TARGET",
        "CHANGE_ARCHETYPE",
    )

    def propose(
        self,
        parent_strategy_id: str,
        parameters: Dict[str, Any],
        archetype: Optional[str] = None,
        limit: int = 9,
    ) -> List[EvolutionProposal]:
        """Return bounded, reproducible semantic mutations of a parent hypothesis."""
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

        add("RELAX_RSI", {"rsi_threshold_long": max(50.0, rsi_long - 3.0), "rsi_threshold_short": min(50.0, rsi_short + 3.0)},
            "Test whether the RSI gate is suppressing too many valid entries.", "Increase trade opportunity while retaining directional context.")
        add("TIGHTEN_RSI", {"rsi_threshold_long": min(70.0, rsi_long + 3.0), "rsi_threshold_short": max(30.0, rsi_short - 3.0)},
            "Test whether stricter momentum confirmation improves quality.", "Trade less frequently with stronger momentum confirmation.")
        add("FAST_EMA_SHIFT", {"ema_fast": max(2, fast - 2)},
            "Test a faster reaction to regime changes.", "Potentially improve timing in short-lived moves.")
        add("SLOW_EMA_SHIFT", {"ema_slow": max(fast + 2, slow + 10)},
            "Test a slower regime anchor.", "Potentially reduce noise at the cost of delayed entries.")
        add("WIDEN_STOP", {"sl_atr_mult": sl + 0.5},
            "Test whether stop-outs are caused by normal volatility noise.", "Reduce premature exits if the signal survives wider excursions.")
        add("TIGHTEN_STOP", {"sl_atr_mult": max(0.5, sl - 0.5)},
            "Test whether tail losses can be reduced without destroying expectancy.", "Reduce loss size at the cost of possible stop sensitivity.")
        add("WIDEN_TARGET", {"tp_atr_mult": tp + 1.0},
            "Test whether winners are being cut too early.", "Increase payoff asymmetry if trends persist.")
        add("TIGHTEN_TARGET", {"tp_atr_mult": max(1.0, tp - 1.0)},
            "Test whether the target is too ambitious for the market/timeframe.", "Increase hit rate if the shorter target improves execution quality.")

        families = ["TREND_FOLLOWING", "RSI_MOMENTUM", "MEAN_REVERSION", "MOMENTUM_BREAKOUT"]
        next_family = next((f for f in families if f != (archetype or "")), "TREND_FOLLOWING")
        add("CHANGE_ARCHETYPE", {"archetype": next_family, "ema_fast": fast, "ema_slow": slow, "rsi_period": rsi},
            "Challenge the parent market hypothesis rather than only optimizing parameters.",
            f"Explore a different semantic family: {next_family}.")

        return result[: max(0, int(limit))]
