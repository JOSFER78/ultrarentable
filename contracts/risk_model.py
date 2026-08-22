"""contracts/risk_model.py
Universal Risk Model Contract (v3.0.0).

DOCTRINA CANÓNICA DE RIESGO:
- Supports both Route ULTRA ($1k bullet subaccounts, compounding, aggressive pyramiding) and Route FONDEO ($50k prop firm institutional DD preservation).
- Allows dynamic custom risk policies without modifying the execution engine.
"""

from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class RiskDoctrine(str, Enum):
    ULTRA = "ULTRA"                       # $1k subaccounts, hyper-leverage up to 500x, compounding, pyramiding, max DD <= 85%
    FONDEO = "FONDEO"                     # $50k institutional capital, 0.20%-0.50% risk, linear fixed contracts, max DD <= 4.0%
    FIXED_PERCENTAGE = "FIXED_PERCENTAGE" # Fixed % of equity
    FIXED_NOMINAL = "FIXED_NOMINAL"       # Fixed $ nominal risk per trade
    VOLATILITY_PARITY = "VOLATILITY_PARITY" # Inversely proportional to ATR


class PyramidingTierSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    tier_index: int = Field(1, ge=1)
    trigger_r_multiple: float = Field(1.5, gt=0.0, description="Múltiplo R para añadir tramo")
    reinvest_fraction_pct: float = Field(50.0, ge=1.0, le=100.0, description="% de ganancia flotante a reinvertir")
    move_stop_to_breakeven: bool = Field(True)


class RiskModel(BaseModel):
    """Modelo explícito e inmutable de dimensionamiento de posición y gestión de riesgo."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    model_id: str = Field(default="CANONICAL_RISK_MODEL")
    doctrine: RiskDoctrine = Field(RiskDoctrine.ULTRA)
    base_capital_usd: float = Field(default=1000.0, gt=0.0)
    
    # Sizing
    base_risk_pct: float = Field(default=10.0, ge=0.1, le=100.0, description="Riesgo base por trade (% sobre equidad)")
    fixed_contracts_count: Optional[float] = Field(None, ge=0.01, description="Contratos fijos para Fondeo si aplica")
    max_leverage: float = Field(default=100.0, ge=1.0, le=500.0)
    
    # Compounding & Pyramiding
    compounding_enabled: bool = Field(True)
    pyramiding_enabled: bool = Field(False)
    pyramiding_max_tiers: int = Field(default=3, ge=1, le=10)
    pyramiding_tiers: List[PyramidingTierSpec] = Field(default_factory=list)

    # Institutional & Safety Guardrails
    max_drawdown_limit_pct: float = Field(default=85.0, ge=0.5, le=100.0)
    daily_loss_limit_pct: Optional[float] = Field(None, ge=0.5, le=100.0)
    
    # Vault Harvest Ratchet (Ultra Route)
    vault_harvest_enabled: bool = Field(False)
    vault_harvest_trigger_roi_pct: float = Field(default=200.0, ge=10.0)
    vault_harvest_transfer_pct: float = Field(default=50.0, ge=1.0, le=100.0)

    @classmethod
    def create_ultra(cls, base_capital: float = 1000.0, risk_pct: float = 12.5, max_leverage: float = 100.0) -> RiskModel:
        """Crea la configuración oficial de la Ruta Ultra."""
        tiers = [
            PyramidingTierSpec(tier_index=1, trigger_r_multiple=1.5, reinvest_fraction_pct=50.0),
            PyramidingTierSpec(tier_index=2, trigger_r_multiple=3.0, reinvest_fraction_pct=50.0),
            PyramidingTierSpec(tier_index=3, trigger_r_multiple=4.5, reinvest_fraction_pct=50.0),
        ]
        return cls(
            model_id="ROUTE_ULTRA_CANONICAL",
            doctrine=RiskDoctrine.ULTRA,
            base_capital_usd=base_capital,
            base_risk_pct=risk_pct,
            max_leverage=max_leverage,
            compounding_enabled=True,
            pyramiding_enabled=True,
            pyramiding_max_tiers=3,
            pyramiding_tiers=tiers,
            max_drawdown_limit_pct=85.0,
            vault_harvest_enabled=True,
            vault_harvest_trigger_roi_pct=200.0,
            vault_harvest_transfer_pct=50.0,
        )

    @classmethod
    def create_fondeo(cls, base_capital: float = 50000.0, risk_pct: float = 0.25, max_contracts: float = 1.0) -> RiskModel:
        """Crea la configuración oficial de la Ruta Fondeo."""
        return cls(
            model_id="ROUTE_FONDEO_CANONICAL",
            doctrine=RiskDoctrine.FONDEO,
            base_capital_usd=base_capital,
            base_risk_pct=risk_pct,
            fixed_contracts_count=max_contracts,
            max_leverage=1.0,
            compounding_enabled=False,
            pyramiding_enabled=False,
            max_drawdown_limit_pct=4.0,
            daily_loss_limit_pct=2.0,
            vault_harvest_enabled=False,
        )

    def canonical_json(self) -> str:
        return json.dumps(self.model_dump(), sort_keys=True, separators=(",", ":"))

    def compute_hash(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()
