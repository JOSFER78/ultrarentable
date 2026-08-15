from __future__ import annotations

import math
import os
from dataclasses import asdict, dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class CampaignPlan:
    workers: int
    population: int
    generations: int
    optimizer_trials: int
    elite_count: int
    stagnation_patience: int
    leverage_tiers: tuple[int, ...]
    evaluation_budget: int
    mode: str = "ultra"

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["leverage_tiers"] = list(self.leverage_tiers)
        return result


class AutomaticCampaignPlanner:
    """Derive a bounded search campaign from the verified market and machine.

    No trading knob is requested from the user. The budget grows with available
    independent market information, but remains bounded so a single HTTP request
    cannot accidentally create an unending campaign.
    """

    def plan(
        self,
        opportunity: Mapping[str, Any],
        *,
        max_leverage: int,
        cpu_count: int | None = None,
        mode: str = "ultra",
    ) -> CampaignPlan:
        interval = str(opportunity["interval"])
        timeframe_minutes = {"1m": 1, "5m": 5, "15m": 15, "1h": 60}[interval]
        history_days = max(1.0, float(opportunity["history_days"]))
        record_count = max(1, int(opportunity.get("record_count", 1)))
        cores = max(1, int(cpu_count or os.cpu_count() or 1))
        workers = min(4, cores)

        information_scale = math.log2(1.0 + record_count / max(1.0, 1440 / timeframe_minutes))
        population = max(8, min(48, int(round(6 + 2.5 * information_scale))))
        generations = max(3, min(14, int(round(2 + math.sqrt(history_days) / 2))))
        optimizer_trials = max(6, min(40, int(round(population * 0.6))))
        elite_count = max(2, int(math.ceil(population * 0.15)))
        stagnation_patience = max(2, min(5, generations // 3))
        leverage_cap = min(500, max(1, int(max_leverage)))
        # Every integer leverage is part of the search domain. The optimizer may
        # therefore explore arbitrary values such as 3x, 11x, 32x or 311x.
        tiers = tuple(range(1, leverage_cap + 1))
        evaluation_budget = population * generations + optimizer_trials * elite_count
        return CampaignPlan(
            workers=workers,
            population=population,
            generations=generations,
            optimizer_trials=optimizer_trials,
            elite_count=elite_count,
            stagnation_patience=stagnation_patience,
            leverage_tiers=tiers or (1,),
            evaluation_budget=evaluation_budget,
            mode=str(mode).lower(),
        )
