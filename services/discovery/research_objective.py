"""Deterministic multi-objective ranking for quantitative discovery.

The objective is used only on IS/validation data. Blind OOS is never an input.
"""

from __future__ import annotations

import math
from typing import Iterable, Optional, Sequence


def _positive_pf(profit_factor: float) -> float:
    return max(0.0, float(profit_factor))


def contiguous_stability_score(returns_pct: Sequence[float], blocks: int = 4) -> float:
    """Score consistency across contiguous samples instead of rewarding one lucky period."""
    values = [float(value) for value in returns_pct if math.isfinite(float(value))]
    if len(values) < max(4, blocks):
        return 0.0

    block_count = min(max(2, int(blocks)), len(values))
    block_size = len(values) // block_count
    means: list[float] = []
    for index in range(block_count):
        start = index * block_size
        end = len(values) if index == block_count - 1 else (index + 1) * block_size
        segment = values[start:end]
        means.append(sum(segment) / len(segment))

    positive_blocks = sum(1 for value in means if value > 0.0) / block_count
    worst = min(means)
    dispersion = math.sqrt(sum((value - sum(means) / len(means)) ** 2 for value in means) / len(means))
    central = abs(sum(means) / len(means)) + 1e-9
    consistency = 1.0 / (1.0 + dispersion / central)
    worst_penalty = 1.0 if worst >= 0.0 else max(0.0, 1.0 + worst / (abs(max(means)) + 1e-9))
    return max(0.0, min(1.0, 0.55 * positive_blocks + 0.30 * consistency + 0.15 * worst_penalty))


def robust_research_score(
    *,
    profit_factor: float,
    max_drawdown_pct: float,
    trades: int,
    initial_capital_usd: float,
    net_profit_usd: float,
    drawdown_ceiling_pct: float,
    reference_profit_factor: Optional[float] = None,
    returns_pct: Optional[Iterable[float]] = None,
) -> float:
    """Score a trial without rewarding raw return alone.

    Components: profitability, drawdown survival, trade-count confidence, sample
    stability, and optional cross-sample PF stability.
    """
    if trades <= 0 or initial_capital_usd <= 0:
        return float("-inf")

    pf = _positive_pf(profit_factor)
    if not math.isfinite(pf):
        return float("-inf")

    dd = max(0.0, float(max_drawdown_pct))
    ceiling = max(0.1, float(drawdown_ceiling_pct))
    dd_ratio = dd / ceiling
    dd_survival = math.exp(-1.5 * dd_ratio)

    trade_confidence = min(1.0, math.log1p(trades) / math.log1p(100.0))
    pf_quality = math.log1p(pf)
    return_quality = math.tanh((float(net_profit_usd) / initial_capital_usd) * 2.0)
    return_quality = (return_quality + 1.0) / 2.0
    sample_stability = contiguous_stability_score(list(returns_pct or [])) if returns_pct is not None else 0.5

    pf_stability = 1.0
    if reference_profit_factor is not None:
        ref = max(0.0, float(reference_profit_factor))
        denom = max(ref, 1.0)
        pf_stability = max(0.0, 1.0 - min(1.0, abs(pf - ref) / denom))

    return (
        0.32 * pf_quality
        + 0.22 * dd_survival
        + 0.16 * trade_confidence
        + 0.12 * return_quality
        + 0.10 * sample_stability
        + 0.08 * pf_stability
    ) * 100.0
