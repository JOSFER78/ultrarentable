"""services/api/app/api/research_lab_router.py
Router FastAPI para el Laboratorio Cuantitativo de Investigación, Debate de 8 Roles y Síntesis AST.
Especificación oficial según Sección 7 y 8 del Informe Maestro v5.3.0.
"""

from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from contracts.research_contracts import (
    ResearchDebateResponse,
    ResearchSynthesisResponse,
)
from services.api.app.db.database import get_db
from services.research.research_lab import QuantitativeResearchLab
from services.semantic_ai.learning_store import learning_store


research_lab_router = APIRouter(prefix="/research-lab", tags=["Quantitative Research Lab (8 Roles)"])


class SynthesizeRequest(BaseModel):
    strategy_id: str
    debate_id: str


@research_lab_router.post("/debate/{strategy_id}", response_model=ResearchDebateResponse)
def trigger_research_debate(strategy_id: str, db: Session = Depends(get_db)) -> ResearchDebateResponse:
    """Inicia un debate estructurado entre los 8 roles especializados bajo protocolo Blind Scope."""
    lab = QuantitativeResearchLab(db)
    return lab.run_research_debate(strategy_id)


@research_lab_router.post("/synthesize", response_model=ResearchSynthesisResponse)
def synthesize_strategy_mutation(payload: SynthesizeRequest, db: Session = Depends(get_db)) -> ResearchSynthesisResponse:
    """Sintetiza una nueva mutación StrategyDSL semánticamente válida basada en el consenso del debate."""
    lab = QuantitativeResearchLab(db)
    return lab.synthesize_reprogramming(payload.strategy_id, payload.debate_id)


@research_lab_router.get("/proposals")
def list_research_proposals() -> List[Dict[str, Any]]:
    """Lista las propuestas de investigación persistidas en LearningStore."""
    rows = learning_store.get_proposals()
    return [r.model_dump() for r in rows]


@research_lab_router.get("/experiments")
def list_research_experiments() -> List[Dict[str, Any]]:
    """Lista los experimentos y resultados de investigación cuantitativa."""
    rows = learning_store.get_experiments()
    return [r.model_dump() for r in rows]
