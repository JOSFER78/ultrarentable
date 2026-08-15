from __future__ import annotations

from types import SimpleNamespace

from services.api.app.factory.campaign_suite import FastEngineCampaignSuite
from services.api.app.factory.optimization_loop import CandidateResult


class FakeRunner:
    def __init__(self, outcomes, calls):
        self.outcomes = outcomes
        self.calls = calls

    def run(self, opportunity, **kwargs):
        self.calls.append((opportunity["interval"], kwargs.get("initial_population")))
        return self.outcomes.pop(0)


def _outcome(equity, *, champion=None, control=None):
    candidate = CandidateResult(
        {"market": {"timeframe": "test"}, "value": equity},
        equity,
        0.7,
        bool(champion),
    )
    search = SimpleNamespace(
        best_attempts=(candidate,),
        evaluations=10,
        stopped_for_stagnation=False,
        control_status=control,
    )
    return SimpleNamespace(
        status="VALIDATED_CANDIDATE" if champion else "NO_VALID_CANDIDATE",
        champion=champion,
        search=search,
    )


def test_suite_continues_lineage_then_rotates_coarse_to_fine() -> None:
    outcomes = [
        _outcome(9_000),
        _outcome(9_005),
        _outcome(12_000, champion={"strategy": {"ok": True}}),
    ]
    calls = []

    def factory(db, seed):
        return FakeRunner(outcomes, calls)

    suite = FastEngineCampaignSuite(object(), seed=10, runner_factory=factory)
    result = suite.run(
        [
            {"interval": "1m", "record_count": 100},
            {"interval": "15m", "record_count": 10},
        ],
        max_leverage=20,
        rounds_per_market=3,
    )
    assert result.status == "VALIDATED_CANDIDATE"
    assert [item[0] for item in calls] == ["15m", "15m", "1m"]
    assert calls[0][1] is None
    assert calls[1][1]
    assert calls[2][1] is None
    assert result.evaluations == 30


def test_suite_propagates_control_stop() -> None:
    outcomes = [_outcome(9_000, control="STOPPED")]
    calls = []
    suite = FastEngineCampaignSuite(
        object(),
        runner_factory=lambda db, seed: FakeRunner(outcomes, calls),
    )
    result = suite.run(
        [{"interval": "15m", "record_count": 10}],
        max_leverage=20,
    )
    assert result.status == "STOPPED"
    assert len(calls) == 1
