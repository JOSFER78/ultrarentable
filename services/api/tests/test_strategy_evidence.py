import json

from services.api.app.factory.strategy_evidence import (
    EvidenceStatus,
    StrategyEvidenceJudge,
    load_trade_evidence,
)


def _distributed_timestamps(count: int, history_days: int = 160) -> list[int]:
    span = history_days * 86_400_000
    return [int(index * span / count) for index in range(count)]


def test_one_lucky_trade_is_never_rankable() -> None:
    decision = StrategyEvidenceJudge().evaluate(
        initial_equity=10_000,
        final_equity=40_000,
        timeframe_minutes=1,
        history_days=160,
        trade_returns=[3.0],
        trade_timestamps_ms=[0],
        strategy={"entry": {"kind": "breakout"}},
        alternatives_tried=40,
    )

    assert decision.status is EvidenceStatus.NEEDS_MORE_EVIDENCE
    assert decision.rankable is False
    assert "RESULT_DEPENDS_ON_TOO_FEW_OUTLIER_TRADES" in decision.reasons


def test_summary_without_ledger_is_not_rankable() -> None:
    decision = StrategyEvidenceJudge().evaluate(
        initial_equity=10_000,
        final_equity=25_000,
        timeframe_minutes=5,
        history_days=160,
        trade_returns=None,
        reported_trade_count=250,
    )

    assert decision.status is EvidenceStatus.NEEDS_MORE_EVIDENCE
    assert decision.reasons == (
        "TRADE_LEDGER_REQUIRED",
        "SUMMARY_ONLY_RESULT_NOT_RANKABLE",
    )


def test_bankruptcy_is_terminal_even_with_prior_profits() -> None:
    decision = StrategyEvidenceJudge().evaluate(
        initial_equity=10_000,
        final_equity=0,
        timeframe_minutes=15,
        history_days=160,
        trade_returns=[0.5, 0.8, -1.0],
        liquidated=True,
    )

    assert decision.status is EvidenceStatus.BANKRUPT
    assert decision.rankable is False


def test_consistent_distributed_strategy_can_be_ranked() -> None:
    returns = [0.012, 0.009, -0.003, 0.014, 0.008, 0.011, -0.002, 0.013] * 20
    decision = StrategyEvidenceJudge().evaluate(
        initial_equity=10_000,
        final_equity=31_000,
        timeframe_minutes=15,
        history_days=160,
        trade_returns=returns,
        trade_timestamps_ms=_distributed_timestamps(len(returns)),
        strategy={"entry": {"kind": "trend"}, "exit": {"kind": "trailing"}},
        alternatives_tried=5,
    )

    assert decision.status is EvidenceStatus.VALID
    assert decision.rankable is True
    assert decision.temporal_coverage >= 0.5


def test_many_losses_are_rejected_without_fixed_trade_threshold() -> None:
    returns = [-0.01, -0.02, 0.002, -0.015, -0.008] * 12
    decision = StrategyEvidenceJudge().evaluate(
        initial_equity=10_000,
        final_equity=4_000,
        timeframe_minutes=5,
        history_days=160,
        trade_returns=returns,
        trade_timestamps_ms=_distributed_timestamps(len(returns)),
        alternatives_tried=1,
    )

    assert decision.status is EvidenceStatus.REJECTED


def test_same_trade_count_is_judged_against_strategy_context() -> None:
    returns = [0.02, 0.015, -0.002, 0.018, 0.012, 0.014, -0.001, 0.016] * 5
    timestamps = _distributed_timestamps(len(returns))
    judge = StrategyEvidenceJudge()
    fast = judge.evaluate(
        initial_equity=10_000,
        final_equity=17_000,
        timeframe_minutes=1,
        history_days=160,
        trade_returns=returns,
        trade_timestamps_ms=timestamps,
        strategy={"entry": {"a": 1}, "exit": {"b": 2}},
        alternatives_tried=10,
    )
    slow = judge.evaluate(
        initial_equity=10_000,
        final_equity=17_000,
        timeframe_minutes=60,
        history_days=160,
        trade_returns=returns,
        trade_timestamps_ms=timestamps,
        strategy={"entry": {"a": 1}, "exit": {"b": 2}},
        alternatives_tried=10,
    )

    assert slow.score > fast.score
    assert fast.trade_count == slow.trade_count


def test_trade_evidence_is_loaded_from_result_or_persisted_ledger(tmp_path) -> None:
    inline_returns, inline_times = load_trade_evidence(
        {"trades": [{"netPnl": 12.5, "exitTime": 100}, {"pnl": -2, "time": 200}]}
    )
    assert inline_returns == [12.5, -2.0]
    assert inline_times == [100_000, 200_000]

    ledger = tmp_path / "ledger.json"
    ledger.write_text(
        json.dumps({"executions": [{"realizedPnl": 4, "closeTime": 300}]}),
        encoding="utf-8",
    )
    file_returns, file_times = load_trade_evidence({}, str(ledger))
    assert file_returns == [4.0]
    assert file_times == [300_000]


def test_research_start_prevents_late_cluster_from_looking_distributed() -> None:
    returns = [0.01] * 40
    day_ms = 86_400_000
    timestamps = [150 * day_ms + index * 60_000 for index in range(40)]
    decision = StrategyEvidenceJudge().evaluate(
        initial_equity=10_000,
        final_equity=15_000,
        timeframe_minutes=1,
        history_days=160,
        trade_returns=returns,
        trade_timestamps_ms=timestamps,
        research_start_ms=0,
    )
    assert decision.temporal_coverage < 0.5
    assert decision.rankable is False


def test_trade_percentage_is_preferred_over_compounded_cash_pnl() -> None:
    returns, timestamps = load_trade_evidence({
        "trades": [{
            "net_pnl": 8_000.0,
            "return_pct": 2.5,
            "exit_time": 123,
        }]
    })
    assert returns == [2.5]
    assert timestamps == [123_000]


def test_bootstrap_resolution_scales_with_search_budget() -> None:
    decision = StrategyEvidenceJudge(bootstrap_samples=512).evaluate(
        initial_equity=10_000,
        final_equity=15_000,
        timeframe_minutes=15,
        history_days=160,
        trade_returns=[0.5, 0.4, -0.1, 0.6] * 30,
        trade_timestamps_ms=_distributed_timestamps(120),
        alternatives_tried=248,
    )
    assert decision.alternatives_tried == 248
    assert decision.bootstrap_samples >= 248 * 8
