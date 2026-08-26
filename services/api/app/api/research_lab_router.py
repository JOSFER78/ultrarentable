"""Compatibility router for the Research Lab.

The legacy 8-role implementation is no longer a source of truth. These endpoints
now delegate to the real-only research daemon and return research state/proposals.
No endpoint here certifies a strategy.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from services.api.app.db.database import CandidateModel, get_db
from services.engine_version import CURRENT_ENGINE_VERSION
from services.optimization.continuous_research_daemon import continuous_research_daemon
from services.semantic_ai.learning_store import learning_store

research_lab_router = APIRouter(prefix="/research-lab", tags=["Quantitative Research Lab"])


class SynthesizeRequest(BaseModel):
    strategy_id: str
    debate_id: str


@research_lab_router.post("/evolve/{strategy_id}")
def evolve_strategy(strategy_id: str) -> Dict[str, Any]:
    """Run the real-only evolutionary research loop for an existing candidate."""
    result = continuous_research_daemon.optimize_candidate_closed_loop(
        candidate_id=strategy_id,
        max_iterations=3,
        generation_round=1,
    )
    return {
        "strategy_id": strategy_id,
        "engine_version": CURRENT_ENGINE_VERSION,
        "mode": "REAL_ONLY",
        "certification_owned_by": "canonical_validation_pipeline",
        "result": result,
    }


@research_lab_router.post("/debate/{strategy_id}")
def trigger_research_debate(strategy_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Compatibility endpoint: returns evidence-backed research direction, not certification."""
    candidate = db.query(CandidateModel).filter(CandidateModel.candidate_id == strategy_id).first()
    if candidate is None:
        raise HTTPException(status_code=404, detail=f"Candidato {strategy_id} no encontrado.")
    result = continuous_research_daemon.optimize_candidate_closed_loop(
        candidate_id=strategy_id,
        max_iterations=1,
        generation_round=1,
    )
    return {
        "status": result.get("status"),
        "strategy_id": strategy_id,
        "engine_version": CURRENT_ENGINE_VERSION,
        "mode": "REAL_ONLY",
        "research": result,
    }


@research_lab_router.post("/synthesize")
def synthesize_strategy_mutation(payload: SynthesizeRequest) -> Dict[str, Any]:
    """Compatibility endpoint. Mutation generation is now performed by StrategyEvolutionEngine."""
    result = continuous_research_daemon.optimize_candidate_closed_loop(
        candidate_id=payload.strategy_id,
        max_iterations=1,
        generation_round=1,
    )
    return {
        "status": result.get("status"),
        "strategy_id": payload.strategy_id,
        "debate_id": payload.debate_id,
        "engine_version": CURRENT_ENGINE_VERSION,
        "mode": "REAL_ONLY",
        "mutation_result": result,
        "note": "No certification or synthetic metric is produced by this endpoint.",
    }


@research_lab_router.get("/proposals")
def list_research_proposals() -> List[Dict[str, Any]]:
    rows = learning_store.get_proposals()
    return [r.model_dump() for r in rows]


@research_lab_router.get("/experiments")
def list_research_experiments() -> List[Dict[str, Any]]:
    rows = learning_store.get_experiments()
    return [r.model_dump() for r in rows]
