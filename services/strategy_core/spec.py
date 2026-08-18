"""Formato Común y Neutro de Estrategia (StrategySpec) para Ultra Rentable V2.

Basado estrictamente en la Sección 7 del documento maestro PROYECTO_INTEGRAL_ULTRA_RENTABLE_FONDEO_PASO_A_PASO.md.
Desacopla las estrategias generadas por StrategyQuant X de NinjaTrader, Tradovate, Pine, EasyLanguage o Python.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator


class AssetClass(str, Enum):
    FUTURES = "FUTURES"
    CRYPTO = "CRYPTO"
    PERPETUAL = "PERPETUAL"
    FOREX = "FOREX"
    SPOT = "SPOT"


class StrategySource(str, Enum):
    STRATEGYQUANT_MCP = "STRATEGYQUANT_MCP"
    PYTHON_NATIVE = "PYTHON_NATIVE"
    PINESCRIPT = "PINESCRIPT"
    NINJATRADER = "NINJATRADER"


class StrategyStatus(str, Enum):
    DRAFT = "DRAFT"
    CANDIDATE = "CANDIDATE"
    VALIDATED = "VALIDATED"
    EXPLOITATION_EXTREME = "EXPLOITATION_EXTREME"
    EXPLOITATION_PROP = "EXPLOITATION_PROP"
    REJECTED = "REJECTED"
    RETIRED = "RETIRED"


class OriginSpec(BaseModel):
    engine: str = Field("strategyquant", description="Motor de origen (ej. strategyquant)")
    project: Optional[str] = Field(None, description="Nombre del proyecto en SQX")
    databank: Optional[str] = Field(None, description="Databank de origen en SQX")
    build_id: Optional[str] = Field(None, description="Identificador único de compilación")


class InstrumentSpec(BaseModel):
    symbol: str = Field(..., description="Símbolo principal ej. NQ, ES, CL, ETH-USDT")
    exchange: str = Field("CME", description="Mercado u origen ej. CME, BingX, Binance")
    contract_type: str = Field("FUTURES", description="FUTURES, PERPETUAL, SPOT, FOREX")
    point_value: float = Field(20.0, description="Valor del punto/tick en USD")
    tick_size: float = Field(0.25, description="Tamaño de tick mínimo")


class SessionSpec(BaseModel):
    timezone: str = Field("America/New_York", description="Zona horaria de la sesión")
    start: str = Field("09:30", description="Hora de inicio de la sesión")
    end: str = Field("16:00", description="Hora de fin de la sesión")
    close_at_end: bool = Field(True, description="Forzar cierre de posiciones al fin de sesión")


class RuleConditionSpec(BaseModel):
    indicator: str = Field(..., description="Nombre del indicador ej. RSI, EMA, ATR, Bollinger")
    timeframe: str = Field("1h", description="Timeframe ej. 1m, 5m, 1h, 4h, 1d")
    period: int = Field(14, description="Período del indicador")
    comparison: str = Field("GREATER_THAN", description="Operador: GREATER_THAN, LESS_THAN, CROSSES_ABOVE, CROSSES_BELOW")
    threshold_value: Optional[float] = Field(None, description="Valor numérico de umbral")
    threshold_indicator: Optional[str] = Field(None, description="Indicador secundario de comparación")


# Alias for backward compatibility
RuleCondition = RuleConditionSpec


class EntriesSpec(BaseModel):
    long: List[RuleConditionSpec] = Field(default_factory=list)
    short: List[RuleConditionSpec] = Field(default_factory=list)


class ExitsSpec(BaseModel):
    stop_loss_ticks: Optional[int] = Field(None, description="Distancia de Stop Loss en ticks")
    stop_loss_atr_mult: Optional[float] = Field(None, description="Distancia de Stop Loss en multiplicador ATR")
    take_profit_ticks: Optional[int] = Field(None, description="Distancia de Take Profit en ticks")
    take_profit_atr_mult: Optional[float] = Field(None, description="Distancia de Take Profit en multiplicador ATR")
    trailing_stop_ticks: Optional[int] = Field(None, description="Distancia de Trailing Stop")
    break_even_ticks: Optional[int] = Field(None, description="Trigger de Break Even en ticks")
    time_exit_bars: Optional[int] = Field(None, description="Cierre por tiempo en N barras")


class PositionSizingSpec(BaseModel):
    method: str = Field("FIXED_RISK_PCT", description="FIXED_RISK_PCT, FIXED_CONTRACTS, CAPITAL_COMPOUND")
    risk_pct: float = Field(1.0, description="Porcentaje de riesgo por operación")
    max_contracts: int = Field(10, description="Límite máximo de contratos")


class CostsSpec(BaseModel):
    commission_per_contract: float = Field(2.50, description="Comisión por contrato ida y vuelta en USD")
    slippage_ticks: int = Field(1, description="Slippage estimado por orden en ticks")


class ValidationMetricsSpec(BaseModel):
    dataset_hash: Optional[str] = None
    trades_count: int = 0
    profit_factor: float = 0.0
    net_profit_usd: float = 0.0
    max_drawdown_pct: float = 0.0
    win_rate: float = 0.0
    in_sample_pf: Optional[float] = None
    out_of_sample_pf: Optional[float] = None
    walk_forward_passed: bool = False
    monte_carlo_passed: bool = False


class DeploymentSpec(BaseModel):
    allowed_platforms: List[str] = Field(default_factory=lambda: ["TRADOVATE", "NINJATRADER", "PROJECTX", "SIMULATOR"])
    allowed_risk_policies: List[str] = Field(default_factory=lambda: ["PROP_FIRM_50K", "ULTRA_EXTREME_COMPOUND"])


class StrategySpec(BaseModel):
    """Objeto neutro de definición de estrategia para Ultra Rentable V2."""
    strategy_id: str = Field(..., description="Identificador único de estrategia e.g. UR-000001")
    version: int = Field(1, description="Versión incremental de la estrategia")
    name: str = Field(..., description="Nombre descriptivo de la estrategia")
    status: StrategyStatus = Field(StrategyStatus.DRAFT, description="Estado en el ciclo de vida")
    
    origin: OriginSpec = Field(default_factory=OriginSpec)
    instrument: Optional[InstrumentSpec] = Field(None, description="Especificación del instrumento")
    timeframe: str = Field("1h", description="Timeframe principal de ejecución")
    session: SessionSpec = Field(default_factory=SessionSpec)
    
    entries: EntriesSpec = Field(default_factory=EntriesSpec)
    exits: ExitsSpec = Field(default_factory=ExitsSpec)
    position_sizing: PositionSizingSpec = Field(default_factory=PositionSizingSpec)
    costs: CostsSpec = Field(default_factory=CostsSpec)
    validation: ValidationMetricsSpec = Field(default_factory=ValidationMetricsSpec)
    deployment: DeploymentSpec = Field(default_factory=DeploymentSpec)

    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadatos arbitrarios y estadísticas adicionales")

    @model_validator(mode="before")
    @classmethod
    def _normalize_flexible_input(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Convenience mapping for flat symbol
            if "symbol" in data and "instrument" not in data:
                sym = data.pop("symbol")
                contract_type = str(data.pop("asset_class", "FUTURES"))
                if hasattr(contract_type, "value"):
                    contract_type = contract_type.value
                data["instrument"] = InstrumentSpec(
                    symbol=sym,
                    contract_type=str(contract_type),
                    exchange="CME" if "USDT" not in sym else "BINGX"
                )
            
            # Convenience mapping for session close
            if "close_at_session_end" in data:
                close_end = data.pop("close_at_session_end")
                if "session" not in data:
                    data["session"] = SessionSpec(close_at_end=bool(close_end))
                elif isinstance(data["session"], dict):
                    data["session"]["close_at_end"] = bool(close_end)

            # Convenience mapping for entry rules
            if "entry_long_rules" in data:
                rules = data.pop("entry_long_rules")
                if "entries" not in data:
                    data["entries"] = EntriesSpec(long=rules)
                elif isinstance(data["entries"], dict):
                    data["entries"]["long"] = rules

            # Convenience mapping for timeframe
            if "main_timeframe" in data and "timeframe" not in data:
                data["timeframe"] = data.pop("main_timeframe")

            # Convenience mapping for exits
            if "stop_loss_ticks" in data or "take_profit_ticks" in data:
                sl = data.pop("stop_loss_ticks", None)
                tp = data.pop("take_profit_ticks", None)
                if "exits" not in data:
                    data["exits"] = ExitsSpec(stop_loss_ticks=sl, take_profit_ticks=tp)

            # Default instrument if still missing
            if "instrument" not in data:
                data["instrument"] = InstrumentSpec(symbol="NQ")

        return data

    @property
    def symbol(self) -> str:
        return self.instrument.symbol if self.instrument else "NQ"

    @property
    def close_at_session_end(self) -> bool:
        return self.session.close_at_end if self.session else True
