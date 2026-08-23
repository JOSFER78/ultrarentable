"""contracts/canonical_strategy.py
Modelo Canónico Unificado de Estrategia (CanonicalStrategy v2.0.0).
Garantiza interoperabilidad total entre FastEngine, SQX, Semantic AI y Execution Brokers.
"""

from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrategyLifecycleStatus(str, Enum):
    GENERATED = "GENERATED"
    BACKTESTED = "BACKTESTED"
    OOS_PASSED = "OOS_PASSED"
    ROBUSTNESS_PASSED = "ROBUSTNESS_PASSED"
    EVIDENCE_APPROVED = "EVIDENCE_APPROVED"
    CANDIDATE = "CANDIDATE"
    INCUBATION_PAPER = "INCUBATION_PAPER"
    LIVE_ACTIVE = "LIVE_ACTIVE"
    REJECTED = "REJECTED"
    RETIRED = "RETIRED"


class ExecutionTrack(str, Enum):
    TRACK_FONDEO = "TRACK_FONDEO"
    TRACK_ULTRA = "TRACK_ULTRA"
    TRACK_HYBRID = "TRACK_HYBRID"


class ComparisonOperator(str, Enum):
    GREATER_THAN = "GREATER_THAN"
    LESS_THAN = "LESS_THAN"
    GREATER_EQUAL = "GREATER_EQUAL"
    LESS_EQUAL = "LESS_EQUAL"
    CROSSES_ABOVE = "CROSSES_ABOVE"
    CROSSES_BELOW = "CROSSES_BELOW"
    EQUALS = "EQUALS"


class IndicatorSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    name: str = Field(..., description="Nombre del indicador e.g. RSI, EMA, ATR, MACD, BOLLINGER")
    timeframe: str = Field("1h", description="Timeframe e.g. 1m, 5m, 15m, 1h, 4h, 1d")
    period: int = Field(14, ge=1, description="Periodo principal del indicador")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parámetros adicionales e.g. std_dev: 2.0")


class RuleCondition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    left_indicator: IndicatorSpec
    operator: ComparisonOperator
    right_indicator: Optional[IndicatorSpec] = None
    threshold_value: Optional[float] = None
    lookback_bars: int = Field(0, ge=0, description="Offset de barras hacia atrás")


class RuleTree(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    long_conditions: List[RuleCondition] = Field(default_factory=list)
    short_conditions: List[RuleCondition] = Field(default_factory=list)
    logical_operator: str = Field("AND", description="AND / OR para combinar condiciones")


class SessionWindow(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    timezone: str = "America/New_York"
    start_time: str = "09:30"
    end_time: str = "16:00"
    force_close_at_end: bool = True


class TargetInstrument(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    symbol: str = Field(..., description="e.g. NQ, ES, MES, MNQ, BTC-USDT, ETH-USDT")
    exchange: str = Field("CME", description="CME, BINGX, BINANCE, RITHMIC")
    contract_type: str = Field("FUTURES", description="FUTURES, PERPETUAL, SPOT")
    point_value: float = Field(20.0, gt=0.0)
    tick_size: float = Field(0.25, gt=0.0)


class ExitModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    stop_loss_atr_mult: Optional[float] = None
    stop_loss_ticks: Optional[int] = None
    take_profit_atr_mult: Optional[float] = None
    take_profit_ticks: Optional[int] = None
    trailing_stop_atr_mult: Optional[float] = None
    break_even_atr_mult: Optional[float] = None
    max_bars_in_trade: Optional[int] = None


class SizingAndRisk(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    base_risk_pct: float = Field(1.0, ge=0.1, le=100.0)
    max_contracts_or_lots: float = Field(5.0, ge=0.01)
    base_leverage: float = Field(1.0, ge=1.0, le=500.0)
    pyramiding_max_layers: int = Field(0, ge=0, le=5)
    pyramiding_reinvest_ratio: float = Field(0.40, ge=0.0, le=1.0)


class ProvenanceMetadata(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    source_engine: str = Field(..., description="strategyquant, internal_genetic, semantic_ai, manual")
    project_name: Optional[str] = None
    databank_name: Optional[str] = None
    build_id: Optional[str] = None
    created_timestamp_utc: int = Field(...)
    author_or_agent: str = Field("SYSTEM_GENERATOR")


class CanonicalStrategy(BaseModel):
    """Contrato Canónico Universal de Estrategia para Ultrarentable V2."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: str = "2.0.0"
    strategy_id: str = Field(..., description="ID único e.g. UR-CAND-BTC-00140")
    name: str = Field(...)
    target_track: ExecutionTrack = ExecutionTrack.TRACK_FONDEO
    status: StrategyLifecycleStatus = StrategyLifecycleStatus.GENERATED
    
    instrument: TargetInstrument
    timeframe: str = Field("1h")
    session: SessionWindow = Field(default_factory=SessionWindow)
    
    rules: RuleTree = Field(default_factory=RuleTree)
    exits: ExitModel = Field(default_factory=ExitModel)
    sizing_and_risk: SizingAndRisk = Field(default_factory=SizingAndRisk)
    
    provenance: ProvenanceMetadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def validate_metadata_purity(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        forbidden_keys = {"risk", "leverage", "stop_loss", "take_profit", "timeframe", "symbol", "rules", "sizing", "session"}
        if v:
            for k in v.keys():
                if k.lower() in forbidden_keys:
                    raise ValueError(f"VIOLACION_SSOT_METADATA: Parámetro funcional '{k}' prohibido en metadata administrativa.")
        return v

    def compute_sha256(self) -> str:
        """Calcula el hash criptográfico SHA-256 inmutable de la definición canónica."""
        canonical_dict = self.model_dump(exclude={"metadata": True, "status": True})
        serialized = json.dumps(canonical_dict, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
