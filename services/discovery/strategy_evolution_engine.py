"""Semantic strategy evolution engine.

Turns validated strategy hypotheses into auditable child hypotheses. The engine never
claims profitability: it only proposes deterministic, traceable mutations that must
be evaluated again by the canonical backtest and validation pipeline.
"""

from __future__ import annotations

import hashlib
import json
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
    """Deterministic semantic mutation generator for adaptive research.

    Every parameter emitted by this engine is consumed by the current canonical
    discovery builder. No mutation is allowed to exist merely as UI metadata.
    """

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
        "MOMENTUM_BREAKOUT",
        "TREND_FOLLOWING",
        "RSI_MOMENTUM",
        "MEAN_REVERSION",
    )
    EXIT_FAMILIES: Sequence[str] = (
        "ATR_DYNAMIC",
        "RR_DYNAMIC",
        "TIME_DECAY",
        "TRAILING_PROFIT",
    )

    MUTATION_GROUPS: Sequence[tuple[str, Sequence[str]]] = (
        (
            "ENTRY_DYNAMICS",
            ("RELAX_CONFIRMATION", "TIGHTEN_CONFIRMATION", "SHIFT_FAST_REACTION", "SHIFT_SLOW_ANCHOR"),
        ),
        (
            "STRUCTURAL_REGIME",
            (
                "SWAP_SIGNAL_FAMILY",
                "ADD_VOLATILITY_FILTER",
                "REMOVE_VOLATILITY_FILTER",
                "ADD_VOLUME_CONFIRMATION",
                "ADD_BREAKOUT_CONFIRMATION",
            ),
        ),
        (
            "EXIT_RISK",
            ("CHANGE_EXIT_FAMILY", "WIDEN_STOP", "TIGHTEN_STOP", "WIDEN_TARGET", "TIGHTEN_TARGET"),
        ),
        (
            "SESSION_COMPLEXITY",
            ("CHANGE_SESSION", "REDUCE_COMPLEXITY", "INCREASE_COMPLEXITY"),
        ),
    )

    @staticmethod
    def _deterministic_rank(parent_strategy_id: str, proposal: EvolutionProposal) -> str:
        payload = json.dumps(
            proposal.parameters,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(
            f"{parent_strategy_id}|{proposal.mutation_type}|{payload}".encode("utf-8")
        ).hexdigest()

    def _select_diverse_proposals(
        self,
        proposals: List[EvolutionProposal],
        parent_strategy_id: str,
        limit: int,
    ) -> List[EvolutionProposal]:
        """Select a small child budget without collapsing onto the first mutations.

        The continuous daemon normally asks for only four children. A naïve
        ``proposals[:4]`` would therefore test only confirmation/EMA nudges and
        silently starve structural, regime and exit hypotheses. For limits >= the
        number of semantic groups we guarantee one deterministic representative
        from each group, then fill remaining slots by a hash-ranked exploration.
        """
        limit = max(0, int(limit))
        if limit == 0 or not proposals:
            return []
        if limit >= len(proposals):
            return proposals

        by_type = {proposal.mutation_type: proposal for proposal in proposals}
        selected: List[EvolutionProposal] = []
        selected_ids: set[str] = set()

        group_priority = (
            "STRUCTURAL_REGIME",
            "EXIT_RISK",
            "SESSION_COMPLEXITY",
            "ENTRY_DYNAMICS",
        )
        ranked_groups = {
            name: tuple(mutations)
            for name, mutations in self.MUTATION_GROUPS
        }

        for group_name in group_priority:
            if len(selected) >= limit:
                break
            candidates = [
                by_type[m]
                for m in ranked_groups[group_name]
                if m in by_type
            ]
            if not candidates:
                continue
            chosen = min(candidates, key=lambda p: self._deterministic_rank(parent_strategy_id, p))
            if chosen.mutation_id not in selected_ids:
                selected.append(chosen)
                selected_ids.add(chosen.mutation_id)

        if len(selected) < limit:
            remaining = [p for p in proposals if p.mutation_id not in selected_ids]
            remaining.sort(key=lambda p: self._deterministic_rank(parent_strategy_id, p))
            selected.extend(remaining[: limit - len(selected)])

        return selected

    def propose(
        self,
        parent_strategy_id: str,
        parameters: Dict[str, Any],
        archetype: Optional[str] = None,
        limit: int = 16,
    ) -> List[EvolutionProposal]:
        """Return bounded, reproducible semantic mutations of a parent hypothesis."""
        base = dict(parameters)
        result: List[EvolutionProposal] = []

        def add(mutation_type: str, changes: Dict[str, Any], rationale: str, effect: str) -> None:
            # A mutation that produces no effective parameter change is a wasted
            # trial and must not consume the bounded research budget.
            if not any(base.get(key) != value for key, value in changes.items()):
                return
            next_params = {**base, **changes}
            mutation_id = f"{parent_strategy_id}:{mutation_type}:{len(result)+1:02d}"
            result.append(
                EvolutionProposal(
                    parent_strategy_id,
                    mutation_id,
                    mutation_type,
                    rationale,
                    next_params,
                    effect,
                )
            )

        fast = int(base.get("ema_fast", 20))
        slow = int(base.get("ema_slow", 50))
        sl = float(base.get("sl_atr_mult", 2.0))
        tp = float(base.get("tp_atr_mult", 6.0))
        rsi_long = float(base.get("rsi_threshold_long", 52.0))
        rsi_short = float(base.get("rsi_threshold_short", 48.0))
        current_family = str(base.get("archetype") or archetype or "MOMENTUM_BREAKOUT").upper()
        current_exit = str(base.get("exit_family") or "ATR_DYNAMIC").upper()
        complexity = int(base.get("complexity", 2))

        add(
            "RELAX_CONFIRMATION",
            {
                "rsi_threshold_long": max(50.0, rsi_long - 3.0),
                "rsi_threshold_short": min(50.0, rsi_short + 3.0),
            },
            "Test whether confirmation filters suppress too many valid opportunities.",
            "Increase opportunity while retaining the parent semantic family.",
        )
        add(
            "TIGHTEN_CONFIRMATION",
            {
                "rsi_threshold_long": min(70.0, rsi_long + 3.0),
                "rsi_threshold_short": max(30.0, rsi_short - 3.0),
            },
            "Test whether stronger confirmation improves conditional expectancy.",
            "Trade less frequently with stricter confirmation.",
        )
        add(
            "SHIFT_FAST_REACTION",
            {"ema_fast": max(2, fast - 2)},
            "Test earlier response to regime changes.",
            "Potentially improve timing in fast regimes.",
        )
        add(
            "SHIFT_SLOW_ANCHOR",
            {"ema_slow": max(fast + 2, slow + 10)},
            "Test a slower regime anchor.",
            "Potentially reduce noise at the cost of delay.",
        )

        family_index = self.SIGNAL_FAMILIES.index(current_family) if current_family in self.SIGNAL_FAMILIES else 0
        next_family = self.SIGNAL_FAMILIES[(family_index + 1) % len(self.SIGNAL_FAMILIES)]
        add(
            "SWAP_SIGNAL_FAMILY",
            {"archetype": next_family},
            "Challenge the parent market hypothesis rather than only tuning parameters.",
            f"Explore executable semantic family {next_family}.",
        )

        add(
            "ADD_VOLATILITY_FILTER",
            {"volatility_filter": "ATR_REGIME"},
            "Test whether the strategy benefits from explicit volatility conditioning.",
            "Require ATR(14) to exceed ATR(50) before entry.",
        )
        add(
            "REMOVE_VOLATILITY_FILTER",
            {"volatility_filter": None},
            "Test whether volatility conditioning is overfitting the parent.",
            "Return to a simpler regime-neutral hypothesis.",
        )
        add(
            "ADD_VOLUME_CONFIRMATION",
            {"volume_confirmation": "RELATIVE_VOLUME"},
            "Test whether participation confirmation separates stronger moves.",
            "Require current volume to exceed its 20-period average.",
        )
        add(
            "ADD_BREAKOUT_CONFIRMATION",
            {"breakout_confirmation": True, "breakout_lookback": 20},
            "Test whether structural price breaks improve entry timing.",
            "Add executable Donchian breakout confirmation.",
        )

        exit_index = self.EXIT_FAMILIES.index(current_exit) if current_exit in self.EXIT_FAMILIES else 0
        next_exit = self.EXIT_FAMILIES[(exit_index + 1) % len(self.EXIT_FAMILIES)]
        add(
            "CHANGE_EXIT_FAMILY",
            {"exit_family": next_exit},
            "Test whether the edge is being lost in exits rather than entries.",
            f"Use executable exit family {next_exit}.",
        )

        add(
            "WIDEN_STOP",
            {"sl_atr_mult": sl + 0.5},
            "Test whether normal volatility is causing premature stop-outs.",
            "Allow more room only if the signal remains robust.",
        )
        add(
            "TIGHTEN_STOP",
            {"sl_atr_mult": max(0.5, sl - 0.5)},
            "Test whether the loss tail can be reduced.",
            "Reduce adverse excursion at the cost of sensitivity.",
        )
        add(
            "WIDEN_TARGET",
            {"tp_atr_mult": tp + 1.0},
            "Test whether winners are being cut too early.",
            "Increase payoff asymmetry if trends persist.",
        )
        add(
            "TIGHTEN_TARGET",
            {"tp_atr_mult": max(1.0, tp - 1.0)},
            "Test whether the target is too ambitious.",
            "Increase hit rate if the edge remains after costs.",
        )

        add(
            "CHANGE_SESSION",
            {"session_profile": "LIQUIDITY_CORE"},
            "Test whether the strategy depends on a particular liquid market window.",
            "Apply the explicit liquidity-core session contract.",
        )
        add(
            "REDUCE_COMPLEXITY",
            {
                "complexity": max(1, complexity - 1),
                "volatility_filter": None,
                "volume_confirmation": None,
                "breakout_confirmation": False,
            },
            "Fight overfitting by removing optional filters.",
            "Simplify the executable rule set while preserving the core family.",
        )
        add(
            "INCREASE_COMPLEXITY",
            {
                "complexity": min(5, complexity + 1),
                "volatility_filter": "ATR_REGIME",
            },
            "Test whether one controlled additional filter improves stability rather than IS only.",
            "Add one executable volatility-regime condition.",
        )

        return self._select_diverse_proposals(result, parent_strategy_id, limit)
