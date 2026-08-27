"""Evidence-driven meta-strategy construction for Phase 2/3.

A meta-strategy is selected from already-evaluated strategy evidence. The
engine favors complementary return profiles and penalizes highly correlated
strategies. It never invents performance and never promotes a strategy that
does not carry an immutable evidence reference.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from math import sqrt
from typing import Any, Dict, List, Sequence, Tuple


@dataclass(frozen=True)
class StrategyEvidence:
    strategy_id: str
    strategy_hash: str
    route: str
    symbol: str
    timeframe: str
    oos_returns: Tuple[float, ...]
    oos_profit_factor: float
    oos_drawdown_pct: float
    robustness_passed: bool
    evidence_hash: str

    @property
    def quality(self) -> float:
        return self.oos_profit_factor * max(0.0, 1.0 - self.oos_drawdown_pct / 100.0)


def _corr(a: Sequence[float], b: Sequence[float]) -> float:
    n = min(len(a), len(b))
    if n < 3:
        return 1.0
    x = list(a[-n:])
    y = list(b[-n:])
    mx = sum(x) / n
    my = sum(y) / n
    dx = [v - mx for v in x]
    dy = [v - my for v in y]
    den = sqrt(sum(v * v for v in dx) * sum(v * v for v in dy))
    return sum(u * v for u, v in zip(dx, dy)) / den if den else 1.0


class MetaStrategyEngine:
    """Greedy deterministic diversity optimizer over evidence-backed OOS returns."""

    def __init__(self, version: str = "meta-strategy-v1") -> None:
        self.version = version

    def build(
        self,
        strategies: Sequence[StrategyEvidence],
        max_members: int = 5,
        max_pair_correlation: float = 0.75,
    ) -> Dict[str, Any]:
        eligible = [
            s for s in strategies
            if s.evidence_hash and s.strategy_hash and s.robustness_passed and s.oos_returns and s.oos_profit_factor > 1.0
        ]
        eligible.sort(key=lambda s: (-s.quality, s.route, s.symbol, s.timeframe, s.strategy_id))
        selected: List[StrategyEvidence] = []

        for candidate in eligible:
            if len(selected) >= max_members:
                break
            if not selected:
                selected.append(candidate)
                continue
            correlations = [abs(_corr(candidate.oos_returns, member.oos_returns)) for member in selected]
            if max(correlations) <= max_pair_correlation:
                selected.append(candidate)

        if not selected:
            return {
                "status": "NO_META_STRATEGY",
                "reason": "No evidence-backed robust OOS candidates satisfy the minimum quality criteria.",
                "members": [],
            }

        weights = self._risk_balanced_weights(selected)
        canonical = [
            {
                "strategy_id": s.strategy_id,
                "strategy_hash": s.strategy_hash,
                "evidence_hash": s.evidence_hash,
                "route": s.route,
                "symbol": s.symbol,
                "timeframe": s.timeframe,
                "weight": round(weights[s.strategy_id], 8),
            }
            for s in selected
        ]
        material = f"{self.version}|" + "|".join(
            f"{row['strategy_id']}:{row['strategy_hash']}:{row['evidence_hash']}:{row['weight']}" for row in canonical
        )
        return {
            "status": "META_STRATEGY_CANDIDATE",
            "meta_strategy_id": sha256(material.encode()).hexdigest()[:24],
            "version": self.version,
            "member_count": len(canonical),
            "members": canonical,
            "max_pair_correlation": max_pair_correlation,
        }

    @staticmethod
    def _risk_balanced_weights(strategies: Sequence[StrategyEvidence]) -> Dict[str, float]:
        raw: Dict[str, float] = {}
        for strategy in strategies:
            risk_penalty = max(0.1, strategy.oos_drawdown_pct)
            raw[strategy.strategy_id] = max(0.0, strategy.quality) / risk_penalty
        total = sum(raw.values())
        if total <= 0.0:
            equal = 1.0 / len(strategies)
            return {s.strategy_id: equal for s in strategies}
        return {key: value / total for key, value in raw.items()}
