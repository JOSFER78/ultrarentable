"""Strict StrategyQuant -> canonical conversion.

This module is intentionally conservative. SQX performance statistics alone do
not contain enough information to reconstruct a trading rule set, risk model or
execution policy. Therefore conversion to a canonical executable strategy is
allowed only when the source payload explicitly contains the required semantic
fields. Missing information raises an error rather than being guessed.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict, Optional, Tuple

from contracts.canonical_strategy import CanonicalStrategy, ExecutionTrack
from services.strategy_core.spec import StrategySpec


class StrategyConversionError(ValueError):
    """Raised when the source payload is insufficient for canonical conversion."""


def _required_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StrategyConversionError(f"MISSING_REQUIRED_FIELD:{field}")
    return value.strip()


def _required_positive(value: Any, field: str) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise StrategyConversionError(f"INVALID_REQUIRED_FIELD:{field}") from exc
    if numeric <= 0:
        raise StrategyConversionError(f"INVALID_REQUIRED_FIELD:{field}")
    return numeric


def clean_symbol(raw_symbol: str) -> str:
    """Normalize an explicitly supplied symbol; never invent one."""
    if not isinstance(raw_symbol, str) or not raw_symbol.strip():
        raise StrategyConversionError("MISSING_REQUIRED_FIELD:symbol")
    symbol = raw_symbol.strip().upper()
    if symbol in {"NONE", "NULL", "UNKNOWN", "N/A"}:
        raise StrategyConversionError("INVALID_REQUIRED_FIELD:symbol")
    symbol = re.sub(r"(_AUTO|_FUT|_PERP)$", "", symbol)
    symbol = symbol.replace("/", "-").replace("_", "-")
    if symbol.endswith("USDT") and "-" not in symbol:
        symbol = f"{symbol[:-4]}-USDT"
    return symbol


def resolve_instrument_specs(symbol: str, exchange: Optional[str] = None, contract_type: Optional[str] = None) -> Tuple[str, str, float, float]:
    """Resolve instrument semantics only from an explicit source or registry entry."""
    normalized = clean_symbol(symbol)
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
    if normalized not in registry:
        # A non-registry instrument must carry explicit economics from source.
        src_exchange = _required_text(exchange, "exchange")
        src_contract = _required_text(contract_type, "contract_type")
        raise StrategyConversionError(
            "INSTRUMENT_ECONOMICS_REQUIRED: unknown symbol requires explicit point_value and tick_size in source payload"
        )
    src_exchange, src_contract, point_value, tick_size = registry[normalized]
    return exchange or src_exchange, contract_type or src_contract, point_value, tick_size


def _raw_rules(sqx_stats: Dict[str, Any]) -> Dict[str, Any]:
    for key in ("rules", "strategy_rules", "entry_rules", "dsl", "strategy_dsl", "canonical_dsl"):
        value = sqx_stats.get(key)
        if isinstance(value, dict) and value:
            return value
    raise StrategyConversionError("SOURCE_RULES_UNAVAILABLE: SQX statistics do not contain executable strategy rules")


def _explicit_value(source: Dict[str, Any], names: tuple[str, ...], field: str) -> Any:
    for name in names:
        if name in source and source[name] not in (None, ""):
            return source[name]
    raise StrategyConversionError(f"MISSING_REQUIRED_FIELD:{field}")


def sqx_candidate_to_canonical(
    project_name: str,
    databank_name: str,
    strategy_name: str,
    sqx_stats: Dict[str, Any],
    *,
    source_sha256: Optional[str] = None,
) -> CanonicalStrategy:
    """Convert only when SQX provides complete executable semantics.

    The previous implementation accepted missing semantics and filled them with
    fabricated defaults. This function now rejects such payloads.
    """
    if not isinstance(sqx_stats, dict) or not sqx_stats:
        raise StrategyConversionError("EMPTY_SQX_SOURCE")
    source = sqx_stats
    symbol = clean_symbol(str(_explicit_value(source, ("symbol", "instrument", "market", "asset"), "symbol")))
    timeframe = _required_text(_explicit_value(source, ("timeframe", "tf", "period", "bar_period"), "timeframe"), "timeframe")
    exchange = source.get("exchange")
    contract_type = source.get("contract_type")
    exchange_name, contract_name, point_value, tick_size = resolve_instrument_specs(symbol, exchange, contract_type)

    rules = _raw_rules(sqx_stats)
    exits = sqx_stats.get("exits") or sqx_stats.get("exit_model")
    sizing = sqx_stats.get("sizing_and_risk") or sqx_stats.get("risk")
    session = sqx_stats.get("session") or sqx_stats.get("session_window")

    if not isinstance(exits, dict) or not exits:
        raise StrategyConversionError("MISSING_REQUIRED_FIELD:exit_model")
    if not isinstance(sizing, dict) or not sizing:
        raise StrategyConversionError("MISSING_REQUIRED_FIELD:sizing_and_risk")
    if not isinstance(session, dict) or not session:
        raise StrategyConversionError("MISSING_REQUIRED_FIELD:session_window")

    strategy_hash = source_sha256 or hashlib.sha256(json.dumps(sqx_stats, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    # Return the source payload for the canonical layer to compile only if the
    # canonical model itself accepts the explicit semantics. No guessed values.
    from contracts.canonical_strategy import ExitModel, ProvenanceMetadata, RuleTree, SessionWindow, SizingAndRisk, StrategyLifecycleStatus, TargetInstrument

    return CanonicalStrategy(
        schema_version="2.0.0",
        strategy_id=f"SQX:{project_name}:{databank_name}:{strategy_name}",
        name=strategy_name,
        target_track=ExecutionTrack(source.get("target_track", "TRACK_ULTRA")),
        status=StrategyLifecycleStatus.CANDIDATE,
        instrument=TargetInstrument(symbol=symbol, exchange=exchange_name, contract_type=contract_name, point_value=point_value, tick_size=tick_size),
        timeframe=timeframe,
        session=SessionWindow(**session),
        rules=RuleTree(**rules),
        exits=ExitModel(**exits),
        sizing_and_risk=SizingAndRisk(**sizing),
        provenance=ProvenanceMetadata(
            source_engine="strategyquant",
            project_name=project_name,
            databank_name=databank_name,
            build_id=_required_text(source.get("build_id"), "build_id"),
            created_timestamp_utc=int(_required_positive(source.get("created_timestamp_utc"), "created_timestamp_utc")),
            author_or_agent=_required_text(source.get("author_or_agent"), "author_or_agent"),
        ),
        metadata={"source_strategy_hash": strategy_hash, "raw_sqx_stats": sqx_stats},
    )


def sqx_candidate_to_spec(
    project_name: str,
    databank_name: str,
    strategy_name: str,
    sqx_stats: Dict[str, Any],
    *,
    source_sha256: Optional[str] = None,
) -> StrategySpec:
    """Strict StrategySpec conversion; no defaults and no inferred metrics."""
    if not isinstance(sqx_stats, dict) or not sqx_stats:
        raise StrategyConversionError("EMPTY_SQX_SOURCE")
    symbol = clean_symbol(str(_explicit_value(sqx_stats, ("symbol", "instrument", "market", "asset"), "symbol")))
    timeframe = _required_text(_explicit_value(sqx_stats, ("timeframe", "tf", "period", "bar_period"), "timeframe"), "timeframe")
    exchange, contract_type, point_value, tick_size = resolve_instrument_specs(symbol, sqx_stats.get("exchange"), sqx_stats.get("contract_type"))
    from services.strategy_core.spec import InstrumentSpec, OriginSpec, StrategyStatus
    return StrategySpec(
        strategy_id=f"UR-SQX-{strategy_name.replace(' ', '_')}",
        version=1,
        name=strategy_name,
        status=StrategyStatus.CANDIDATE,
        origin=OriginSpec(
            engine="strategyquant",
            project=_required_text(project_name, "project_name"),
            databank=_required_text(databank_name, "databank_name"),
            build_id=_required_text(sqx_stats.get("build_id"), "build_id"),
        ),
        instrument=InstrumentSpec(symbol=symbol, exchange=exchange, contract_type=contract_type, point_value=point_value, tick_size=tick_size),
        timeframe=timeframe,
        validation=None,
        metadata={"source_sha256": source_sha256, "raw_sqx_stats": sqx_stats},
    )
