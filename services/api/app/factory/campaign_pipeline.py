from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from services.api.app.factory.adversarial_validation import (
    AdversarialValidator,
    ScenarioResult,
    ValidationDecision,
    ValidationScenario,
)
from services.api.app.factory.campaign_planner import AutomaticCampaignPlanner, CampaignPlan
from services.api.app.factory.optimization_loop import (
    AggressiveOptimizationLoop,
    CandidateResult,
    LoopResult,
)


@dataclass(frozen=True)
class CampaignOutcome:
    status: str
    plan: CampaignPlan
    search: LoopResult
    validation: ValidationDecision | None
    deployable_strategy: dict[str, Any] | None


class AutonomousStrategyCampaign:
    """One automatic route: plan -> evolve -> adversarially validate.

    The concrete application injects FastEngine-backed callbacks. This module
    owns promotion rules, ensuring no stage can bypass evidence or lockbox gates.
    """

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self.planner = AutomaticCampaignPlanner()
        self.validator = AdversarialValidator(seed=seed)

    def run(
        self,
        *,
        opportunity: Mapping[str, Any],
        max_leverage: int,
        initial_population: Sequence[dict[str, Any]],
        evaluate_candidate: Callable[[dict[str, Any], int], CandidateResult],
        mutate: Callable,
        fresh: Callable,
        evaluate_scenario: Callable[[Mapping[str, Any], ValidationScenario], ScenarioResult],
        cpu_count: int | None = None,
    ) -> CampaignOutcome:
        plan = self.planner.plan(opportunity, max_leverage=max_leverage, cpu_count=cpu_count)
        search = AggressiveOptimizationLoop(seed=self.seed).run(
            initial_population=initial_population,
            evaluate=evaluate_candidate,
            mutate=mutate,
            fresh=fresh,
            population_size=plan.population,
            generations=plan.generations,
            elite_count=plan.elite_count,
            stagnation_patience=plan.stagnation_patience,
        )
        if search.champion is None:
            return CampaignOutcome("NO_VALID_CANDIDATE", plan, search, None, None)
        validation = self.validator.validate(search.champion.strategy, evaluate_scenario)
        if not validation.passed:
            return CampaignOutcome("FAILED_ADVERSARIAL_VALIDATION", plan, search, validation, None)
        return CampaignOutcome(
            "VALIDATED_CANDIDATE",
            plan,
            search,
            validation,
            dict(search.champion.strategy),
        )
