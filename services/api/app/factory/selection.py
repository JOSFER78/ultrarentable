"""Kamikaze Selection and Novelty Archive."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CandidateEvaluation:
    strategy_dict: dict[str, Any]
    canonical_hash: str
    status: str  # COMPLETED, LIQUIDATED, FAILED, INVALID
    final_equity: float
    initial_capital: float
    net_return_pct: float
    failure_code: str | None = None
    fitness: float = -9999.0
    novelty_score: float = 0.0

    def __post_init__(self):
        if self.status == "COMPLETED" and self.final_equity > 0 and self.initial_capital > 0:
            self.fitness = math.log(self.final_equity / self.initial_capital)
        else:
            self.fitness = -9999.0


class NoveltyArchive:
    """Tracks structural diversity of strategies to prevent premature convergence."""

    def __init__(self, max_size: int = 500):
        self.max_size = max_size
        self.seen_hashes: set[str] = set()

    def add(self, canonical_hash: str) -> None:
        self.seen_hashes.add(canonical_hash)

    def is_novel(self, canonical_hash: str) -> bool:
        return canonical_hash not in self.seen_hashes


class KamikazeSelection:
    """Implements hard-filtered Kamikaze Selection with diversity preservation."""

    def __init__(
        self,
        top_equity_pct: float = 0.60,
        novelty_pct: float = 0.20,
        seed_pct: float = 0.10,
        repair_pct: float = 0.10,
    ):
        self.top_equity_pct = top_equity_pct
        self.novelty_pct = novelty_pct
        self.seed_pct = seed_pct
        self.repair_pct = repair_pct
        self.archive = NoveltyArchive()

    def filter_survivors(self, evaluations: list[CandidateEvaluation]) -> list[CandidateEvaluation]:
        """Hard filter: Only COMPLETED evaluations with positive final equity survive."""
        survivors = [
            e for e in evaluations
            if e.status == "COMPLETED" and e.final_equity > 0 and e.fitness > -9990.0
        ]
        survivors.sort(key=lambda x: x.fitness, reverse=True)
        return survivors

    def select_next_generation(
        self,
        evaluations: list[CandidateEvaluation],
        target_size: int,
    ) -> list[CandidateEvaluation]:
        survivors = self.filter_survivors(evaluations)
        if not survivors:
            return []

        for s in survivors:
            self.archive.add(s.canonical_hash)

        n_top = max(1, int(target_size * self.top_equity_pct))
        selected = survivors[:n_top]
        return selected
