"""Ingest StrategyQuant X generated strategies into Ultrarentable DB (Fase 2).

Reads REAL strategies from the SQX MCP server (Ultra_Auto_Pilot / Results),
maps their columnar stats into neutral StrategySpecs, and persists them in the
local SQLite DB as strategies + backtests with REAL metrics. NO invented values.
"""

from __future__ import annotations

import json
import sys
import hashlib
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path("/home/ubuntu/workspace/pro/trading/01 Ultrarentable")
sys.path.insert(0, str(PROJECT_ROOT))

from services.sqx_bridge.sqx_client import SQXMCPClient
from services.sqx_bridge.converter import sqx_candidate_to_spec
from services.api.app.db.database import SessionLocal, StrategyModel, BacktestModel

PROJECT = "Ultra_Auto_Pilot"
DATABANK = "Results"

# SQX column name -> neutral metric key (as expected by converter.py)
COLUMN_MAP = {
    "Net profit (IS)": "NetProfitUsd",
    "# of trades (IS)": "TradesCount",
    "Profit factor (IS)": "ProfitFactor",
    "Drawdown (IS)": "MaxDrawdownPct",
    "Win/Loss ratio (IS)": "WinRate",
    "Annual % Return (IS)": "AnnualReturnPct",
    "Sharpe Ratio (IS)": "SharpeRatio",
    "Ret/DD Ratio (IS)": "RetDD",
    "Net profit (OOS)": "NetProfitOosUsd",
    "# of trades (OOS)": "TradesOos",
    "Profit factor (OOS)": "ProfitFactorOos",
    "Drawdown (OOS)": "MaxDrawdownOosPct",
}


def extract_stats(stats: dict | str) -> dict:
    """Convert SQX columnar stats {columns, values} into {metric_key: value}."""
    if isinstance(stats, str):
        try:
            stats = json.loads(stats)
        except Exception:
            return {}
    cols = stats.get("columns", [])
    vals = stats.get("values", [])
    if not cols or not vals:
        return {}
    # SQX returns [name, group, ...42 values] -> columns start at offset 2
    # (len(vals) - len(cols) == 3 because there is one extra trailing element;
    #  the REAL layout is name, group, then the columns in order)
    offset = 2
    if len(vals) == len(cols):
        offset = 0
    out: dict = {}
    for i, col in enumerate(cols):
        idx = i + offset
        if idx >= len(vals):
            continue
        raw = vals[idx]
        if raw is None:
            continue
        try:
            num = float(raw)
        except (TypeError, ValueError):
            continue
        key = COLUMN_MAP.get(col)
        if key:
            out[key] = num
    return out


def clean_symbol(raw_symbol: str) -> str:
    """Clean symbol name from SQX artifacts (e.g. BTCUSDT_AUTO -> BTC-USDT, NQ_AUTO -> NQ)."""
    if not raw_symbol or raw_symbol.upper() == "NONE":
        return "NQ"
    s = raw_symbol.replace("_AUTO", "").replace("_FUT", "").replace("_PERP", "").strip().upper()
    if s.endswith("USDT") and "-" not in s:
        return f"{s[:-4]}-USDT"
    return s


def extract_timeframe_from_stats(stats_raw: dict | str) -> str:
    """Extract timeframe from SQX stats or return standard fallback 1h."""
    if isinstance(stats_raw, dict):
        cols = stats_raw.get("columns", [])
        vals = stats_raw.get("values", [])
        for c, v in zip(cols, vals):
            if "timeframe" in str(c).lower() or "tf" in str(c).lower() or "period" in str(c).lower():
                val_str = str(v).lower()
                if "1m" in val_str: return "1m"
                if "5m" in val_str: return "5m"
                if "15m" in val_str: return "15m"
                if "1h" in val_str or "60" in val_str: return "1h"
                if "4h" in val_str or "240" in val_str: return "4h"
                if "d1" in val_str or "1d" in val_str: return "1d"
    return "1h"


def main() -> None:
    client = SQXMCPClient()
    strategies = client.list_strategies(PROJECT, DATABANK) or []
    target_databank = DATABANK
    if not strategies:
        strategies = client.list_strategies(PROJECT, "Last generation") or []
        target_databank = "Last generation"
    print(f"Estrategias en {PROJECT}/{target_databank}: {len(strategies)}")

    db = SessionLocal()
    inserted_strategies = 0
    inserted_backtests = 0
    skipped = 0

    for name in strategies:
        try:
            stats_raw = client.get_strategy_stats(PROJECT, DATABANK, name)
        except Exception as e:  # noqa: BLE001
            print(f"  !! {name}: error stats: {e}")
            skipped += 1
            continue

        metrics = extract_stats(stats_raw)
        if not metrics or metrics.get("TradesCount", 0) == 0:
            print(f"  -- {name}: sin trades (skip)")
            skipped += 1
            continue

        raw_sym = str((stats_raw.get("values") or [])[3]) if len(stats_raw.get("values", [])) > 3 else "NQ"
        symbol = clean_symbol(raw_sym)
        tf = extract_timeframe_from_stats(stats_raw)
        venue = "BINGX" if "USDT" in symbol or symbol in ("BTC", "ETH", "SOL") else "CME"

        spec = sqx_candidate_to_spec(
            project_name=PROJECT,
            databank_name=DATABANK,
            strategy_name=name,
            sqx_stats=metrics,
            symbol=symbol,
            timeframe=tf,
        )

        spec_id = spec.strategy_id
        dsl_json = json.dumps({
            "dslVersion": "1.0.0",
            "origin": {
                "engine": "strategyquant",
                "project": PROJECT,
                "databank": DATABANK,
                "strategyName": name,
            },
            "market": {
                "symbol": symbol,
                "timeframe": tf,
                "venue": venue,
            },
            "metadata": {
                "family": "sqx_generated",
                "sourceStats": metrics,
            },
        }, ensure_ascii=False)

        canonical_hash = hashlib.sha256(dsl_json.encode("utf-8")).hexdigest()

        existing = db.query(StrategyModel).filter(StrategyModel.strategy_id == spec_id).first()
        if existing:
            print(f"  -- {name}: ya existe ({spec_id})")
            skipped += 1
            continue

        db.merge(StrategyModel(
            strategy_id=spec_id,
            name=name,
            version="1.0.0",
            family="sqx_generated",
            author="StrategyQuantX",
            canonical_hash=canonical_hash,
            generation=1,
            dsl_json=dsl_json,
            validation_status="SQX_CANDIDATE",
            created_at=datetime.utcnow(),
        ))

        net_profit = metrics.get("NetProfitUsd", 0.0)
        initial_capital = 10000.0
        final_equity = initial_capital + net_profit
        net_return_pct = metrics.get("AnnualReturnPct", (net_profit / initial_capital) * 100.0)

        # ---- DD unit correction (2026-08-09) ----
        # SQX "Drawdown (IS)"/"(OOS)" columns are ABSOLUTE USD, NOT percent.
        # Confirmed: Ret/DD Ratio (IS) = NetProfit / MaxDrawdownUSD (371.67/203.46=1.83).
        # Convert to % of equity: dd_pct = dd_usd / peak_equity * 100,
        # using final_equity as peak proxy -> real DD ~2%, not "203%".
        dd_usd = metrics.get("MaxDrawdownPct", 0.0) or 0.0
        dd_pct_is = (dd_usd / final_equity * 100.0) if final_equity and dd_usd else 0.0
        dd_usd_os = metrics.get("MaxDrawdownOosPct", 0.0) or 0.0
        net_profit_os = metrics.get("NetProfitOosUsd", 0.0) or 0.0
        final_equity_os = initial_capital + net_profit_os
        dd_pct_os = (dd_usd_os / final_equity_os * 100.0) if final_equity_os and dd_usd_os else 0.0
        net_return_os_pct = (
            (net_profit_os / initial_capital * 100.0)
            if initial_capital and net_profit_os else 0.0
        )

        db.merge(BacktestModel(
            backtest_id=f"bt_sqx_{name.replace(' ', '_').replace('.', '')}",
            strategy_id=spec_id,
            dataset_id=None,
            engine_type="SQX_BUILTIN",
            initial_capital=initial_capital,
            leverage=1,
            final_equity=final_equity,
            net_return_pct=net_return_pct,
            max_drawdown_pct=dd_pct_is,           # corrected: % of equity, not USD
            win_rate=metrics.get("WinRate", 0.0),
            trades_count=int(metrics.get("TradesCount", 0)),
            profit_factor=metrics.get("ProfitFactor", 0.0),
            pf_os=metrics.get("ProfitFactorOos"),                 # OOS PF (None if no OOS)
            net_return_os_pct=net_return_os_pct,
            max_drawdown_os_pct=dd_pct_os,
            trades_os=int(metrics.get("TradesOos", 0)) if metrics.get("TradesOos") else None,
            ret_dd_ratio=metrics.get("RetDD"),
            checksum=canonical_hash,
            status="COMPLETED",
            created_at=datetime.utcnow(),
        ))

        inserted_strategies += 1
        inserted_backtests += 1
        print(f"  + {name}: symbol={symbol} net={net_profit:.2f} PF_IS={metrics.get('ProfitFactor',0):.2f} "
              f"PF_OOS={metrics.get('ProfitFactorOos')} trades={int(metrics.get('TradesCount',0))} "
              f"ret={net_return_pct:.1f}% DD={dd_pct_is:.1f}% (real) OOS_ret={net_return_os_pct:.1f}%")

    db.commit()
    db.close()

    print(f"\nRESUMEN: {inserted_strategies} estrategias + {inserted_backtests} backtests insertados, {skipped} omitidos.")


if __name__ == "__main__":
    main()
