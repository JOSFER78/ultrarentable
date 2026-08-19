"""services/paper/shadow_dispatcher.py
Dispatcher de Paper Trading y Shadow Execution (Fase 15).
Gestiona el ciclo de vida de incubación y envío de órdenes en tiempo real simulado.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from contracts.snapshots.strategy_snapshot import StrategySnapshot, StrategyRoute


class ShadowDeploymentConfig(BaseModel):
    strategy_id: str
    canonical_hash: str
    target_venue: Literal["BINGX_DEMO", "BINANCE_TESTNET", "TRADOVATE_SIM", "RITHMIC_PAPER"]
    route: StrategyRoute
    allocated_capital_usd: float = Field(default=1000.0, gt=0.0)
    max_position_size: float = Field(default=1.0, gt=0.0)


class ShadowExecutionEngine:
    """Motor de despacho de órdenes en entornos de Shadow Trading."""

    def __init__(self):
        self.active_deployments: Dict[str, ShadowDeploymentConfig] = {}

    def deploy_to_shadow(self, config: ShadowDeploymentConfig) -> Dict[str, Any]:
        self.active_deployments[config.strategy_id] = config
        return {
            "strategy_id": config.strategy_id,
            "status": "SHADOW_ACTIVE",
            "target_venue": config.target_venue,
            "allocated_capital_usd": config.allocated_capital_usd,
            "deployed_at_ms": int(time.time() * 1000),
        }

    def stop_shadow(self, strategy_id: str) -> Dict[str, Any]:
        if strategy_id in self.active_deployments:
            del self.active_deployments[strategy_id]
            return {"strategy_id": strategy_id, "status": "SHADOW_STOPPED"}
        return {"strategy_id": strategy_id, "status": "NOT_FOUND"}
