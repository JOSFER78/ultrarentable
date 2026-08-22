"""StrategyQuant X Candidate to StrategySpec & CanonicalStrategy Converter (Fase 3)."""

from __future__ import annotations

import time
from typing import Any, Dict
from contracts.canonical_strategy import (
    CanonicalStrategy,
    ExecutionTrack,
    StrategyLifecycleStatus,
    TargetInstrument,
    RuleTree,
    ExitModel,
    SizingAndRisk,
    SessionWindow,
    ProvenanceMetadata,
)
from services.strategy_core.spec import (
    StrategySpec,
    StrategyStatus,
    OriginSpec,
    InstrumentSpec,
    ValidationMetricsSpec,
)


def normalize_drawdown_pct(raw_dd: float, net_profit: float, initial_capital: float = 10000.0) -> float:
    """Convierte drawdowns absolutos en USD o porcentuales a porcentaje relativo normalizado."""
    if raw_dd <= 0.0:
        return 0.0
    if raw_dd <= 100.0:
        return round(raw_dd, 2)
    # Si el valor de DD viene en USD absoluto (> 100 USD)
    peak = max(initial_capital, initial_capital + net_profit)
    return round((raw_dd / peak) * 100.0, 2)


def sqx_candidate_to_canonical(
    project_name: str,
    databank_name: str,
    strategy_name: str,
    sqx_stats: Dict[str, Any],
    symbol: str = "NQ",
    target_track: ExecutionTrack = ExecutionTrack.TRACK_FONDEO,
) -> CanonicalStrategy:
    """Convierte candidato SQX directamente al modelo Canónico CanonicalStrategy v2.0.0."""
    trades_count = int(sqx_stats.get("TradesCount", sqx_stats.get("NetTrades", 0)))
    profit_factor = float(sqx_stats.get("ProfitFactor", 0.0))
    net_profit = float(sqx_stats.get("NetProfitUsd", sqx_stats.get("NetProfit", 0.0)))
    raw_dd = float(sqx_stats.get("MaxDrawdownPct", sqx_stats.get("DrawdownPct", 0.0)))
    max_dd = normalize_drawdown_pct(raw_dd, net_profit)
    win_rate = float(sqx_stats.get("WinRate", 0.0))

    spec_id = f"UR-SQX-{strategy_name.replace(' ', '_')}"
    exchange = "CME" if symbol in ("NQ", "ES", "CL", "MES", "MNQ") else "BINGX"
    contract_type = "FUTURES" if exchange == "CME" else "PERPETUAL"
    point_val = 20.0 if symbol in ("NQ", "MNQ") else (50.0 if symbol in ("ES", "MES") else 1.0)
    tick_sz = 0.25 if symbol in ("NQ", "ES", "MES", "MNQ") else 0.1

    return CanonicalStrategy(
        schema_version="3.0.0",
        strategy_id=spec_id,
        name=strategy_name,
        target_track=target_track,
        status=StrategyLifecycleStatus.CANDIDATE,
        instrument=TargetInstrument(
            symbol=symbol,
            exchange=exchange,
            contract_type=contract_type,
            point_value=point_val,
            tick_size=tick_sz,
        ),
        timeframe="1h",
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
) -> StrategySpec:
    """Compatibilidad con StrategySpec legado."""
    trades_count = int(sqx_stats.get("TradesCount", sqx_stats.get("NetTrades", 0)))
    profit_factor = float(sqx_stats.get("ProfitFactor", 0.0))
    net_profit = float(sqx_stats.get("NetProfitUsd", sqx_stats.get("NetProfit", 0.0)))
    raw_dd = float(sqx_stats.get("MaxDrawdownPct", sqx_stats.get("DrawdownPct", 0.0)))
    max_dd = normalize_drawdown_pct(raw_dd, net_profit)
    win_rate = float(sqx_stats.get("WinRate", 0.0))

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
            symbol=symbol,
            exchange="CME" if symbol in ("NQ", "ES", "CL", "MES", "MNQ") else "BINGX",
            contract_type="FUTURES",
            point_value=20.0 if symbol in ("NQ", "MNQ") else 50.0,
            tick_size=0.25,
        ),
        timeframe="1h",
        validation=ValidationMetricsSpec(
            trades_count=trades_count,
            profit_factor=profit_factor,
            net_profit_usd=net_profit,
            max_drawdown_pct=max_dd,
            win_rate=win_rate,
        ),
        metadata=sqx_stats,
    )
