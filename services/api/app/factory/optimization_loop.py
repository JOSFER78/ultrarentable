from __future__ import annotations

import hashlib
import json
import random
import time
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping, Sequence

from services.api.app.factory.quality_gates import (
    drawdown_penalty_factor,
    is_ruinous,
    risk_adjusted_fitness,
)


@dataclass(frozen=True)
class CandidateResult:
    strategy: dict[str, Any]
    final_equity: float
    evidence_score: float
    rankable: bool
    bankrupt: bool = False
    validation_score: float = 0.0
    evidence: dict[str, Any] | None = None
    max_drawdown_pct: float | None = None
    net_return_pct: float = 0.0
    mode: str = "ultra"

    @property
    def fitness(self) -> float:
        if self.bankrupt or not self.rankable:
            return float("-inf")
        # Hard ruin gate during the SEARCH itself: a strategy that destroyed the
        # account (drawdown >= 100%) is never allowed to climb the leaderboard,
        # no matter how high the equity curve momentarily reached. This applies
        # in BOTH modes: real ruin is unconditionally invalid.
        if is_ruinous(self.max_drawdown_pct or 0.0):
            return float("-inf")
        growth = max(0.0, self.final_equity)
        # In ULTRA mode we do not penalise drawdown at all: the kamikaze search
        # explicitly tolerates aggressive-but-solvent drawdown. In FONDEO mode
        # the risk and penalty terms apply.
        risk = risk_adjusted_fitness(self.net_return_pct, self.max_drawdown_pct, mode=self.mode)
        penalty = drawdown_penalty_factor(self.max_drawdown_pct, mode=self.mode)
        return growth * (0.35 + 0.30 * self.evidence_score + 0.15 * self.validation_score + 0.20 * risk) * penalty

    @property
    def breeding_fitness(self) -> float:
        """Selection score; never grants promotion to an unrankable candidate."""
        if self.bankrupt or self.final_equity <= 0.0:
            return float("-inf")
        if is_ruinous(self.max_drawdown_pct or 0.0):
            return float("-inf")
        evidence = max(0.0, min(1.0, self.evidence_score))
        penalty = drawdown_penalty_factor(self.max_drawdown_pct, mode=self.mode)
        risk = risk_adjusted_fitness(self.net_return_pct, self.max_drawdown_pct, mode=self.mode)
        # Even a losing but solvent candidate provides a gradient toward break-even.
        score = self.final_equity + 5_000.0 * evidence + 5_000.0 * risk
        if self.rankable:
            score += 10_000.0
        return score * penalty


@dataclass(frozen=True)
class LoopResult:
    champion: CandidateResult | None
    generations_run: int
    evaluations: int
    stopped_for_stagnation: bool
    archive: tuple[CandidateResult, ...]
    best_attempts: tuple[CandidateResult, ...]
    control_status: str | None = None


class AggressiveOptimizationLoop:
    """Generic, deterministic evolution loop that can wrap the real FastEngine.

    Only evidence-rankable, non-bankrupt candidates enter the elite archive.
    Diversity is protected by canonical strategy hashes; stagnating lineages are
    replaced with fresh seeds instead of endlessly tuning one local optimum.
    """

    def __init__(self, seed: int = 42) -> None:
        self.rng = random.Random(seed)

    @staticmethod
    def _key(strategy: Mapping[str, Any]) -> str:
        payload = json.dumps(strategy, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def run(
        self,
        *,
        initial_population: Sequence[dict[str, Any]],
        evaluate: Callable[[dict[str, Any], int], CandidateResult],
        mutate: Callable[[dict[str, Any], random.Random], dict[str, Any]],
        fresh: Callable[[random.Random], dict[str, Any]],
        population_size: int,
        generations: int,
        elite_count: int,
        stagnation_patience: int,
        control_state: Callable[[], str] | None = None,
        crossover: Callable[
            [dict[str, Any], dict[str, Any], random.Random],
            dict[str, Any],
        ] | None = None,
    ) -> LoopResult:
        population = [dict(item) for item in initial_population[:population_size]]
        while len(population) < population_size:
            population.append(fresh(self.rng))
        archive: dict[str, CandidateResult] = {}
        breeding_archive: dict[str, CandidateResult] = {}
        evaluations = 0
        best_fitness = float("-inf")
        stale = 0
        stopped = False

        def control_gate() -> str:
            if control_state is None:
                return "RUNNING"
            while True:
                state = str(control_state() or "RUNNING").upper()
                if state != "PAUSED":
                    return state
                time.sleep(1.0)

        for generation in range(generations):
            state = control_gate()
            if state in {"STOPPED", "CANCELLED"}:
                return self._finish(
                    archive.values(),
                    breeding_archive.values(),
                    generation,
                    evaluations,
                    False,
                    state,
                )
            breeding_pool: list[CandidateResult] = []
            for strategy in population:
                state = control_gate()
                if state in {"STOPPED", "CANCELLED"}:
                    return self._finish(
                        archive.values(),
                        breeding_archive.values(),
                        generation,
                        evaluations,
                        False,
                        state,
                    )
                result = evaluate(strategy, evaluations + 1)
                evaluations += 1
                if not result.bankrupt and result.final_equity > 0.0:
                    breeding_pool.append(result)
                    key = self._key(result.strategy)
                    previous_attempt = breeding_archive.get(key)
                    if (
                        previous_attempt is None
                        or result.breeding_fitness > previous_attempt.breeding_fitness
                    ):
                        breeding_archive[key] = result
                if result.rankable and not result.bankrupt:
                    key = self._key(result.strategy)
                    previous = archive.get(key)
                    if previous is None or result.fitness > previous.fitness:
                        archive[key] = result

            breeding_pool.sort(key=lambda item: item.breeding_fitness, reverse=True)
            generation_best = (
                breeding_pool[0].breeding_fitness if breeding_pool else float("-inf")
            )
            if generation_best > best_fitness:
                best_fitness = generation_best
                stale = 0
            else:
                stale += 1
            if stale >= stagnation_patience:
                stopped = True
                return self._finish(
                    archive.values(), breeding_archive.values(), generation + 1, evaluations, stopped
                )

            elites = breeding_pool[: max(1, elite_count)]
            next_population = [dict(item.strategy) for item in elites]
            while len(next_population) < population_size:
                draw = self.rng.random()
                if elites and draw < 0.60:
                    parent = self.rng.choice(elites).strategy
                    next_population.append(mutate(dict(parent), self.rng))
                elif crossover is not None and len(elites) >= 2 and draw < 0.85:
                    parent_a, parent_b = self.rng.sample(elites, 2)
                    child = crossover(
                        dict(parent_a.strategy),
                        dict(parent_b.strategy),
                        self.rng,
                    )
                    next_population.append(child)
                else:
                    next_population.append(fresh(self.rng))
            population = next_population

        return self._finish(
            archive.values(), breeding_archive.values(), generations, evaluations, stopped
        )

    @staticmethod
    def _finish(
        archive: Iterable[CandidateResult],
        attempts: Iterable[CandidateResult],
        generations: int,
        evaluations: int,
        stopped: bool,
        control_status: str | None = None,
    ) -> LoopResult:
        ordered = tuple(sorted(archive, key=lambda item: item.fitness, reverse=True))
        best_attempts = tuple(
            sorted(attempts, key=lambda item: item.breeding_fitness, reverse=True)[:20]
        )
        return LoopResult(
            ordered[0] if ordered else None,
            generations,
            evaluations,
            stopped,
            ordered,
            best_attempts,
            control_status,
        )
