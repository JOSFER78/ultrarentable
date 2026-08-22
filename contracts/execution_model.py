"""contracts/execution_model.py
Universal Execution Model Contract (v3.0.0).

DOCTRINA ZERO-MAGIC COSTS:
- Defines explicit, reproducible friction models (commissions, slippage, spread, funding, exchange fees).
- Preserves the exact execution parameters used for any backtest in an immutable hash.
"""

from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class SlippageMode(str, Enum):
    FIXED_BPS = "FIXED_BPS"
    VOLATILITY_ATR_RATIO = "VOLATILITY_ATR_RATIO"
    TICK_BASED = "TICK_BASED"
    STRESSED_SLIPPAGE = "STRESSED_SLIPPAGE"


class ExecutionModel(BaseModel):
    """Modelo explícito e inmutable de ejecución y costes de mercado."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    model_id: str = Field(default="DEFAULT_TAKER_EXECUTION")
    taker_fee_pct: float = Field(default=0.05, ge=0.0, description="Comisión Taker en % (0.05% = 0.0005)")
    maker_fee_pct: float = Field(default=0.02, ge=0.0, description="Comisión Maker en %")
    cme_clearing_fee_per_contract: float = Field(default=0.0, ge=0.0, description="Tarifas CME por contrato")
    
    slippage_mode: SlippageMode = Field(SlippageMode.FIXED_BPS)
    base_slippage_bps: float = Field(default=2.0, ge=0.0, description="Deslizamiento base en puntos básicos (2.0 bps = 0.0002)")
    slippage_atr_multiplier: float = Field(default=0.05, ge=0.0, description="Multiplicador ATR para deslizamiento dinámico")
    
    funding_settlement_enabled: bool = Field(False)
    funding_rate_8h: float = Field(default=0.0001)

    def canonical_json(self) -> str:
        return json.dumps(self.model_dump(), sort_keys=True, separators=(",", ":"))

    def compute_hash(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    def calculate_commission(self, notional_usd: float, contract_count: float = 1.0) -> float:
        """Calcula el coste de comisión exacto."""
        if self.cme_clearing_fee_per_contract > 0:
            return round(contract_count * self.cme_clearing_fee_per_contract, 4)
        return round(notional_usd * (self.taker_fee_pct / 100.0), 4)

    def calculate_slippage_cost(self, notional_usd: float, atr_usd: float = 0.0) -> float:
        """Calcula el coste de deslizamiento en USD."""
        if self.slippage_mode == SlippageMode.VOLATILITY_ATR_RATIO and atr_usd > 0:
            slip_rate = (atr_usd * self.slippage_atr_multiplier) / max(1.0, notional_usd)
            return round(notional_usd * slip_rate, 4)
        return round(notional_usd * (self.base_slippage_bps / 10000.0), 4)
