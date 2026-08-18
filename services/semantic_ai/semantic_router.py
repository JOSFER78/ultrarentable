"""services/semantic_ai/semantic_router.py
Router FastAPI para el Semantic Quant Engine y FailureKnowledgeDB.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from contracts.canonical_strategy import CanonicalStrategy, ExecutionTrack
from contracts.validation_contracts import ValidationTrack
from services.core.event_bus import StrategyGeneratedEvent, event_bus
from services.semantic_ai.failure_knowledge import (
    FailureCategory,
    FailureKnowledgeDB,
    FailureRecord,
)
from services.semantic_ai.semantic_engine import SemanticQuantEngine

router = APIRouter()

failure_db_instance = FailureKnowledgeDB()
semantic_engine_instance = SemanticQuantEngine(failure_db=failure_db_instance)


class GenerateCandidateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    symbol: str = "NQ"
    timeframe: str = "1h"
    track: ExecutionTrack = ExecutionTrack.TRACK_FONDEO


class RecordFailureRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    strategy: CanonicalStrategy
    track: ValidationTrack
    category: FailureCategory
    rejection_reasons: List[str]
    market_regime: str = "UNKNOWN"
    metrics_snapshot: Dict[str, float] = Field(default_factory=dict)


@router.post("/generate", response_model=CanonicalStrategy)
async def generate_semantic_candidate(req: GenerateCandidateRequest) -> CanonicalStrategy:
    """Genera una estrategia canónica a partir de semántica y restricciones de track."""
    candidate = semantic_engine_instance.generate_candidate(
        symbol=req.symbol, timeframe=req.timeframe, track=req.track
    )
    await event_bus.publish(StrategyGeneratedEvent(strategy=candidate))
    return candidate


@router.post("/improve", response_model=CanonicalStrategy)
async def improve_candidate(strategy: CanonicalStrategy) -> CanonicalStrategy:
    """Muta y mejora una estrategia evitando patrones fallidos indexados."""
    improved = semantic_engine_instance.improve_candidate(strategy)
    if not improved:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No fue posible mutar la estrategia sin colisionar con la Memoria de Fallos.",
        )
    return improved


@router.post("/critique")
async def critique_candidate(strategy: CanonicalStrategy) -> Dict[str, Any]:
    """Audita una estrategia contra la base de fallos y reglas de track."""
    passed, warnings = semantic_engine_instance.critic.critique(strategy)
    return {
        "strategy_id": strategy.strategy_id,
        "approved": passed,
        "warnings": warnings,
        "blacklisted_rule_tree": failure_db_instance.is_rule_tree_blacklisted(strategy.rules),
    }


@router.post("/describe")
async def describe_candidate(strategy: CanonicalStrategy) -> Dict[str, Any]:
    """Traduce AST y parámetros a descripción semántica estructurada."""
    return semantic_engine_instance.interpreter.describe_strategy(strategy)


@router.get("/failures/stats")
async def get_failure_statistics() -> Dict[str, Any]:
    """Estadísticas analíticas de fallos y combinaciones prohibidas."""
    return failure_db_instance.get_failure_statistics()


@router.get("/failures/recent", response_model=List[FailureRecord])
async def get_recent_failures(limit: int = 20) -> List[FailureRecord]:
    """Lista las últimas autopsias cuantitativas registradas."""
    return failure_db_instance.get_recent_failures(limit=limit)


@router.post("/failures/record", response_model=FailureRecord)
async def record_failure_autopsy(req: RecordFailureRequest) -> FailureRecord:
    """Registra un fallo cuantitativo e indexa la firma en la lista de exclusión."""
class DebateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    strategy_id: str
    name: str = "Quantitative Champion Strategy"
    symbol: str = "SOL-USDT"
    timeframe: str = "15m"
    route: str = "ULTRA"
    profit_factor_oos: float = 1.35
    max_dd_pct: float = 4.2
    win_rate: float = 40.0


@router.post("/debate")
async def debate_strategy_agents(req: DebateRequest) -> Dict[str, Any]:
    """Ejecuta el debate multi-agente cuantitativo (Interpreter, Critic, Improver, Regime, Adversarial)."""
    return semantic_engine_instance.debate_candidate(
        strategy_id=req.strategy_id,
        name=req.name,
        symbol=req.symbol,
        timeframe=req.timeframe,
        route=req.route,
        pf_oos=req.profit_factor_oos,
        max_dd_pct=req.max_dd_pct,
        win_rate=req.win_rate,
    )


class EnsembleDebateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    route: str = "ULTRA"
    strategies: List[Dict[str, Any]]


@router.post("/ensemble-debate")
async def debate_ensemble_portfolio(req: EnsembleDebateRequest) -> Dict[str, Any]:
    """Ejecuta el debate multi-agente para la creación y sinergia de una Meta-Estrategia Ensamblada."""
    return semantic_engine_instance.ensemble_debate(
        route=req.route,
        strategies=req.strategies,
    )

