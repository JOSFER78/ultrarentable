"""contracts/canonical_strategy.py
Definici?n Can?nica Inmutable de Estrategia, AST, Compilaci?n y Runtime SSOT (Fase 02 Rework AG2-P02-007).
ZERO-MOCKS ? REAL-ONLY ? PROVENANCE-LOCKED ? NO-SYNTHETIC-DEFAULTS ? FAIL-CLOSED
SSOT inmutable para la representaci?n declarativa de reglas, condiciones, salidas, compilaci?n y runtime.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, model_validator


class InvalidStrategyError(Exception):
    """Lanzada cuando una definici?n de estrategia es inv?lida o incompleta."""
    pass


class StrategyIntegrityError(Exception):
    """Lanzada cuando el hash can?nico de la estrategia no coincide con su AST o identidad sem?ntica."""
    pass


class StrategyLifecycleStatus(str, Enum):
    DRAFT = "DRAFT"
    GENERATED = "GENERATED"
    BACKTESTED = "BACKTESTED"
    OOS_PASSED = "OOS_PASSED"
    ROBUSTNESS_PASSED = "ROBUSTNESS_PASSED"
    EVIDENCE_APPROVED = "EVIDENCE_APPROVED"
    CANDIDATE = "CANDIDATE"
    INCUBATION_PAPER = "INCUBATION_PAPER"
    LIVE_ACTIVE = "LIVE_ACTIVE"
    INCUBADORA = "INCUBADORA"
    VALIDATING = "VALIDATING"
    APPROVED = "APPROVED"
    CERTIFIED_CURRENT = "CERTIFIED_CURRENT"
    CERTIFIED_LEGACY = "CERTIFIED_LEGACY"
    STALE = "STALE"
    REVALIDATION_REQUIRED = "REVALIDATION_REQUIRED"
    REJECTED = "REJECTED"
    RETIRED = "RETIRED"


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
    """Especificaci?n declarativa de un indicador t?cnico determinista sin defaults silenciosos (P02-003-01)."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(..., description="Nombre can?nico del indicador e.g. EMA, SMA, RSI, ATR, DONCHIAN")
    params: Dict[str, Any] = Field(..., description="Par?metros num?ricos expl?citos e.g. {'period': 20}")
    source_field: str = Field(..., description="Campo fuente expl?cito e.g. 'close', 'high', 'low', 'volume'")
    shift: int = Field(..., ge=0, description="Desplazamiento temporal t-shift (0 = barra actual)")


class ConditionNode(BaseModel):
    """Nodo at?mico de condici?n dentro del ?rbol de reglas (AST)."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    left: Union[IndicatorSpec, str, float] = Field(..., description="Lado izquierdo de la comparaci?n")
    op: ComparisonOp = Field(..., description="Operador de comparaci?n")
    right: Union[IndicatorSpec, str, float] = Field(..., description="Lado derecho de la comparaci?n")


# Alias can?nico
RuleCondition = ConditionNode


class RuleTree(BaseModel):
    """?rbol can?nico de reglas l?gicas de entrada sin defaults silenciosos (P02-003-01 / P02-007)."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    logic: LogicalOp = Field(..., description="Operador l?gico de composici?n: AND / OR")
    direction: Literal["LONG", "SHORT", "BOTH"] = Field(..., description="Direcci?n de la operaci?n")
    conditions: Optional[List[ConditionNode]] = Field(
        default=None,
        description="Lista de condiciones at?micas para direcci?n LONG o SHORT",
    )
    long_conditions: Optional[List[ConditionNode]] = Field(
        default=None,
        description="Ramas expl?citas de condiciones LONG (estrictamente obligatorio cuando direction es BOTH)",
    )
    short_conditions: Optional[List[ConditionNode]] = Field(
        default=None,
        description="Ramas expl?citas de condiciones SHORT (estrictamente obligatorio cuando direction es BOTH)",
    )

    @model_validator(mode="after")
    def validate_direction_branches(self) -> RuleTree:
        """Valida que la configuraci?n de ramas cumpla con la sem?ntica determinista Fail-Closed."""
        if self.direction in ("LONG", "SHORT"):
            has_conditions = bool(self.conditions and len(self.conditions) > 0)
            has_long = self.direction == "LONG" and bool(self.long_conditions and len(self.long_conditions) > 0)
            has_short = self.direction == "SHORT" and bool(self.short_conditions and len(self.short_conditions) > 0)
            if not has_conditions and not has_long and not has_short:
                raise InvalidStrategyError(
                    f"Para direction '{self.direction}', se requiere una lista no vac?a de 'conditions'."
                )
        elif self.direction == "BOTH":
            # Prohibici?n terminante de inversi?n heur?stica de operadores (Fail-Closed P02-007)
            if not self.long_conditions or len(self.long_conditions) == 0:
                raise InvalidStrategyError(
                    "Para direction 'BOTH', es estrictamente obligatorio proporcionar ramas expl?citas 'long_conditions'. "
                    "La inversi?n heur?stica de operadores est? prohibida (Fail-Closed)."
                )
            if not self.short_conditions or len(self.short_conditions) == 0:
                raise InvalidStrategyError(
                    "Para direction 'BOTH', es estrictamente obligatorio proporcionar ramas expl?citas 'short_conditions'. "
                    "La inversi?n heur?stica de operadores est? prohibida (Fail-Closed)."
                )
        return self


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
    """Modelo can?nico de salida, SL, TP y gesti?n de trailing stop sin defaults silenciosos (P02-003-01)."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    sl_type: StopLossType = Field(..., description="Tipo expl?cito de Stop Loss")
    sl_value: float = Field(..., gt=0.0, description="Valor del Stop Loss (e.g. 2.0x ATR o 1.5%)")
    tp_type: TakeProfitType = Field(..., description="Tipo expl?cito de Take Profit")
    tp_value: float = Field(..., gt=0.0, description="Valor del Take Profit (e.g. 3.0 R:R)")
    
    trail_after_r: Optional[float] = Field(default=None, gt=0.0, description="Mueve a BE tras alcanzar R m?ltiplos")
    time_stop_bars: Optional[int] = Field(default=None, ge=1, description="Cierre por tiempo tras N barras")


class SizingType(str, Enum):
    RISK_PCT_EQUITY = "RISK_PCT_EQUITY"
    FIXED_CONTRACTS = "FIXED_CONTRACTS"
    FIXED_USD = "FIXED_USD"
    VOLATILITY_ADJUSTED = "VOLATILITY_ADJUSTED"


class SizingAndRisk(BaseModel):
    """Gesti?n de dimensionamiento de posici?n y l?mites de riesgo sin defaults silenciosos (P02-003-01)."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    sizing_type: SizingType = Field(..., description="Tipo de dimensionamiento expl?cito")
    risk_value: float = Field(..., gt=0.0, description="Riesgo base por trade e.g. 1.0% o 1 contrato")
    max_open_positions: int = Field(..., ge=1, le=10, description="M?ximo de posiciones simult?neas")
    max_daily_loss_usd: Optional[float] = Field(default=None, gt=0.0)


class SessionWindow(BaseModel):
    """Ventana horaria de sesi?n operativa permitida en horario UTC sin defaults silenciosos."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    start_time_utc: str = Field(..., description="HH:MM UTC apertura")
    end_time_utc: str = Field(..., description="HH:MM UTC cierre")
    close_at_eod: bool = Field(..., description="Cerrar posiciones al final del d?a")
    allowed_days: List[int] = Field(..., description="Lista expl?cita de d?as permitidos (0=Lun, 4=Vie)")


class TargetInstrument(BaseModel):
    """Especificaci?n can?nica del instrumento objetivo sin defaults silenciosos."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    symbol: str = Field(..., description="S?mbolo base normalizado e.g. NQ, BTCUSDT")
    asset_class: str = Field(..., description="FUTURES, CRYPTO_PERP, FOREX")
    timeframe: str = Field(..., description="1m, 5m, 15m, 1h, 4h, 1d")
    exchange: str = Field(..., description="CME, BINGX, BINANCE, FOREX")


class ProvenanceMetadata(BaseModel):
    """Metadatos de procedencia y autor?a criptogr?fica sin defaults silenciosos (P02-003-01)."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    author: str = Field(..., description="Identidad del autor o subagente creador")
    engine_version: str = Field(..., description="Versi?n exacta del motor")
    policy_version: str = Field(..., description="Versi?n exacta de la pol?tica de ejecuci?n")
    created_at_utc: str = Field(..., description="Marca temporal ISO UTC de creaci?n")
    parent_hash: Optional[str] = Field(default=None, description="Hash SHA-256 de la estrategia padre en caso de mutaci?n")
    mutation_type: Optional[str] = Field(default=None, description="Tipo expl?cito de mutaci?n aplicada")


class ExecutableRuntimeInstruction(BaseModel):
    """Instrucci?n de ejecuci?n en runtime compilada que preserva 100% de la sem?ntica can?nica (P02-003-02 / P02-007)."""
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
    compiled_conditions: List[Dict[str, Any]] = Field(default_factory=list)
    compiled_long_conditions: List[Dict[str, Any]] = Field(default_factory=list)
    compiled_short_conditions: List[Dict[str, Any]] = Field(default_factory=list)
    sl_config: Dict[str, Any]
    tp_config: Dict[str, Any]
    sizing_config: Dict[str, Any]
    session_config: Optional[Dict[str, Any]] = None
    provenance: Dict[str, Any]


class CanonicalStrategy(BaseModel):
    """Entidad SSOT Inmutable de Estrategia Cuantitativa (Fase 02 Rework AG2-P02-007)."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    strategy_id: str = Field(..., description="ID un?voco determinista")
    name: str = Field(..., description="Nombre humano e.g. NQ Trend Breakout")
    version: str = Field(..., description="Versi?n sem?ntica expl?cita de la estrategia e.g. 1.0.0")
    symbol: str = Field(..., description="S?mbolo base e.g. NQ, BTCUSDT, EURUSD")
    timeframe: str = Field(..., description="Timeframe e.g. 1m, 5m, 15m, 1h, 4h, 1d")
    route: Literal["ULTRA", "FONDEO", "PORTFOLIO"] = Field(..., description="Ruta de explotaci?n")
    archetype: str = Field(..., description="Arquetipo cuantitativo")

    entry_rules: RuleTree = Field(..., description="Reglas de entrada")
    exit_rules: ExitModel = Field(..., description="Reglas de salida y SL/TP")
    sizing_and_risk: SizingAndRisk = Field(..., description="Gesti?n de tama?o y riesgo")
    session_window: Optional[SessionWindow] = None
    provenance: ProvenanceMetadata = Field(..., description="Metadatos de procedencia y versiones de motor")
    
    strategy_hash: str = Field(..., min_length=64, max_length=64, description="Hash SHA-256 inmutable de la identidad sem?ntica completa")

    @classmethod
    def compute_strategy_hash(cls, payload: Dict[str, Any]) -> str:
        """Calcula el hash determinista SHA-256 can?nico cubriendo la identidad sem?ntica completa (P02-003-01)."""
        raw_json = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(raw_json.encode("utf-8")).hexdigest()

    def get_semantic_payload(self) -> Dict[str, Any]:
        """Extrae el payload sem?ntico completo para el c?lculo de hash inmutable."""
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
        """Fabrica una CanonicalStrategy inmutable y calcula su hash determinista sobre todos los campos sem?nticos."""
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
        """Verifica que el strategy_hash coincida exactamente con la identidad sem?ntica completa."""
        payload = self.get_semantic_payload()
        expected = self.compute_strategy_hash(payload)
        return self.strategy_hash == expected

    def compile_to_runtime(self) -> ExecutableRuntimeInstruction:
        """Compila la CanonicalStrategy en una instrucci?n ejecutable de runtime preservando 100% de la sem?ntica (P02-003-02 / P02-007)."""
        if not self.verify_integrity():
            raise StrategyIntegrityError(f"Estrategia {self.strategy_id} tiene hash corrupto o no coincide con su identidad sem?ntica.")

        def _compile_nodes(nodes: Optional[List[ConditionNode]]) -> List[Dict[str, Any]]:
            if not nodes:
                return []
            res = []
            for cond in nodes:
                left_val = cond.left.model_dump() if isinstance(cond.left, IndicatorSpec) else cond.left
                right_val = cond.right.model_dump() if isinstance(cond.right, IndicatorSpec) else cond.right
                res.append({
                    "left": left_val,
                    "op": cond.op.value if isinstance(cond.op, ComparisonOp) else str(cond.op),
                    "right": right_val,
                })
            return res

        raw_conds = _compile_nodes(self.entry_rules.conditions)
        raw_long = _compile_nodes(self.entry_rules.long_conditions)
        raw_short = _compile_nodes(self.entry_rules.short_conditions)

        if self.entry_rules.direction == "LONG":
            compiled_long_conditions = raw_long if raw_long else raw_conds
            compiled_short_conditions = []
            compiled_conditions = compiled_long_conditions
        elif self.entry_rules.direction == "SHORT":
            compiled_long_conditions = []
            compiled_short_conditions = raw_short if raw_short else raw_conds
            compiled_conditions = compiled_short_conditions
        elif self.entry_rules.direction == "BOTH":
            if not raw_long or not raw_short:
                raise InvalidStrategyError(
                    f"Estrategia '{self.strategy_id}' con direction 'BOTH' requiere ramas expl?citas 'long_conditions' y 'short_conditions'."
                )
            compiled_long_conditions = raw_long
            compiled_short_conditions = raw_short
            compiled_conditions = raw_long + raw_short
        else:
            raise InvalidStrategyError(f"Direcci?n '{self.entry_rules.direction}' no soportada.")

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
            compiled_conditions=compiled_conditions,
            compiled_long_conditions=compiled_long_conditions,
            compiled_short_conditions=compiled_short_conditions,
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

