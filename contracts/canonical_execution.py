"""contracts/canonical_execution.py
Contratos Can?nicos de Ejecuci?n y Microestructura (Fase 02 / Fase 03).
ZERO-MOCKS ? REAL-ONLY ? DETERMINISTIC ? NO-LOOKAHEAD ? PROVENANCE-LOCKED ? FAIL-CLOSED
"""

from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class AssetClass(str, Enum):
    CRYPTO_PERPETUAL = "CRYPTO_PERPETUAL"
    CRYPTO_SPOT = "CRYPTO_SPOT"
    FOREX_SPOT = "FOREX_SPOT"
    CME_FUTURES = "CME_FUTURES"
    COMMODITIES = "COMMODITIES"
    COMMODITY_FUTURES = "COMMODITIES"
    EQUITY_STOCK = "EQUITY_STOCK"
    INDEX_CFD = "INDEX_CFD"


class InstrumentCostProfile(BaseModel):
    """Perfil can?nico inmutable de costes y microestructura de un activo."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    symbol: str = Field(..., description="S?mbolo can?nico del activo (ej. BTCUSDT, NQ, EURUSD)")
    asset_class: AssetClass = Field(..., description="Clase de activo can?nico")
    point_value: float = Field(..., gt=0.0, description="Valor monetario en USD por punto completo de movimiento")
    tick_size: float = Field(..., gt=0.0, description="Tama?o m?nimo de variaci?n de precio (tick)")
    contract_multiplier: float = Field(default=1.0, gt=0.0, description="Multiplicador de contrato o tama?o de lote")
    taker_fee_pct: float = Field(default=0.0, ge=0.0, description="Comisi?n taker porcentual (ej. 0.050 para 0.050%)")
    maker_fee_pct: float = Field(default=0.0, ge=0.0, description="Comisi?n maker porcentual (ej. 0.020 para 0.020%)")
    typical_spread_ticks: float = Field(default=1.0, ge=0.0, description="Spread t?pico en ticks")
    slippage_ticks_baseline: float = Field(default=1.0, ge=0.0, description="Deslizamiento esperado baseline en ticks")
    funding_rate_8h_pct: float = Field(default=0.0, ge=0.0, description="Tasa de financiaci?n estimada cada 8h en %")

