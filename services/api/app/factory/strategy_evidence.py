from __future__ import annotations

import math
import random
import json
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from services.api.app.factory.quality_gates import (
    MIN_CALMAR_RATIO,
    calmar_ratio,
    is_ruinous,
)


class EvidenceStatus(str, Enum):
    VALID = "VALID"
    NEEDS_MORE_EVIDENCE = "NEEDS_MORE_EVIDENCE"
    REJECTED = "REJECTED"
    BANKRUPT = "BANKRUPT"


@dataclass(frozen=True)
class EvidenceDecision:
    status: EvidenceStatus
    score: float
    reasons: tuple[str, ...]
    trade_count: int
    effective_sample_size: float
    expected_independent_opportunities: float
    temporal_coverage: float
    best_trade_dependency: float
    bootstrap_positive_probability: float
    multiple_testing_adjusted_probability: float
    alternatives_tried: int
    bootstrap_samples: int
    max_drawdown_pct: float | None = None

    @property
    def rankable(self) -> bool:
        return self.status is EvidenceStatus.VALID

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        payload["rankable"] = self.rankable
        payload["reasons"] = list(self.reasons)
        return payload


class StrategyEvidenceJudge:
    """Judge whether a profitable backtest contains enough evidence to rank.

    There is deliberately no universal minimum-trade rule. Required evidence grows
    from the amount of market history, timeframe, strategy holding horizon,
    strategy complexity and the number of alternatives already tried.
    """

    def __init__(self, bootstrap_samples: int = 512, seed: int = 42) -> None:
        if bootstrap_samples < 64:
            raise ValueError("bootstrap_samples must be at least 64")
        self.bootstrap_samples = bootstrap_samples
        self.seed = seed

    @staticmethod
    def _finite(values: Iterable[float]) -> list[float]:
        return [float(value) for value in values if math.isfinite(float(value))]

    @staticmethod
    def _strategy_complexity(strategy: Mapping[str, Any] | None) -> int:
        if not strategy:
            return 1

        def visit(value: Any) -> int:
            if isinstance(value, Mapping):
                return 1 + sum(visit(item) for item in value.values())
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                return 1 + sum(visit(item) for item in value)
            return 1

        return max(1, visit(strategy))

    @staticmethod
    def _effective_sample_size(returns: Sequence[float]) -> float:
        size = len(returns)
        if size < 2:
            return float(size)
        mean = sum(returns) / size
        variance = sum((value - mean) ** 2 for value in returns)
        if variance <= 1e-18:
            return 1.0
        lag_covariance = sum(
            (returns[index] - mean) * (returns[index - 1] - mean)
            for index in range(1, size)
        )
        rho = max(-0.95, min(0.95, lag_covariance / variance))
        estimate = size * (1.0 - rho) / (1.0 + rho)
        return max(1.0, min(float(size), estimate))

    def _bootstrap_positive_probability(
        self,
        returns: Sequence[float],
        samples: int,
    ) -> float:
        if not returns:
            return 0.0
        rng = random.Random(self.seed)
        size = len(returns)
        positive = 0
        for _ in range(samples):
            sampled_mean = sum(returns[rng.randrange(size)] for _ in range(size)) / size
            positive += sampled_mean > 0.0
        return positive / samples

    @staticmethod
    def _temporal_coverage(
        timestamps_ms: Sequence[int] | None,
        trade_count: int,
        history_days: float,
        expected_opportunities: float,
        research_start_ms: int | None = None,
    ) -> float:
        target_bins = max(2, min(12, int(round(math.sqrt(max(1.0, expected_opportunities))))))
        if not timestamps_ms or len(timestamps_ms) != trade_count:
            # Without timestamps the result remains auditable only at summary level.
            return min(1.0, trade_count / target_bins) * 0.5
        start = int(research_start_ms) if research_start_ms is not None else min(timestamps_ms)
        end = max(timestamps_ms)
        research_span_ms = max(1.0, history_days * 86_400_000.0)
        # Anchor bins to the research span, not to first/last trade, so clustered
        # trades cannot masquerade as broad temporal coverage.
        occupied = {
            min(target_bins - 1, max(0, int(((stamp - start) / research_span_ms) * target_bins)))
            for stamp in timestamps_ms
        }
        if end == start:
            occupied = {0}
        return min(1.0, len(occupied) / target_bins)

    def evaluate(
        self,
        *,
        initial_equity: float,
        final_equity: float,
        timeframe_minutes: int,
        history_days: float,
        trade_returns: Sequence[float] | None,
        trade_timestamps_ms: Sequence[int] | None = None,
        reported_trade_count: int | None = None,
        strategy: Mapping[str, Any] | None = None,
        expected_holding_bars: float | None = None,
        alternatives_tried: int = 1,
        liquidated: bool = False,
        research_start_ms: int | None = None,
        max_drawdown_pct: float | None = None,
        mode: str = "ultra",
    ) -> EvidenceDecision:
        if timeframe_minutes <= 0 or history_days <= 0:
            raise ValueError("timeframe_minutes and history_days must be positive")

        raw_returns = self._finite(trade_returns or [])
        trade_count = reported_trade_count if reported_trade_count is not None else len(raw_returns)
        complexity = self._strategy_complexity(strategy)
        holding_bars = max(1.0, float(expected_holding_bars or math.sqrt(complexity)))
        market_bars = history_days * 1_440.0 / timeframe_minutes
        expected_opportunities = max(1.0, market_bars / (holding_bars * math.sqrt(complexity)))
        tried = max(1, int(alternatives_tried))
        bootstrap_samples = max(self.bootstrap_samples, min(8_192, tried * 8))

        empty_metrics = dict(
            trade_count=max(0, int(trade_count)),
            effective_sample_size=float(len(raw_returns)),
            expected_independent_opportunities=round(expected_opportunities, 6),
            temporal_coverage=0.0,
            best_trade_dependency=1.0,
            bootstrap_positive_probability=0.0,
            multiple_testing_adjusted_probability=0.0,
            alternatives_tried=tried,
            bootstrap_samples=bootstrap_samples,
            max_drawdown_pct=max_drawdown_pct,
        )

        # Hard quality gate: a candidate that destroyed its account (drawdown
        # >= 100%) is never rankable, even if the summary numbers looked green.
        # A 20% net return with 260% drawdown is not an edge — it is ruin dressed
        # up as a backtest. This gate applies regardless of mode or trade evidence.
        is_ruin = is_ruinous(max_drawdown_pct or 0.0)
        if is_ruin:
            return EvidenceDecision(
                EvidenceStatus.REJECTED,
                0.0,
                ("RUINOUS_DRAWDOWN", "MAX_DRAWDOWN_EXCEEDS_100_PCT"),
                **empty_metrics,
            )

        if liquidated or not math.isfinite(final_equity) or final_equity <= 0.0:
            return EvidenceDecision(
                EvidenceStatus.BANKRUPT,
                0.0,
                ("ACCOUNT_BANKRUPTCY_OR_LIQUIDATION",),
                **empty_metrics,
            )
        if trade_count <= 0:
            return EvidenceDecision(
                EvidenceStatus.REJECTED,
                0.0,
                ("NO_EXECUTED_TRADES",),
                **empty_metrics,
            )
        if len(raw_returns) != trade_count:
            return EvidenceDecision(
                EvidenceStatus.NEEDS_MORE_EVIDENCE,
                0.05,
                ("TRADE_LEDGER_REQUIRED", "SUMMARY_ONLY_RESULT_NOT_RANKABLE"),
                **empty_metrics,
            )

        effective_size = self._effective_sample_size(raw_returns)
        probability = self._bootstrap_positive_probability(raw_returns, bootstrap_samples)
        adjusted_probability = max(0.0, 1.0 - ((1.0 - probability) * tried))
        temporal_coverage = self._temporal_coverage(
            trade_timestamps_ms,
            trade_count,
            history_days,
            expected_opportunities,
            research_start_ms,
        )
        positive = [max(0.0, value) for value in raw_returns]
        total_positive = sum(positive)
        best_dependency = max(positive, default=0.0) / total_positive if total_positive > 0 else 1.0
        sample_strength = 1.0 - math.exp(
            -effective_size / math.sqrt(expected_opportunities)
        )
        independence = 1.0 - best_dependency
        score = (
            0.32 * sample_strength
            + 0.24 * temporal_coverage
            + 0.24 * adjusted_probability
            + 0.20 * independence
        )
        score = max(0.0, min(1.0, score))

        net_return = final_equity / initial_equity - 1.0 if initial_equity > 0 else -1.0
        # calmar_ratio expects return and drawdown in the same unit. Drawdown is
        # supplied as a percentage; convert the fractional net return to %.
        calmar = calmar_ratio(net_return * 100.0, max_drawdown_pct)
        # In FONDEO mode low Calmar invalidates ranking; in ULTRA mode it is
        # intentionally ignored because aggressive drawdown is part of the search.
        low_calmar = str(mode).lower() == "fondeo" and max_drawdown_pct is not None and calmar < MIN_CALMAR_RATIO

        reasons: list[str] = []
        if net_return <= 0.0 and probability < 0.5:
            status = EvidenceStatus.REJECTED
            reasons.append("NON_POSITIVE_EXPECTANCY")
        elif (
            adjusted_probability >= 0.80
            and sample_strength >= 0.35
            and temporal_coverage >= 0.50
            and best_dependency <= 0.65
            and score >= 0.60
            and not low_calmar
        ):
            status = EvidenceStatus.VALID
            reasons.append("EVIDENCE_SUFFICIENT_FOR_RANKING")
        else:
            status = EvidenceStatus.NEEDS_MORE_EVIDENCE
            if low_calmar:
                reasons.append("RETURN_TO_DRAWDOWN_RATIO_TOO_WEAK")
            if sample_strength < 0.35:
                reasons.append("EFFECTIVE_SAMPLE_TOO_WEAK_FOR_AVAILABLE_MARKET_HISTORY")
            if temporal_coverage < 0.50:
                reasons.append("TRADES_TOO_CONCENTRATED_IN_TIME")
            if best_dependency > 0.65:
                reasons.append("RESULT_DEPENDS_ON_TOO_FEW_OUTLIER_TRADES")
            if adjusted_probability < 0.80:
                reasons.append("BOOTSTRAP_CONFIDENCE_FAILS_MULTIPLE_TESTING_ADJUSTMENT")

        return EvidenceDecision(
            status=status,
            score=round(score, 8),
            reasons=tuple(reasons),
            trade_count=trade_count,
            effective_sample_size=round(effective_size, 6),
            expected_independent_opportunities=round(expected_opportunities, 6),
            temporal_coverage=round(temporal_coverage, 6),
            best_trade_dependency=round(best_dependency, 6),
            bootstrap_positive_probability=round(probability, 6),
            multiple_testing_adjusted_probability=round(adjusted_probability, 6),
            alternatives_tried=tried,
            bootstrap_samples=bootstrap_samples,
            max_drawdown_pct=max_drawdown_pct,
        )


def load_trade_evidence(
    backtest_payload: Mapping[str, Any] | None,
    ledger_path: str | None = None,
) -> tuple[list[float], list[int] | None]:
    """Extract auditable per-trade outcomes from common FastEngine ledger shapes."""
    payload: Any = backtest_payload or {}
    candidates: list[Any] = []
    if isinstance(payload, Mapping):
        for key in ("trades", "ledger", "executions", "positions"):
            value = payload.get(key)
            if isinstance(value, list):
                candidates = value
                break

    if not candidates and ledger_path:
        path = Path(ledger_path)
        if path.is_file():
            try:
                loaded = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                loaded = None
            if isinstance(loaded, list):
                candidates = loaded
            elif isinstance(loaded, Mapping):
                for key in ("trades", "ledger", "executions", "positions"):
                    value = loaded.get(key)
                    if isinstance(value, list):
                        candidates = value
                        break

    returns: list[float] = []
    timestamps: list[int] = []
    complete_timestamps = True
    # Prefer scale-free per-trade returns. Absolute PnL would overweight later
    # compounded trades and distort bootstrap confidence.
    pnl_keys = ("returnPct", "return_pct", "netPnl", "net_pnl", "pnl", "realizedPnl")
    time_keys = ("exitTime", "exit_time", "closeTime", "close_time", "timestamp", "time")
    for item in candidates:
        if not isinstance(item, Mapping):
            continue
        pnl = next((item.get(key) for key in pnl_keys if item.get(key) is not None), None)
        try:
            value = float(pnl)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(value):
            continue
        returns.append(value)
        stamp = next((item.get(key) for key in time_keys if item.get(key) is not None), None)
        try:
            normalized_stamp = int(stamp)
            # Some ledgers use Unix seconds while BingX datasets use milliseconds.
            if 0 < normalized_stamp < 10_000_000_000:
                normalized_stamp *= 1000
            timestamps.append(normalized_stamp)
        except (TypeError, ValueError):
            complete_timestamps = False

    return returns, timestamps if complete_timestamps and len(timestamps) == len(returns) else None
