"""Adaptive hypothesis engine for ULTRARENTABLE Phase 2.

The purpose is not to replace SQX. SQX is the high-throughput hypothesis factory.
This module learns from the *observed research history* and deterministically
chooses which semantic families, indicator families and exit profiles deserve
more evaluation next. It never changes validation thresholds and never touches
blind OOS data.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Sequence, Tuple


@dataclass(frozen=True)
class FamilyStats:
    family: str
    trials: int
    validation_survivors: int
    mean_validation_score: float
    mean_oos_score: float
    robustness_pass_rate: float

    @property
    def exploitation_value(self) -> float:
        sample_bonus = min(1.0, self.trials / 50.0)
        return self.mean_validation_score * (0.5 + 0.5 * sample_bonus)


@dataclass(frozen=True)
class HypothesisPlan:
    plan_id: str
    family: str
    signal_family: str
    exit_family: str
    complexity_budget: int
    rationale: str


class AdaptiveHypothesisEngine:
    """Evidence-driven deterministic planner for large strategy search spaces."""

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

    def __init__(self, planner_version: str = "adaptive-hypothesis-v1") -> None:
        self.planner_version = planner_version

    @staticmethod
    def _row_score(row: Dict[str, Any]) -> float:
        val = row.get("validation_score")
        if val is not None:
            try:
                return float(val)
            except (TypeError, ValueError):
                pass
        pf = float(row.get("profit_factor_validation", 0.0) or 0.0)
        dd = float(row.get("max_drawdown_validation_pct", 100.0) or 100.0)
        return pf * max(0.0, 1.0 - dd / 100.0)

    def summarize(self, history: Iterable[Dict[str, Any]]) -> Dict[str, FamilyStats]:
        buckets: Dict[str, List[Dict[str, Any]]] = {}
        for row in history:
            family = str(row.get("archetype") or row.get("family") or "UNKNOWN").upper()
            buckets.setdefault(family, []).append(row)

        summary: Dict[str, FamilyStats] = {}
        for family, rows in buckets.items():
            scores = [self._row_score(r) for r in rows]
            survivors = [r for r in rows if str(r.get("status", "")).upper() in {"SURVIVED", "PASSED", "CANDIDATE", "ROBUSTNESS_PASSED"}]
            oos_scores = []
            for r in rows:
                try:
                    pf = float(r.get("profit_factor_oos", 0.0) or 0.0)
                    dd = float(r.get("max_drawdown_oos_pct", r.get("max_drawdown_pct", 100.0)) or 100.0)
                    oos_scores.append(pf * max(0.0, 1.0 - dd / 100.0))
                except (TypeError, ValueError):
                    continue
            robust_pass = sum(1 for r in rows if str(r.get("robustness_status", "")).upper() in {"PASS", "PASSED"})
            summary[family] = FamilyStats(
                family=family,
                trials=len(rows),
                validation_survivors=len(survivors),
                mean_validation_score=sum(scores) / len(scores) if scores else 0.0,
                mean_oos_score=sum(oos_scores) / len(oos_scores) if oos_scores else 0.0,
                robustness_pass_rate=robust_pass / len(rows) if rows else 0.0,
            )
        return summary

    def _rank_family(self, family: str, stats: FamilyStats | None) -> float:
        # Cold-start exploration gets priority when evidence is scarce.
        if stats is None or stats.trials < 8:
            return 0.25 + (8 - (stats.trials if stats else 0)) * 0.05
        return stats.exploitation_value + stats.mean_oos_score * 0.35 + stats.robustness_pass_rate * 0.2

    def plan(self, dataset_sha256: str, history: Iterable[Dict[str, Any]], budget: int = 128) -> List[HypothesisPlan]:
        stats = self.summarize(history)
        candidates: List[Tuple[float, str, str, str, int, str]] = []
        for signal in self.SIGNAL_FAMILIES:
            family_stats = stats.get(signal)
            family_score = self._rank_family(signal, family_stats)
            for exit_family in self.EXIT_FAMILIES:
                combo = f"{signal}|{exit_family}"
                digest = sha256(f"{dataset_sha256}|{self.planner_version}|{combo}".encode()).hexdigest()
                jitter = int(digest[:8], 16) / 0xFFFFFFFF
                score = family_score + jitter * 0.001
                complexity = 2 if signal in {"PRICE_ACTION", "HYBRID_REGIME"} else 1
                rationale = (
                    "Exploit a family with positive observed research value."
                    if family_stats and family_stats.trials >= 8
                    else "Explore an under-sampled semantic family before exploitation."
                )
                candidates.append((score, signal, signal, exit_family, complexity, rationale))

        candidates.sort(key=lambda x: (-x[0], x[1], x[3]))
        selected = candidates[: max(1, int(budget))]
        plans: List[HypothesisPlan] = []
        for idx, (_, family, signal, exit_family, complexity, rationale) in enumerate(selected):
            raw = f"{dataset_sha256}|{self.planner_version}|{family}|{signal}|{exit_family}|{idx}"
            plans.append(
                HypothesisPlan(
                    plan_id=sha256(raw.encode()).hexdigest()[:20],
                    family=family,
                    signal_family=signal,
                    exit_family=exit_family,
                    complexity_budget=complexity,
                    rationale=rationale,
                )
            )
        return plans
