import random

from services.api.app.factory.adversarial_validation import AdversarialValidator, ScenarioResult
from services.api.app.factory.campaign_pipeline import AutonomousStrategyCampaign
from services.api.app.factory.campaign_planner import AutomaticCampaignPlanner
from services.api.app.factory.optimization_loop import AggressiveOptimizationLoop, CandidateResult


def test_campaign_parameters_are_automatic_and_bounded() -> None:
    plan = AutomaticCampaignPlanner().plan(
        {"interval": "1m", "history_days": 160, "record_count": 230_400},
        max_leverage=125,
        cpu_count=32,
    )
    assert plan.workers == 4
    assert 8 <= plan.population <= 48
    assert 3 <= plan.generations <= 14
    assert plan.leverage_tiers[-1] == 125
    assert plan.evaluation_budget > plan.population


def test_campaign_plan_exposes_every_integer_leverage_up_to_market_cap() -> None:
    plan = AutomaticCampaignPlanner().plan(
        {"interval": "5m", "history_days": 160, "record_count": 46_079},
        max_leverage=500,
        cpu_count=4,
    )
    assert plan.leverage_tiers == tuple(range(1, 501))
    assert {3, 11, 32, 150, 200, 311, 500}.issubset(plan.leverage_tiers)


def test_bankrupt_and_unrankable_candidates_never_become_champion() -> None:
    def evaluate(strategy, attempt):
        kind = strategy["kind"]
        return CandidateResult(
            strategy=strategy,
            final_equity={"bankrupt": 0, "lucky": 1_000_000, "sound": 25_000}[kind],
            evidence_score={"bankrupt": 0, "lucky": 0.1, "sound": 0.9}[kind],
            rankable=kind == "sound",
            bankrupt=kind == "bankrupt",
        )

    loop = AggressiveOptimizationLoop(seed=7)
    result = loop.run(
        initial_population=[{"kind": "bankrupt"}, {"kind": "lucky"}, {"kind": "sound"}],
        evaluate=evaluate,
        mutate=lambda parent, rng: dict(parent),
        fresh=lambda rng: {"kind": "sound"},
        population_size=3,
        generations=3,
        elite_count=1,
        stagnation_patience=2,
    )
    assert result.champion is not None
    assert result.champion.strategy["kind"] == "sound"
    assert all(item.rankable and not item.bankrupt for item in result.archive)


def test_promising_unrankable_candidate_can_breed_but_not_be_promoted() -> None:
    def evaluate(strategy, attempt):
        generation = strategy["generation"]
        return CandidateResult(
            strategy,
            final_equity=30_000 + generation,
            evidence_score=0.45 if generation == 0 else 0.9,
            rankable=generation > 0,
        )

    result = AggressiveOptimizationLoop(seed=4).run(
        initial_population=[{"generation": 0}, {"generation": 0}],
        evaluate=evaluate,
        mutate=lambda parent, rng: {"generation": parent["generation"] + 1},
        fresh=lambda rng: {"generation": 0},
        population_size=2,
        generations=2,
        elite_count=1,
        stagnation_patience=3,
    )
    assert result.champion is not None
    assert result.champion.strategy["generation"] == 1
    assert all(item.rankable for item in result.archive)


def test_solvent_losing_candidate_can_evolve_toward_profit() -> None:
    def evaluate(strategy, attempt):
        equity = strategy["equity"]
        return CandidateResult(
            strategy,
            final_equity=equity,
            evidence_score=0.6,
            rankable=equity > 10_000,
        )

    result = AggressiveOptimizationLoop(seed=8).run(
        initial_population=[{"equity": 6_000.0}, {"equity": 8_000.0}],
        evaluate=evaluate,
        mutate=lambda parent, rng: {"equity": parent["equity"] + 1_500.0},
        fresh=lambda rng: {"equity": 5_000.0},
        population_size=2,
        generations=3,
        elite_count=1,
        stagnation_patience=3,
    )
    assert result.champion is not None
    assert result.champion.final_equity > 10_000
    assert result.champion.rankable is True


def test_control_stop_prevents_further_evaluations() -> None:
    calls = []

    result = AggressiveOptimizationLoop(seed=9).run(
        initial_population=[{"value": 1}],
        evaluate=lambda strategy, attempt: calls.append(attempt) or CandidateResult(
            strategy, 11_000, 0.9, True
        ),
        mutate=lambda parent, rng: dict(parent),
        fresh=lambda rng: {"value": 1},
        population_size=1,
        generations=3,
        elite_count=1,
        stagnation_patience=2,
        control_state=lambda: "STOPPED",
    )
    assert calls == []
    assert result.control_status == "STOPPED"
    assert result.evaluations == 0


def test_adversarial_validation_requires_positive_lockbox() -> None:
    validator = AdversarialValidator(seed=1)

    def evaluate(strategy, scenario):
        lockbox_failure = scenario.locked
        return ScenarioResult(
            scenario=scenario,
            return_pct=-5.0 if lockbox_failure else 20.0,
            max_drawdown_pct=30.0,
            bankrupt=False,
            rankable=not lockbox_failure,
        )

    decision = validator.validate({"kind": "overfit"}, evaluate)
    assert decision.passed is False
    assert "UNTOUCHED_LOCKBOX_FAILED" in decision.reasons


def test_adversarial_validation_accepts_broad_survival() -> None:
    validator = AdversarialValidator(seed=1)

    def evaluate(strategy, scenario):
        return ScenarioResult(scenario, 12.0, 35.0, False, True)

    decision = validator.validate({"kind": "broad"}, evaluate)
    assert decision.passed is True
    assert decision.score == 1.0


def test_full_campaign_only_promotes_lockbox_survivor() -> None:
    population = [{"edge": index} for index in range(8)]

    def candidate(strategy, attempt):
        edge = strategy["edge"]
        return CandidateResult(strategy, 10_000 + edge * 1_000, 0.85, edge >= 4)

    def mutate(parent, rng):
        return {"edge": min(9, parent["edge"] + 1)}

    def fresh(rng):
        return {"edge": rng.randrange(10)}

    def scenario(strategy, window):
        value = 8.0 + strategy["edge"]
        return ScenarioResult(window, value, 25.0, False, True)

    outcome = AutonomousStrategyCampaign(seed=3).run(
        opportunity={"interval": "15m", "history_days": 160, "record_count": 15_359},
        max_leverage=20,
        initial_population=population,
        evaluate_candidate=candidate,
        mutate=mutate,
        fresh=fresh,
        evaluate_scenario=scenario,
        cpu_count=4,
    )
    assert outcome.status == "VALIDATED_CANDIDATE"
    assert outcome.deployable_strategy is not None
