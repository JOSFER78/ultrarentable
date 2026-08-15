from __future__ import annotations

import random
from dataclasses import dataclass
from statistics import median
from typing import Any, Callable, Mapping, Sequence

from services.api.app.factory.quality_gates import drawdown_acceptable, drawdown_sustainable


@dataclass(frozen=True)
class ValidationScenario:
    name: str
    start_fraction: float
    end_fraction: float
    fee_multiplier: float
    slippage_multiplier: float
    locked: bool = False


@dataclass(frozen=True)
class ScenarioResult:
    scenario: ValidationScenario
    return_pct: float
    max_drawdown_pct: float
    bankrupt: bool
    rankable: bool


@dataclass(frozen=True)
class ValidationDecision:
    passed: bool
    score: float
    reasons: tuple[str, ...]
    results: tuple[ScenarioResult, ...]


class AdversarialValidator:
    """Create temporal, random, cost-stress and untouched lockbox checks."""

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed

    def scenarios(self, random_windows: int = 4) -> tuple[ValidationScenario, ...]:
        rng = random.Random(self.seed)
        scenarios = [
            ValidationScenario("walk-forward-1", 0.00, 0.25, 1.0, 1.0),
            ValidationScenario("walk-forward-2", 0.25, 0.50, 1.0, 1.0),
            ValidationScenario("walk-forward-3", 0.50, 0.75, 1.0, 1.0),
            ValidationScenario("cost-stress", 0.10, 0.80, 1.75, 2.0),
        ]
        for index in range(random_windows):
            start = rng.uniform(0.0, 0.62)
            scenarios.append(ValidationScenario(f"random-{index + 1}", start, start + 0.20, 1.25, 1.5))
        scenarios.append(ValidationScenario("lockbox", 0.80, 1.00, 1.0, 1.0, True))
        return tuple(scenarios)

    def validate(
        self,
        strategy: Mapping[str, Any],
        evaluate: Callable[[Mapping[str, Any], ValidationScenario], ScenarioResult],
        mode: str = "ultra",
    ) -> ValidationDecision:
        results = tuple(evaluate(strategy, scenario) for scenario in self.scenarios())
        reasons: list[str] = []
        if any(result.bankrupt for result in results):
            reasons.append("BANKRUPTCY_IN_ADVERSARIAL_SCENARIO")
        # In ULTRA mode only real ruin (drawdown >= 100%) invalidates a candidate.
        # In FONDEO mode unsustainable drawdown also invalidates.
        if not all(drawdown_sustainable(result.max_drawdown_pct, mode=mode) for result in results):
            reasons.append("RUINOUS_DRAWDOWN_IN_ADVERSARIAL_WINDOW")
        rankable_ratio = sum(result.rankable for result in results) / len(results)
        profitable_ratio = sum(result.return_pct > 0 for result in results) / len(results)
        lockbox = next(result for result in results if result.scenario.locked)
        returns = [result.return_pct for result in results]
        positive_total = sum(max(0.0, value) for value in returns)
        concentration = max((max(0.0, value) for value in returns), default=0.0) / positive_total if positive_total else 1.0
        if rankable_ratio < 0.60:
            reasons.append("INSUFFICIENT_EVIDENCE_ACROSS_WINDOWS")
        if profitable_ratio < 0.55:
            reasons.append("RETURNS_DO_NOT_SURVIVE_REGIME_CHANGES")
        if not lockbox.rankable or lockbox.return_pct <= 0:
            reasons.append("UNTOUCHED_LOCKBOX_FAILED")
        if concentration > 0.70:
            reasons.append("RESULT_CONCENTRATED_IN_ONE_WINDOW")
        score = max(0.0, min(1.0, 0.35 * rankable_ratio + 0.35 * profitable_ratio + 0.20 * (lockbox.return_pct > 0) + 0.10 * (median(returns) > 0)))
        return ValidationDecision(not reasons, round(score, 8), tuple(reasons), results)
