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
    is_24_7: bool = Field(True, description="True si opera en régimen continuo 24/7 sin restricción horaria")
    timezone: Optional[str] = Field(None, description="Zona horaria e.g. America/New_York, UTC")
    start_time: Optional[str] = Field(None, description="Hora de inicio HH:MM")
    end_time: Optional[str] = Field(None, description="Hora de fin HH:MM")
    force_close_at_end: bool = Field(False, description="Cerrar forzosamente al fin de sesión diaria")


class TargetInstrument(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    symbol: str = Field(..., description="Símbolo canónico e.g. NQ, ES, MES, MNQ, BTC-USDT, ETH-USDT")
    exchange: Optional[str] = Field(None, description="CME, BINGX, BINANCE, RITHMIC (si es None, se resuelve de CANONICAL_COST_REGISTRY)")
    contract_type: Optional[str] = Field(None, description="FUTURES, PERPETUAL, SPOT (si es None, se resuelve de CANONICAL_COST_REGISTRY)")
    point_value: Optional[float] = Field(None, gt=0.0, description="Valor del punto monetario")
    tick_size: Optional[float] = Field(None, gt=0.0, description="Tamaño mínimo de variación de precio")


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


from contracts.evidence_bundle import EvidenceBundle


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
    evidence_bundle: Optional[EvidenceBundle] = Field(default=None, description="Paquete de evidencia criptográfica verificado")

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
        """Calcula el hash criptográfico SHA-256 inmutable de la definición canónica (excluyendo metadata, status y evidence_bundle)."""
        canonical_dict = self.model_dump(exclude={"metadata": True, "status": True, "evidence_bundle": True})
        serialized = json.dumps(canonical_dict, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def attach_evidence_bundle(self, bundle: EvidenceBundle) -> CanonicalStrategy:
        """Asocia un EvidenceBundle verificado a la estrategia validando linaje criptográfico."""
        ast_sha = self.compute_sha256()
        if bundle.strategy_sha256 != ast_sha:
            raise ValueError(
                f"DISCREPANCIA_LINEAJE: EvidenceBundle.strategy_sha256 ({bundle.strategy_sha256}) "
                f"no coincide con el SHA-256 canónico de la estrategia ({ast_sha})."
            )
        bundle.verify_integrity(expected_strategy_sha256=ast_sha)
        return self.model_copy(update={"evidence_bundle": bundle})
