"""Local Campaign Orchestrator for Autonomous Strategy Search."""
from __future__ import annotations

import json
import logging
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from services.api.app.config import DATA_DIR
from services.api.app.db.database import (
    CampaignModel,
    DatasetModel,
    InstrumentModel,
    InstrumentRuleSnapshotModel,
    StrategyModel,
    SessionLocal,
)
from services.api.app.dsl.engine import StrategyDSL, compile_to_ir, canonical_hash, canonical_json
from services.api.app.engine.fast_engine import FastEngine, FastEngineException
from services.api.app.factory.genetic import GeneticOperators
from services.api.app.factory.grammar import TypedGrammar
from services.api.app.factory.optimizer import OptunaOptimizer
from services.api.app.factory.repairer import DirectedRepairer
from services.api.app.factory.seed_factory import SeedFactory
from services.api.app.factory.selection import CandidateEvaluation, KamikazeSelection

logger = logging.getLogger(__name__)


class AutonomousCampaignOrchestrator:
    """Local, pauseable, resumeable autonomous campaign orchestrator."""

    def __init__(self, campaign_id: str):
        self.campaign_id = campaign_id

    def run_generation_cycle(
        self,
        *,
        symbol: str = "ETH-USDT",
        timeframe: str = "1h",
        population_size: int = 10,
        generations_count: int = 2,
        seed: int = 42,
        mode: str = "EXPLORE",  # EXPLORE, IMPROVE, REGIME_SEARCH
        target_multiplier: float = 11.0,
    ) -> dict[str, Any]:
        """Execute a full autonomous search cycle using FastAPI local DB session."""
        db = SessionLocal()
        try:
            campaign = db.query(CampaignModel).filter(CampaignModel.campaign_id == self.campaign_id).first()
            if not campaign:
                campaign = CampaignModel(
                    campaign_id=self.campaign_id,
                    name=f"Autonomous_{symbol}_{timeframe}",
                    symbol=symbol,
                    interval=timeframe,
                    population_size=population_size,
                    generations_count=generations_count,
                    current_generation=0,
                    seed=seed,
                    status="GENERATING",
                )
                db.merge(campaign)
                db.commit()

            # Ensure dataset exists and is APPROVED
            datasets = (
                db.query(DatasetModel)
                .filter(DatasetModel.symbol == symbol, DatasetModel.interval == timeframe, DatasetModel.status == "APPROVED")
                .all()
            )
            if not datasets:
                campaign.status = "FAILED"
                db.commit()
                return {
                    "campaignId": self.campaign_id,
                    "status": "FAILED",
                    "reason": f"NO_APPROVED_DATASET_FOR_{symbol}_{timeframe}",
                }

            dataset_id = datasets[0].dataset_id

            # Ensure fee snapshot exists for symbol
            inst = db.query(InstrumentModel).filter(InstrumentModel.symbol == symbol).first()
            if not inst or inst.maker_fee_rate is None or inst.taker_fee_rate is None:
                # Store real fee snapshot for ETH-USDT if not present
                db.merge(
                    InstrumentModel(
                        symbol=symbol,
                        asset=symbol.split("-")[0],
                        currency="USDT",
                        maker_fee_rate=0.0002,
                        taker_fee_rate=0.0005,
                        status=1,
                    )
                )
                db.commit()

            rule_snapshot = (
                db.query(InstrumentRuleSnapshotModel)
                .filter(InstrumentRuleSnapshotModel.symbol == symbol)
                .order_by(InstrumentRuleSnapshotModel.captured_at.desc())
                .first()
            )
            leverage_cap = min(
                500, max(1, int(rule_snapshot.max_leverage if rule_snapshot else 20))
            )
            leverage_rng = random.Random(seed ^ 0x5F3759DF)
            seed_factory = SeedFactory(seed=seed)
            genetic = GeneticOperators(
                rng=random.Random(seed), max_leverage=leverage_cap
            )
            repairer = DirectedRepairer(rng=random.Random(seed))
            selection = KamikazeSelection()
            fast_engine = FastEngine(db)

            # Generate initial population
            population_dsls = seed_factory.generate_population(population_size, symbol=symbol, timeframe=timeframe)
            for strategy in population_dsls:
                strategy.setdefault("position", {})["leverage"] = leverage_rng.randint(
                    1, leverage_cap
                )
            current_evaluations: list[CandidateEvaluation] = []
            target_hits: list[dict[str, Any]] = []

            for gen in range(generations_count):
                campaign.current_generation = gen + 1
                campaign.status = "FAST_EVALUATING"
                db.commit()

                gen_evaluations: list[CandidateEvaluation] = []
                repaired_candidates: list[dict[str, Any]] = []
                generation_population = list(population_dsls[:population_size])
                for idx, strat_dict in enumerate(generation_population):
                    try:
                        parsed = StrategyDSL(**strat_dict)
                        ir = compile_to_ir(parsed)
                        dsl_hash = canonical_hash(parsed)

                        # Save strategy to DB
                        strat_id = f"strat_{dsl_hash[:16]}"
                        db.merge(
                            StrategyModel(
                                strategy_id=strat_id,
                                name=parsed.metadata.name,
                                version="1.0.0",
                                family=parsed.metadata.family.value,
                                author="AutonomousFactory",
                                canonical_hash=dsl_hash,
                                generation=gen + 1,
                                dsl_json=canonical_json(parsed),
                                validation_status="COMPILED",
                            )
                        )
                        db.commit()

                        # Execute Fast Engine
                        res = fast_engine.execute(
                            strategy_dsl=parsed,
                            compiled_ir=ir,
                            dataset_id=dataset_id,
                            initial_capital=10000.0,
                            persist_artifacts=False,
                        )

                        metrics = res["metrics"]
                        eval_obj = CandidateEvaluation(
                            strategy_dict=strat_dict,
                            canonical_hash=dsl_hash,
                            status=res["status"],
                            final_equity=metrics["final_equity"],
                            initial_capital=10000.0,
                            net_return_pct=metrics["net_return_pct"],
                        )
                        gen_evaluations.append(eval_obj)

                        # Check Target Hit (>= 11x)
                        if metrics["final_equity"] >= 10000.0 * target_multiplier:
                            target_hits.append({
                                "strategy_id": strat_id,
                                "canonical_hash": dsl_hash,
                                "final_equity": metrics["final_equity"],
                                "net_return_pct": metrics["net_return_pct"],
                                "tag": "FAST_TARGET_HIT",
                            })

                    except FastEngineException as exc:
                        # Queue repairs for the next finite generation. Never mutate
                        # the list currently being iterated.
                        repaired_dict = repairer.repair(strat_dict, exc.code)
                        repaired_dict.setdefault("position", {})["marginMode"] = "ISOLATED"
                        repaired_candidates.append(repaired_dict)
                    except Exception as exc:
                        continue

                # Evolutionary Selection and Mutation for next generation
                survivors = selection.filter_survivors(gen_evaluations)
                next_pop: list[dict[str, Any]] = [
                    survivor.strategy_dict
                    for survivor in survivors[: max(1, population_size // 2)]
                ]
                for repaired in repaired_candidates:
                    if len(next_pop) >= population_size:
                        break
                    next_pop.append(repaired)

                # Fill a bounded next generation. If no candidate survived, create
                # fresh isolated candidates instead of retrying a rejected batch.
                while len(next_pop) < population_size:
                    if survivors:
                        parent_a = random.choice(survivors).strategy_dict
                        if len(survivors) > 1 and random.random() < 0.5:
                            parent_b = random.choice(survivors).strategy_dict
                            child = genetic.crossover(parent_a, parent_b)
                        else:
                            child = genetic.mutate(parent_a)
                    else:
                        child = seed_factory.generate_population(
                            1, symbol=symbol, timeframe=timeframe
                        )[0]
                    child.setdefault("position", {})["marginMode"] = "ISOLATED"
                    child["position"]["leverage"] = leverage_rng.randint(1, leverage_cap)
                    next_pop.append(child)
                population_dsls = next_pop

            campaign.status = "COMPLETED"
            db.commit()

            return {
                "campaignId": self.campaign_id,
                "status": "COMPLETED",
                "generationsCompleted": generations_count,
                "totalEvaluations": len(gen_evaluations),
                "targetHits": target_hits,
            }
        finally:
            db.close()
