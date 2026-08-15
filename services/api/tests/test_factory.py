"""Mandatory unit tests for Phase F — Autonomous Strategy Factory & Campaigns Autopilot."""
from __future__ import annotations

import json
import random
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from services.api.app.db.database import (
    CampaignModel,
    DatasetModel,
    InstrumentModel,
    StrategyModel,
    engine as db_engine,
    get_db,
    init_db,
)
from services.api.app.factory.genetic import GeneticOperators
from services.api.app.factory.grammar import TypedGrammar
from services.api.app.factory.orchestrator import AutonomousCampaignOrchestrator
from services.api.app.factory.repairer import DirectedRepairer
from services.api.app.factory.seed_factory import SeedFactory
from services.api.app.factory.selection import CandidateEvaluation, KamikazeSelection


@pytest.fixture(scope="module")
def db_session() -> Session:
    init_db()
    session = Session(bind=db_engine)
    yield session
    session.close()


def test_typed_grammar_generates_valid_strategy_ast() -> None:
    """Grammar must generate valid DSL v1.0.0 trees by construction."""
    grammar = TypedGrammar(rng=random.Random(123))
    strat = grammar.generate_strategy(symbol="ETH-USDT", timeframe="1h")
    assert strat["dslVersion"] == "1.0.0"
    assert strat["market"]["symbol"] == "ETH-USDT"
    assert "longEntry" in strat["signals"]
    assert "shortEntry" in strat["signals"]


def test_seed_factory_generates_population() -> None:
    """SeedFactory must produce initial population with requested size."""
    sf = SeedFactory(seed=42)
    pop = sf.generate_population(5, symbol="ETH-USDT", timeframe="1h")
    assert len(pop) == 5
    assert all("dslVersion" in s for s in pop)


def test_genetic_operators_mutation_and_crossover() -> None:
    """Genetic operators must mutate and crossover strategies cleanly."""
    sf = SeedFactory(seed=42)
    pop = sf.generate_population(2, symbol="ETH-USDT", timeframe="1h")
    genetic = GeneticOperators(rng=random.Random(42))

    mutated = genetic.mutate(pop[0])
    assert mutated["metadata"]["origin"] == "MUTATION"
    assert len(mutated["metadata"]["parents"]) == 1

    crossed = genetic.crossover(pop[0], pop[1])
    assert crossed["metadata"]["origin"] == "CROSSOVER"
    assert len(crossed["metadata"]["parents"]) == 2


def test_directed_repairer() -> None:
    """Directed Repairer must modify failed strategy parameters."""
    sf = SeedFactory(seed=42)
    strat = sf.create_template_strategy(0)
    strat["position"]["leverage"] = 20

    repairer = DirectedRepairer()
    repaired = repairer.repair(strat, "LIQUIDATED")

    assert repaired["position"]["leverage"] < 20
    assert repaired["position"]["marginMode"] == "ISOLATED"


def test_kamikaze_selection_filters_failures() -> None:
    """Kamikaze selection must discard failed / liquidated strategies."""
    evals = [
        CandidateEvaluation(
            strategy_dict={},
            canonical_hash="hash1",
            status="COMPLETED",
            final_equity=15000.0,
            initial_capital=10000.0,
            net_return_pct=50.0,
        ),
        CandidateEvaluation(
            strategy_dict={},
            canonical_hash="hash2",
            status="LIQUIDATED",
            final_equity=0.0,
            initial_capital=10000.0,
            net_return_pct=-100.0,
        ),
    ]

    selection = KamikazeSelection()
    survivors = selection.filter_survivors(evals)

    assert len(survivors) == 1
    assert survivors[0].canonical_hash == "hash1"


def test_autonomous_campaign_orchestration(db_session: Session) -> None:
    """Full autonomous campaign orchestration cycle execution."""
    manifests = list(Path("data/normalized").glob("*_manifest.json"))
    assert manifests, "Approved dataset manifest required for test"

    campaign_id = "cmp_test_auto_unit"
    orchestrator = AutonomousCampaignOrchestrator(campaign_id)

    res = orchestrator.run_generation_cycle(
        symbol="ETH-USDT",
        timeframe="1h",
        population_size=4,
        generations_count=2,
        seed=42,
    )

    assert res["status"] == "COMPLETED"
    assert res["generationsCompleted"] == 2
    assert "totalEvaluations" in res
