"""DSL v1.0.0 — Pydantic models, AST parser, canonical serializer, semantic validator, IR compiler.

This module is the single source of truth for strategy representation.
No eval, no exec, no arbitrary code, no imports, no look-ahead.
"""
from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

DSL_VERSION = "1.0.0"
COMPILER_VERSION = "1.0.0"

# ─── Enums ────────────────────────────────────────────────────────────────────

class StrategyFamily(str, Enum):
    BREAKOUT = "breakout"
    MEAN_REVERSION = "mean_reversion"
    TREND_FOLLOWING = "trend_following"
    MOMENTUM = "momentum"
    VOLATILITY = "volatility"
    STATISTICAL_ARBITRAGE = "statistical_arbitrage"

class StrategyOrigin(str, Enum):
    MANUAL = "MANUAL"
    RESEARCH = "RESEARCH"
    MUTATION = "MUTATION"
    CROSSOVER = "CROSSOVER"

class MarginMode(str, Enum):
    ISOLATED = "ISOLATED"
    CROSS = "CROSS"

class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"

class SeriesName(str, Enum):
    OPEN = "OPEN"
    HIGH = "HIGH"
    LOW = "LOW"
    CLOSE = "CLOSE"
    VOLUME = "VOLUME"
    MARK_PRICE = "MARK_PRICE"
    INDEX_PRICE = "INDEX_PRICE"
    FUNDING_RATE = "FUNDING_RATE"
    OPEN_INTEREST = "OPEN_INTEREST"

class IndicatorName(str, Enum):
    SMA = "SMA"
    EMA = "EMA"
    RSI = "RSI"
    ATR = "ATR"
    HIGHEST = "HIGHEST"
    LOWEST = "LOWEST"
    ROC = "ROC"
    STDDEV = "STDDEV"
    VOLUME_RATIO = "VOLUME_RATIO"

COMPARISON_OPS = ("GT", "GTE", "LT", "LTE", "EQ", "CROSS_ABOVE", "CROSS_BELOW")
LOGIC_OPS = ("ALL", "ANY")
TIMEFRAMES = ("1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w")
BASIC_SERIES = {SeriesName.OPEN, SeriesName.HIGH, SeriesName.LOW, SeriesName.CLOSE, SeriesName.VOLUME}
EXTRA_SERIES = {SeriesName.MARK_PRICE, SeriesName.INDEX_PRICE, SeriesName.FUNDING_RATE, SeriesName.OPEN_INTEREST}

# ─── Value Nodes (discriminated by "type") ────────────────────────────────────

class SeriesNode(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["SERIES"] = "SERIES"
    series: SeriesName
    offset: int = Field(default=0, ge=0)

class IndicatorParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    period: int = Field(ge=1, le=10000)

class IndicatorNode(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["INDICATOR"] = "INDICATOR"
    indicator: IndicatorName
    source: "ValueNode"
    params: IndicatorParams
    offset: int = Field(default=0, ge=0)

class ConstantNode(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["CONSTANT"] = "CONSTANT"
    value: float

ValueNode = Union[SeriesNode, IndicatorNode, ConstantNode]

# ─── Signal Nodes (discriminated by "nodeType") ──────────────────────────────

class ComparisonNode(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nodeType: Literal["COMPARISON"] = "COMPARISON"
    op: str  # one of COMPARISON_OPS
    left: ValueNode
    right: ValueNode

    @field_validator("op")
    @classmethod
    def validate_op(cls, v: str) -> str:
        if v not in COMPARISON_OPS:
            raise ValueError(f"Comparison op must be one of {COMPARISON_OPS}, got '{v}'")
        return v

class LogicNode(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nodeType: Literal["LOGIC"] = "LOGIC"
    op: str  # one of LOGIC_OPS
    children: list["SignalNode"] = Field(min_length=1)

    @field_validator("op")
    @classmethod
    def validate_op(cls, v: str) -> str:
        if v not in LOGIC_OPS:
            raise ValueError(f"Logic op must be one of {LOGIC_OPS}, got '{v}'")
        return v

class NotNode(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nodeType: Literal["NOT"] = "NOT"
    child: "SignalNode"

SignalNode = Union[ComparisonNode, LogicNode, NotNode]

# Rebuild for recursive references
IndicatorNode.model_rebuild()
LogicNode.model_rebuild()
NotNode.model_rebuild()
ComparisonNode.model_rebuild()

# ─── Top-Level Sections ──────────────────────────────────────────────────────

class Metadata(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=200)
    family: StrategyFamily
    parents: list[str] = Field(default_factory=list)
    origin: StrategyOrigin

class Market(BaseModel):
    model_config = ConfigDict(extra="forbid")
    venue: Literal["BINGX"] = "BINGX"
    symbol: str = Field(min_length=3, max_length=40)
    timeframe: str

    @field_validator("timeframe")
    @classmethod
    def validate_timeframe(cls, v: str) -> str:
        if v not in TIMEFRAMES:
            raise ValueError(f"Timeframe must be one of {TIMEFRAMES}")
        return v

class Pyramiding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool
    maxEntries: int = Field(ge=1, le=10)

class RiskManagement(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stopLossPct: float = Field(gt=0.0, le=50.0)
    takeProfitPct: float = Field(gt=0.0, le=5000.0)
    trailingStopPct: float | None = Field(default=None, gt=0.0, le=50.0)
    maxHoldingBars: int = Field(ge=1, le=10_000)


class Position(BaseModel):
    model_config = ConfigDict(extra="forbid")
    marginMode: MarginMode
    leverage: int = Field(ge=1, le=500)
    allocationPct: float = Field(ge=0.01, le=100.0)
    compound: bool
    pyramiding: Pyramiding | None = None
    riskManagement: RiskManagement | None = None

class Execution(BaseModel):
    model_config = ConfigDict(extra="forbid")
    entryOrderType: OrderType
    exitOrderType: OrderType
    signalTiming: Literal["BAR_CLOSE_EXECUTE_NEXT_OPEN"] = "BAR_CLOSE_EXECUTE_NEXT_OPEN"

class Signals(BaseModel):
    model_config = ConfigDict(extra="forbid")
    longEntry: SignalNode
    shortEntry: SignalNode
    longExit: SignalNode
    shortExit: SignalNode

class StrategyDSL(BaseModel):
    """Root model for DSL v1.0.0 strategy."""
    model_config = ConfigDict(extra="forbid")
    dslVersion: Literal["1.0.0"] = "1.0.0"
    metadata: Metadata
    market: Market
    signals: Signals
    position: Position
    execution: Execution


# ─── Canonical Serialization ─────────────────────────────────────────────────

def canonical_json(obj: Any) -> str:
    """Deterministic JSON: sorted keys, minimal separators, no ASCII escaping."""
    if isinstance(obj, BaseModel):
        obj = obj.model_dump(mode="json")
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_hash(dsl: StrategyDSL | dict) -> str:
    """SHA-256 of the canonical JSON representation."""
    text = canonical_json(dsl)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ─── AST Extraction ──────────────────────────────────────────────────────────

def _collect_series(node: Any) -> set[SeriesName]:
    """Walk the AST and collect all referenced series."""
    result: set[SeriesName] = set()
    if isinstance(node, SeriesNode):
        result.add(node.series)
    elif isinstance(node, IndicatorNode):
        result |= _collect_series(node.source)
    elif isinstance(node, ComparisonNode):
        result |= _collect_series(node.left)
        result |= _collect_series(node.right)
    elif isinstance(node, LogicNode):
        for child in node.children:
            result |= _collect_series(child)
    elif isinstance(node, NotNode):
        result |= _collect_series(node.child)
    return result


def _collect_max_lookback(node: Any) -> int:
    """Walk the AST and determine the maximum lookback period needed."""
    if isinstance(node, SeriesNode):
        return node.offset
    elif isinstance(node, ConstantNode):
        return 0
    elif isinstance(node, IndicatorNode):
        return node.offset + node.params.period + _collect_max_lookback(node.source)
    elif isinstance(node, ComparisonNode):
        return max(_collect_max_lookback(node.left), _collect_max_lookback(node.right))
    elif isinstance(node, LogicNode):
        return max((_collect_max_lookback(c) for c in node.children), default=0)
    elif isinstance(node, NotNode):
        return _collect_max_lookback(node.child)
    return 0


def extract_required_series(dsl: StrategyDSL) -> set[SeriesName]:
    """Return all series referenced across all four signal branches."""
    result: set[SeriesName] = set()
    for signal in [dsl.signals.longEntry, dsl.signals.shortEntry,
                   dsl.signals.longExit, dsl.signals.shortExit]:
        result |= _collect_series(signal)
    return result


def extract_max_lookback(dsl: StrategyDSL) -> int:
    """Return the maximum lookback bars needed across all signal branches."""
    return max(
        _collect_max_lookback(dsl.signals.longEntry),
        _collect_max_lookback(dsl.signals.shortEntry),
        _collect_max_lookback(dsl.signals.longExit),
        _collect_max_lookback(dsl.signals.shortExit),
    )


# ─── Semantic Validation ─────────────────────────────────────────────────────

class DSLValidationError(BaseModel):
    code: str
    path: str
    message: str


class ValueDimension(str, Enum):
    PRICE = "PRICE"
    PRICE_DELTA = "PRICE_DELTA"
    VOLUME = "VOLUME"
    VOLUME_DELTA = "VOLUME_DELTA"
    RATE = "RATE"
    OSCILLATOR = "OSCILLATOR"
    RATIO = "RATIO"
    CONSTANT = "CONSTANT"


_PRICE_SERIES = {
    SeriesName.OPEN, SeriesName.HIGH, SeriesName.LOW, SeriesName.CLOSE,
    SeriesName.MARK_PRICE, SeriesName.INDEX_PRICE,
}
_VOLUME_SERIES = {SeriesName.VOLUME, SeriesName.OPEN_INTEREST}
_PRESERVE_DIMENSION_INDICATORS = {
    IndicatorName.SMA, IndicatorName.EMA,
    IndicatorName.HIGHEST, IndicatorName.LOWEST,
}


def _value_dimension(node: ValueNode) -> ValueDimension:
    if isinstance(node, ConstantNode):
        return ValueDimension.CONSTANT
    if isinstance(node, SeriesNode):
        if node.series in _PRICE_SERIES:
            return ValueDimension.PRICE
        if node.series in _VOLUME_SERIES:
            return ValueDimension.VOLUME
        return ValueDimension.RATE
    if node.indicator is IndicatorName.RSI:
        return ValueDimension.OSCILLATOR
    if node.indicator is IndicatorName.ROC:
        return ValueDimension.RATE
    if node.indicator is IndicatorName.VOLUME_RATIO:
        return ValueDimension.RATIO
    if node.indicator in {IndicatorName.ATR, IndicatorName.STDDEV}:
        source_dimension = _value_dimension(node.source)
        if source_dimension is ValueDimension.PRICE:
            return ValueDimension.PRICE_DELTA
        if source_dimension is ValueDimension.VOLUME:
            return ValueDimension.VOLUME_DELTA
        return source_dimension
    if node.indicator in _PRESERVE_DIMENSION_INDICATORS:
        return _value_dimension(node.source)
    raise ValueError(f"Unsupported indicator dimension: {node.indicator}")


def _comparison_errors(node: SignalNode, path: str) -> list[DSLValidationError]:
    if isinstance(node, LogicNode):
        errors: list[DSLValidationError] = []
        for index, child in enumerate(node.children):
            errors.extend(_comparison_errors(child, f"{path}.children[{index}]"))
        return errors
    if isinstance(node, NotNode):
        return _comparison_errors(node.child, f"{path}.child")
    if not isinstance(node, ComparisonNode):
        return []

    left_dimension = _value_dimension(node.left)
    right_dimension = _value_dimension(node.right)
    compatible = (
        left_dimension is right_dimension
        or left_dimension is ValueDimension.CONSTANT
        or right_dimension is ValueDimension.CONSTANT
    )
    errors = []
    if not compatible:
        errors.append(DSLValidationError(
            code="INCOMPATIBLE_VALUE_DIMENSIONS",
            path=path,
            message=(
                f"Cannot compare {left_dimension.value} with "
                f"{right_dimension.value}; signal operands must share units"
            ),
        ))
    if node.left.model_dump(mode="json") == node.right.model_dump(mode="json"):
        errors.append(DSLValidationError(
            code="DEGENERATE_COMPARISON",
            path=path,
            message="A value cannot be compared with itself",
        ))
    return errors


def validate_semantics(
    dsl: StrategyDSL,
    *,
    available_symbols: set[str] | None = None,
    available_timeframes: set[str] | None = None,
    available_series: set[SeriesName] | None = None,
    max_leverage: int | None = None,
) -> list[DSLValidationError]:
    """
    Semantic validation against real venue constraints.
    Returns empty list if valid.
    """
    errors: list[DSLValidationError] = []

    if available_symbols is not None and dsl.market.symbol not in available_symbols:
        errors.append(DSLValidationError(
            code="SYMBOL_NOT_IN_CATALOG",
            path="market.symbol",
            message=f"Symbol '{dsl.market.symbol}' not found in approved instrument catalog",
        ))

    if available_timeframes is not None and dsl.market.timeframe not in available_timeframes:
        errors.append(DSLValidationError(
            code="TIMEFRAME_NOT_AVAILABLE",
            path="market.timeframe",
            message=f"Timeframe '{dsl.market.timeframe}' not available in dataset",
        ))

    if max_leverage is not None and dsl.position.leverage > max_leverage:
        errors.append(DSLValidationError(
            code="LEVERAGE_EXCEEDS_VENUE_LIMIT",
            path="position.leverage",
            message=f"Leverage {dsl.position.leverage}x exceeds venue limit {max_leverage}x for {dsl.market.symbol}",
        ))

    for field_name in ("entryOrderType", "exitOrderType"):
        if getattr(dsl.execution, field_name) is OrderType.LIMIT:
            errors.append(DSLValidationError(
                code="UNPRICED_LIMIT_ORDER_UNSUPPORTED",
                path=f"execution.{field_name}",
                message=(
                    "DSL v1 has no limit price or fill model; automatic fills "
                    "would introduce look-ahead and maker-fee optimism"
                ),
            ))

    required = extract_required_series(dsl)
    if available_series is not None:
        missing = required - available_series
        for series in sorted(missing, key=lambda s: s.value):
            errors.append(DSLValidationError(
                code="SERIES_NOT_AVAILABLE",
                path=f"signals.*.{series.value}",
                message=f"Series '{series.value}' required by strategy but not available in dataset",
            ))

    for signal_name in ("longEntry", "shortEntry", "longExit", "shortExit"):
        errors.extend(_comparison_errors(
            getattr(dsl.signals, signal_name),
            f"signals.{signal_name}",
        ))

    return errors


# ─── IR Compilation ──────────────────────────────────────────────────────────

class IRInstruction(BaseModel):
    """Single instruction in the intermediate representation."""
    op: str
    args: dict[str, Any] = Field(default_factory=dict)
    output: str


class CompiledIR(BaseModel):
    """Compiled intermediate representation of a strategy."""
    irVersion: str = "1.0.0"
    compilerVersion: str = COMPILER_VERSION
    dslVersion: str = DSL_VERSION
    dslHash: str
    instructions: list[IRInstruction]
    requiredSeries: list[str]
    maxLookback: int
    irHash: str = ""


_counter = 0

def _reset_counter() -> None:
    global _counter
    _counter = 0

def _next_id(prefix: str) -> str:
    global _counter
    _counter += 1
    return f"{prefix}_{_counter}"


def _compile_value(node: Any, instructions: list[IRInstruction]) -> str:
    if isinstance(node, SeriesNode):
        reg = _next_id("series")
        instructions.append(IRInstruction(op="LOAD_SERIES", args={"series": node.series.value, "offset": node.offset}, output=reg))
        return reg
    elif isinstance(node, ConstantNode):
        reg = _next_id("const")
        instructions.append(IRInstruction(op="LOAD_CONSTANT", args={"value": node.value}, output=reg))
        return reg
    elif isinstance(node, IndicatorNode):
        source_reg = _compile_value(node.source, instructions)
        reg = _next_id("ind")
        instructions.append(IRInstruction(op=f"COMPUTE_{node.indicator.value}", args={"source": source_reg, "period": node.params.period, "offset": node.offset}, output=reg))
        return reg
    raise ValueError(f"Unknown value node type: {type(node)}")


def _compile_signal(node: Any, instructions: list[IRInstruction]) -> str:
    if isinstance(node, ComparisonNode):
        left_reg = _compile_value(node.left, instructions)
        right_reg = _compile_value(node.right, instructions)
        reg = _next_id("cmp")
        instructions.append(IRInstruction(op=f"COMPARE_{node.op}", args={"left": left_reg, "right": right_reg}, output=reg))
        return reg
    elif isinstance(node, LogicNode):
        child_regs = [_compile_signal(c, instructions) for c in node.children]
        reg = _next_id("logic")
        instructions.append(IRInstruction(op=f"LOGIC_{node.op}", args={"inputs": child_regs}, output=reg))
        return reg
    elif isinstance(node, NotNode):
        child_reg = _compile_signal(node.child, instructions)
        reg = _next_id("not")
        instructions.append(IRInstruction(op="LOGIC_NOT", args={"input": child_reg}, output=reg))
        return reg
    raise ValueError(f"Unknown signal node type: {type(node)}")


def compile_to_ir(dsl: StrategyDSL) -> CompiledIR:
    """Compile a validated DSL strategy to an intermediate representation."""
    _reset_counter()
    instructions: list[IRInstruction] = []

    long_entry_reg = _compile_signal(dsl.signals.longEntry, instructions)
    short_entry_reg = _compile_signal(dsl.signals.shortEntry, instructions)
    long_exit_reg = _compile_signal(dsl.signals.longExit, instructions)
    short_exit_reg = _compile_signal(dsl.signals.shortExit, instructions)

    instructions.append(IRInstruction(op="ASSIGN_SIGNAL", args={"signal": "LONG_ENTRY", "source": long_entry_reg}, output="signal_long_entry"))
    instructions.append(IRInstruction(op="ASSIGN_SIGNAL", args={"signal": "SHORT_ENTRY", "source": short_entry_reg}, output="signal_short_entry"))
    instructions.append(IRInstruction(op="ASSIGN_SIGNAL", args={"signal": "LONG_EXIT", "source": long_exit_reg}, output="signal_long_exit"))
    instructions.append(IRInstruction(op="ASSIGN_SIGNAL", args={"signal": "SHORT_EXIT", "source": short_exit_reg}, output="signal_short_exit"))

    instructions.append(IRInstruction(
        op="CONFIGURE_POSITION",
        args={
            "marginMode": dsl.position.marginMode.value,
            "leverage": dsl.position.leverage,
            "allocationPct": dsl.position.allocationPct,
            "compound": dsl.position.compound,
            "entryOrderType": dsl.execution.entryOrderType.value,
            "exitOrderType": dsl.execution.exitOrderType.value,
            "signalTiming": dsl.execution.signalTiming,
        },
        output="position_config",
    ))

    required = extract_required_series(dsl)
    dsl_hash = canonical_hash(dsl)
    ir = CompiledIR(
        dslHash=dsl_hash,
        instructions=instructions,
        requiredSeries=sorted([s.value for s in required]),
        maxLookback=extract_max_lookback(dsl),
    )
    ir_text = canonical_json(ir.model_dump(mode="json", exclude={"irHash"}))
    ir.irHash = hashlib.sha256(ir_text.encode("utf-8")).hexdigest()
    return ir
