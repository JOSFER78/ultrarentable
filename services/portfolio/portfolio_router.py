"""services/portfolio/portfolio_router.py
Router FastAPI para PortfolioEngine, MetaStrategyEngine y Debate Multi-Agente de Portafolio.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Literal, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field

from contracts.backtest import TradeLog
from contracts.portfolio import PortfolioAllocation, PortfolioRequest
from services.core.event_bus import PortfolioRebalancedEvent, event_bus
from services.portfolio.portfolio_engine import PortfolioEngine
from services.portfolio.meta_strategy_engine import MetaStrategyEngine, DuplicateAssetError
from services.semantic_ai.portfolio_debate_engine import PortfolioDebateEngine

router = APIRouter()

portfolio_engine_instance = PortfolioEngine()
meta_strategy_engine_instance = MetaStrategyEngine()
portfolio_debate_engine_instance = PortfolioDebateEngine()


class AllocateCapitalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request: PortfolioRequest
    asset_trades: Dict[str, List[TradeLog]]
    asset_point_values: Optional[Dict[str, float]] = Field(default_factory=dict)


class GenerateMetaEnsembleRequest(BaseModel):
    portfolio_id: Optional[str] = None
    route: Literal["ULTRA", "FONDEO"] = "ULTRA"
    strategies: List[Dict[str, Any]]
    allocation_method: Literal["INVERSE_VOLATILITY", "RISK_PARITY", "EQUAL_WEIGHT"] = "INVERSE_VOLATILITY"
    total_capital_usd: Optional[float] = None
    custom_name: Optional[str] = None


class DebateMetaEnsembleRequest(BaseModel):
    portfolio_id: str
    route: Literal["ULTRA", "FONDEO"] = "ULTRA"
    strategies: List[Dict[str, Any]]
    meta_metrics: Dict[str, Any]


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


@router.post("/meta-ensemble/generate")
async def generate_meta_ensemble(req: GenerateMetaEnsembleRequest) -> Dict[str, Any]:
    """Genera, simula y evalúa una Estrategia de Estrategias con validación de no duplicidad de activos."""
    portfolio_id = req.portfolio_id or f"META_{req.route}_{uuid.uuid4().hex[:6].upper()}"
    try:
        meta_result = meta_strategy_engine_instance.assemble_meta_portfolio(
            portfolio_id=portfolio_id,
            route=req.route,
            strategies=req.strategies,
            allocation_method=req.allocation_method,
            total_capital_usd=req.total_capital_usd,
            custom_name=req.custom_name,
        )
        
        # Ejecutar debate de los 5 agentes automáticamente para adjuntarlo al snapshot
        debate_res = portfolio_debate_engine_instance.conduct_portfolio_debate(
            route=req.route,
            portfolio_id=portfolio_id,
            strategies=req.strategies,
            meta_metrics=meta_result,
        )
        meta_result["debate"] = debate_res
        meta_result["consensus_score"] = debate_res.get("consensus_score", 95.0)

        # Actualizar persistencia con debate
        meta_strategy_engine_instance._persist_meta_portfolio(meta_result)

        return meta_result
    except DuplicateAssetError as dup_err:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(dup_err))
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error ensamblando portafolio: {exc}")


@router.post("/meta-ensemble/debate")
async def debate_meta_ensemble(req: DebateMetaEnsembleRequest) -> Dict[str, Any]:
    """Ejecuta el debate cuantitativo de los 5 agentes sobre un ensamble de estrategias."""
    try:
        debate_result = portfolio_debate_engine_instance.conduct_portfolio_debate(
            route=req.route,
            portfolio_id=req.portfolio_id,
            strategies=req.strategies,
            meta_metrics=req.meta_metrics,
        )
        return debate_result
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error en debate de portafolio: {exc}")


@router.get("/meta-ensembles")
async def list_meta_ensembles(route: Optional[str] = Query(None)) -> List[Dict[str, Any]]:
    """Lista todos los meta-portafolios persistidos."""
    return meta_strategy_engine_instance.list_meta_portfolios(route=route)
