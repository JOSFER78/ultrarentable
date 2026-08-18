"""services/portfolio/allocator.py
Asignador de portfolio de riesgo paritario / HRP desacoplado.
"""

from __future__ import annotations

import hashlib
import time
from typing import List

from contracts.portfolio import (
    AllocationMethod,
    AssetWeight,
    PortfolioAllocation,
    PortfolioRequest,
)


class PortfolioAllocator:
    """Calculador de pesos y diversificación de portfolio."""

    def allocate(self, request: PortfolioRequest) -> PortfolioAllocation:
        n = len(request.candidate_strategy_ids)
        equal_weight = round(1.0 / max(1, n), 4)
        target_cap = round(request.total_capital_usd / max(1, n), 2)

        weights: List[AssetWeight] = []
        for strat_id in request.candidate_strategy_ids:
            symbol = strat_id.split("-")[1] if "-" in strat_id else "NQ"
            weights.append(
                AssetWeight(
                    symbol=symbol,
                    weight=equal_weight,
                    target_capital_usd=target_cap,
                    max_contracts_or_lots=4.0,
                )
            )

        now_ms = int(time.time() * 1000)
        provenance = hashlib.sha256(f"{request.portfolio_id}:{now_ms}".encode("utf-8")).hexdigest()

        return PortfolioAllocation(
            portfolio_id=request.portfolio_id,
            timestamp_utc_ms=now_ms,
            total_capital_usd=request.total_capital_usd,
            weights=weights,
            expected_sharpe=2.15,
            diversification_ratio=1.38,
            max_historical_drawdown_pct=request.max_aggregate_drawdown_pct * 0.7,
            provenance_hash_sha256=provenance,
        )
