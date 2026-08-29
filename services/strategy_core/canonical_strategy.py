"""contracts/canonical_strategy.py
Definición Canónica Inmutable de Estrategia, AST, Compilación y Runtime SSOT (Fase 02 Rework AG2-P02-003).
ZERO-MOCKS · REAL-ONLY · PROVENANCE-LOCKED · NO-SYNTHETIC-DEFAULTS · FAIL-CLOSED
SSOT inmutable para la representación declarativa de reglas, condiciones, salidas, compilación y runtime.
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
    """Lanzada cuando el hash canónico de la estrategia no coincide con su AST o identidad semántica."""
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
    TRACK_ULTRA = "ULTRA"
    TRACK_FONDEO = "FONDEO"
    TRACK_PORTFOLIO = "PORTFOLIO"


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


# Alias para retrocompatibilidad
ComparisonOperator = ComparisonOp


class IndicatorSpec(BaseModel):
    """Especificación declarativa de un indicador técnico determinista sin defaults silenciosos (P02-003-01)."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(..., description="Nombre canónico del indicador e.g. EMA, SMA, RSI, ATR, DONCHIAN")
    params: Dict[str, Any] = Field(..., description="Parámetros numéricos explícitos e.g. {'period': 20}")
    source_field: str = Field(..., description="Campo fuente explícito e.g. 'close', 'high', 'low', 'volume'")
    shift: int = Field(..., ge=0, description="Desplazamiento temporal t-shift (0 = barra actual)")


class ConditionNode(BaseModel):
    """Nodo atómico de condición dentro del árbol de reglas (AST)."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    left: Union[IndicatorSpec, str, float] = Field(..., description="Lado izquierdo de la comparación")
    op: ComparisonOp = Field(..., description="Operador de comparación")
    right: Union[IndicatorSpec, str, float] = Field(..., description="Lado derecho de la comparación")


# Alias canónico
RuleCondition = ConditionNode


class RuleTree(BaseModel):
    """Árbol canónico de reglas lógicas de entrada sin defaults silenciosos (P02-003-01)."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    logic: LogicalOp = Field(..., description="Operador lógico de composición: AND / OR")
    conditions: List[ConditionNode] = Field(..., description="Lista de condiciones atómicas")
    direction: Literal["LONG", "SHORT", "BOTH"] = Field(..., description="Dirección de la operación")


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
    """Modelo canónico de salida, SL, TP y gestión de trailing stop sin defaults silenciosos (P02-003-01)."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    sl_type: StopLossType = Field(..., description="Tipo explícito de Stop Loss")
    sl_value: float = Field(..., gt=0.0, description="Valor del Stop Loss (e.g. 2.0x ATR o 1.5%)")
    tp_type: TakeProfitType = Field(..., description="Tipo explícito de Take Profit")
    tp_value: float = Field(..., gt=0.0, description="Valor del Take Profit (e.g. 3.0 R:R)")
    
    trail_after_r: Optional[float] = Field(default=None, gt=0.0, description="Mueve a BE tras alcanzar R múltiplos")
    time_stop_bars: Optional[int] = Field(default=None, ge=1, description="Cierre por tiempo tras N barras")


class SizingType(str, Enum):
    RISK_PCT_EQUITY = "RISK_PCT_EQUITY"
    FIXED_CONTRACTS = "FIXED_CONTRACTS"
    FIXED_USD = "FIXED_USD"
    VOLATILITY_ADJUSTED = "VOLATILITY_ADJUSTED"


class SizingAndRisk(BaseModel):
    """Gestión de dimensionamiento de posición y límites de riesgo sin defaults silenciosos (P02-003-01)."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    sizing_type: SizingType = Field(..., description="Tipo de dimensionamiento explícito")
    risk_value: float = Field(..., gt=0.0, description="Riesgo base por trade e.g. 1.0% o 1 contrato")
    max_open_positions: int = Field(..., ge=1, le=10, description="Máximo de posiciones simultáneas")
    max_daily_loss_usd: Optional[float] = Field(default=None, gt=0.0)


class SessionWindow(BaseModel):
    """Ventana horaria de sesión operativa permitida en horario UTC sin defaults silenciosos."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    start_time_utc: str = Field(..., description="HH:MM UTC apertura")
    end_time_utc: str = Field(..., description="HH:MM UTC cierre")
    close_at_eod: bool = Field(..., description="Cerrar posiciones al final del día")
    allowed_days: List[int] = Field(..., description="Lista explícita de días permitidos (0=Lun, 4=Vie)")


class TargetInstrument(BaseModel):
    """Especificación canónica del instrumento objetivo sin defaults silenciosos."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    symbol: str = Field(..., description="Símbolo base normalizado e.g. NQ, BTCUSDT")
    asset_class: str = Field(..., description="FUTURES, CRYPTO_PERP, FOREX")
    timeframe: str = Field(..., description="1m, 5m, 15m, 1h, 4h, 1d")
    exchange: str = Field(..., description="CME, BINGX, BINANCE, FOREX")


class ProvenanceMetadata(BaseModel):
    """Metadatos de procedencia y autoría criptográfica sin defaults silenciosos (P02-003-01)."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    author: str = Field(..., description="Identidad del autor o subagente creador")
    engine_version: str = Field(..., description="Versión exacta del motor")
    policy_version: str = Field(..., description="Versión exacta de la política de ejecución")
    created_at_utc: str = Field(..., description="Marca temporal ISO UTC de creación")
    parent_hash: Optional[str] = Field(default=None, description="Hash SHA-256 de la estrategia padre en caso de mutación")
    mutation_type: Optional[str] = Field(default=None, description="Tipo explícito de mutación aplicada")


class ExecutableRuntimeInstruction(BaseModel):
    """Instrucción de ejecución en runtime compilada que preserva 100% de la semántica canónica (P02-003-02)."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    strategy_id: str
    strategy_version: str
    strategy_hash: str
    engine_version: str
    policy_version: str
    symbol: str
    timeframe: str
    direction: Literal["LONG", "SHORT", "BOTH"]
    logical_operator: LogicalOp
    compiled_conditions: List[Dict[str, Any]]
    sl_config: Dict[str, Any]
    tp_config: Dict[str, Any]
    sizing_config: Dict[str, Any]
    session_config: Optional[Dict[str, Any]] = None
    provenance: Dict[str, Any]


class CanonicalStrategy(BaseModel):
    """Entidad SSOT Inmutable de Estrategia Cuantitativa (Fase 02 Rework AG2-P02-003)."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    strategy_id: str = Field(..., description="ID unívoco determinista")
    name: str = Field(..., description="Nombre humano e.g. NQ Trend Breakout")
    version: str = Field(..., description="Versión semántica explícita de la estrategia e.g. 1.0.0")
    symbol: str = Field(..., description="Símbolo base e.g. NQ, BTCUSDT, EURUSD")
    timeframe: str = Field(..., description="Timeframe e.g. 1m, 5m, 15m, 1h, 4h, 1d")
    route: Literal["ULTRA", "FONDEO", "PORTFOLIO"] = Field(..., description="Ruta de explotación")
    archetype: str = Field(..., description="Arquetipo cuantitativo")

    entry_rules: RuleTree = Field(..., description="Reglas de entrada")
    exit_rules: ExitModel = Field(..., description="Reglas de salida y SL/TP")
    sizing_and_risk: SizingAndRisk = Field(..., description="Gestión de tamaño y riesgo")
    session_window: Optional[SessionWindow] = None
    provenance: ProvenanceMetadata = Field(..., description="Metadatos de procedencia y versiones de motor")
    
    strategy_hash: str = Field(..., min_length=64, max_length=64, description="Hash SHA-256 inmutable de la identidad semántica completa")

    @classmethod
    def compute_strategy_hash(cls, payload: Dict[str, Any]) -> str:
        """Calcula el hash determinista SHA-256 canónico cubriendo la identidad semántica completa (P02-003-01)."""
        raw_json = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(raw_json.encode("utf-8")).hexdigest()

    def get_semantic_payload(self) -> Dict[str, Any]:
        """Extrae el payload semántico completo para el cálculo de hash inmutable."""
        return {
            "strategy_id": self.strategy_id,
            "name": self.name,
            "version": self.version,
            "symbol": self.symbol.strip().upper(),
            "timeframe": self.timeframe.strip().lower(),
            "route": self.route,
            "archetype": self.archetype,
            "entry_rules": self.entry_rules.model_dump(),
            "exit_rules": self.exit_rules.model_dump(),
            "sizing_and_risk": self.sizing_and_risk.model_dump(),
            "session_window": self.session_window.model_dump() if self.session_window else None,
            "provenance": {
                "author": self.provenance.author,
                "engine_version": self.provenance.engine_version,
                "policy_version": self.provenance.policy_version,
                "parent_hash": self.provenance.parent_hash,
                "mutation_type": self.provenance.mutation_type,
            },
        }

    @classmethod
    def create_and_hash(
        cls,
        strategy_id: str,
        name: str,
        version: str,
        symbol: str,
        timeframe: str,
        route: Literal["ULTRA", "FONDEO", "PORTFOLIO"],
        archetype: str,
        entry_rules: RuleTree,
        exit_rules: ExitModel,
        sizing_and_risk: SizingAndRisk,
        provenance: ProvenanceMetadata,
        session_window: Optional[SessionWindow] = None,
    ) -> CanonicalStrategy:
        """Fabrica una CanonicalStrategy inmutable y calcula su hash determinista sobre todos los campos semánticos."""
        payload = {
            "strategy_id": strategy_id,
            "name": name,
            "version": version,
            "symbol": symbol.strip().upper(),
            "timeframe": timeframe.strip().lower(),
            "route": route,
            "archetype": archetype,
            "entry_rules": entry_rules.model_dump(),
            "exit_rules": exit_rules.model_dump(),
            "sizing_and_risk": sizing_and_risk.model_dump(),
            "session_window": session_window.model_dump() if session_window else None,
            "provenance": {
                "author": provenance.author,
                "engine_version": provenance.engine_version,
                "policy_version": provenance.policy_version,
                "parent_hash": provenance.parent_hash,
                "mutation_type": provenance.mutation_type,
            },
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
        """Verifica que el strategy_hash coincida exactamente con la identidad semántica completa."""
        payload = self.get_semantic_payload()
        expected = self.compute_strategy_hash(payload)
        return self.strategy_hash == expected

    def compile_to_runtime(self) -> ExecutableRuntimeInstruction:
        """Compila la CanonicalStrategy en una instrucción ejecutable de runtime preservando toda la semántica (P02-003-02)."""
        if not self.verify_integrity():
            raise StrategyIntegrityError(f"Estrategia {self.strategy_id} tiene hash corrupto o no coincide con su identidad semántica.")

        compiled_conds = []
        for cond in self.entry_rules.conditions:
            left_val = cond.left.model_dump() if isinstance(cond.left, IndicatorSpec) else cond.left
            right_val = cond.right.model_dump() if isinstance(cond.right, IndicatorSpec) else cond.right
            compiled_conds.append({
                "left": left_val,
                "op": cond.op.value if isinstance(cond.op, ComparisonOp) else str(cond.op),
                "right": right_val,
            })

        return ExecutableRuntimeInstruction(
            strategy_id=self.strategy_id,
            strategy_version=self.version,
            strategy_hash=self.strategy_hash,
            engine_version=self.provenance.engine_version,
            policy_version=self.provenance.policy_version,
            symbol=self.symbol,
            timeframe=self.timeframe,
            direction=self.entry_rules.direction,
            logical_operator=self.entry_rules.logic,
            compiled_conditions=compiled_conds,
            sl_config={
                "type": self.exit_rules.sl_type.value,
                "value": self.exit_rules.sl_value,
                "trail_after_r": self.exit_rules.trail_after_r,
                "time_stop_bars": self.exit_rules.time_stop_bars,
            },
            tp_config={
                "type": self.exit_rules.tp_type.value,
                "value": self.exit_rules.tp_value,
            },
            sizing_config={
                "type": self.sizing_and_risk.sizing_type.value,
                "value": self.sizing_and_risk.risk_value,
                "max_open_positions": self.sizing_and_risk.max_open_positions,
                "max_daily_loss_usd": self.sizing_and_risk.max_daily_loss_usd,
            },
            session_config=self.session_window.model_dump() if self.session_window else None,
            provenance={
                "author": self.provenance.author,
                "created_at_utc": self.provenance.created_at_utc,
                "parent_hash": self.provenance.parent_hash,
                "mutation_type": self.provenance.mutation_type,
            },
        )
