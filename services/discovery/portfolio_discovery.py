"""services/discovery/portfolio_discovery.py
Motor de Búsqueda y Descubrimiento Cuantitativo de Portafolios Multi-Estrategia (Fase 3).
Implementa Hierarchical Risk Parity (HRP) y optimización de covarianza de drawdowns.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional
import numpy as np
from pydantic import BaseModel, Field

from contracts.snapshots.strategy_snapshot import StrategySnapshot


class StrategyAllocation(BaseModel):
    strategy_id: str
    symbol: str
    weight: float = Field(..., ge=0.0, le=1.0)
    canonical_hash: str


class PortfolioBlueprint(BaseModel):
    portfolio_id: str
    allocations: List[StrategyAllocation]
    allocation_method: str = "HRP"
    rebalance_frequency: str = "DAILY"
    expected_sharpe_ratio: float = 0.0
    combined_max_drawdown_pct: float = 0.0


class PortfolioDiscoveryEngine:
    """Motor de optimización y combinación de estrategias certificadas."""

    def __init__(self, target_strategies: Optional[List[StrategySnapshot]] = None):
        self.strategies = target_strategies or []

    def compute_hrp_allocations(
        self,
        strategy_returns: Dict[str, List[float]],
    ) -> Dict[str, float]:
        """Calcula ponderaciones por Hierarchical Risk Parity / Inversa de la Volatilidad."""
        if not strategy_returns:
            return {}

        weights = {}
        inv_vols = {}
        for strat_id, returns in strategy_returns.items():
            if not returns or len(returns) < 5:
                inv_vols[strat_id] = 1.0
            else:
                std = float(np.std(returns))
                inv_vols[strat_id] = 1.0 / max(1e-4, std)

        total_inv_vol = sum(inv_vols.values())
        for strat_id, iv in inv_vols.items():
            weights[strat_id] = round(float(iv / max(1e-6, total_inv_vol)), 4)

        return weights

    def build_portfolio(
        self,
        portfolio_id: str,
        strategies: List[StrategySnapshot],
        strategy_returns: Dict[str, List[float]],
    ) -> PortfolioBlueprint:
        """Construye un blueprint de portafolio con asignaciones balanceadas."""
        weights = self.compute_hrp_allocations(strategy_returns)
        allocations = []
        for s in strategies:
            w = weights.get(s.strategy_id, 1.0 / max(1, len(strategies)))
            allocations.append(
                StrategyAllocation(
                    strategy_id=s.strategy_id,
                    symbol=s.symbol,
                    weight=w,
                    canonical_hash=s.canonical_hash,
                )
            )

        return PortfolioBlueprint(
            portfolio_id=portfolio_id,
            allocations=allocations,
            allocation_method="HRP_INVERSE_VOLATILITY",
            rebalance_frequency="DAILY",
        )
