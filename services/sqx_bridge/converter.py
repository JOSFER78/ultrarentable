"""services/sqx_bridge/converter.py
StrategyQuant X Candidate to StrategySpec & CanonicalStrategy Converter (Fase 3 & Fase 4).

Desacopla y normaliza las métricas y especificaciones de candidatos generados por SQX
hacia los contratos canónicos de Ultrarentable V2 (CanonicalStrategy y StrategySpec),
soportando bifurcación dual completa (TRACK_FONDEO y TRACK_ULTRA) para cualquier activo (CME, Forex, Cripto).
"""

from __future__ import annotations

import re
import time
from typing import Any, Dict, Optional, Tuple

from contracts.canonical_strategy import (
    CanonicalStrategy,
    ExecutionTrack,
    ExitModel,
    ProvenanceMetadata,
    RuleTree,
    SessionWindow,
    SizingAndRisk,
    StrategyLifecycleStatus,
    TargetInstrument,
)
from services.strategy_core.spec import (
    InstrumentSpec,
    OriginSpec,
    StrategySpec,
    StrategyStatus,
    ValidationMetricsSpec,
)

# Catálogo canónico de especificaciones de instrumentos por activo
INSTRUMENT_CATALOG: Dict[str, Dict[str, Any]] = {
    # Micro y Mini Futuros CME / NYMEX / COMEX
    "NQ": {"exchange": "CME", "contract_type": "FUTURES", "point_value": 20.0, "tick_size": 0.25},
    "MNQ": {"exchange": "CME", "contract_type": "FUTURES", "point_value": 2.0, "tick_size": 0.25},
    "ES": {"exchange": "CME", "contract_type": "FUTURES", "point_value": 50.0, "tick_size": 0.25},
    "MES": {"exchange": "CME", "contract_type": "FUTURES", "point_value": 5.0, "tick_size": 0.25},
    "YM": {"exchange": "CME", "contract_type": "FUTURES", "point_value": 5.0, "tick_size": 1.0},
    "MYM": {"exchange": "CME", "contract_type": "FUTURES", "point_value": 0.5, "tick_size": 1.0},
    "RTY": {"exchange": "CME", "contract_type": "FUTURES", "point_value": 50.0, "tick_size": 0.1},
    "M2K": {"exchange": "CME", "contract_type": "FUTURES", "point_value": 5.0, "tick_size": 0.1},
    "GC": {"exchange": "COMEX", "contract_type": "FUTURES", "point_value": 100.0, "tick_size": 0.10},
    "MGC": {"exchange": "COMEX", "contract_type": "FUTURES", "point_value": 10.0, "tick_size": 0.10},
    "CL": {"exchange": "NYMEX", "contract_type": "FUTURES", "point_value": 1000.0, "tick_size": 0.01},
    "MCL": {"exchange": "NYMEX", "contract_type": "FUTURES", "point_value": 100.0, "tick_size": 0.01},
    # Micro Futuros Cripto CME (Permitidos en Prop Firms como Topstep y Apex)
    "MBT": {"exchange": "CME", "contract_type": "FUTURES", "point_value": 0.1, "tick_size": 5.0},
    "MET": {"exchange": "CME", "contract_type": "FUTURES", "point_value": 0.1, "tick_size": 0.5},
    # Forex Majors
    "EURUSD": {"exchange": "FOREX", "contract_type": "FOREX", "point_value": 100000.0, "tick_size": 0.00001},
    "GBPUSD": {"exchange": "FOREX", "contract_type": "FOREX", "point_value": 100000.0, "tick_size": 0.00001},
    "USDJPY": {"exchange": "FOREX", "contract_type": "FOREX", "point_value": 100000.0, "tick_size": 0.001},
    "AUDUSD": {"exchange": "FOREX", "contract_type": "FOREX", "point_value": 100000.0, "tick_size": 0.00001},
    "USDCAD": {"exchange": "FOREX", "contract_type": "FOREX", "point_value": 100000.0, "tick_size": 0.00001},
    "USDCHF": {"exchange": "FOREX", "contract_type": "FOREX", "point_value": 100000.0, "tick_size": 0.00001},
    # Criptoactivos Perpetuos BingX
    "BTC-USDT": {"exchange": "BINGX", "contract_type": "PERPETUAL", "point_value": 1.0, "tick_size": 0.10},
    "ETH-USDT": {"exchange": "BINGX", "contract_type": "PERPETUAL", "point_value": 1.0, "tick_size": 0.01},
    "SOL-USDT": {"exchange": "BINGX", "contract_type": "PERPETUAL", "point_value": 1.0, "tick_size": 0.001},
    "DOGE-USDT": {"exchange": "BINGX", "contract_type": "PERPETUAL", "point_value": 1.0, "tick_size": 0.00001},
    "AVAX-USDT": {"exchange": "BINGX", "contract_type": "PERPETUAL", "point_value": 1.0, "tick_size": 0.001},
    "SUI-USDT": {"exchange": "BINGX", "contract_type": "PERPETUAL", "point_value": 1.0, "tick_size": 0.0001},
    "LINK-USDT": {"exchange": "BINGX", "contract_type": "PERPETUAL", "point_value": 1.0, "tick_size": 0.001},
    "BNB-USDT": {"exchange": "BINGX", "contract_type": "PERPETUAL", "point_value": 1.0, "tick_size": 0.01},
    "XRP-USDT": {"exchange": "BINGX", "contract_type": "PERPETUAL", "point_value": 1.0, "tick_size": 0.0001},
}


def clean_symbol(raw_symbol: str) -> str:
    """Normaliza un símbolo proveniente de SQX eliminando sufijos automáticos."""
    if not raw_symbol or str(raw_symbol).upper() in ("NONE", "NULL", ""):
        return "NQ"
    s = str(raw_symbol).strip().upper()
    s = re.sub(r"(_AUTO|_FUT|_PERP|_H1|_M15|_M5|_D1)$", "", s)
    s = s.replace("_", "-").replace("/", "-")

    if s.endswith("USDT") and "-" not in s:
        s = f"{s[:-4]}-USDT"
    elif s.endswith("USD") and len(s) == 6 and "-" not in s:
        s = s.replace("-", "")

    return s


def resolve_instrument_specs(
    symbol: str,
    target_track: Optional[ExecutionTrack] = None,
    exchange_override: Optional[str] = None,
    contract_type_override: Optional[str] = None,
) -> Tuple[str, str, float, float]:
    """Resuelve deterministamente exchange, contract_type, point_value y tick_size."""
    clean_sym = clean_symbol(symbol)
    lookup_key = clean_sym.replace("/", "")

    info = INSTRUMENT_CATALOG.get(lookup_key)

    if info:
        exchange = exchange_override or info["exchange"]
        contract_type = contract_type_override or info["contract_type"]
        point_value = float(info["point_value"])
        tick_size = float(info["tick_size"])
    else:
        if "USDT" in clean_sym or clean_sym in ("BTC", "ETH", "SOL"):
            exchange = exchange_override or "BINGX"
            contract_type = contract_type_override or "PERPETUAL"
            point_value = 1.0
            tick_size = 0.01
        elif any(fx in clean_sym for fx in ("EUR", "GBP", "JPY", "AUD", "CAD", "CHF")):
            exchange = exchange_override or "FOREX"
            contract_type = contract_type_override or "FOREX"
            point_value = 100000.0
            tick_size = 0.0001
        else:
            exchange = exchange_override or "CME"
            contract_type = contract_type_override or "FUTURES"
            point_value = 20.0
            tick_size = 0.25

    return exchange, contract_type, point_value, tick_size


def normalize_drawdown_pct(raw_dd: float, net_profit: float, initial_capital: float = 10000.0) -> float:
    """Convierte drawdowns absolutos en USD o porcentuales a porcentaje relativo normalizado."""
    if raw_dd <= 0.0:
        return 0.0
    if raw_dd <= 100.0:
        return round(raw_dd, 2)
    peak = max(initial_capital, initial_capital + net_profit)
    return round((raw_dd / peak) * 100.0, 2)


def sqx_candidate_to_canonical(
    project_name: str,
    databank_name: str,
    strategy_name: str,
    sqx_stats: Dict[str, Any],
    symbol: str = "NQ",
    timeframe: str = "1h",
    target_track: ExecutionTrack = ExecutionTrack.TRACK_FONDEO,
    exchange: Optional[str] = None,
    contract_type: Optional[str] = None,
) -> CanonicalStrategy:
    """Convierte candidato SQX directamente al modelo Canónico CanonicalStrategy v2.0.0."""
    trades_count = int(sqx_stats.get("TradesCount", sqx_stats.get("NetTrades", 0)))
    profit_factor = float(sqx_stats.get("ProfitFactor", 0.0))
    net_profit = float(sqx_stats.get("NetProfitUsd", sqx_stats.get("NetProfit", 0.0)))
    raw_dd = float(sqx_stats.get("MaxDrawdownPct", sqx_stats.get("DrawdownPct", 0.0)))

    base_cap = 50000.0 if target_track == ExecutionTrack.TRACK_FONDEO else 1000.0
    max_dd = normalize_drawdown_pct(raw_dd, net_profit, initial_capital=base_cap)
    win_rate = float(sqx_stats.get("WinRate", 0.0))

    norm_symbol = clean_symbol(symbol)
    resolved_exchange, resolved_contract, point_val, tick_sz = resolve_instrument_specs(
        norm_symbol,
        target_track=target_track,
        exchange_override=exchange,
        contract_type_override=contract_type,
    )

    spec_id = f"UR-SQX-{strategy_name.replace(' ', '_')}"

    return CanonicalStrategy(
        schema_version="2.0.0",
        strategy_id=spec_id,
        name=strategy_name,
        target_track=target_track,
        status=StrategyLifecycleStatus.CANDIDATE,
        instrument=TargetInstrument(
            symbol=norm_symbol,
            exchange=resolved_exchange,
            contract_type=resolved_contract,
            point_value=point_val,
            tick_size=tick_sz,
        ),
        timeframe=timeframe,
        session=SessionWindow(
            timezone="America/New_York",
            start_time="09:30",
            end_time="16:00",
            force_close_at_end=(target_track == ExecutionTrack.TRACK_FONDEO),
        ),
        rules=RuleTree(),
        exits=ExitModel(stop_loss_ticks=20, take_profit_ticks=60),
        sizing_and_risk=SizingAndRisk(
            base_risk_pct=1.0 if target_track == ExecutionTrack.TRACK_FONDEO else 5.0,
            max_contracts_or_lots=4.0 if target_track == ExecutionTrack.TRACK_FONDEO else 10.0,
            base_leverage=1.0 if target_track == ExecutionTrack.TRACK_FONDEO else 20.0,
            pyramiding_max_layers=0 if target_track == ExecutionTrack.TRACK_FONDEO else 3,
            pyramiding_reinvest_ratio=0.40,
        ),
        provenance=ProvenanceMetadata(
            source_engine="strategyquant",
            project_name=project_name,
            databank_name=databank_name,
            build_id=f"sqx_build_{strategy_name}",
            created_timestamp_utc=int(time.time() * 1000),
            author_or_agent="SQX_MCP_FACTORY",
        ),
        metadata={
            "trades_count": trades_count,
            "profit_factor": profit_factor,
            "net_profit_usd": net_profit,
            "max_drawdown_pct": max_dd,
            "win_rate_pct": win_rate,
            "raw_sqx_stats": sqx_stats,
        },
    )


def sqx_candidate_to_spec(
    project_name: str,
    databank_name: str,
    strategy_name: str,
    sqx_stats: Dict[str, Any],
    symbol: str = "NQ",
    timeframe: str = "1h",
    target_track: Optional[ExecutionTrack] = None,
    exchange: Optional[str] = None,
    contract_type: Optional[str] = None,
) -> StrategySpec:
    """Compatibilidad con StrategySpec neutro."""
    trades_count = int(sqx_stats.get("TradesCount", sqx_stats.get("NetTrades", 0)))
    profit_factor = float(sqx_stats.get("ProfitFactor", 0.0))
    net_profit = float(sqx_stats.get("NetProfitUsd", sqx_stats.get("NetProfit", 0.0)))
    raw_dd = float(sqx_stats.get("MaxDrawdownPct", sqx_stats.get("DrawdownPct", 0.0)))
    max_dd = normalize_drawdown_pct(raw_dd, net_profit)
    win_rate = float(sqx_stats.get("WinRate", 0.0))

    norm_symbol = clean_symbol(symbol)
    resolved_exchange, resolved_contract, point_val, tick_sz = resolve_instrument_specs(
        norm_symbol,
        target_track=target_track,
        exchange_override=exchange,
        contract_type_override=contract_type,
    )

    spec_id = f"UR-SQX-{strategy_name.replace(' ', '_')}"

    return StrategySpec(
        strategy_id=spec_id,
        version=1,
        name=strategy_name,
        status=StrategyStatus.CANDIDATE,
        origin=OriginSpec(
            engine="strategyquant",
            project=project_name,
            databank=databank_name,
            build_id=f"sqx_build_{strategy_name}",
        ),
        instrument=InstrumentSpec(
            symbol=norm_symbol,
            exchange=resolved_exchange,
            contract_type=resolved_contract,
            point_value=point_val,
            tick_size=tick_sz,
        ),
        timeframe=timeframe,
        validation=ValidationMetricsSpec(
            trades_count=trades_count,
            profit_factor=profit_factor,
            net_profit_usd=net_profit,
            max_drawdown_pct=max_dd,
            win_rate=win_rate,
        ),
        metadata=sqx_stats,
    )
