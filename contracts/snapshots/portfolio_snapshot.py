"""contracts/snapshots/portfolio_snapshot.py
Source of Truth Inmutable de Portafolio Multi-Estrategia (Fase 7).
Registra las asignaciones, correlaciones reales y la equidad combinada punto a punto.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class PortfolioStrategyAllocation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    strategy_id: str
    symbol: str
    weight: float = Field(..., ge=0.0, le=1.0)
    canonical_hash: str


class PortfolioSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    portfolio_id: str = Field(..., description="ID unívoco del portafolio")
    canonical_hash: str = Field(..., description="Hash SHA256 inmutable de la configuración")
    allocation_method: Literal["HRP", "EQUAL_WEIGHT", "INVERSE_VOLATILITY", "RISK_PARITY"]
    rebalance_frequency: Literal["DAILY", "WEEKLY", "BAR_BY_BAR"]
    strategies: List[PortfolioStrategyAllocation]
    correlation_matrix: Dict[str, Dict[str, float]]
    drawdown_correlation_matrix: Dict[str, Dict[str, float]]
    total_capital_usd: float
    combined_net_profit_usd: float
    combined_profit_factor: float
    combined_max_drawdown_pct: float
    diversification_ratio: float
    combined_equity_curve: List[float]
    created_at_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def create_and_hash(
        cls,
        portfolio_id: str,
        allocation_method: Literal["HRP", "EQUAL_WEIGHT", "INVERSE_VOLATILITY", "RISK_PARITY"],
        rebalance_frequency: Literal["DAILY", "WEEKLY", "BAR_BY_BAR"],
        strategies: List[PortfolioStrategyAllocation],
        correlation_matrix: Dict[str, Dict[str, float]],
        drawdown_correlation_matrix: Dict[str, Dict[str, float]],
        total_capital_usd: float,
        combined_net_profit_usd: float,
        combined_profit_factor: float,
        combined_max_drawdown_pct: float,
        diversification_ratio: float,
        combined_equity_curve: List[float],
    ) -> PortfolioSnapshot:
        content_dict = {
            "portfolio_id": portfolio_id,
            "allocation_method": allocation_method,
            "rebalance_frequency": rebalance_frequency,
            "strategies": [s.model_dump() for s in strategies],
            "correlation_matrix": correlation_matrix,
            "drawdown_correlation_matrix": drawdown_correlation_matrix,
            "total_capital_usd": total_capital_usd,
        }
        canonical_str = json.dumps(content_dict, sort_keys=True, separators=(",", ":"))
        canonical_hash = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

        return cls(
            portfolio_id=portfolio_id,
            canonical_hash=canonical_hash,
            allocation_method=allocation_method,
            rebalance_frequency=rebalance_frequency,
            strategies=strategies,
            correlation_matrix=correlation_matrix,
            drawdown_correlation_matrix=drawdown_correlation_matrix,
            total_capital_usd=total_capital_usd,
            combined_net_profit_usd=combined_net_profit_usd,
            combined_profit_factor=combined_profit_factor,
            combined_max_drawdown_pct=combined_max_drawdown_pct,
            diversification_ratio=diversification_ratio,
            combined_equity_curve=combined_equity_curve,
        )
