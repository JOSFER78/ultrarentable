"""services/paper/paper_router.py
Router FastAPI para el PaperSandboxEngine e IncubationEvaluator (14 días).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from contracts.backtest import BacktestResult, TradeLog
from contracts.canonical_strategy import CanonicalStrategy
from services.paper.incubation_evaluator import IncubationEvaluator, IncubationReport
from services.paper.paper_sandbox_engine import (
    PaperPosition,
    PaperSandboxEngine,
    PositionSide,
)
from services.validation.validation_router import registry_instance

router = APIRouter()

sandbox_instance = PaperSandboxEngine()
incubation_evaluator_instance = IncubationEvaluator()


class OpenPaperPositionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    strategy: CanonicalStrategy
    side: PositionSide
    market_price: float = Field(..., gt=0.0)
    quantity: float = Field(..., gt=0.0)
    timestamp_ms: int
    stop_loss_ticks: Optional[int] = None
    take_profit_ticks: Optional[int] = None


class PriceTickRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    strategy: CanonicalStrategy
    current_price: float = Field(..., gt=0.0)
    timestamp_ms: int


class EvaluateIncubationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    strategy: CanonicalStrategy
    backtest_baseline: BacktestResult
    paper_trades: List[TradeLog]
    observation_start_ms: int
    current_time_ms: int


@router.post("/open", response_model=PaperPosition)
async def open_paper_position(req: OpenPaperPositionRequest) -> PaperPosition:
    """Abre una posición en el Sandbox de Paper Trading con slippage y latencia."""
    return sandbox_instance.open_position(
        strategy=req.strategy,
        side=req.side,
        market_price=req.market_price,
        quantity=req.quantity,
        timestamp_ms=req.timestamp_ms,
        stop_loss_ticks=req.stop_loss_ticks,
        take_profit_ticks=req.take_profit_ticks,
    )


@router.post("/price-tick")
async def update_paper_price_tick(req: PriceTickRequest) -> Dict[str, Any]:
    """Actualiza precio de mercado y comprueba disparos de SL / TP."""
    pos, closed_trade = sandbox_instance.update_market_price(
        strategy=req.strategy,
        current_price=req.current_price,
        timestamp_ms=req.timestamp_ms,
    )
    return {
        "position": pos,
        "closed_trade": closed_trade,
    }


@router.get("/position/{strategy_id}")
async def get_paper_position(strategy_id: str) -> PaperPosition:
    """Consulta la posición actual y el historial de trades en el sandbox."""
    try:
        return sandbox_instance.get_position(strategy_id)
    except KeyError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))


@router.post("/close-session")
async def force_close_session(req: PriceTickRequest) -> Dict[str, Any]:
    """Fuerza el cierre de posición al final de sesión (Regla Prop CME)."""
    closed_trade = sandbox_instance.close_all_session_end(
        strategy=req.strategy,
        current_price=req.current_price,
        timestamp_ms=req.timestamp_ms,
    )
    return {"closed_trade": closed_trade}


@router.post("/evaluate-incubation", response_model=IncubationReport)
async def evaluate_incubation_progress(req: EvaluateIncubationRequest) -> IncubationReport:
    """Evalúa la estabilidad OOS en vivo y decide si promover a LIVE_ACTIVE tras 14 días."""
    return incubation_evaluator_instance.evaluate(
        strategy=req.strategy,
        backtest_baseline=req.backtest_baseline,
        paper_trades=req.paper_trades,
        observation_start_ms=req.observation_start_ms,
        current_time_ms=req.current_time_ms,
        registry=registry_instance,
    )
