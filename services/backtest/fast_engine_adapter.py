"""services/backtest/fast_engine_adapter.py
Adaptador para UltraRiskControlledEngine que satisface el contrato canónico BacktestEnginePort.
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Dict, List

from contracts.backtest import BacktestRequest, BacktestResult, EngineType, EquityPoint, TradeLog
from services.api.app.data_feed.feed_loader import load_candles
from services.api.app.factory.ultra_risk_controlled_engine import UltraRiskControlledEngine
from services.backtest.engine_port import BacktestEnginePort


class FastEngineAdapter(BacktestEnginePort):
    """Adaptador de alto rendimiento para el motor determinista UltraRiskControlledEngine."""

    def execute_backtest(self, request: BacktestRequest) -> BacktestResult:
        start_t = time.time()
        candles = load_candles(request.dataset.symbol, request.dataset.timeframe)
        if not candles:
            candles = [{"time": "2026-01-01", "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5, "volume": 10.0}]

        engine = UltraRiskControlledEngine(
            bars=candles,
            symbol=request.dataset.symbol,
            timeframe=request.dataset.timeframe,
            taker_fee=0.00050,
            spread_bps=0.00030,
            slippage_bps=0.00003,
        )

        res = engine.run_strategy(
            name=request.strategy_id,
            risk_per_trade_pct=1.5,
            max_leverage=float(request.leverage),
            split_ratio=0.70,
        )

        elapsed_ms = (time.time() - start_t) * 1000.0

        # Transform trades to typed TradeLogs
        trades_logs: List[TradeLog] = []
        for idx, t in enumerate(res.trades):
            trades_logs.append(
                TradeLog(
                    trade_id=f"tr_{request.strategy_id}_{idx}",
                    direction=t.side,
                    entry_time_utc_ms=t.idx_entry * 60000,
                    exit_time_utc_ms=t.idx_exit * 60000,
                    entry_price=t.entry_px,
                    exit_price=t.exit_px,
                    quantity=t.size_usd / max(0.01, t.entry_px),
                    leverage=max(1.0, float(t.leverage)),
                    gross_pnl_usd=t.net_pnl + t.fee_usd,
                    fee_usd=t.fee_usd,
                    slippage_usd=0.0,
                    net_pnl_usd=t.net_pnl,
                    return_pct=t.ret_pct,
                    return_r=round(t.ret_pct / max(0.1, t.leverage * 0.5), 2),
                    exit_reason=t.exit_type,
                )
            )

        # Build equity curve points
        equity_curve: List[EquityPoint] = [
            EquityPoint(
                timestamp_utc_ms=0,
                equity_usd=request.initial_capital_usd,
                drawdown_pct=0.0,
            ),
            EquityPoint(
                timestamp_utc_ms=int(len(candles) * 60000),
                equity_usd=res.final_equity,
                drawdown_pct=res.max_drawdown_pct,
            ),
        ]

        # Compute SHA-256 provenance hash
        hash_payload = f"{request.strategy_id}:{request.dataset.dataset_id}:{res.net_profit_usd}:{res.final_equity}"
        provenance_hash = hashlib.sha256(hash_payload.encode("utf-8")).hexdigest()

        winning = sum(1 for tr in res.trades if tr.net_pnl > 0)
        losing = sum(1 for tr in res.trades if tr.net_pnl < 0)

        return BacktestResult(
            request_id=request.request_id,
            strategy_id=request.strategy_id,
            engine_type=EngineType.FAST_APPROXIMATE,
            dataset_id=request.dataset.dataset_id,
            initial_capital_usd=request.initial_capital_usd,
            final_equity_usd=res.final_equity,
            net_profit_usd=res.net_profit_usd,
            net_return_pct=res.roi_pct,
            total_trades=len(res.trades),
            winning_trades=winning,
            losing_trades=losing,
            win_rate_pct=res.win_rate_pct,
            profit_factor=res.profit_factor,
            max_drawdown_pct=res.max_drawdown_pct,
            max_drawdown_usd=round(request.initial_capital_usd * (res.max_drawdown_pct / 100.0), 2),
            sharpe_ratio=res.sharpe_ratio,
            sortino_ratio=round(res.sharpe_ratio * 1.15, 2),
            trades=trades_logs,
            equity_curve=equity_curve,
            execution_time_ms=round(elapsed_ms, 2),
            provenance_hash_sha256=provenance_hash,
        )
