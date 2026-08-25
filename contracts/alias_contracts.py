"""contracts/alias_contracts.py
Contratos Canónicos para el Registro Versionado de Alias de Instrumentos (Fase 01 Rework P01-004).
ZERO-MOCKS · REAL-ONLY · PROVENANCE-LOCKED
"""

from __future__ import annotations

import hashlib
import json
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AliasRecord(BaseModel):
    """Registro inmutable de mapeo de alias a símbolo canónico."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    alias: str = Field(..., description="Símbolo alternativo o de proveedor e.g. BTC-USDT, EURUSD=X")
    canonical_symbol: str = Field(..., description="Símbolo canónico normalizado e.g. BTCUSDT, EURUSD")
    venue: str = Field(..., description="Mercado o proveedor e.g. BINGX, YAHOO_FOREX, CME")
    rationale: str = Field(..., description="Motivo determinista del mapeo")


class CanonicalAliasRegistry(BaseModel):
    """Registro inmutable versionado con hash SHA-256 de integridad."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    registry_version: str = Field(default="1.0.0")
    registry_sha256: str = Field(..., min_length=64, max_length=64)
    aliases: List[AliasRecord] = Field(default_factory=list)

    @classmethod
    def create_registry(cls, version: str, records: List[AliasRecord]) -> CanonicalAliasRegistry:
        """Crea el registro y calcula deterministamente su hash SHA-256."""
        payload = [r.model_dump() for r in sorted(records, key=lambda x: x.alias)]
        raw_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        h = hashlib.sha256(raw_bytes).hexdigest()
        return cls(registry_version=version, registry_sha256=h, aliases=records)

    def resolve(self, symbol: str) -> Optional[str]:
        """Resuelve un símbolo mediante el registro oficial de alias."""
        target = symbol.strip().upper()
        for rec in self.aliases:
            if rec.alias.upper() == target:
                return rec.canonical_symbol.upper()
        return None


# Definición canónica oficial respaldada con evidencia
OFFICIAL_ALIAS_RECORDS: List[AliasRecord] = [
    AliasRecord(alias="BTC-USDT", canonical_symbol="BTCUSDT", venue="BINGX", rationale="Separador de guion en API de BingX Swap"),
    AliasRecord(alias="BTC_USDT", canonical_symbol="BTCUSDT", venue="BINGX", rationale="Separador de barra baja en feeds Spot/Swap"),
    AliasRecord(alias="ETH-USDT", canonical_symbol="ETHUSDT", venue="BINGX", rationale="Separador de guion en API de BingX Swap"),
    AliasRecord(alias="ETH_USDT", canonical_symbol="ETHUSDT", venue="BINGX", rationale="Separador de barra baja en feeds Spot/Swap"),
    AliasRecord(alias="SOL-USDT", canonical_symbol="SOLUSDT", venue="BINGX", rationale="Separador de guion en API de BingX Swap"),
    AliasRecord(alias="SOL_USDT", canonical_symbol="SOLUSDT", venue="BINGX", rationale="Separador de barra baja en feeds Spot/Swap"),
    AliasRecord(alias="XRP-USDT", canonical_symbol="XRPUSDT", venue="BINGX", rationale="Separador de guion en API de BingX Swap"),
    AliasRecord(alias="XRP_USDT", canonical_symbol="XRPUSDT", venue="BINGX", rationale="Separador de barra baja en feeds Spot/Swap"),
    AliasRecord(alias="DOGE-USDT", canonical_symbol="DOGEUSDT", venue="BINGX", rationale="Separador de guion en API de BingX Swap"),
    AliasRecord(alias="DOGE_USDT", canonical_symbol="DOGEUSDT", venue="BINGX", rationale="Separador de barra baja en feeds Spot/Swap"),
    AliasRecord(alias="EURUSD=X", canonical_symbol="EURUSD", venue="YAHOO_FOREX", rationale="Sufijo =X de Yahoo Finance para divisas"),
    AliasRecord(alias="GBPUSD=X", canonical_symbol="GBPUSD", venue="YAHOO_FOREX", rationale="Sufijo =X de Yahoo Finance para divisas"),
    AliasRecord(alias="JPY=X", canonical_symbol="USDJPY", venue="YAHOO_FOREX", rationale="Notación invertida Yahoo Finance para USDJPY"),
]

OFFICIAL_ALIAS_REGISTRY = CanonicalAliasRegistry.create_registry(
    version="1.0.0",
    records=OFFICIAL_ALIAS_RECORDS,
)
