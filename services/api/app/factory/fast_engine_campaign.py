from __future__ import annotations

import json
import random
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from sqlalchemy.orm import Session

from services.api.app.db.database import BacktestModel
from services.api.app.dsl.engine import StrategyDSL, compile_to_ir, validate_semantics
from services.api.app.engine.fast_engine import FastEngine
from services.api.app.factory.adversarial_validation import (
    AdversarialValidator,
    ScenarioResult,
    ValidationDecision,
    ValidationScenario,
)
from services.api.app.factory.campaign_planner import AutomaticCampaignPlanner, CampaignPlan
from services.api.app.factory.genetic import GeneticOperators
from services.api.app.factory.optimization_loop import (
    AggressiveOptimizationLoop,
    CandidateResult,
    LoopResult,
)
from services.api.app.factory.seed_factory import SeedFactory
from services.api.app.factory.strategy_evidence import StrategyEvidenceJudge, load_trade_evidence


@dataclass(frozen=True)
class FastCampaignOutcome:
    status: str
    plan: CampaignPlan
    search: LoopResult
    validation: ValidationDecision | None
    champion: dict[str, Any] | None
    mode: str = "ultra"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "mode": self.mode,
            "plan": self.plan.to_dict(),
            "evaluations": self.search.evaluations,
            "generations": self.search.generations_run,
            "archiveSize": len(self.search.archive),
            "topAttempts": [
                {
                    "strategy": item.strategy,
                    "finalEquity": item.final_equity,
                    "evidenceScore": item.evidence_score,
                    "rankable": item.rankable,
                    "bankrupt": item.bankrupt,
                    "breedingFitness": item.breeding_fitness,
                    "evidence": item.evidence,
                    "maxDrawdownPct": item.max_drawdown_pct,
                    "netReturnPct": item.net_return_pct,
                }
                for item in self.search.best_attempts
            ],
            "stoppedForStagnation": self.search.stopped_for_stagnation,
            "controlStatus": self.search.control_status,
            "champion": self.champion,
            "validation": None
            if self.validation is None
            else {
                "passed": self.validation.passed,
                "score": self.validation.score,
                "reasons": list(self.validation.reasons),
                "scenarios": [
                    {
                        "name": result.scenario.name,
                        "returnPct": result.return_pct,
                        "maxDrawdownPct": result.max_drawdown_pct,
                        "bankrupt": result.bankrupt,
                        "rankable": result.rankable,
                    }
                    for result in self.validation.results
                ],
            },
        }


class FastEngineCampaignRunner:
    """Real FastEngine evolutionary search with an untouched final lockbox."""

    _TF_MINUTES = {"1m": 1, "5m": 5, "15m": 15, "1h": 60, "4h": 240, "1d": 1440}

    def __init__(self, db: Session, seed: int = 42) -> None:
        self.db = db
        self.seed = seed
        self.engine = FastEngine(db)
        self.judge = StrategyEvidenceJudge(seed=seed)

    def _evidence(
        self,
        result: Mapping[str, Any],
        strategy: Mapping[str, Any],
        opportunity: Mapping[str, Any],
        alternatives_tried: int,
        start_fraction: float,
        end_fraction: float,
        max_drawdown_pct: float | None = None,
        mode: str = "ultra",
    ):
        backtest = self.db.query(BacktestModel).filter(
            BacktestModel.backtest_id == result.get("backtestId")
        ).first()
        returns, timestamps = load_trade_evidence(
            result, backtest.ledger_path if backtest else result.get("ledgerPath")
        )
        history_days = float(opportunity["history_days"]) * (end_fraction - start_fraction)
        full_span_ms = float(opportunity["history_days"]) * 86_400_000.0
        research_start = int(float(opportunity["start_time"]) + full_span_ms * start_fraction)
        return self.judge.evaluate(
            initial_equity=10_000.0,
            final_equity=float(result.get("finalEquity", 0.0)),
            timeframe_minutes=self._TF_MINUTES[opportunity["interval"]],
            history_days=history_days,
            trade_returns=returns,
            trade_timestamps_ms=timestamps,
            reported_trade_count=int(result.get("tradesCount", len(returns))),
            strategy=strategy,
            alternatives_tried=alternatives_tried,
            liquidated=bool(result.get("liquidated", False)),
            research_start_ms=research_start,
            max_drawdown_pct=max_drawdown_pct,
            mode=mode,
        )

    @staticmethod
    def _valid_strategy(strategy: dict[str, Any]) -> bool:
        try:
            dsl = StrategyDSL.model_validate(strategy)
            return not validate_semantics(dsl) and bool(compile_to_ir(dsl).dslHash)
        except Exception:
            return False

    def run(
        self,
        opportunity: Mapping[str, Any],
        max_leverage: int,
        initial_population: Sequence[Mapping[str, Any]] | None = None,
        control_state: Callable[[], str] | None = None,
        mode: str = "ultra",
    ) -> FastCampaignOutcome:
        plan = AutomaticCampaignPlanner().plan(opportunity, max_leverage=max_leverage, mode=mode)
        symbol, interval = str(opportunity["symbol"]), str(opportunity["interval"])
        dataset_id = str(opportunity["dataset_id"])
        factory = SeedFactory(seed=self.seed)
        generated = factory.generate_population(
            plan.population, symbol=symbol, timeframe=interval
        )
        leverage_rng = random.Random(self.seed ^ 0x5F3759DF)
        for strategy in generated:
            strategy.setdefault("position", {})["leverage"] = leverage_rng.choice(
                plan.leverage_tiers
            )
        carried: list[dict[str, Any]] = []
        seen: set[str] = set()
        for candidate in initial_population or ():
            strategy = dict(candidate)
            if not self._valid_strategy(strategy):
                continue
            key = json.dumps(strategy, sort_keys=True, separators=(",", ":"))
            if key in seen:
                continue
            seen.add(key)
            carried.append(strategy)
            if len(carried) >= plan.population // 2:
                break
        initial = carried + generated[: max(0, plan.population - len(carried))]
        genetic = GeneticOperators(
            random.Random(self.seed), max_leverage=plan.leverage_tiers[-1]
        )

        def evaluate(strategy: dict[str, Any], attempt: int) -> CandidateResult:
            if not self._valid_strategy(strategy):
                return CandidateResult(strategy, 0.0, 0.0, False, mode=mode)
            try:
                result = self.engine.run_backtest(
                    strategy,
                    dataset_id=dataset_id,
                    start_fraction=0.0,
                    end_fraction=0.8,
                    fee_multiplier=1.0,
                    slippage_bps=2.0,
                    persist_artifacts=False,
                )
                # Every candidate is judged against the same declared search
                # budget; evaluation order must never change statistical validity.
                evidence = self._evidence(
                    result,
                    strategy,
                    opportunity,
                    plan.evaluation_budget,
                    0.0,
                    0.8,
                    max_drawdown_pct=float(result.get("maxDrawdownPct", 0.0)),
                )
                return CandidateResult(
                    strategy=dict(strategy),
                    final_equity=float(result.get("finalEquity", 0.0)),
                    evidence_score=evidence.score,
                    rankable=evidence.rankable,
                    bankrupt=bool(result.get("liquidated", False)),
                    evidence=evidence.to_dict(),
                    max_drawdown_pct=float(result.get("maxDrawdownPct", 0.0)),  # type: ignore[arg-type]
                    net_return_pct=float(result.get("netReturnPct", 0.0)),
                    mode=mode,
                )
            except Exception:
                return CandidateResult(strategy, 0.0, 0.0, False, mode=mode)

        def mutate(parent: dict[str, Any], rng: random.Random) -> dict[str, Any]:
            genetic.rng = rng
            child = genetic.mutate(parent)
            child.setdefault("position", {})["leverage"] = rng.choice(plan.leverage_tiers)
            return child

        def crossover(
            parent_a: dict[str, Any],
            parent_b: dict[str, Any],
            rng: random.Random,
        ) -> dict[str, Any]:
            genetic.rng = rng
            child = genetic.crossover(parent_a, parent_b)
            child.setdefault("position", {})["leverage"] = rng.choice(
                plan.leverage_tiers
            )
            return child

        def fresh(rng: random.Random) -> dict[str, Any]:
            fresh_factory = SeedFactory(seed=rng.randrange(1, 2**31 - 1))
            strategy = fresh_factory.generate_population(1, symbol=symbol, timeframe=interval)[0]
            strategy.setdefault("position", {})["leverage"] = rng.choice(plan.leverage_tiers)
            return strategy

        search = AggressiveOptimizationLoop(seed=self.seed).run(
            initial_population=initial,
            evaluate=evaluate,
            mutate=mutate,
            fresh=fresh,
            population_size=plan.population,
            generations=plan.generations,
            elite_count=plan.elite_count,
            stagnation_patience=plan.stagnation_patience,
            control_state=control_state,
            crossover=crossover,
        )
        if search.control_status:
            return FastCampaignOutcome(search.control_status, plan, search, None, None)
        if search.champion is None:
            return FastCampaignOutcome("NO_VALID_CANDIDATE", plan, search, None, None)

        def scenario_eval(strategy: Mapping[str, Any], scenario: ValidationScenario) -> ScenarioResult:
            try:
                result = self.engine.run_backtest(
                    dict(strategy),
                    dataset_id=dataset_id,
                    start_fraction=scenario.start_fraction,
                    end_fraction=scenario.end_fraction,
                    fee_multiplier=scenario.fee_multiplier,
                    slippage_bps=2.0 * scenario.slippage_multiplier,
                    persist_artifacts=False,
                )
                evidence = self._evidence(
                    result,
                    strategy,
                    opportunity,
                    search.evaluations,
                    scenario.start_fraction,
                    scenario.end_fraction,
                    max_drawdown_pct=float(result.get("maxDrawdownPct", 0.0)),
                )
                return ScenarioResult(
                    scenario,
                    float(result.get("netReturnPct", 0.0)),
                    float(result.get("maxDrawdownPct", 0.0)),
                    bool(result.get("liquidated", False)),
                    evidence.rankable,
                )
            except Exception:
                return ScenarioResult(scenario, -100.0, 100.0, True, False)

        validation = AdversarialValidator(seed=self.seed).validate(
            search.champion.strategy, scenario_eval
        )
        if not validation.passed:
            return FastCampaignOutcome(
                "FAILED_ADVERSARIAL_VALIDATION", plan, search, validation, None
            )
        champion = {
            "strategy": search.champion.strategy,
            "finalEquitySearch": search.champion.final_equity,
            "evidenceScore": search.champion.evidence_score,
            "validationScore": validation.score,
        }
        return FastCampaignOutcome("VALIDATED_CANDIDATE", plan, search, validation, champion)
