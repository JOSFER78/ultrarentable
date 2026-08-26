"""StrategyQuant conversion boundary — intentionally fail-closed.

SQX performance statistics are not a strategy definition. The old converter used
to synthesize executable semantics from incomplete statistics. That path is retired.
Only pure numeric helpers remain here; canonical conversion requires a complete real
source payload and is handled by the Strategy Lab strict importer.
"""
from __future__ import annotations

from typing import Any, Optional, Tuple


class StrategyConversionError(ValueError):
    pass


def normalize_drawdown_pct(
    drawdown_value: float,
    profit_or_peak_delta: float,
    *,
    initial_capital: float | None = None,
) -> float:
    """Normalize an explicit drawdown value; never infer missing capital."""
    try:
        dd = float(drawdown_value)
        reference = float(profit_or_peak_delta)
    except (TypeError, ValueError) as exc:
        raise StrategyConversionError("INVALID_DRAWDOWN_INPUT") from exc
    if dd < 0:
        raise StrategyConversionError("INVALID_NEGATIVE_DRAWDOWN")
    if initial_capital is None:
        return dd
    cap = float(initial_capital)
    if cap <= 0 or reference < 0:
        raise StrategyConversionError("INVALID_DRAWDOWN_REFERENCE")
    peak = cap + reference
    if peak <= 0:
        raise StrategyConversionError("INVALID_PEAK_EQUITY")
    return (dd / peak) * 100.0


def _disabled(*_: Any, **__: Any) -> Any:
    raise StrategyConversionError(
        "LEGACY_SQX_CONVERTER_DISABLED: statistics-only SQX payload cannot become a canonical executable strategy; "
        "obtain explicit source rules/DSL, instrument, timeframe, session, exits and risk metadata first."
    )


def clean_symbol(raw_symbol: str) -> str:
    if not isinstance(raw_symbol, str) or not raw_symbol.strip():
        raise StrategyConversionError("MISSING_REQUIRED_FIELD:symbol")
    symbol = raw_symbol.strip().upper()
    if symbol in {"NONE", "NULL", "UNKNOWN", "N/A"}:
        raise StrategyConversionError("INVALID_REQUIRED_FIELD:symbol")
    return symbol.replace("/", "-").replace("_", "-")


def resolve_instrument_specs(symbol: str, exchange: Optional[str] = None, contract_type: Optional[str] = None) -> Tuple[str, str, float, float]:
    registry = {
        "NQ": ("CME", "FUTURES", 20.0, 0.25),
        "MNQ": ("CME", "FUTURES", 2.0, 0.25),
        "ES": ("CME", "FUTURES", 50.0, 0.25),
        "MES": ("CME", "FUTURES", 5.0, 0.25),
        "YM": ("CME", "FUTURES", 5.0, 1.0),
        "MYM": ("CME", "FUTURES", 0.5, 1.0),
        "RTY": ("CME", "FUTURES", 50.0, 0.1),
        "M2K": ("CME", "FUTURES", 5.0, 0.1),
        "GC": ("COMEX", "FUTURES", 100.0, 0.1),
        "MGC": ("COMEX", "FUTURES", 10.0, 0.1),
        "CL": ("NYMEX", "FUTURES", 1000.0, 0.01),
        "MCL": ("NYMEX", "FUTURES", 100.0, 0.01),
        "MBT": ("CME", "FUTURES", 0.1, 5.0),
        "MET": ("CME", "FUTURES", 0.1, 0.5),
        "EURUSD": ("FOREX", "FOREX", 100000.0, 0.00001),
        "GBPUSD": ("FOREX", "FOREX", 100000.0, 0.00001),
        "USDJPY": ("FOREX", "FOREX", 100000.0, 0.001),
        "AUDUSD": ("FOREX", "FOREX", 100000.0, 0.00001),
        "USDCAD": ("FOREX", "FOREX", 100000.0, 0.00001),
        "USDCHF": ("FOREX", "FOREX", 100000.0, 0.00001),
    }
    normalized = clean_symbol(symbol)
    if normalized not in registry:
        raise StrategyConversionError("UNKNOWN_INSTRUMENT: explicit registry economics required")
    reg_exchange, reg_contract, point_value, tick_size = registry[normalized]
    return exchange or reg_exchange, contract_type or reg_contract, point_value, tick_size


def sqx_candidate_to_canonical(*args: Any, **kwargs: Any) -> Any:
    return _disabled(*args, **kwargs)


def sqx_candidate_to_spec(*args: Any, **kwargs: Any) -> Any:
    return _disabled(*args, **kwargs)
