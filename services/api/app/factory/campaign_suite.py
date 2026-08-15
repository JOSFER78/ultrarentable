from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from sqlalchemy.orm import Session

from services.api.app.factory.fast_engine_campaign import (
    FastCampaignOutcome,
    FastEngineCampaignRunner,
)


@dataclass(frozen=True)
class CampaignRound:
    interval: str
    round_index: int
    outcome: FastCampaignOutcome

    def summary(self) -> dict[str, Any]:
        attempts = self.outcome.search.best_attempts
        return {
            "interval": self.interval,
            "round": self.round_index,
            "status": self.outcome.status,
            "evaluations": self.outcome.search.evaluations,
            "topEquity": attempts[0].final_equity if attempts else None,
            "topEvidence": attempts[0].evidence_score if attempts else None,
            "stoppedForStagnation": self.outcome.search.stopped_for_stagnation,
        }


@dataclass(frozen=True)
class CampaignSuiteOutcome:
    status: str
    rounds: tuple[CampaignRound, ...]

    @property
    def champion_outcome(self) -> FastCampaignOutcome | None:
        return next(
            (item.outcome for item in self.rounds if item.outcome.champion is not None),
            None,
        )

    @property
    def evaluations(self) -> int:
        return sum(item.outcome.search.evaluations for item in self.rounds)

    def to_dict(self) -> dict[str, Any]:
        champion = self.champion_outcome
        attempts = [
            candidate
            for item in self.rounds
            for candidate in item.outcome.search.best_attempts
        ]
        best = max(attempts, key=lambda item: item.final_equity, default=None)
        return {
            "status": self.status,
            "evaluations": self.evaluations,
            "rounds": [item.summary() for item in self.rounds],
            "bestObserved": None if best is None else {
                "finalEquity": best.final_equity,
                "evidenceScore": best.evidence_score,
                "rankable": best.rankable,
                "evidence": best.evidence,
                "strategy": best.strategy,
            },
            "validatedCampaign": champion.to_dict() if champion else None,
        }


class FastEngineCampaignSuite:
    """Bounded coarse-to-fine rounds with lineage continuation and rotation."""

    def __init__(
        self,
        db: Session,
        *,
        seed: int = 42,
        runner_factory: Callable[[Session, int], FastEngineCampaignRunner] | None = None,
    ) -> None:
        self.db = db
        self.seed = seed
        self.runner_factory = runner_factory or (
            lambda session, value: FastEngineCampaignRunner(session, seed=value)
        )

    def run(
        self,
        opportunities: Sequence[Mapping[str, Any]],
        *,
        max_leverage: int,
        rounds_per_market: int = 3,
        control_state: Callable[[], str] | None = None,
    ) -> CampaignSuiteOutcome:
        # Coarse bars are cheaper and expose broad regime behavior first.
        ordered = sorted(opportunities, key=lambda item: int(item["record_count"]))
        completed: list[CampaignRound] = []
        seed_offset = 0
        for opportunity in ordered:
            carried: list[dict[str, Any]] | None = None
            previous_best: float | None = None
            stagnant_rounds = 0
            for round_index in range(1, max(1, rounds_per_market) + 1):
                runner = self.runner_factory(self.db, self.seed + seed_offset)
                seed_offset += 1
                outcome = runner.run(
                    opportunity,
                    max_leverage=max_leverage,
                    initial_population=carried,
                    control_state=control_state,
                )
                completed.append(CampaignRound(
                    str(opportunity["interval"]),
                    round_index,
                    outcome,
                ))
                if outcome.champion is not None:
                    return CampaignSuiteOutcome(
                        "VALIDATED_CANDIDATE",
                        tuple(completed),
                    )
                if outcome.search.control_status:
                    return CampaignSuiteOutcome(
                        outcome.search.control_status,
                        tuple(completed),
                    )

                attempts = list(outcome.search.best_attempts)
                carried = [dict(item.strategy) for item in attempts]
                best_equity = (
                    max((item.final_equity for item in attempts), default=0.0)
                )
                if previous_best is not None:
                    meaningful = max(10.0, abs(previous_best) * 0.001)
                    if best_equity <= previous_best + meaningful:
                        stagnant_rounds += 1
                    else:
                        stagnant_rounds = 0
                previous_best = best_equity
                # One failed continuation after a completed round is enough to
                # rotate timeframe; fresh seeds still occupy half each round.
                if stagnant_rounds >= 1:
                    break

        return CampaignSuiteOutcome(
            "NO_VALID_CANDIDATE_AFTER_BOUNDED_SEARCH",
            tuple(completed),
        )
