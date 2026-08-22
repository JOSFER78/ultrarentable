"""contracts/instrument_specification.py
Universal Instrument Specification Contract (v3.0.0).

DOCTRINA ZERO-HARDCODED ASSETS:
- Every market asset (Crypto Perpetuals, CME Futures, Forex) is completely defined by this contract.
- The engine NEVER contains `if symbol == 'BTC'` or hardcoded tick sizes.
- Pure immutable Pydantic model with deterministic SHA-256 fingerprinting.
"""

from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class AssetClass(str, Enum):
    CRYPTO_PERPETUAL = "CRYPTO_PERPETUAL"
    CME_FUTURES = "CME_FUTURES"
    FOREX_MAJOR = "FOREX_MAJOR"
    FOREX_CROSS = "FOREX_CROSS"
    COMMODITY = "COMMODITY"
    INDEX_FUTURES = "INDEX_FUTURES"


class MarginType(str, Enum):
    ISOLATED = "ISOLATED"
    CROSS_MARGIN = "CROSS_MARGIN"
    PORTFOLIO_MARGIN = "PORTFOLIO_MARGIN"


class CommissionType(str, Enum):
    PERCENTAGE_OF_NOTIONAL = "PERCENTAGE_OF_NOTIONAL"  # e.g. 0.05% taker on crypto
    FIXED_PER_CONTRACT = "FIXED_PER_CONTRACT"          # e.g. $2.50 per CME contract
    PER_LOT = "PER_LOT"                                # e.g. $7.00 per Forex standard lot


class MaintenanceTier(BaseModel):
    """Tramo de margen de mantenimiento según nocional expuesto."""
    model_config = ConfigDict(frozen=True, extra="forbid")
    tier_index: int = Field(1, ge=1)
    max_notional_usd: float = Field(..., gt=0.0)
    maintenance_margin_rate: float = Field(..., gt=0.0, le=1.0)
    max_leverage: float = Field(..., ge=1.0, le=500.0)


class InstrumentSpecification(BaseModel):
    """Especificación canónica completa de un instrumento financiero negociable."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    symbol: str = Field(..., description="Símbolo canónico e.g. BTC-USDT, NQ, ES, GC, SI, EURUSD")
    raw_symbol: str = Field(..., description="Símbolo del broker e.g. BTCUSDT, NQU24, EUR/USD")
    asset_class: AssetClass = Field(...)
    exchange_or_venue: str = Field(..., description="BINGX, BINANCE, CME, NYMEX, COMEX, OANDA, RITHMIC")
    base_currency: str = Field(..., description="BTC, ETH, NQ, EUR, XAU, etc.")
    quote_currency: str = Field(..., description="USDT, USD, etc.")

    # Microestructura de Precios y Cantidades
    tick_size: float = Field(..., gt=0.0, description="Mínima variación de precio (e.g. 0.25 para NQ, 0.1 para BTC)")
    point_value: float = Field(..., gt=0.0, description="Valor en USD de 1 punto entero (e.g. $20 para NQ, $50 para ES, $1 para Cripto)")
    contract_size: float = Field(default=1.0, gt=0.0, description="Multiplicador de contrato")
    min_quantity: float = Field(..., gt=0.0, description="Cantidad mínima negociable (e.g. 0.001 BTC, 1 contrato NQ)")
    quantity_step: float = Field(..., gt=0.0, description="Incremento mínimo de cantidad")
    price_precision: int = Field(..., ge=0, description="Decimales de precio")
    quantity_precision: int = Field(..., ge=0, description="Decimales de cantidad")

    # Modelo de Comisiones y Fricción
    commission_type: CommissionType = Field(CommissionType.PERCENTAGE_OF_NOTIONAL)
    taker_fee_rate: float = Field(default=0.0005, ge=0.0, description="Tasa taker (0.05% = 0.0005)")
    maker_fee_rate: float = Field(default=0.0002, ge=0.0, description="Tasa maker (0.02% = 0.0002)")
    cme_exchange_fee_per_contract: float = Field(default=0.0, ge=0.0, description="Tasa fija CME de compensación por contrato")
    typical_spread_ticks: float = Field(default=1.0, ge=0.0, description="Spread medio en ticks")
    typical_slippage_ticks: float = Field(default=1.0, ge=0.0, description="Deslizamiento base en ticks")

    # Reglas de Margen y Apalancamiento
    max_allowed_leverage: float = Field(default=10.0, ge=1.0, le=500.0)
    initial_margin_rate: float = Field(default=0.10, ge=0.002, le=1.0)
    maintenance_margin_rate: float = Field(default=0.05, ge=0.001, le=1.0)
    maintenance_tiers: List[MaintenanceTier] = Field(default_factory=list)

    # Tasa de Financiación (Perpetuos Cripto)
    is_perpetual: bool = Field(False)
    funding_interval_hours: int = Field(default=8, ge=1)
    default_funding_rate: float = Field(default=0.0001)

    def canonical_json(self) -> str:
        return json.dumps(self.model_dump(), sort_keys=True, separators=(",", ":"))

    def compute_hash(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    def round_price_to_tick(self, price: float) -> float:
        """Ajusta un precio al tick_size exacto del instrumento."""
        ticks = round(price / self.tick_size)
        return round(ticks * self.tick_size, self.price_precision)

    def round_quantity_to_step(self, qty: float) -> float:
        """Ajusta una cantidad al step exacto del instrumento."""
        steps = round(qty / self.quantity_step)
        adjusted = max(self.min_quantity, steps * self.quantity_step)
        return round(adjusted, self.quantity_precision)
