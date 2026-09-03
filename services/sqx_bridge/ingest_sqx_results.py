"""Read-only StrategyQuant source parsing utilities.

This module intentionally contains NO database writer and NO backtest writer.
The canonical extraction endpoint is ``/api/v2/strategy-lab/extract/{project}``.
This file remains only as a compatibility parser for raw SQX columnar responses.

REAL-ONLY / ZERO-MOCK / ZERO-FORCING:
missing market identity stays missing; no capital, dataset, venue, timeframe or
profitability result is invented here.
"""
from __future__ import annotations

import json
from typing import Any

PROJECT = "Ultra_Auto_Pilot"
DATABANK = "Results"

COLUMN_MAP = {
    "Net profit (IS)": "NetProfitUsd",
    "# of trades (IS)": "TradesCount",
    "Profit factor (IS)": "ProfitFactor",
    "Drawdown (IS)": "MaxDrawdownUsd",
    "Win/Loss ratio (IS)": "WinLossRatio",
    "Annual % Return (IS)": "AnnualReturnPct",
    "Sharpe Ratio (IS)": "SharpeRatio",
    "Ret/DD Ratio (IS)": "RetDD",
    "Net profit (OOS)": "NetProfitOosUsd",
    "# of trades (OOS)": "TradesOos",
    "Profit factor (OOS)": "ProfitFactorOos",
    "Drawdown (OOS)": "MaxDrawdownOosUsd",
}


def extract_stats(stats: dict[str, Any] | str) -> dict[str, float]:
    """Map explicitly recognised SQX columns to numeric source statistics."""
    if isinstance(stats, str):
        try:
            stats = json.loads(stats)
        except json.JSONDecodeError:
            return {}
    if not isinstance(stats, dict):
        return {}

    columns = stats.get("columns") or []
    values = stats.get("values") or []
    if not columns or not values:
        # Soporte para filas planas de exportación CSV (sqcli export)
        out: dict[str, float] = {}
        for col_name, key in COLUMN_MAP.items():
            raw = stats.get(col_name)
            if raw is not None and str(raw).strip() != "":
                try:
                    out[key] = float(str(raw).strip())
                except (TypeError, ValueError):
                    pass
        return out

    # SQX commonly prefixes the metric array with source name/group. Preserve the
    # documented offset only when the shape proves it; never invent missing values.
    offset = 2 if len(values) >= len(columns) + 2 else 0
    out: dict[str, float] = {}
    for index, column in enumerate(columns):
        value_index = index + offset
        if value_index >= len(values):
            continue
        raw = values[value_index]
        key = COLUMN_MAP.get(str(column))
        if key is None or raw is None:
            continue
        try:
            out[key] = float(raw)
        except (TypeError, ValueError):
            continue
    return out


def explicit_symbol(stats: dict[str, Any] | str) -> str | None:
    """Return a symbol only when SQX labels the field explicitly."""
    if isinstance(stats, str):
        try:
            stats = json.loads(stats)
        except json.JSONDecodeError:
            return None
    if not isinstance(stats, dict):
        return None
    columns = stats.get("columns") or []
    values = stats.get("values") or []
    for column, value in zip(columns, values):
        if str(column).strip().lower() not in {"symbol", "instrument", "market", "asset"}:
            continue
        text = str(value).strip() if value is not None else ""
        return text.upper() if text else None
    return None


def explicit_timeframe(stats: dict[str, Any] | str) -> str | None:
    """Return a timeframe only when SQX labels it explicitly; never default."""
    if isinstance(stats, str):
        try:
            stats = json.loads(stats)
        except json.JSONDecodeError:
            return None
    if not isinstance(stats, dict):
        return None
    columns = stats.get("columns") or []
    values = stats.get("values") or []
    for column, value in zip(columns, values):
        if str(column).strip().lower() not in {"timeframe", "tf", "period", "bar period"}:
            continue
        text = str(value).strip() if value is not None else ""
        return text or None
    return None


# Deprecated compatibility entrypoint: writing from this module is forbidden.
def main() -> None:
    raise RuntimeError(
        "LEGACY_SQX_WRITER_DISABLED: use the read-only Strategy Lab API "
        "/api/v2/strategy-lab/extract/{project_name}."
    )


if __name__ == "__main__":
    main()
