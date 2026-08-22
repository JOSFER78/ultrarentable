"""services/backtest/fast_engine_adapter.py
Adaptador para UltraRiskControlledEngine que satisface el contrato canónico BacktestEnginePort.

DOCTRINA ZERO-MOCKS (FASE 1d):
- Sin datos reales de mercado NO se ejecuta el backtest (antes se inventaba 1 vela sintética).
- La curva de equity se construye operación a operación con el capital interno del motor.
- R y sortino se calculan a partir de PnL reales, no con fórmulas aproximadas.
- El hash de provenance cubre motor, datos, costes y parámetros.
LIMITACIÓN CONOCIDA (a resolver en FASE 2): el motor interno ejecuta una estrategia fija
EMA/Donchian; este adaptador sólo traduce resultados. El motor universal
(UniversalDeterministicBacktestEngine) es el camino canónico.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
import time
from typing import Any, Dict, List

from contracts.backtest import BacktestRequest, BacktestResult, EngineType, EquityPoint, TradeLog
from services.api.app.data_feed.feed_loader import load_candles
from services.api.app.factory.ultra_risk_controlled_engine import UltraRiskControlledEngine
from services.backtest.engine_port import BacktestEnginePort

# Costes por defecto del adaptador (fracción, no bps): deben provenir del ExecutionSpec en FASE 2
TAKER_FEE = 0.00050
SPREAD = 0.00030
SLIPPAGE = 0.00003
RISK_PER_TRADE_PCT = 1.5
SPLIT_RATIO = 0.70
ENGINE_INTERNAL_CAPITAL = 10_000.0  # capital fijo interno de UltraRiskControlledEngine


def _candle_ms(candle: Dict[str, Any]) -> int:
    """Timestamp real de la vela en ms UTC; 0 si no es parseable (best-effort, sin inventar fechas)."""
    raw = str(candle.get("time", ""))
    try:
        return int(_dt.datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp() * 1000)
    except ValueError:
        return 0


class FastEngineAdapter(BacktestEnginePort):
    """Adaptador de alto rendimiento para el motor determinista UltraRiskControlledEngine."""

    def execute_backtest(self, request: BacktestRequest) -> BacktestResult:
        start_t = time.time()
        candles = load_candles(request.dataset.symbol, request.dataset.timeframe)
        if not candles:
            # ZERO-MOCKS: sin velas reales no hay backtest (antes: vela sintética {open: 100...})
            raise ValueError(
                "NO_DATA: dataset vacío para "
                f"{request.dataset.symbol} {request.dataset.timeframe} — backtest cancelado (ZERO-MOCKS)"
            )
        times_ms = [_candle_ms(c) for c in candles]

        engine = UltraRiskControlledEngine(
            bars=candles,
            symbol=request.dataset.symbol,
            timeframe=request.dataset.timeframe,
            taker_fee=TAKER_FEE,
            spread_bps=SPREAD,
            slippage_bps=SLIPPAGE,
        )

        res = engine.run_strategy(
            name=request.strategy_id,
            risk_per_trade_pct=RISK_PER_TRADE_PCT,
            max_leverage=float(request.leverage),
            split_ratio=SPLIT_RATIO,
        )

        elapsed_ms = (time.time() - start_t) * 1000.0

        # Transform trades to typed TradeLogs con R real (pnl / riesgo presupuestado de la operación)
        trades_logs: List[TradeLog] = []
        equity = ENGINE_INTERNAL_CAPITAL
        for idx, t in enumerate(res.trades):
            risk_usd = equity * (RISK_PER_TRADE_PCT / 100.0)
            entry_ms = times_ms[t.idx_entry] if 0 <= t.idx_entry < len(times_ms) else 0
            exit_ms = times_ms[t.idx_exit] if 0 <= t.idx_exit < len(times_ms) else 0
            qty = t.size_usd / max(0.01, t.entry_px)
            trades_logs.append(
                TradeLog(
                    trade_id=f"tr_{request.strategy_id}_{idx}",
                    direction=t.side,
                    entry_time_utc_ms=entry_ms,
                    exit_time_utc_ms=exit_ms,
                    entry_price=t.entry_px,
                    exit_price=t.exit_px,
                    quantity=qty,
                    leverage=max(1.0, float(t.leverage)),
                    gross_pnl_usd=t.net_pnl + t.fee_usd,  # reconstruido: net + fee (el motor no expone bruto)
                    fee_usd=t.fee_usd,
                    # Estimación derivada de la configuración (slippage sobre nocional en entry+exit)
                    slippage_usd=round(t.size_usd * SLIPPAGE * 2.0, 4),
                    net_pnl_usd=t.net_pnl,
                    return_pct=t.ret_pct,
                    return_r=round(t.net_pnl / risk_usd, 2) if risk_usd > 0 else 0.0,
                    exit_reason=t.exit_type,
                )
            )
            equity += t.net_pnl

        # Curva de equity real operación a operación (antes: sólo 2 puntos)
        equity_curve: List[EquityPoint] = []
        eq = ENGINE_INTERNAL_CAPITAL
        peak = eq
        equity_curve.append(EquityPoint(timestamp_utc_ms=times_ms[0] if times_ms else 0, equity_usd=round(eq, 2), drawdown_pct=0.0))
        for tl, t in zip(trades_logs, res.trades):
            eq += t.net_pnl
            peak = max(peak, eq)
            dd_pct = round((peak - eq) / peak * 100.0, 2) if peak > 0 else 0.0
            equity_curve.append(EquityPoint(timestamp_utc_ms=tl.exit_time_utc_ms, equity_usd=round(eq, 2), drawdown_pct=dd_pct))

        # Provenance ampliado: motor, datos, costes y parámetros (antes: 4 campos)
        hash_payload = json.dumps(
            {
                "engine": "UltraRiskControlledEngine",
                "adapter": "fast_engine_adapter",
                "strategy_id": request.strategy_id,
                "dataset_id": request.dataset.dataset_id,
                "symbol": request.dataset.symbol,
                "timeframe": request.dataset.timeframe,
                "n_bars": len(candles),
                "first_bar": times_ms[0] if times_ms else None,
                "last_bar": times_ms[-1] if times_ms else None,
                "taker_fee": TAKER_FEE,
                "spread": SPREAD,
                "slippage": SLIPPAGE,
                "risk_per_trade_pct": RISK_PER_TRADE_PCT,
                "split_ratio": SPLIT_RATIO,
                "leverage": request.leverage,
                "net_profit_usd": res.net_profit_usd,
                "final_equity": res.final_equity,
            },
            sort_keys=True,
        )
        provenance_hash = hashlib.sha256(hash_payload.encode("utf-8")).hexdigest()

        winning = sum(1 for tr in res.trades if tr.net_pnl > 0)
        losing = sum(1 for tr in res.trades if tr.net_pnl < 0)

        # Sortino real por trade (media de PnL / desviación downside), antes: sharpe * 1.15
        pnls = [t.net_pnl for t in res.trades]
        neg = [p for p in pnls if p < 0]
        downside = math.sqrt(sum(x * x for x in neg) / len(neg)) if neg else 0.0
        mean_pnl = (sum(pnls) / len(pnls)) if pnls else 0.0
        sortino = round(mean_pnl / downside, 2) if downside > 0 else 0.0

        return BacktestResult(
            request_id=request.request_id,
            strategy_id=request.strategy_id,
            engine_type=EngineType.FAST_APPROXIMATE,
            dataset_id=request.dataset.dataset_id,
            # FASE 2: sustituir por el hash del CanonicalExecutionLedger real cuando exista
            ledger_hash=provenance_hash,
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
            max_drawdown_usd=round(res.max_drawdown_pct / 100.0 * ENGINE_INTERNAL_CAPITAL, 2),
            sharpe_ratio=res.sharpe_ratio,
            sortino_ratio=sortino,
            trades=trades_logs,
            equity_curve=equity_curve,
            execution_time_ms=round(elapsed_ms, 2),
            provenance_hash_sha256=provenance_hash,
        )
