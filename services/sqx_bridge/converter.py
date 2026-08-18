"""StrategyQuant X Candidate to StrategySpec Converter (Fase 4)."""

from typing import Any, Dict
from services.strategy_core.spec import (
    StrategySpec,
    StrategyStatus,
    OriginSpec,
    InstrumentSpec,
    ValidationMetricsSpec
)


def _resolve_instrument_specs(symbol: str) -> tuple[str, str, float, float]:
    """Resolve exchange, contract_type, point_value, and tick_size for any market."""
    s = symbol.upper().replace("/", "").replace("-", "")
    if s in ("NQ", "MNQ"):
        return ("CME", "FUTURES", 20.0 if s == "NQ" else 2.0, 0.25)
    elif s in ("ES", "MES"):
        return ("CME", "FUTURES", 50.0 if s == "ES" else 5.0, 0.25)
    elif s in ("YM", "MYM"):
        return ("CBOT", "FUTURES", 5.0 if s == "YM" else 0.5, 1.0)
    elif s in ("RTY", "M2K"):
        return ("CME", "FUTURES", 50.0 if s == "RTY" else 5.0, 0.10)
    elif s in ("CL", "MCL"):
        return ("NYMEX", "FUTURES", 1000.0 if s == "CL" else 100.0, 0.01)
    elif s in ("GC", "MGC"):
        return ("COMEX", "FUTURES", 100.0 if s == "GC" else 10.0, 0.10)
    elif "USDT" in s or "PERP" in s or s in ("BTC", "ETH", "SOL", "DOGE", "AVAX", "XRP", "BNB"):
        return ("BINGX", "PERPETUAL", 1.0, 0.01 if "BTC" not in s else 0.10)
    elif s in ("EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"):
        return ("FOREX", "SPOT", 100000.0, 0.00001)
    else:
        return ("UNIVERSAL", "FUTURES", 1.0, 0.01)


def sqx_candidate_to_spec(
    project_name: str,
    databank_name: str,
    strategy_name: str,
    sqx_stats: Dict[str, Any],
    symbol: str = "NQ",
    timeframe: str = "1h"
) -> StrategySpec:
    """Convert a StrategyQuant X candidate strategy and its metrics into a neutral StrategySpec."""
    trades_count = int(sqx_stats.get("TradesCount", sqx_stats.get("NetTrades", 0)))
    profit_factor = float(sqx_stats.get("ProfitFactor", 0.0))
    net_profit = float(sqx_stats.get("NetProfitUsd", sqx_stats.get("NetProfit", 0.0)))
    max_dd = float(sqx_stats.get("MaxDrawdownPct", sqx_stats.get("DrawdownPct", 0.0)))
    win_rate = float(sqx_stats.get("WinRate", 0.0))

    tf = str(sqx_stats.get("Timeframe", timeframe)).lower()
    sym = str(sqx_stats.get("Symbol", symbol))
    exchange, contract_type, point_val, tick_sz = _resolve_instrument_specs(sym)

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
            symbol=sym,
            exchange=exchange,
            contract_type=contract_type,
            point_value=point_val,
            tick_size=tick_sz
        ),
        timeframe=tf,
        validation=ValidationMetricsSpec(
            trades_count=trades_count,
            profit_factor=profit_factor,
            net_profit_usd=net_profit,
            max_drawdown_pct=max_dd,
            win_rate=win_rate
        ),
        metadata=sqx_stats
    )
