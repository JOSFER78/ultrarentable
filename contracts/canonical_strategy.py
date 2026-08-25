"""contracts/canonical_strategy.py
Definición Canónica Inmutable de Estrategia, AST y Representación (Fase 02).
ZERO-MOCKS · REAL-ONLY · PROVENANCE-LOCKED · FAIL-CLOSED
SSOT inmutable para la representación declarativa de reglas, condiciones, salidas y gestión de riesgo.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, ConfigDict, Field


class InvalidStrategyError(Exception):
    """Lanzada cuando una definición de estrategia es inválida o incompleta."""
    pass


class StrategyIntegrityError(Exception):
    """Lanzada cuando el hash canónico de la estrategia no coincide con su AST."""
    pass


class StrategyLifecycleStatus(str, Enum):
    DRAFT = "DRAFT"
    INCUBADORA = "INCUBADORA"
    VALIDATING = "VALIDATING"
    APPROVED = "APPROVED"
    CERTIFIED_CURRENT = "CERTIFIED_CURRENT"
    CERTIFIED_LEGACY = "CERTIFIED_LEGACY"
    STALE = "STALE"
    REVALIDATION_REQUIRED = "REVALIDATION_REQUIRED"
    REJECTED = "REJECTED"


class ExecutionTrack(str, Enum):
    ULTRA = "ULTRA"
    FONDEO = "FONDEO"
    PORTFOLIO = "PORTFOLIO"


class LogicalOp(str, Enum):
    AND = "AND"
    OR = "OR"


class ComparisonOp(str, Enum):
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    EQ = "=="
    CROSS_ABOVE = "CROSS_ABOVE"
    CROSS_BELOW = "CROSS_BELOW"


class IndicatorSpec(BaseModel):
    """Especificación declarativa de un indicador técnico determinista."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(..., description="Nombre del indicador e.g. EMA, SMA, RSI, ATR, DONCHIAN")
    params: Dict[str, Any] = Field(default_factory=dict, description="Parámetros numéricos e.g. {'period': 20}")
    source_field: str = Field(default="close", description="Campo fuente e.g. close, high, low, volume")
    shift: int = Field(default=0, ge=0, description="Desplazamiento temporal t-shift (0 = barra actual)")


class ConditionNode(BaseModel):
    """Nodo atómico de condición dentro del árbol de reglas (AST)."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    left: Union[IndicatorSpec, str, float] = Field(..., description="Lado izquierdo de la comparación")
    op: ComparisonOp = Field(..., description="Operador de comparación")
    right: Union[IndicatorSpec, str, float] = Field(..., description="Lado derecho de la comparación")


# Alias canónico
RuleCondition = ConditionNode


class RuleTree(BaseModel):
    """Árbol canónico de reglas lógicas de entrada (Long / Short)."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    logic: LogicalOp = Field(default=LogicalOp.AND)
    conditions: List[ConditionNode] = Field(default_factory=list)
    direction: Literal["LONG", "SHORT", "BOTH"] = Field(default="LONG")


class StopLossType(str, Enum):
    ATR_MULTIPLE = "ATR_MULTIPLE"
    FIXED_POINTS = "FIXED_POINTS"
    PERCENTAGE = "PERCENTAGE"
    BAR_LOW_HIGH = "BAR_LOW_HIGH"


class TakeProfitType(str, Enum):
    RR_MULTIPLE = "RR_MULTIPLE"
    ATR_MULTIPLE = "ATR_MULTIPLE"
    PERCENTAGE = "PERCENTAGE"
    FIXED_POINTS = "FIXED_POINTS"


class ExitModel(BaseModel):
    """Modelo canónico de salida, SL, TP y gestión de trailing stop."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    sl_type: StopLossType = Field(default=StopLossType.ATR_MULTIPLE)
    sl_value: float = Field(..., gt=0.0, description="Valor del Stop Loss (e.g. 2.0x ATR o 1.5%)")
    tp_type: TakeProfitType = Field(default=TakeProfitType.RR_MULTIPLE)
    tp_value: float = Field(..., gt=0.0, description="Valor del Take Profit (e.g. 3.0 R:R)")
    
    trail_after_r: Optional[float] = Field(default=None, gt=0.0, description="Mueve a BE tras alcanzar R múltiplos")
    time_stop_bars: Optional[int] = Field(default=None, ge=1, description="Cierre por tiempo tras N barras")


class SizingType(str, Enum):
    RISK_PCT_EQUITY = "RISK_PCT_EQUITY"
    FIXED_CONTRACTS = "FIXED_CONTRACTS"
    FIXED_USD = "FIXED_USD"
    VOLATILITY_ADJUSTED = "VOLATILITY_ADJUSTED"


class SizingAndRisk(BaseModel):
    """Gestión de dimensionamiento de posición y límites de riesgo."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    sizing_type: SizingType = Field(default=SizingType.RISK_PCT_EQUITY)
    risk_value: float = Field(..., gt=0.0, description="Riesgo base por trade e.g. 1.0% o 1 contrato")
    max_open_positions: int = Field(default=1, ge=1, le=10)
    max_daily_loss_usd: Optional[float] = Field(default=None, gt=0.0)


class SessionWindow(BaseModel):
    """Ventana horaria de sesión operativa permitida en horario UTC."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    start_time_utc: str = Field(default="00:00", description="HH:MM UTC apertura")
    end_time_utc: str = Field(default="23:59", description="HH:MM UTC cierre")
    close_at_eod: bool = Field(default=False, description="Cerrar posiciones al final del día")
    allowed_days: List[int] = Field(default_factory=lambda: [0, 1, 2, 3, 4], description="0=Lun, 4=Vie")


class TargetInstrument(BaseModel):
    """Especificación canónica del instrumento objetivo."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    symbol: str = Field(..., description="Símbolo base normalizado e.g. NQ, BTCUSDT")
    asset_class: str = Field(default="FUTURES", description="FUTURES, CRYPTO_PERP, FOREX")
    timeframe: str = Field(default="1h", description="1m, 5m, 15m, 1h, 4h, 1d")
    exchange: str = Field(default="CME", description="CME, BINGX, BINANCE, FOREX")


class ProvenanceMetadata(BaseModel):
    """Metadatos de procedencia y autoría criptográfica."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    author: str = Field(default="SYSTEM")
    engine_version: str = Field(default="5.4.0")
    policy_version: str = Field(default="5.4.0")
    created_at_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    parent_hash: Optional[str] = None
    mutation_type: Optional[str] = None


class CanonicalStrategy(BaseModel):
    """Entidad SSOT Inmutable de Estrategia Cuantitativa (Fase 02)."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    strategy_id: str = Field(..., description="ID unívoco determinista")
    name: str = Field(..., description="Nombre humano e.g. NQ Trend Breakout")
    version: str = Field(default="1.0.0", description="Versión semántica de la estrategia")
    symbol: str = Field(..., description="Símbolo base e.g. NQ, BTCUSDT, EURUSD")
    timeframe: str = Field(..., description="Timeframe e.g. 1m, 5m, 15m, 1h, 4h, 1d")
    route: Literal["ULTRA", "FONDEO", "PORTFOLIO"] = Field(..., description="Ruta de explotación")
    archetype: str = Field(default="MOMENTUM_BREAKOUT")

    entry_rules: RuleTree = Field(..., description="Reglas de entrada")
    exit_rules: ExitModel = Field(..., description="Reglas de salida y SL/TP")
    sizing_and_risk: SizingAndRisk = Field(..., description="Gestión de tamaño y riesgo")
    session_window: Optional[SessionWindow] = None
    provenance: Optional[ProvenanceMetadata] = None
    
    strategy_hash: str = Field(..., min_length=64, max_length=64, description="Hash SHA-256 inmutable del AST")

    @classmethod
    def compute_strategy_hash(cls, payload: Dict[str, Any]) -> str:
        """Calcula el hash determinista SHA-256 canónico del AST y parámetros."""
        raw_json = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(raw_json.encode("utf-8")).hexdigest()

    @classmethod
    def create_and_hash(
        cls,
        strategy_id: str,
        name: str,
        symbol: str,
        timeframe: str,
        route: Literal["ULTRA", "FONDEO", "PORTFOLIO"],
        entry_rules: RuleTree,
        exit_rules: ExitModel,
        sizing_and_risk: SizingAndRisk,
        archetype: str = "MOMENTUM_BREAKOUT",
        version: str = "1.0.0",
        session_window: Optional[SessionWindow] = None,
        provenance: Optional[ProvenanceMetadata] = None,
    ) -> CanonicalStrategy:
        """Fabrica una CanonicalStrategy inmutable y calcula su hash determinista."""
        payload = {
            "strategy_id": strategy_id,
            "symbol": symbol.strip().upper(),
            "timeframe": timeframe.strip().lower(),
            "route": route,
            "archetype": archetype,
            "version": version,
            "entry_rules": entry_rules.model_dump(),
            "exit_rules": exit_rules.model_dump(),
            "sizing_and_risk": sizing_and_risk.model_dump(),
            "session_window": session_window.model_dump() if session_window else None,
        }
        computed_hash = cls.compute_strategy_hash(payload)
        return cls(
            strategy_id=strategy_id,
            name=name,
            version=version,
            symbol=symbol.strip().upper(),
            timeframe=timeframe.strip().lower(),
            route=route,
            archetype=archetype,
            entry_rules=entry_rules,
            exit_rules=exit_rules,
            sizing_and_risk=sizing_and_risk,
            session_window=session_window,
            provenance=provenance,
            strategy_hash=computed_hash,
        )

    def verify_integrity(self) -> bool:
        """Verifica que el strategy_hash coincida exactamente con el AST actual."""
        payload = {
            "strategy_id": self.strategy_id,
            "symbol": self.symbol.strip().upper(),
            "timeframe": self.timeframe.strip().lower(),
            "route": self.route,
            "archetype": self.archetype,
            "version": self.version,
            "entry_rules": self.entry_rules.model_dump(),
            "exit_rules": self.exit_rules.model_dump(),
            "sizing_and_risk": self.sizing_and_risk.model_dump(),
            "session_window": self.session_window.model_dump() if self.session_window else None,
        }
        expected = self.compute_strategy_hash(payload)
        return self.strategy_hash == expected
