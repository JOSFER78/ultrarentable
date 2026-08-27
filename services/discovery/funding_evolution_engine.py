"""Deterministic evolutionary mutations for the FONDEO route.

FONDEO uses a different executable parameter schema from ULTRA: fixed-point
stops/targets, bounded risk per trade and explicit session/time-stop controls.
This engine never certifies profitability; it only emits hypotheses for the
canonical backtest/validation pipeline.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class FundingEvolutionProposal:
    parent_strategy_id: str
    mutation_id: str
    mutation_type: str
    rationale: str
    parameters: Dict[str, Any]
    expected_effect: str


class FundingEvolutionEngine:
    """Bounded deterministic mutations for executable FONDEO hypotheses."""

    GROUPS = {
        "ENTRY": (
            "RELAX_CONFIRMATION",
            "TIGHTEN_CONFIRMATION",
            "SHIFT_FAST_REACTION",
            "SHIFT_SLOW_ANCHOR",
        ),
        "RISK_EXIT": (
            "WIDEN_STOP",
            "TIGHTEN_STOP",
            "WIDEN_TARGET",
            "TIGHTEN_TARGET",
            "CHANGE_RISK_PER_TRADE",
        ),
        "SESSION": (
            "CHANGE_SESSION",
            "CHANGE_TIME_STOP",
        ),
    }

    SESSION_WINDOWS = {
        "US_CORE": ("13:30", "20:00"),
        "EU_US_OVERLAP": ("12:00", "16:00"),
        "LONDON_CORE": ("07:00", "16:00"),
    }

    def _rank(self, parent_strategy_id: str, proposal: FundingEvolutionProposal) -> str:
        payload = json.dumps(proposal.parameters, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(
            f"{parent_strategy_id}|{proposal.mutation_type}|{payload}".encode("utf-8")
        ).hexdigest()

    def propose(
        self,
        parent_strategy_id: str,
        parameters: Dict[str, Any],
        limit: int = 8,
    ) -> List[FundingEvolutionProposal]:
        base = dict(parameters)
        proposals: List[FundingEvolutionProposal] = []

        def add(mutation_type: str, changes: Dict[str, Any], rationale: str, effect: str) -> None:
            if not any(base.get(k) != v for k, v in changes.items()):
                return
            next_params = {**base, **changes}
            proposals.append(
                FundingEvolutionProposal(
                    parent_strategy_id=parent_strategy_id,
                    mutation_id=f"{parent_strategy_id}:{mutation_type}:{len(proposals)+1:02d}",
                    mutation_type=mutation_type,
                    rationale=rationale,
                    parameters=next_params,
                    expected_effect=effect,
                )
            )

        fast = int(base.get("ema_fast", 9))
        slow = int(base.get("ema_slow", 21))
        rsi_long = float(base.get("rsi_threshold_long", 50.0))
        rsi_short = float(base.get("rsi_threshold_short", 50.0))
        stop = float(base.get("stop_loss_ticks", 15.0))
        target = float(base.get("target_profit_ticks", 45.0))
        risk = float(base.get("risk_per_trade_pct", 0.25))
        session = str(base.get("session_profile", "US_CORE"))
        time_stop = int(base.get("time_stop_bars", 36))
        current_start = str(base.get("session_start_utc", "13:30"))
        current_end = str(base.get("session_end_utc", "20:00"))

        add("RELAX_CONFIRMATION", {
            "rsi_threshold_long": max(50.0, rsi_long - 2.0),
            "rsi_threshold_short": min(50.0, rsi_short + 2.0),
        }, "Test whether confirmation is suppressing valid trades.", "Increase opportunity with a weaker RSI gate.")
        add("TIGHTEN_CONFIRMATION", {
            "rsi_threshold_long": min(65.0, rsi_long + 2.0),
            "rsi_threshold_short": max(35.0, rsi_short - 2.0),
        }, "Test whether stronger confirmation improves expectancy.", "Reduce trade count while demanding stronger momentum.")
        add("SHIFT_FAST_REACTION", {"ema_fast": max(2, fast - 2)},
            "Test earlier reaction to intraday moves.", "Reduce entry lag in fast regimes.")
        add("SHIFT_SLOW_ANCHOR", {"ema_slow": max(fast + 2, slow + 8)},
            "Test a slower directional anchor.", "Reduce noise at the cost of delay.")

        add("WIDEN_STOP", {"stop_loss_ticks": stop + 5.0},
            "Test whether normal volatility is causing stop-outs.", "Allow more room only if validation improves.")
        add("TIGHTEN_STOP", {"stop_loss_ticks": max(5.0, stop - 5.0)},
            "Test whether losses can be shortened.", "Reduce loss size at the cost of sensitivity.")
        add("WIDEN_TARGET", {"target_profit_ticks": target + 15.0},
            "Test whether winners are being cut early.", "Increase payoff asymmetry if the edge persists.")
        add("TIGHTEN_TARGET", {"target_profit_ticks": max(stop + 5.0, target - 15.0)},
            "Test whether the profit target is too ambitious.", "Improve hit rate if conditional expectancy survives costs.")
        add("CHANGE_RISK_PER_TRADE", {
            "risk_per_trade_pct": min(0.50, max(0.10, 0.20 if risk >= 0.25 else 0.30)),
        }, "Separate entry quality from capital-at-risk sensitivity.", "Test bounded lower/higher risk without changing signal logic.")

        session_cycle = {
            "US_CORE": "EU_US_OVERLAP",
            "EU_US_OVERLAP": "LONDON_CORE",
            "LONDON_CORE": "US_CORE",
        }
        next_session = session_cycle.get(session, "US_CORE")
        next_start, next_end = self.SESSION_WINDOWS[next_session]
        add("CHANGE_SESSION", {
            "session_profile": next_session,
            "session_start_utc": next_start,
            "session_end_utc": next_end,
        }, "Test whether the edge is session-dependent.", "Change the executable UTC operating window, not only a label.")

        time_cycle = {24: 36, 36: 48, 48: 24}
        add("CHANGE_TIME_STOP", {"time_stop_bars": time_cycle.get(time_stop, 36)},
            "Test whether stale positions destroy expectancy.", "Alter maximum holding duration while preserving the entry hypothesis.")

        if limit <= 0:
            return []
        if limit >= len(proposals):
            return proposals

        selected: List[FundingEvolutionProposal] = []
        selected_ids = set()
        by_type = {p.mutation_type: p for p in proposals}
        for group_name in ("ENTRY", "RISK_EXIT", "SESSION"):
            if len(selected) >= limit:
                break
            candidates = [by_type[name] for name in self.GROUPS[group_name] if name in by_type]
            if not candidates:
                continue
            chosen = min(candidates, key=lambda p: self._rank(parent_strategy_id, p))
            selected.append(chosen)
            selected_ids.add(chosen.mutation_id)

        remaining = [p for p in proposals if p.mutation_id not in selected_ids]
        remaining.sort(key=lambda p: self._rank(parent_strategy_id, p))
        selected.extend(remaining[: limit - len(selected)])
        return selected
