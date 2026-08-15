"""Verification test: mode-aware quality gates for ULTRA vs FONDEO search.

ULTRA (kamikaze): accepts extreme drawdown unless the account is truly ruined
(drawdown >= 100%). DD-sustainable and Calmar gates are intentionally disabled
so aggressive-but-solvent candidates can rank.

FONDEO (conservative): applies all gates — ruin, sustainable DD and Calmar —
because the goal is live-funding viability.
"""

from __future__ import annotations

from services.api.app.factory.strategy_evidence import (
    EvidenceStatus,
    StrategyEvidenceJudge,
)
from services.api.app.factory.quality_gates import (
    rentable,
    is_ruinous,
    calmar_ratio,
    drawdown_penalty_factor,
    risk_adjusted_fitness,
)


def _distributed_timestamps(count: int, history_days: int = 160) -> list[int]:
    span = history_days * 86_400_000
    return [int(index * span / count) for index in range(count)]


# The exact pathological profile the user complained about: modest profit, ruinous DD.
PATHOLOGICAL_NET_RETURN_PCT = 20.0
PATHOLOGICAL_DRAWDOWN_PCT = 260.0


def _distributed_green_returns(count: int) -> list[float]:
    # Spread-out small wins so naive statistical evidence WOULD have ranked it
    # before the drawdown gate existed.
    return [0.012, 0.009, -0.003, 0.014, 0.008, 0.011, -0.002, 0.013] * max(1, count // 8)


# ── Ruin gate is unconditional ─────────────────────────────────────────

def test_pathological_profile_is_ruinous() -> None:
    assert is_ruinous(260.0) is True
    assert is_ruinous(99.0) is False
    assert is_ruinous(None) is False


# ── FONDEO mode applies all gates ──────────────────────────────────────

def test_fondeo_rejects_ruinous_drawdown() -> None:
    # 20% net / 260% DD => ruinous, must be rejected in FONDEO.
    assert rentable(20.0, profit_factor=2.0, drawdown_pct=260.0, mode="fondeo") is False


def test_fondeo_rejects_poor_calmar_when_not_technically_ruinous() -> None:
    # 20% net with 50% DD is not ruin yet, but Calmar 0.4 < 0.5 floor => not VALID in FONDEO.
    returns = _distributed_green_returns(160)
    decision = StrategyEvidenceJudge().evaluate(
        initial_equity=10_000,
        final_equity=12_000,
        timeframe_minutes=15,
        history_days=160,
        trade_returns=returns,
        trade_timestamps_ms=_distributed_timestamps(len(returns)),
        strategy={"entry": {"kind": "trend"}, "exit": {"kind": "trailing"}},
        alternatives_tried=5,
        max_drawdown_pct=50.0,
        mode="fondeo",
    )
    assert decision.rankable is False
    assert "RETURN_TO_DRAWDOWN_RATIO_TOO_WEAK" in decision.reasons


def test_fondeo_drawdown_penalty_decreases_with_destructive_dd() -> None:
    assert drawdown_penalty_factor(20.0, mode="fondeo") == 1.0
    assert drawdown_penalty_factor(90.0, mode="fondeo") < 1.0
    assert drawdown_penalty_factor(260.0, mode="fondeo") == 0.0


# ── ULTRA mode ignores sustainable-DD / Calmar gates ───────────────────

def test_ultra_mode_rentable_ignores_destructive_drawdown() -> None:
    # 20% net / 90% DD: PF and return are fine, so in ULTRA this IS rentable
    # (the DD gates are intentionally disabled).
    assert rentable(20.0, profit_factor=2.0, drawdown_pct=90.0, mode="ultra") is True
    # Ruinous DD is still rejected in both modes.
    assert rentable(20.0, profit_factor=2.0, drawdown_pct=260.0, mode="ultra") is False


def test_ultra_mode_drawdown_penalty_is_neutral() -> None:
    assert drawdown_penalty_factor(20.0, mode="ultra") == 1.0
    assert drawdown_penalty_factor(90.0, mode="ultra") == 1.0
    assert drawdown_penalty_factor(260.0, mode="ultra") == 0.0


def test_ultra_mode_risk_adjusted_fitness_is_neutral() -> None:
    assert risk_adjusted_fitness(20.0, 20.0, mode="ultra") == 1.0
    assert risk_adjusted_fitness(20.0, 90.0, mode="ultra") == 1.0
    assert risk_adjusted_fitness(20.0, 260.0, mode="ultra") == 0.0


def test_ultra_mode_evidence_allows_high_dd_if_not_ruinous() -> None:
    # A kamikaze candidate with 90% DD but real positive evidence should be
    # rankable in ULTRA mode (ruin gate does not fire; Calmar gate is ignored).
    returns = _distributed_green_returns(160)
    decision = StrategyEvidenceJudge().evaluate(
        initial_equity=10_000,
        final_equity=20_000,  # +100% terminal
        timeframe_minutes=15,
        history_days=160,
        trade_returns=returns,
        trade_timestamps_ms=_distributed_timestamps(len(returns)),
        strategy={"entry": {"kind": "trend"}, "exit": {"kind": "trailing"}},
        alternatives_tried=5,
        max_drawdown_pct=90.0,
        mode="ultra",
    )
    assert decision.rankable is True
    assert decision.status is EvidenceStatus.VALID


# ── Regression: 20% / 260% is poison everywhere ────────────────────────

def test_pathological_profile_fails_rentable_gate_in_fondeo() -> None:
    # 20% net / 260% DD => Calmar ~0.077, far below the 0.5 floor; DD also ruinous.
    assert calmar_ratio(20.0, 260.0) < 0.5
    assert rentable(20.0, profit_factor=2.0, drawdown_pct=260.0, mode="fondeo") is False


def test_evidence_judge_rejects_ruinous_drawdown_even_with_green_ledger() -> None:
    # Even with a beautifully distributed, independently-sampled profitable
    # ledger, a 260% drawdown must be REJECTED — never VALID / rankable.
    returns = _distributed_green_returns(160)
    decision = StrategyEvidenceJudge().evaluate(
        initial_equity=10_000,
        final_equity=12_000,           # +20%
        timeframe_minutes=15,
        history_days=160,
        trade_returns=returns,
        trade_timestamps_ms=_distributed_timestamps(len(returns)),
        strategy={"entry": {"kind": "trend"}, "exit": {"kind": "trailing"}},
        alternatives_tried=5,
        max_drawdown_pct=260.0,
    )
    assert decision.status is EvidenceStatus.REJECTED
    assert decision.rankable is False
    assert "RUINOUS_DRAWDOWN" in decision.reasons


# ── CandidateResult fitness behaviour ──────────────────────────────────

def test_fitness_term_zeroes_out_ruinous_drawdown() -> None:
    from services.api.app.factory.optimization_loop import CandidateResult

    good = CandidateResult(
        strategy={"id": "good"},
        final_equity=12_000.0,
        evidence_score=0.9,
        rankable=True,
        max_drawdown_pct=30.0,
        net_return_pct=20.0,
    )
    bad = CandidateResult(
        strategy={"id": "bad"},
        final_equity=12_000.0,
        evidence_score=0.9,
        rankable=True,
        max_drawdown_pct=260.0,
        net_return_pct=20.0,
    )
    # Same terminal equity and evidence, but the ruinous one must not even be a
    # finite fitness — the search must discard it, not race it.
    assert good.fitness > 0.0
    assert bad.fitness == float("-inf")
    assert bad.breeding_fitness == float("-inf")


def test_ultra_candidate_can_have_positive_fitness_with_high_dd() -> None:
    from services.api.app.factory.optimization_loop import CandidateResult

    candidate = CandidateResult(
        strategy={"id": "kamikaze"},
        final_equity=25_000.0,
        evidence_score=0.8,
        rankable=True,
        max_drawdown_pct=90.0,
        net_return_pct=150.0,
        mode="ultra",
    )
    assert candidate.fitness > 0.0
    assert candidate.breeding_fitness > 0.0


def test_fondeo_candidate_penalized_for_high_dd() -> None:
    from services.api.app.factory.optimization_loop import CandidateResult

    candidate = CandidateResult(
        strategy={"id": "risky"},
        final_equity=25_000.0,
        evidence_score=0.8,
        rankable=True,
        max_drawdown_pct=90.0,
        net_return_pct=150.0,
        mode="fondeo",
    )
    # In FONDEO the DD penalty reduces fitness, but does not kill it (DD < 100%).
    assert 0.0 < candidate.fitness < float("inf")
    assert 0.0 < candidate.breeding_fitness < float("inf")
