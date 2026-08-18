"""services/portfolio/portfolio_router.py
Router FastAPI para el PortfolioEngine y Asignación de Capital Multi-Activo.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from contracts.backtest import TradeLog
from contracts.portfolio import PortfolioAllocation, PortfolioRequest
from services.core.event_bus import PortfolioRebalancedEvent, event_bus
from services.portfolio.portfolio_engine import PortfolioEngine

router = APIRouter()

portfolio_engine_instance = PortfolioEngine()


class AllocateCapitalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request: PortfolioRequest
    asset_trades: Dict[str, List[TradeLog]]
    asset_point_values: Optional[Dict[str, float]] = Field(default_factory=dict)


@router.post("/allocate", response_model=PortfolioAllocation)
async def allocate_portfolio_capital(req: AllocateCapitalRequest) -> PortfolioAllocation:
    """Calcula la asignación óptima de pesos y contratos por sincronización temporal Epoch UTC."""
    try:
        allocation = portfolio_engine_instance.allocate_capital(
            request=req.request,
            asset_trades=req.asset_trades,
            asset_point_values=req.asset_point_values,
        )
        await event_bus.publish(PortfolioRebalancedEvent(allocation=allocation))
        return allocation
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
