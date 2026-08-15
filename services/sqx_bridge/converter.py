"""StrategyQuant X Candidate to StrategySpec Converter (Fase 4)."""

from typing import Any, Dict
from services.strategy_core.spec import (
    StrategySpec,
    StrategyStatus,
    OriginSpec,
    InstrumentSpec,
    ValidationMetricsSpec
)


def sqx_candidate_to_spec(
    project_name: str,
    databank_name: str,
    strategy_name: str,
    sqx_stats: Dict[str, Any],
    symbol: str = "NQ"
) -> StrategySpec:
    """Convert a StrategyQuant X candidate strategy and its metrics into a neutral StrategySpec."""
    trades_count = int(sqx_stats.get("TradesCount", sqx_stats.get("NetTrades", 0)))
    profit_factor = float(sqx_stats.get("ProfitFactor", 0.0))
    net_profit = float(sqx_stats.get("NetProfitUsd", sqx_stats.get("NetProfit", 0.0)))
    max_dd = float(sqx_stats.get("MaxDrawdownPct", sqx_stats.get("DrawdownPct", 0.0)))
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
            build_id=f"sqx_build_{strategy_name}"
        ),
        instrument=InstrumentSpec(
            symbol=symbol,
            exchange="CME" if symbol in ("NQ", "ES", "CL") else "BINGX",
            contract_type="FUTURES",
            point_value=20.0 if symbol == "NQ" else 50.0,
            tick_size=0.25
        ),
        timeframe="1h",
        validation=ValidationMetricsSpec(
            trades_count=trades_count,
            profit_factor=profit_factor,
            net_profit_usd=net_profit,
            max_drawdown_pct=max_dd,
            win_rate=win_rate
        ),
        metadata=sqx_stats
    )
