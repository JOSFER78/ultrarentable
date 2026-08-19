"""contracts/snapshots/strategy_snapshot.py
Source of Truth Inmutable de Estrategia Cuantitativa (Fase 1).
Congela unívocamente la definición canónica de la estrategia antes de entrar a validación.
Garantiza que ningún Gate ni proceso posterior pueda modificar parámetros.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

from contracts.canonical_strategy import RuleTree, ExitModel, SizingAndRisk, SessionWindow


class StrategyRoute(str, Enum):
    ULTRA = "ULTRA"
    FONDEO = "FONDEO"
    PORTFOLIO = "PORTFOLIO"


class PyramidingTier(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    trigger_pnl_atr_mult: float = Field(..., gt=0.0, description="Múltiplo ATR de ganancia para disparar el tramo")
    added_size_mult: float = Field(..., gt=0.0, description="Multiplicador de tamaño a añadir")
    trail_stop_to_breakeven: bool = Field(True, description="Mueve stop a break-even antes de añadir")


class PyramidingPolicy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    enabled: bool = Field(False)
    max_tiers: int = Field(default=3, ge=1, le=10)
    tiers: List[PyramidingTier] = Field(default_factory=list)


class MarginPolicy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    margin_mode: Literal["ISOLATED", "CROSS_MARGIN"] = Field("CROSS_MARGIN")
    max_leverage_ceiling: float = Field(default=20.0, ge=1.0, le=500.0)
    liquidation_buffer_min_pct: float = Field(default=5.0, ge=0.5, le=90.0)
    reinvestment_rate_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    vault_harvest_rate_pct: float = Field(default=0.0, ge=0.0, le=100.0)


class StrategySnapshot(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    
    strategy_id: str = Field(..., description="ID unívoco canónico de la estrategia")
    version: str = Field(default="2.0.0", description="Versión del contrato de snapshot")
    canonical_hash: str = Field(..., description="Hash SHA256 calculado sobre el contenido canónico")
    route: StrategyRoute = Field(..., description="Ruta de explotación: ULTRA, FONDEO o PORTFOLIO")
    archetype: str = Field(default="MOMENTUM_BREAKOUT", description="Arquetipo cuantitativo")
    symbol: str = Field(..., description="Símbolo base e.g. BTCUSDT, NQ, EURUSD, XAUUSD")
    timeframe: str = Field(..., description="Timeframe canónico e.g. 1m, 5m, 15m, 1h, 4h")
    
    entry_rules: RuleTree = Field(..., description="Árbol canónico de reglas de entrada Long/Short")
    exit_rules: ExitModel = Field(..., description="Reglas canónicas de salida, SL, TP y Trailing")
    sizing_and_risk: SizingAndRisk = Field(..., description="Gestión de tamaño y riesgo base")
    pyramiding_policy: PyramidingPolicy = Field(default_factory=PyramidingPolicy)
    margin_policy: MarginPolicy = Field(default_factory=MarginPolicy)
    session_window: Optional[SessionWindow] = None
    
    dataset_id_reference: str = Field(..., description="ID del dataset exacto con el que fue descubierta")
    dataset_sha256_reference: str = Field(..., description="Hash SHA256 del dataset físico de datos")
    created_at_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def create_and_hash(
        cls,
        strategy_id: str,
        route: StrategyRoute,
        symbol: str,
        timeframe: str,
        entry_rules: RuleTree,
        exit_rules: ExitModel,
        sizing_and_risk: SizingAndRisk,
        dataset_id_reference: str,
        dataset_sha256_reference: str,
        archetype: str = "MOMENTUM_BREAKOUT",
        pyramiding_policy: Optional[PyramidingPolicy] = None,
        margin_policy: Optional[MarginPolicy] = None,
        session_window: Optional[SessionWindow] = None,
    ) -> StrategySnapshot:
        """Construye el snapshot y calcula el hash canónico SHA256 determinista."""
        content_dict = {
            "strategy_id": strategy_id,
            "route": route.value if isinstance(route, StrategyRoute) else str(route),
            "symbol": symbol.upper(),
            "timeframe": timeframe.lower(),
            "archetype": archetype,
            "entry_rules": entry_rules.model_dump(),
            "exit_rules": exit_rules.model_dump(),
            "sizing_and_risk": sizing_and_risk.model_dump(),
            "pyramiding_policy": pyramiding_policy.model_dump() if pyramiding_policy else PyramidingPolicy().model_dump(),
            "margin_policy": margin_policy.model_dump() if margin_policy else MarginPolicy().model_dump(),
            "session_window": session_window.model_dump() if session_window else None,
            "dataset_id_reference": dataset_id_reference,
            "dataset_sha256_reference": dataset_sha256_reference,
        }
        canonical_str = json.dumps(content_dict, sort_keys=True, separators=(",", ":"))
        canonical_hash = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

        return cls(
            strategy_id=strategy_id,
            canonical_hash=canonical_hash,
            route=route,
            archetype=archetype,
            symbol=symbol.upper(),
            timeframe=timeframe.lower(),
            entry_rules=entry_rules,
            exit_rules=exit_rules,
            sizing_and_risk=sizing_and_risk,
            pyramiding_policy=pyramiding_policy or PyramidingPolicy(),
            margin_policy=margin_policy or MarginPolicy(),
            session_window=session_window,
            dataset_id_reference=dataset_id_reference,
            dataset_sha256_reference=dataset_sha256_reference,
        )

    def verify_integrity(self) -> bool:
        """Verifica que el hash canónico coincida exactamente con los parámetros congelados."""
        content_dict = {
            "strategy_id": self.strategy_id,
            "route": self.route.value if isinstance(self.route, StrategyRoute) else str(self.route),
            "symbol": self.symbol.upper(),
            "timeframe": self.timeframe.lower(),
            "archetype": self.archetype,
            "entry_rules": self.entry_rules.model_dump(),
            "exit_rules": self.exit_rules.model_dump(),
            "sizing_and_risk": self.sizing_and_risk.model_dump(),
            "pyramiding_policy": self.pyramiding_policy.model_dump(),
            "margin_policy": self.margin_policy.model_dump(),
            "session_window": self.session_window.model_dump() if self.session_window else None,
            "dataset_id_reference": self.dataset_id_reference,
            "dataset_sha256_reference": self.dataset_sha256_reference,
        }
        canonical_str = json.dumps(content_dict, sort_keys=True, separators=(",", ":"))
        computed_hash = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()
        return computed_hash == self.canonical_hash
