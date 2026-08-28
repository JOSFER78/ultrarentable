"""Robust contiguous-block Validation for Phase-2 strategy selection.

Validation is deliberately separated from Blind OOS. A candidate must perform
persistently across contiguous validation blocks; a single peak cannot dominate
selection. This is a ranking signal, not certification by itself.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Sequence

VALIDATION_BLOCKS = 4


@dataclass(frozen=True)
class ValidationBlock:
    index: int
    trades: int
    profit_factor: float
    max_drawdown_pct: float
    net_profit_usd: float
    win_rate_pct: float


@dataclass(frozen=True)
class RobustValidation:
    score: float
    median_pf: float
    minimum_pf: float
    pf_stddev: float
    profitable_block_fraction: float
    median_trades: float
    worst_drawdown_pct: float
    blocks: List[ValidationBlock]

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["blocks"] = [asdict(block) for block in self.blocks]
        return payload


def split_contiguous(data: Sequence[Dict[str, Any]], blocks: int = VALIDATION_BLOCKS) -> List[List[Dict[str, Any]]]:
    if not data:
        return []
    count = max(1, min(int(blocks), len(data)))
    base, remainder = divmod(len(data), count)
    result: List[List[Dict[str, Any]]] = []
    start = 0
    for index in range(count):
        width = base + (1 if index < remainder else 0)
        result.append(list(data[start : start + width]))
        start += width
    return result


def _safe_pf(value: Any) -> float:
    try:
        value_float = float(value)
    except (TypeError, ValueError):
        return 0.0
    return value_float if math.isfinite(value_float) and value_float >= 0.0 else 0.0


def evaluate_validation(
    engine: Any,
    strategy: Any,
    candles_validation: Sequence[Dict[str, Any]],
    initial_capital_usd: float,
) -> RobustValidation:
    metrics: List[ValidationBlock] = []
    for index, block in enumerate(split_contiguous(candles_validation)):
        result = engine.run_backtest(strategy, block, initial_capital_usd=initial_capital_usd)
        metrics.append(
            ValidationBlock(
                index=index,
                trades=int(result.total_trades),
                profit_factor=_safe_pf(result.profit_factor),
                max_drawdown_pct=max(0.0, float(result.max_drawdown_pct)),
                net_profit_usd=float(result.net_profit_usd),
                win_rate_pct=float(result.win_rate_pct),
            )
        )

    if not metrics:
        return RobustValidation(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, [])

    pfs = sorted(block.profit_factor for block in metrics)
    trades = sorted(block.trades for block in metrics)
    middle = len(pfs) // 2
    median_pf = pfs[middle] if len(pfs) % 2 else (pfs[middle - 1] + pfs[middle]) / 2.0
    middle_trades = len(trades) // 2
    median_trades = (
        float(trades[middle_trades])
        if len(trades) % 2
        else (trades[middle_trades - 1] + trades[middle_trades]) / 2.0
    )
    minimum_pf = min(pfs)
    mean_pf = sum(pfs) / len(pfs)
    pf_stddev = math.sqrt(sum((pf - mean_pf) ** 2 for pf in pfs) / len(pfs))
    profitable_fraction = sum(pf >= 1.0 for pf in pfs) / len(pfs)
    worst_dd = max(block.max_drawdown_pct for block in metrics)

    stability_ratio = max(0.0, 1.0 - pf_stddev / max(median_pf, 1e-9))
    drawdown_factor = max(0.0, 1.0 - worst_dd / 100.0)
    trade_support = 1.0 + math.log1p(max(0.0, median_trades))
    score = (
        0.40 * median_pf
        + 0.25 * minimum_pf
        + 0.20 * profitable_fraction
        + 0.10 * stability_ratio
        + 0.05 * drawdown_factor
    ) * trade_support

    return RobustValidation(
        score=float(score),
        median_pf=float(median_pf),
        minimum_pf=float(minimum_pf),
        pf_stddev=float(pf_stddev),
        profitable_block_fraction=float(profitable_fraction),
        median_trades=float(median_trades),
        worst_drawdown_pct=float(worst_dd),
        blocks=metrics,
    )
