"""services/validation/validation_router.py
Router FastAPI para Quant Validation Fabric (QVF) y Candidate Registry FSM.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from contracts.canonical_strategy import CanonicalStrategy, StrategyLifecycleStatus
from contracts.validation_contracts import (
    BalaExecutionRecord,
    EvidenceGateDecision,
    ValidationTrack,
)
from services.core.event_bus import CandidatePromotedEvent, ValidationCompletedEvent, event_bus
from services.validation.candidate_registry import (
    CandidateRegistry,
    InvalidStateTransitionError,
    StateTransitionRecord,
)
from services.validation.quant_validation_fabric import QuantValidationFabric

router = APIRouter()

fabric_instance = QuantValidationFabric()
registry_instance = CandidateRegistry()


class ValidationEvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    strategy_id: str
    track: ValidationTrack
    # Payload Fondeo
    is_trades: Optional[List[float]] = None
    oos_trades: Optional[List[float]] = None
    daily_pnls: Optional[List[float]] = None
    dsr_score: float = 2.5
    mc_ruin_pct: float = 0.0
    # Payload Ultra
    is_balas: Optional[List[BalaExecutionRecord]] = None
    oos_balas: Optional[List[BalaExecutionRecord]] = None


class TransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    strategy_id: str
    to_status: StrategyLifecycleStatus
    reason: str = Field(..., min_length=3)


@router.post("/evaluate", response_model=EvidenceGateDecision)
async def evaluate_strategy_gate(req: ValidationEvaluationRequest) -> EvidenceGateDecision:
    """Evalúa un candidato a través del Evidence Gate según su Execution Track."""
    payload: Dict[str, Any] = {}
    if req.track == ValidationTrack.TRACK_FONDEO:
        if req.is_trades is None or req.oos_trades is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="TRACK_FONDEO requiere 'is_trades' y 'oos_trades'.",
            )
        payload = {
            "is_trades": req.is_trades,
            "oos_trades": req.oos_trades,
            "daily_pnls": req.daily_pnls or [],
            "dsr_score": req.dsr_score,
            "mc_ruin_pct": req.mc_ruin_pct,
        }
    elif req.track == ValidationTrack.TRACK_ULTRA:
        if req.is_balas is None or req.oos_balas is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="TRACK_ULTRA requiere 'is_balas' y 'oos_balas'.",
            )
        payload = {
            "is_balas": req.is_balas,
            "oos_balas": req.oos_balas,
        }

    decision = fabric_instance.validate(req.strategy_id, req.track, payload)
    await event_bus.publish(ValidationCompletedEvent(decision=decision))
    return decision


@router.post("/registry/register", status_code=status.HTTP_201_CREATED)
async def register_candidate(strategy: CanonicalStrategy) -> Dict[str, Any]:
    """Registra una nueva estrategia canónica en la FSM."""
    try:
        registry_instance.register(strategy)
        return {
            "status": "REGISTERED",
            "strategy_id": strategy.strategy_id,
            "lifecycle_status": strategy.status.value,
            "sha256": strategy.compute_sha256(),
        }
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(err))


@router.post("/registry/transition", response_model=StateTransitionRecord)
async def transition_candidate_status(req: TransitionRequest) -> StateTransitionRecord:
    """Aplica una transición de estado discreto en la FSM."""
    try:
        record = registry_instance.transition(req.strategy_id, req.to_status, req.reason)
        await event_bus.publish(
            CandidatePromotedEvent(
                strategy_id=req.strategy_id,
                new_status=req.to_status.value,
                track="DUAL",
            )
        )
        return record
    except (KeyError, InvalidStateTransitionError) as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.get("/registry/status/{strategy_id}")
async def get_candidate_status(strategy_id: str) -> Dict[str, str]:
    """Obtiene el estado actual en la FSM para una estrategia."""
    try:
        current_status = registry_instance.get_status(strategy_id)
        return {"strategy_id": strategy_id, "status": current_status.value}
    except KeyError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))


@router.get("/registry/history/{strategy_id}", response_model=List[StateTransitionRecord])
async def get_candidate_history(strategy_id: str) -> List[StateTransitionRecord]:
    """Historial inmutable de transiciones de una estrategia."""
    return registry_instance.get_history(strategy_id)


@router.get("/registry/list")
async def list_candidates(status_filter: Optional[StrategyLifecycleStatus] = None) -> Dict[str, Any]:
    """Lista estrategias registradas, opcionalmente filtradas por estado."""
    if status_filter:
        ids = registry_instance.list_by_status(status_filter)
        return {"status": status_filter.value, "count": len(ids), "strategy_ids": ids}
    return {
        status_enum.value: registry_instance.list_by_status(status_enum)
        for status_enum in StrategyLifecycleStatus
    }
