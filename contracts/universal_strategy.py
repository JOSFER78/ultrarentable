"""contracts/universal_strategy.py
Universal Strategy Specification AST and Canonical Models (v3.0.0).

DOCTRINA ZERO-MOCKS & UNIVERSAL DYNAMIC SPECIFICATION:
- Describes any quantitative trading strategy dynamically without hardcoded assumptions.
- Pure immutable Pydantic models.
- Serialized to canonical deterministically-ordered JSON for SHA-256 fingerprinting.
"""

from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrategyFamily(str, Enum):
    TREND_FOLLOWING = "TREND_FOLLOWING"
    MOMENTUM_BREAKOUT = "MOMENTUM_BREAKOUT"
    MEAN_REVERSION = "MEAN_REVERSION"
    VOLATILITY_EXPANSION = "VOLATILITY_EXPANSION"
    STATISTICAL_ARBITRAGE = "STATISTICAL_ARBITRAGE"
    MULTI_TIMEFRAME = "MULTI_TIMEFRAME"
    CUSTOM_DSL = "CUSTOM_DSL"


class IndicatorType(str, Enum):
    # Moving Averages
    SMA = "SMA"
    EMA = "EMA"
    WMA = "WMA"
    HMA = "HMA"
    DEMA = "DEMA"
    TEMA = "TEMA"
    VWAP = "VWAP"
    # Oscillators & Momentum
    RSI = "RSI"
    STOCHASTIC_K = "STOCHASTIC_K"
    STOCHASTIC_D = "STOCHASTIC_D"
    MACD_LINE = "MACD_LINE"
    MACD_SIGNAL = "MACD_SIGNAL"
    MACD_HIST = "MACD_HIST"
    ROC = "ROC"
    CCI = "CCI"
    WILLIAMS_R = "WILLIAMS_R"
    # Volatility & Bands
    ATR = "ATR"
    BOLLINGER_UPPER = "BOLLINGER_UPPER"
    BOLLINGER_MIDDLE = "BOLLINGER_MIDDLE"
    BOLLINGER_LOWER = "BOLLINGER_LOWER"
    BOLLINGER_WIDTH = "BOLLINGER_WIDTH"
    KELTNER_UPPER = "KELTNER_UPPER"
    KELTNER_LOWER = "KELTNER_LOWER"
    DONCHIAN_HIGH = "DONCHIAN_HIGH"
    DONCHIAN_LOW = "DONCHIAN_LOW"
    DONCHIAN_MID = "DONCHIAN_MID"
    STDDEV = "STDDEV"
    PARKINSON_VOLATILITY = "PARKINSON_VOLATILITY"
    # Extremes & Volume
    HIGHEST = "HIGHEST"
    LOWEST = "LOWEST"
    VOLUME_RATIO = "VOLUME_RATIO"
    VOLUME_SMA = "VOLUME_SMA"
    # Raw Series
    PRICE_OPEN = "PRICE_OPEN"
    PRICE_HIGH = "PRICE_HIGH"
    PRICE_LOW = "PRICE_LOW"
    PRICE_CLOSE = "PRICE_CLOSE"
    PRICE_VOLUME = "PRICE_VOLUME"


class ComparisonOperator(str, Enum):
    GREATER_THAN = "GREATER_THAN"       # >
    GREATER_EQUAL = "GREATER_EQUAL"     # >=
    LESS_THAN = "LESS_THAN"             # <
    LESS_EQUAL = "LESS_EQUAL"           # <=
    EQUALS = "EQUALS"                   # ==
    CROSSES_ABOVE = "CROSSES_ABOVE"     # Crosses above (prev <= and curr >)
    CROSSES_BELOW = "CROSSES_BELOW"     # Crosses below (prev >= and curr <)


class LogicalOperator(str, Enum):
    ALL = "ALL"  # AND
    ANY = "ANY"  # OR


class ValueSource(str, Enum):
    SERIES = "SERIES"
    INDICATOR = "INDICATOR"
    CONSTANT = "CONSTANT"


class DynamicValueNode(BaseModel):
    """Nodo dinámico de valor: puede ser una serie de precios, un indicador calculado o una constante."""
    model_config = ConfigDict(frozen=True, extra="forbid")
    source_type: ValueSource
    indicator_type: Optional[IndicatorType] = None
    period: Optional[int] = Field(None, ge=1, description="Período principal de cálculo")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parámetros secundarios e.g. std_dev, fast_period")
    timeframe: Optional[str] = Field(None, description="Timeframe para cálculos multi-timeframe (e.g. '1h', '4h')")
    offset_bars: int = Field(default=0, ge=0, description="Desplazamiento temporal hacia el pasado (0 = barra actual)")
    constant_value: Optional[float] = None

    @classmethod
    def series(cls, indicator: IndicatorType, offset: int = 0) -> DynamicValueNode:
        return cls(source_type=ValueSource.SERIES, indicator_type=indicator, offset_bars=offset)

    @classmethod
    def indicator(cls, indicator: IndicatorType, period: int, params: Optional[Dict[str, Any]] = None, timeframe: Optional[str] = None, offset: int = 0) -> DynamicValueNode:
        return cls(source_type=ValueSource.INDICATOR, indicator_type=indicator, period=period, parameters=params or {}, timeframe=timeframe, offset_bars=offset)

    @classmethod
    def constant(cls, val: float) -> DynamicValueNode:
        return cls(source_type=ValueSource.CONSTANT, constant_value=float(val))


class ConditionNode(BaseModel):
    """Condición atómica de comparación entre dos nodos de valor."""
    model_config = ConfigDict(frozen=True, extra="forbid")
    left: DynamicValueNode
    operator: ComparisonOperator
    right: DynamicValueNode
    name: Optional[str] = Field(None, description="Etiqueta descriptiva opcional")


class RuleGroup(BaseModel):
    """Grupo lógico de condiciones evaluadas bajo ALL (AND) o ANY (OR)."""
    model_config = ConfigDict(frozen=True, extra="forbid")
    logical_operator: LogicalOperator = Field(LogicalOperator.ALL)
    conditions: List[ConditionNode] = Field(default_factory=list)


class DynamicEntryRules(BaseModel):
    """Reglas completas de entrada para posiciones Long y Short."""
    model_config = ConfigDict(frozen=True, extra="forbid")
    long_rules: RuleGroup = Field(default_factory=RuleGroup)
    short_rules: RuleGroup = Field(default_factory=RuleGroup)
    allow_long: bool = Field(True)
    allow_short: bool = Field(True)


class DynamicExitRules(BaseModel):
    """Reglas de gestión de salida: Stop Loss, Take Profit, Trailing Stop, Break-Even, y tiempo máximo."""
    model_config = ConfigDict(frozen=True, extra="forbid")
    # Stop Loss
    stop_loss_type: Literal["ATR_MULTIPLE", "PERCENTAGE", "FIXED_TICKS", "NONE"] = "ATR_MULTIPLE"
    stop_loss_value: float = Field(2.0, gt=0.0, description="Múltiplo ATR, % o ticks para Stop Loss")
    stop_loss_atr_period: int = Field(14, ge=1)
    
    # Take Profit
    take_profit_type: Literal["ATR_MULTIPLE", "PERCENTAGE", "FIXED_TICKS", "RISK_REWARD_MULTIPLE", "NONE"] = "ATR_MULTIPLE"
    take_profit_value: float = Field(6.0, gt=0.0, description="Múltiplo ATR, % o R:R para Take Profit")
    take_profit_atr_period: int = Field(14, ge=1)

    # Break-Even
    break_even_enabled: bool = Field(False)
    break_even_trigger_r: float = Field(1.5, gt=0.0, description="Ganancia en múltiplos R para mover SL a BE")
    break_even_offset_ticks: int = Field(0, ge=0, description="Colchón en ticks sobre el precio de entrada")

    # Trailing Stop
    trailing_stop_enabled: bool = Field(False)
    trailing_trigger_r: float = Field(2.0, gt=0.0, description="Ganancia en R para activar trailing")
    trailing_step_atr_mult: float = Field(1.5, gt=0.0, description="Distancia ATR del trailing")

    # Max Bars in Trade
    max_bars_in_trade: Optional[int] = Field(None, ge=1, description="Cierre por tiempo máximo en barras")


class TimeAndSessionFilter(BaseModel):
    """Filtros de horario y sesiones operativas."""
    model_config = ConfigDict(frozen=True, extra="forbid")
    enabled: bool = Field(False)
    timezone: str = Field("America/New_York")
    session_start: str = Field("09:30", description="HH:MM")
    session_end: str = Field("16:00", description="HH:MM")
    close_all_positions_at_session_end: bool = Field(False)
    allowed_days_of_week: List[int] = Field(default_factory=lambda: [0, 1, 2, 3, 4], description="0=Mon, 4=Fri")


class StrategySpecification(BaseModel):
    """Especificación canónica completa de una estrategia cuantitativa."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    strategy_id: str = Field(..., description="Identificador unívoco canónico")
    version: str = Field(default="3.0.0", description="Versión del contrato de estrategia")
    family: StrategyFamily = Field(StrategyFamily.MOMENTUM_BREAKOUT)
    target_symbol: str = Field(..., description="Símbolo del instrumento base e.g. BTC-USDT, NQ, EURUSD")
    base_timeframe: str = Field(..., description="Timeframe base de ejecución e.g. 1m, 5m, 15m, 1h, 4h, 1d")
    
    entry_rules: DynamicEntryRules = Field(default_factory=DynamicEntryRules)
    exit_rules: DynamicExitRules = Field(default_factory=DynamicExitRules)
    time_filter: TimeAndSessionFilter = Field(default_factory=TimeAndSessionFilter)

    # Identificadores de políticas externas
    risk_policy_id: str = Field(default="DEFAULT_RISK", description="ID del modelo de riesgo a asociar")
    execution_policy_id: str = Field(default="DEFAULT_EXECUTION", description="ID del modelo de ejecución")
    
    # Metadatos del descubrimiento
    dataset_reference_id: str = Field(..., description="ID del dataset donde fue descubierta")
    dataset_sha256: str = Field(..., description="Hash SHA256 del dataset base")
    
    def canonical_json(self) -> str:
        """Serialización determinista estricta para huella SHA-256."""
        return json.dumps(self.model_dump(), sort_keys=True, separators=(",", ":"))

    def compute_hash(self) -> str:
        """Calcula el hash SHA-256 inmutable de la especificación."""
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()
