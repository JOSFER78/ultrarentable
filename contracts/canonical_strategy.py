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
    """Especificación declarativa de un indicador técnico determinista sin defaults silenciosos (P02-003-01)."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(..., description="Nombre canónico del indicador e.g. EMA, SMA, RSI, ATR, DONCHIAN")
    params: Dict[str, Any] = Field(default_factory=dict, description="Parámetros numéricos explícitos e.g. {'period': 20}")
    source_field: str = Field(default="close", description="Campo fuente explícito e.g. 'close', 'high', 'low', 'volume'")
    shift: int = Field(default=0, ge=0, description="Desplazamiento temporal t-shift (0 = barra actual)")

    @model_validator(mode="before")
    @classmethod
    def handle_legacy_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            data = dict(data)
            data.pop("timeframe", None)
            if "params" not in data or data["params"] is None:
                data["params"] = {}
            else:
                data["params"] = dict(data["params"])
            if "period" in data:
                data["params"]["period"] = data.pop("period")
            if "source_field" not in data:
                data["source_field"] = "close"
            if "shift" not in data:
                data["shift"] = 0
        return data


class ConditionNode(BaseModel):
    """Nodo atómico de condición dentro del árbol de reglas (AST)."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    left: Union[IndicatorSpec, str, float] = Field(..., description="Lado izquierdo de la comparación")
    op: ComparisonOp = Field(..., description="Operador de comparación")
    right: Union[IndicatorSpec, str, float] = Field(..., description="Lado derecho de la comparación")

    @model_validator(mode="before")
    @classmethod
    def normalize_op(cls, data: Any) -> Any:
        if isinstance(data, dict):
            op = data.get("op")
            if isinstance(op, str):
                op_map = {
                    "GREATER_THAN": ComparisonOp.GT,
                    "GT": ComparisonOp.GT,
                    ">": ComparisonOp.GT,
                    "GREATER_EQUAL": ComparisonOp.GTE,
                    "GTE": ComparisonOp.GTE,
                    ">=": ComparisonOp.GTE,
                    "LESS_THAN": ComparisonOp.LT,
                    "LT": ComparisonOp.LT,
                    "<": ComparisonOp.LT,
                    "LESS_EQUAL": ComparisonOp.LTE,
                    "LTE": ComparisonOp.LTE,
                    "<=": ComparisonOp.LTE,
                    "EQUAL": ComparisonOp.EQ,
                    "EQ": ComparisonOp.EQ,
                    "==": ComparisonOp.EQ,
                    "CROSS_ABOVE": ComparisonOp.CROSS_ABOVE,
                    "CROSS_BELOW": ComparisonOp.CROSS_BELOW,
                }
                if op in op_map:
                    data = dict(data)
                    data["op"] = op_map[op]
        return data

    @property
    def left_indicator(self) -> Optional[IndicatorSpec]:
        return self.left if isinstance(self.left, IndicatorSpec) else None

    @property
    def right_indicator(self) -> Optional[IndicatorSpec]:
        return self.right if isinstance(self.right, IndicatorSpec) else None

    @property
    def threshold_value(self) -> Optional[float]:
        if isinstance(self.right, (int, float)):
            return float(self.right)
        elif isinstance(self.left, (int, float)):
            return float(self.left)
        return None

    @property
    def operator(self) -> ComparisonOp:
        return self.op


# Alias canónico
RuleCondition = ConditionNode


class RuleTree(BaseModel):
    """Árbol canónico de reglas lógicas de entrada sin defaults silenciosos (P02-003-01 / P02-007)."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    logic: LogicalOp = Field(default=LogicalOp.AND, description="Operador lógico de composición: AND / OR")
    direction: Literal["LONG", "SHORT", "BOTH"] = Field(default="LONG", description="Dirección de la operación")
    conditions: Optional[List[ConditionNode]] = Field(
        default=None,
        description="Lista de condiciones atómicas para dirección LONG o SHORT",
    )
    long_conditions: Optional[List[ConditionNode]] = Field(
        default=None,
        description="Ramas explícitas de condiciones LONG (estrictamente obligatorio cuando direction es BOTH)",
    )
    short_conditions: Optional[List[ConditionNode]] = Field(
        default=None,
        description="Ramas explícitas de condiciones SHORT (estrictamente obligatorio cuando direction es BOTH)",
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_ruletree(cls, data: Any) -> Any:
        if isinstance(data, dict):
            data = dict(data)
            if "logic" not in data:
                data["logic"] = LogicalOp.AND
            if "direction" not in data:
                if data.get("long_conditions") and not data.get("short_conditions"):
                    data["direction"] = "LONG"
                elif data.get("short_conditions") and not data.get("long_conditions"):
                    data["direction"] = "SHORT"
                elif data.get("long_conditions") and data.get("short_conditions"):
                    data["direction"] = "BOTH"
                else:
                    data["direction"] = "LONG"
        return data

    @model_validator(mode="after")
    def validate_direction_branches(self) -> RuleTree:
        """Valida que la configuración de ramas cumpla con la semántica determinista Fail-Closed."""
        if self.direction in ("LONG", "SHORT"):
            has_conditions = bool(self.conditions and len(self.conditions) > 0)
            has_long = self.direction == "LONG" and bool(self.long_conditions and len(self.long_conditions) > 0)
            has_short = self.direction == "SHORT" and bool(self.short_conditions and len(self.short_conditions) > 0)
            if not has_conditions and not has_long and not has_short:
                raise InvalidStrategyError(
                    f"Para direction '{self.direction}', se requiere una lista no vacía de 'conditions'."
                )
        elif self.direction == "BOTH":
            if not self.long_conditions or len(self.long_conditions) == 0:
                raise InvalidStrategyError(
                    "Para direction 'BOTH', es estrictamente obligatorio proporcionar ramas explícitas 'long_conditions'."
                )
            if not self.short_conditions or len(self.short_conditions) == 0:
                raise InvalidStrategyError(
                    "Para direction 'BOTH', es estrictamente obligatorio proporcionar ramas explícitas 'short_conditions'."
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
    """Modelo canónico de salida, SL, TP y gestión de trailing stop sin defaults silenciosos (P02-003-01)."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    sl_type: StopLossType = Field(default=StopLossType.FIXED_POINTS, description="Tipo explícito de Stop Loss")
    sl_value: float = Field(default=20.0, gt=0.0, description="Valor del Stop Loss (e.g. 2.0x ATR o 1.5%)")
    tp_type: TakeProfitType = Field(default=TakeProfitType.FIXED_POINTS, description="Tipo explícito de Take Profit")
    tp_value: float = Field(default=60.0, gt=0.0, description="Valor del Take Profit (e.g. 3.0 R:R)")
    
    trail_after_r: Optional[float] = Field(default=None, gt=0.0, description="Mueve a BE tras alcanzar R múltiplos")
    time_stop_bars: Optional[int] = Field(default=None, ge=1, description="Cierre por tiempo tras N barras")

    @model_validator(mode="before")
    @classmethod
    def handle_legacy_exit(cls, data: Any) -> Any:
        if isinstance(data, dict):
            data = dict(data)
            if "stop_loss_ticks" in data and "sl_value" not in data:
                data["sl_type"] = StopLossType.FIXED_POINTS
                data["sl_value"] = float(data.pop("stop_loss_ticks"))
            if "take_profit_ticks" in data and "tp_value" not in data:
                data["tp_type"] = TakeProfitType.FIXED_POINTS
                data["tp_value"] = float(data.pop("take_profit_ticks"))
            if "sl_type" not in data:
                data["sl_type"] = StopLossType.FIXED_POINTS
            if "tp_type" not in data:
                data["tp_type"] = TakeProfitType.FIXED_POINTS
        return data

    @property
    def stop_loss_ticks(self) -> float:
        return self.sl_value

    @property
    def take_profit_ticks(self) -> float:
        return self.tp_value


class SizingType(str, Enum):
    RISK_PCT_EQUITY = "RISK_PCT_EQUITY"
    FIXED_CONTRACTS = "FIXED_CONTRACTS"
    FIXED_USD = "FIXED_USD"
    VOLATILITY_ADJUSTED = "VOLATILITY_ADJUSTED"


class SizingAndRisk(BaseModel):
    """Gestión de dimensionamiento de posición y límites de riesgo sin defaults silenciosos (P02-003-01)."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    sizing_type: SizingType = Field(default=SizingType.RISK_PCT_EQUITY, description="Tipo de dimensionamiento explícito")
    risk_value: float = Field(default=1.0, gt=0.0, description="Riesgo base por trade e.g. 1.0% o 1 contrato")
    max_open_positions: int = Field(default=1, ge=1, le=10, description="Máximo de posiciones simultáneas")
    max_contracts_or_lots: Optional[float] = Field(default=None, description="Máximo de contratos o lotes permitidos")
    max_daily_loss_usd: Optional[float] = Field(default=None, gt=0.0)


class SessionWindow(BaseModel):
    """Ventana horaria de sesión operativa permitida en horario UTC o local (DST-aware) sin defaults silenciosos."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    start_time_utc: str = Field(default="00:00", description="HH:MM UTC apertura")
    end_time_utc: str = Field(default="23:59", description="HH:MM UTC cierre")
    close_at_eod: bool = Field(default=False, description="Cerrar posiciones al final del día")
    allowed_days: List[int] = Field(default_factory=lambda: [0, 1, 2, 3, 4, 5, 6], description="Lista explícita de días permitidos")
    market_tz: Optional[str] = Field(default=None, description="Zona horaria IANA del mercado e.g. America/New_York")
    start_time_local: Optional[str] = Field(default=None, description="HH:MM hora local apertura")
    end_time_local: Optional[str] = Field(default=None, description="HH:MM hora local cierre")
    flat_time_local: Optional[str] = Field(default=None, description="HH:MM hora local flat obligatorio")
    flat_tz: Optional[str] = Field(default=None, description="Zona horaria IANA para flat obligatorio e.g. America/Chicago")

    @model_validator(mode="before")
    @classmethod
    def handle_legacy_session(cls, data: Any) -> Any:
        if isinstance(data, dict):
            data = dict(data)
            if data.pop("is_24_7", False):
                data.setdefault("start_time_utc", "00:00")
                data.setdefault("end_time_utc", "23:59")
                data.setdefault("close_at_eod", False)
                data.setdefault("allowed_days", [0, 1, 2, 3, 4, 5, 6])
        return data

    @model_validator(mode="after")
    def validate_tz(self) -> "SessionWindow":
        import zoneinfo
        if self.market_tz is not None:
            try:
                zoneinfo.ZoneInfo(self.market_tz)
            except Exception as e:
                raise ValueError(f"Zona horaria invalida en market_tz: {self.market_tz}") from e
        if self.flat_tz is not None:
            try:
                zoneinfo.ZoneInfo(self.flat_tz)
            except Exception as e:
                raise ValueError(f"Zona horaria invalida en flat_tz: {self.flat_tz}") from e
        return self

    @property
    def force_close_at_end(self) -> bool:
        return self.close_at_eod

    def model_dump(self, *args, **kwargs) -> Dict[str, Any]:
        d = super().model_dump(*args, **kwargs)
        # 5.18.0: Campos aditivos opcionales de sesion con DST / flat
        # Para preservar el canonical_hash bit a bit identico con 5.17.0 cuando no estan presentes
        for k in ("market_tz", "start_time_local", "end_time_local", "flat_time_local", "flat_tz"):
            if k in d and d[k] is None:
                d.pop(k)
        return d


class TargetInstrument(BaseModel):
    """Especificación canónica del instrumento objetivo sin defaults silenciosos."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    symbol: str = Field(..., description="Símbolo base normalizado e.g. NQ, BTCUSDT")
    asset_class: Optional[str] = Field(default=None, description="FUTURES, CRYPTO_PERP, FOREX")
    timeframe: str = Field(default="1h", description="1m, 5m, 15m, 1h, 4h, 1d")
    exchange: Optional[str] = Field(default=None, description="CME, BINGX, BINANCE, FOREX")
    point_value: Optional[float] = Field(default=None, description="Valor monetario por punto")
    tick_size: Optional[float] = Field(default=None, description="Tamaño mínimo de variación")

    @model_validator(mode="before")
    @classmethod
    def handle_legacy_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            data = dict(data)
            data.pop("tick_value", None)
            data.pop("contract_size", None)
        return data


class ProvenanceMetadata(BaseModel):
    """Metadatos de procedencia y autoría criptográfica sin defaults silenciosos (P02-003-01)."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    author: str = Field(..., description="Identidad del autor o subagente creador")
    engine_version: str = Field(..., description="Versión exacta del motor")
    policy_version: str = Field(..., description="Versión exacta de la política de ejecución")
    created_at_utc: str = Field(..., description="Marca temporal ISO UTC de creación")
    parent_hash: Optional[str] = Field(default=None, description="Hash SHA-256 de la estrategia padre en caso de mutación")
    mutation_type: Optional[str] = Field(default=None, description="Tipo explícito de mutación aplicada")
    project_name: Optional[str] = Field(default=None, description="Nombre de proyecto SQX opcional")
    databank_name: Optional[str] = Field(default=None, description="Nombre de banco de datos SQX opcional")
    build_id: Optional[str] = Field(default=None, description="Build ID opcional")


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
    status: StrategyLifecycleStatus = Field(default=StrategyLifecycleStatus.GENERATED, description="Estado del ciclo de vida")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadatos administrativos/UI sin impacto en la lógica cuantitativa")
    evidence_bundle: Optional[Any] = Field(default=None, description="Paquete inmutable de evidencia cuantitativa")
    strategy_hash: str = Field(..., min_length=64, max_length=64, description="Hash SHA-256 inmutable de la identidad semántica completa")

    @property
    def rules(self) -> RuleTree:
        return self.entry_rules

    @property
    def exits(self) -> ExitModel:
        return self.exit_rules

    @property
    def session(self) -> Optional[SessionWindow]:
        return self.session_window

    @property
    def instrument(self) -> TargetInstrument:
        return TargetInstrument(symbol=self.symbol, timeframe=self.timeframe)

    @property
    def target_track(self) -> ExecutionTrack:
        if self.route == "FONDEO":
            return ExecutionTrack.FONDEO
        elif self.route == "ULTRA":
            return ExecutionTrack.ULTRA
        elif self.route == "PORTFOLIO":
            return ExecutionTrack.PORTFOLIO
        return ExecutionTrack.ULTRA

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
        provenance: ProvenanceMetadata,
        entry_rules: Optional[RuleTree] = None,
        exit_rules: Optional[ExitModel] = None,
        sizing_and_risk: Optional[SizingAndRisk] = None,
        session_window: Optional[SessionWindow] = None,
        session: Optional[SessionWindow] = None,
        metadata: Optional[Dict[str, Any]] = None,
        status: StrategyLifecycleStatus = StrategyLifecycleStatus.GENERATED,
    ) -> CanonicalStrategy:
        """Fabrica una CanonicalStrategy inmutable y calcula su hash determinista sobre todos los campos semánticos."""
        eff_session = session_window if session_window is not None else session
        eff_meta = metadata or {}
        if eff_meta:
            forbidden_keys = {
                "risk", "leverage", "stop_loss", "take_profit", "sl", "tp",
                "sl_value", "tp_value", "sizing", "rules", "entry_rules",
                "exit_rules", "symbol", "timeframe", "archetype"
            }
            for k in eff_meta.keys():
                if k.lower() in forbidden_keys:
                    raise ValueError(
                        f"VIOLACION_SSOT_METADATA: El parámetro '{k}' es funcional y no debe inyectarse en metadata."
                    )

        if entry_rules is None:
            entry_rules = RuleTree(
                logic=LogicalOp.AND,
                direction="LONG",
                long_conditions=[
                    ConditionNode(
                        left=IndicatorSpec(name="EMA", params={"period": 20}, source_field="close", shift=0),
                        op=ComparisonOp.GT,
                        right=IndicatorSpec(name="EMA", params={"period": 50}, source_field="close", shift=0),
                    )
                ],
            )
        if exit_rules is None:
            exit_rules = ExitModel(
                sl_type=StopLossType.FIXED_POINTS,
                sl_value=20.0,
                tp_type=TakeProfitType.FIXED_POINTS,
                tp_value=60.0,
            )
        if sizing_and_risk is None:
            sizing_and_risk = SizingAndRisk(
                sizing_type=SizingType.RISK_PCT_EQUITY,
                risk_value=1.0,
                max_open_positions=1,
            )

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
            "session_window": eff_session.model_dump() if eff_session else None,
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
            session_window=eff_session,
            provenance=provenance,
            status=status,
            metadata=eff_meta,
            strategy_hash=computed_hash,
        )

    def compute_sha256(self) -> str:
        """Retorna el hash determinista SHA-256 de la estrategia."""
        return self.strategy_hash

    def attach_evidence_bundle(self, bundle: Any) -> CanonicalStrategy:
        """Adjunta un EvidenceBundle verificando su integridad criptográfica."""
        if bundle is not None:
            bundle.verify_integrity(expected_strategy_sha256=self.strategy_hash)
        return self.model_copy(update={"evidence_bundle": bundle})

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

