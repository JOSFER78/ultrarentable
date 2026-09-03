"""services/backtest/fast_engine_adapter.py
Adaptador Canónico Universal que conecta BacktestRequest con UniversalDeterministicBacktestEngine.

DOCTRINA ZERO-MOCKS & REAL-ONLY (v3.0.0):
- Cero estrategias hardcodeadas fijas: compila y ejecuta el AST (RuleTree) del CanonicalStrategy.
- Cero capitales inventados: el capital inicial proviene 100% de request.initial_capital_usd.
- Cero costes fijos no canónicos: provienen exclusivamente de CANONICAL_COST_REGISTRY[symbol].
- Cero pseudo-hashes: calcula el CanonicalExecutionLedger con encadenamiento Merkle SHA-256 real.
- Aislamiento físico IS/OOS soportado mediante run_isolated_is_oos().
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import time
from typing import Any, Dict, List, Optional, Tuple

from contracts.backtest import BacktestRequest, BacktestResult, DatasetSnapshot, EngineType, EquityPoint, TradeLog
from contracts.dataset_specification import DatasetSpecification, DatasetQualityReport
from contracts.canonical_execution import (
    AssetClass as CanAssetClass,
    CanonicalExecutionLedger,
    ExecutionTruth,
    ExitReason as CanExitReason,
    OrderSide,
)
from contracts.canonical_strategy import (
    CanonicalStrategy,
    ComparisonOperator as CanCompOp,
    ExecutionTrack,
    ExitModel,
    IndicatorSpec,
    ProvenanceMetadata,
    RuleCondition,
    RuleTree,
    SessionWindow,
    SizingAndRisk,
    StrategyLifecycleStatus,
    TargetInstrument,
)
from contracts.evidence_bundle import EvidenceBundle
from services.api.app.data_feed.feed_loader import load_candles
from services.backtest.engine_port import BacktestEnginePort
from services.data.instrument_cost_registry import CANONICAL_COST_REGISTRY, InstrumentCostProfile, get_instrument_cost_profile
from services.engine.universal_backtest_engine import UniversalDeterministicBacktestEngine
from services.engine_version import CURRENT_ENGINE_VERSION
from services.strategy_core.canonical_compiler import CanonicalCompiler


def _candle_ms(candle: Dict[str, Any]) -> int:
    """Timestamp real de la vela en ms UTC."""
    ts = candle.get("timestamp_utc_ms") or candle.get("timestamp_ms") or candle.get("timestamp") or candle.get("time")
    if isinstance(ts, (int, float)) and ts > 0:
        return int(ts)
    raw = str(candle.get("time", ""))
    try:
        return int(_dt.datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp() * 1000)
    except ValueError:
        return 0


class FastEngineAdapter(BacktestEnginePort):
    """Adaptador canónico universal para el UniversalDeterministicBacktestEngine."""

    def __init__(self) -> None:
        self.engine = UniversalDeterministicBacktestEngine()

    def _lookup_strategy(self, strategy_id: str) -> Optional[CanonicalStrategy]:
        """Busca una estrategia canónica persistida en base de datos o catálogo.

        Retorna None si no existe para que se aplique la doctrina fail-closed.
        """
        try:
            from services.discovery.strategy_search_registry import StrategySearchRegistry
            registry = StrategySearchRegistry()
            with sqlite3.connect(registry.db_path, timeout=5.0) as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT rules_json FROM discovery_search_trials WHERE trial_id = ?",
                    (strategy_id,),
                )
                row = cur.fetchone()
                if row and row[0]:
                    try:
                        return CanonicalStrategy.model_validate_json(row[0])
                    except Exception:
                        pass
        except Exception:
            pass

        for cat_dir in [Path("data/catalogs"), Path("data/artifacts")]:
            cat_path = cat_dir / f"{strategy_id}.json"
            if cat_path.exists():
                try:
                    with open(cat_path, "r", encoding="utf-8") as f:
                        return CanonicalStrategy.model_validate_json(f.read())
                except Exception:
                    pass

        return None

    def execute_backtest(self, request: BacktestRequest) -> BacktestResult:
        symbol = request.dataset.symbol
        timeframe = request.dataset.timeframe

        # Validate the canonical cost model before touching market-data loading.
        # Unknown instruments must fail closed with MissingCostModelError, never as a misleading NO_DATA.
        get_instrument_cost_profile(symbol)

        candles = load_candles(symbol, timeframe)
        if not candles:
            raise ValueError(
                f"NO_DATA: dataset vacío para {symbol} {timeframe} — backtest cancelado (ZERO-MOCKS)"
            )

        return self._execute_on_candles(request, candles)

    def _execute_on_candles(self, request: BacktestRequest, candles: List[Dict[str, Any]]) -> BacktestResult:
        start_t = time.perf_counter()
        symbol = request.dataset.symbol
        timeframe = request.dataset.timeframe

        strategy_obj = request.strategy
        if strategy_obj is None or not isinstance(strategy_obj, CanonicalStrategy):
            strategy_obj = self._lookup_strategy(request.strategy_id)
            if strategy_obj is None:
                raise ValueError(
                    f"MISSING_CANONICAL_STRATEGY: No se proporcionó definición de estrategia para {request.strategy_id}"
                )

        strat_spec, inst_spec, exec_model, risk_model = CanonicalCompiler.compile(
            strategy=strategy_obj,
            dataset_id=request.dataset.dataset_id,
            dataset_sha256=request.dataset.sha256_hash,
            initial_capital_usd=request.initial_capital_usd,
            override_symbol=symbol,
        )

        start_ts = _candle_ms(candles[0]) if candles else request.dataset.start_timestamp_utc_ms
        end_ts = _candle_ms(candles[-1]) if candles else request.dataset.end_timestamp_utc_ms

        ds_spec = DatasetSpecification(
            dataset_id=request.dataset.dataset_id,
            symbol=symbol,
            venue="CME" if symbol in ("NQ", "ES", "MES", "MNQ", "GC", "CL") else "BINGX",
            timeframe=timeframe,
            start_time_ms=start_ts,
            end_time_ms=end_ts,
            start_iso=_dt.datetime.fromtimestamp(start_ts / 1000, tz=_dt.timezone.utc).isoformat() if start_ts > 0 else "UNKNOWN",
            end_iso=_dt.datetime.fromtimestamp(end_ts / 1000, tz=_dt.timezone.utc).isoformat() if end_ts > 0 else "UNKNOWN",
            bar_count=len(candles),
            sha256_hash=request.dataset.sha256_hash,
            file_path=f"data/{symbol}_{timeframe}.parquet",
            quality_report=DatasetQualityReport(total_bars=len(candles)),
        )

        univ_res = self.engine.run(
            strategy=strat_spec,
            instrument=inst_spec,
            dataset=ds_spec,
            candles=candles,
            execution_model=exec_model,
            risk_model=risk_model,
            initial_capital_override=request.initial_capital_usd,
        )

        trades_logs: List[TradeLog] = []
        exec_truths: List[ExecutionTruth] = []

        for tr in univ_res.trades:
            exit_reason_str = tr.exit_reason or "TAKE_PROFIT"
            can_exit_reason = CanExitReason.TAKE_PROFIT
            if "STOP" in exit_reason_str:
                can_exit_reason = CanExitReason.STOP_LOSS
            elif "TRAILING" in exit_reason_str:
                can_exit_reason = CanExitReason.TRAILING_STOP
            elif "SESSION" in exit_reason_str:
                can_exit_reason = CanExitReason.SESSION_END

            trades_logs.append(
                TradeLog(
                    trade_id=tr.trade_id,
                    direction=tr.direction,
                    entry_time_utc_ms=tr.entry_time_ms,
                    exit_time_utc_ms=tr.exit_time_ms,
                    entry_price=tr.entry_price,
                    exit_price=tr.exit_price,
                    quantity=tr.quantity,
                    leverage=tr.leverage_used,
                    gross_pnl_usd=tr.gross_pnl_usd,
                    fee_usd=tr.commission_usd + tr.funding_usd,
                    slippage_usd=tr.slippage_usd,
                    net_pnl_usd=tr.net_pnl_usd,
                    return_pct=tr.return_pct,
                    return_r=tr.return_r,
                    exit_reason=exit_reason_str,
                )
            )

            exec_truths.append(
                ExecutionTruth(
                    trade_id=tr.trade_id,
                    symbol=tr.symbol,
                    side=OrderSide.BUY if tr.direction.upper() == "LONG" else OrderSide.SELL,
                    entry_timestamp_utc_ms=tr.entry_time_ms,
                    exit_timestamp_utc_ms=tr.exit_time_ms,
                    market_data_hash=request.dataset.sha256_hash,
                    strategy_snapshot_hash=strategy_obj.strategy_hash,
                    execution_config_hash=request.execution_config_hash or exec_model.compute_hash(),
                    decision_price=tr.entry_price,
                    requested_qty=tr.quantity,
                    filled_qty=tr.quantity,
                    entry_price=tr.entry_price,
                    exit_price=tr.exit_price,
                    commission_usd=tr.commission_usd,
                    slippage_usd=tr.slippage_usd,
                    funding_usd=tr.funding_usd,
                    total_friction_cost_usd=tr.commission_usd + tr.slippage_usd + tr.funding_usd,
                    gross_pnl_usd=tr.gross_pnl_usd,
                    net_pnl_usd=tr.net_pnl_usd,
                    return_r=tr.return_r,
                    exit_reason=can_exit_reason,
                    notional_usd=tr.notional_usd,
                    margin_used_usd=tr.notional_usd / max(1.0, tr.leverage_used),
                    leverage_actual=tr.leverage_used,
                    equity_before_usd=tr.equity_before_usd,
                    equity_after_usd=tr.equity_after_usd,
                    drawdown_after_pct=0.0,
                )
            )

        ledger = CanonicalExecutionLedger(
            strategy_id=request.strategy_id,
            strategy_snapshot_hash=strategy_obj.strategy_hash,
            dataset_sha256=request.dataset.sha256_hash,
            execution_config_hash=request.execution_config_hash or exec_model.compute_hash(),
            engine_name="UniversalDeterministicBacktestEngine",
            initial_capital_usd=request.initial_capital_usd,
            final_equity_usd=univ_res.final_equity_usd,
            net_profit_usd=univ_res.net_profit_usd,
            roi_pct=univ_res.total_roi_pct,
            profit_factor=univ_res.profit_factor,
            win_rate_pct=univ_res.win_rate_pct,
            max_drawdown_pct=univ_res.max_drawdown_pct,
            peak_leverage_used=univ_res.peak_margin_utilization_pct / 100.0 * risk_model.max_leverage,
            total_trades_count=univ_res.total_trades,
            winning_trades_count=univ_res.winning_trades,
            losing_trades_count=univ_res.losing_trades,
            total_commission_paid_usd=univ_res.total_commissions_usd,
            total_slippage_paid_usd=univ_res.total_slippage_usd,
            total_funding_paid_usd=univ_res.total_funding_usd,
            trades=exec_truths,
        )

        if univ_res.bar_ledger:
            equity_curve: List[EquityPoint] = [
                EquityPoint(timestamp_utc_ms=ep.timestamp_ms, equity_usd=ep.equity_usd, drawdown_pct=ep.drawdown_pct)
                for ep in univ_res.bar_ledger
            ]
        elif univ_res.trades:
            equity_curve = [
                EquityPoint(timestamp_utc_ms=t.exit_time_ms, equity_usd=t.equity_after_usd, drawdown_pct=0.0)
                for t in univ_res.trades
            ]
        else:
            first_ts = _candle_ms(candles[0]) if candles else 0
            equity_curve = [
                EquityPoint(timestamp_utc_ms=first_ts, equity_usd=request.initial_capital_usd, drawdown_pct=0.0)
            ]

        trade_returns = [t.return_pct for t in univ_res.trades]
        n_trades = len(trade_returns)
        if n_trades >= 2:
            span_ms = (end_ts - start_ts) if (end_ts > start_ts and start_ts > 0) else 0
            span_years = max(1.0 / 365.25, (span_ms / (1000.0 * 86400.0)) / 365.25) if span_ms > 0 else 1.0
            trades_per_year = n_trades / span_years
            mean_ret = sum(trade_returns) / n_trades
            variance = sum((r - mean_ret) ** 2 for r in trade_returns) / n_trades
            std_ret = math.sqrt(variance)
            sharpe_ratio = round((mean_ret / std_ret) * math.sqrt(trades_per_year), 2) if std_ret > 1e-8 else 0.0
            neg = [r for r in trade_returns if r < 0]
            if neg:
                downside_std = math.sqrt(sum(x * x for x in neg) / len(neg))
                sortino_ratio = round((mean_ret / downside_std) * math.sqrt(trades_per_year), 2) if downside_std > 1e-8 else 0.0
            else:
                sortino_ratio = 0.0
        else:
            sharpe_ratio = 0.0
            sortino_ratio = 0.0

        elapsed_ms = (time.perf_counter() - start_t) * 1000.0

        return BacktestResult(
            request_id=request.request_id,
            strategy_id=request.strategy_id,
            engine_type=EngineType.FAST_APPROXIMATE,
            dataset_id=request.dataset.dataset_id,
            ledger_hash=ledger.ledger_hash,
            initial_capital_usd=request.initial_capital_usd,
            final_equity_usd=univ_res.final_equity_usd,
            net_profit_usd=univ_res.net_profit_usd,
            net_return_pct=univ_res.total_roi_pct,
            total_trades=univ_res.total_trades,
            winning_trades=univ_res.winning_trades,
            losing_trades=univ_res.losing_trades,
            win_rate_pct=univ_res.win_rate_pct,
            profit_factor=univ_res.profit_factor,
            max_drawdown_pct=univ_res.max_drawdown_pct,
            max_drawdown_usd=round((univ_res.max_drawdown_pct / 100.0) * request.initial_capital_usd, 2),
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            trades=trades_logs,
            equity_curve=equity_curve,
            execution_time_ms=round(elapsed_ms, 2),
            provenance_hash_sha256=univ_res.provenance_hash,
        )

    def run_isolated_is_oos(
        self,
        request: BacktestRequest,
        split_ratio: float = 0.70,
        commit_sha: str = "HEAD",
    ) -> Tuple[BacktestResult, BacktestResult, EvidenceBundle]:
        """Ejecuta In-Sample y Out-of-Sample de forma 100% aislada con 0% data leakage y empaqueta en EvidenceBundle."""
        symbol = request.dataset.symbol
        timeframe = request.dataset.timeframe

        get_instrument_cost_profile(symbol)
        candles = load_candles(symbol, timeframe)
        if not candles:
            raise ValueError(
                f"NO_DATA: dataset vacío para {symbol} {timeframe} — backtest cancelado (ZERO-MOCKS)"
            )

        strategy_obj = request.strategy
        if strategy_obj is None or not isinstance(strategy_obj, CanonicalStrategy):
            strategy_obj = self._lookup_strategy(request.strategy_id)
            if strategy_obj is None:
                raise ValueError(
                    f"MISSING_CANONICAL_STRATEGY: No se proporcionó definición de estrategia para {request.strategy_id}"
                )

        n_bars = len(candles)
        split_idx = int(n_bars * split_ratio)
        if split_idx < 20 or (n_bars - split_idx) < 10:
            raise ValueError(
                f"INSUFFICIENT_DATA_FOR_SPLIT: Muestra total ({n_bars} barras), split={split_ratio} inválido"
            )

        is_candles = candles[:split_idx]
        oos_candles = candles[split_idx:]
        base_request = request.model_copy(update={"strategy": strategy_obj})
        is_sha = hashlib.sha256(json.dumps(is_candles, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        oos_sha = hashlib.sha256(json.dumps(oos_candles, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        split_bar_ts = int(candles[split_idx].get("timestamp_utc_ms") or candles[split_idx].get("timestamp_ms") or 0)
        is_dataset = request.dataset.model_copy(update={
            "dataset_id": f"{request.dataset.dataset_id}_IS",
            "sha256_hash": is_sha,
            "total_bars": split_idx,
            "end_timestamp_utc_ms": split_bar_ts,
            "is_in_sample": True,
        })
        oos_dataset = request.dataset.model_copy(update={
            "dataset_id": f"{request.dataset.dataset_id}_OOS",
            "sha256_hash": oos_sha,
            "total_bars": n_bars - split_idx,
            "start_timestamp_utc_ms": split_bar_ts,
            "is_in_sample": False,
        })
        is_request = base_request.model_copy(update={"request_id": f"{request.request_id}:IS", "dataset": is_dataset})
        oos_request = base_request.model_copy(update={"request_id": f"{request.request_id}:OOS", "dataset": oos_dataset})
        is_result = self._execute_on_candles(is_request, is_candles)
        oos_result = self._execute_on_candles(oos_request, oos_candles)

        evidence = EvidenceBundle(
            bundle_id=f"EB-{request.request_id}",
            strategy_id=request.strategy_id,
            strategy_sha256=strategy_obj.strategy_hash,
            dataset_id=request.dataset.dataset_id,
            dataset_is_sha256=is_sha,
            dataset_oos_sha256=oos_sha,
            symbol=symbol,
            timeframe=timeframe,
            target_track=str(getattr(strategy_obj, "route", request.strategy.route)),
            execution_config_hash=request.execution_config_hash or hashlib.sha256(
                json.dumps({"fee_multiplier": request.fee_multiplier, "slippage_bps": request.slippage_bps}, sort_keys=True).encode()
            ).hexdigest(),
            engine_name="UniversalDeterministicBacktestEngine",
            # W4.2: antes hardcodeado a "5.4.0" -- estampaba SIEMPRE un motor viejo en el
            # EvidenceBundle aunque el backtest se ejecutara con el motor vigente (SSOT:
            # services/engine_version.py). Aguas abajo (is_version_stale, gobernanza_regla26)
            # eso descartaba la evidencia como STALE pase lo que pase.
            engine_version=CURRENT_ENGINE_VERSION,
            commit_sha=commit_sha,
            initial_capital_usd=request.initial_capital_usd,
            is_trades_count=is_result.total_trades,
            oos_trades_count=oos_result.total_trades,
            is_metrics={
                "profit_factor": is_result.profit_factor,
                "net_return_pct": is_result.net_return_pct,
                "max_drawdown_pct": is_result.max_drawdown_pct,
            },
            oos_metrics={
                "profit_factor": oos_result.profit_factor,
                "net_return_pct": oos_result.net_return_pct,
                "max_drawdown_pct": oos_result.max_drawdown_pct,
            },
            ledger_hash=hashlib.sha256((is_result.ledger_hash + oos_result.ledger_hash).encode()).hexdigest(),
            gates_evaluation={},
        )
        return is_result, oos_result, evidence
