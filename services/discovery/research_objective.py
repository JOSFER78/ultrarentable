"""Deterministic multi-objective ranking for quantitative discovery.

The objective is used only on IS/validation data. Blind OOS is never an input.
"""

from __future__ import annotations

import math
from typing import Optional


def _positive_pf(profit_factor: float) -> float:
    return max(0.0, float(profit_factor))


def robust_research_score(
    *,
    profit_factor: float,
    max_drawdown_pct: float,
    trades: int,
    initial_capital_usd: float,
    net_profit_usd: float,
    drawdown_ceiling_pct: float,
    reference_profit_factor: Optional[float] = None,
) -> float:
    """Score a trial without rewarding raw return alone.

    Components: profitability, drawdown survival, trade-count confidence and,
    when a reference PF exists, stability between samples.
    """
    if trades <= 0 or initial_capital_usd <= 0:
        return float("-inf")

    pf = _positive_pf(profit_factor)
    if not math.isfinite(pf):
        return float("-inf")

    dd = max(0.0, float(max_drawdown_pct))
    ceiling = max(0.1, float(drawdown_ceiling_pct))
    dd_ratio = dd / ceiling
    dd_survival = math.exp(-1.5 * dd_ratio) if dd_ratio >= 0 else 1.0

    trade_confidence = min(1.0, math.log1p(trades) / math.log1p(100.0))
    pf_quality = math.log1p(pf)
    return_quality = math.tanh((float(net_profit_usd) / initial_capital_usd) * 2.0)
    return_quality = (return_quality + 1.0) / 2.0

    stability = 1.0
    if reference_profit_factor is not None:
        ref = max(0.0, float(reference_profit_factor))
        denom = max(ref, 1.0)
        stability = max(0.0, 1.0 - min(1.0, abs(pf - ref) / denom))

    return (
        0.38 * pf_quality
        + 0.24 * dd_survival
        + 0.18 * trade_confidence
        + 0.10 * return_quality
        + 0.10 * stability
    ) * 100.0
