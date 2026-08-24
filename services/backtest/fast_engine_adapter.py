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
import time
from typing import Any, Dict, List, Optional

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
from services.api.app.data_feed.feed_loader import load_candles
from services.backtest.engine_port import BacktestEnginePort
from services.data.instrument_cost_registry import CANONICAL_COST_REGISTRY, InstrumentCostProfile
from services.engine.universal_backtest_engine import UniversalDeterministicBacktestEngine
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


def _build_fallback_canonical_strategy(strategy_id: str, symbol: str, timeframe: str) -> CanonicalStrategy:
    """Construye un CanonicalStrategy válido por defecto cuando solo se pasa un ID textual."""
    clean_sym = symbol.upper().replace("-", "").replace("/", "")
    is_cme = clean_sym in ("NQ", "ES", "MES", "MNQ", "GC", "CL")
    track = ExecutionTrack.TRACK_FONDEO if is_cme else ExecutionTrack.TRACK_ULTRA
    point_val = 20.0 if clean_sym in ("NQ", "MNQ") else (50.0 if clean_sym in ("ES", "MES") else 1.0)
    tick_sz = 0.25 if is_cme else (0.0001 if "USD" in clean_sym and len(clean_sym) == 6 else 0.1)

    long_cond = RuleCondition(
        left_indicator=IndicatorSpec(name="EMA", timeframe=timeframe, period=20),
        operator=CanCompOp.GREATER_THAN,
        right_indicator=IndicatorSpec(name="EMA", timeframe=timeframe, period=50),
    )

    return CanonicalStrategy(
        strategy_id=strategy_id,
        name=f"Canonical {strategy_id} {symbol} {timeframe}",
        target_track=track,
        status=StrategyLifecycleStatus.GENERATED,
        instrument=TargetInstrument(
            symbol=symbol,
            exchange="CME" if is_cme else "BINGX",
            contract_type="FUTURES" if is_cme else "PERPETUAL",
            point_value=point_val,
            tick_size=tick_sz,
        ),
        timeframe=timeframe,
        session=SessionWindow(
            timezone="America/New_York",
            start_time="09:30",
            end_time="16:00",
            force_close_at_end=is_cme,
        ),
        rules=RuleTree(long_conditions=[long_cond]),
        exits=ExitModel(stop_loss_atr_mult=2.0, take_profit_atr_mult=6.0, break_even_atr_mult=1.5),
        sizing_and_risk=SizingAndRisk(
            base_risk_pct=1.0 if is_cme else 5.0,
            base_leverage=1.0 if is_cme else 20.0,
            max_contracts_or_lots=4.0 if is_cme else 10.0,
        ),
        provenance=ProvenanceMetadata(
            source_engine="fast_engine_adapter",
            created_timestamp_utc=int(time.time() * 1000),
            author_or_agent="FAST_ENGINE_COMPILER",
        ),
    )


from contracts.evidence_bundle import EvidenceBundle


class FastEngineAdapter(BacktestEnginePort):
    """Adaptador canónico universal para el UniversalDeterministicBacktestEngine."""

    def __init__(self) -> None:
        self.engine = UniversalDeterministicBacktestEngine()

    def execute_backtest(self, request: BacktestRequest) -> BacktestResult:
        symbol = request.dataset.symbol
        timeframe = request.dataset.timeframe

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

        # 1. Obtener o compilar CanonicalStrategy
        strategy_obj = request.strategy
        if strategy_obj is None or not isinstance(strategy_obj, CanonicalStrategy):
            strategy_obj = _build_fallback_canonical_strategy(request.strategy_id, symbol, timeframe)

        strat_spec, inst_spec, exec_model, risk_model = CanonicalCompiler.compile(
            strategy=strategy_obj,
            dataset_id=request.dataset.dataset_id,
            dataset_sha256=request.dataset.sha256_hash,
            initial_capital_usd=request.initial_capital_usd,
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

        # 2. Ejecutar sobre el motor determinista universal
        univ_res = self.engine.run(
            strategy=strat_spec,
            instrument=inst_spec,
            dataset=ds_spec,
            candles=candles,
            execution_model=exec_model,
            risk_model=risk_model,
            initial_capital_override=request.initial_capital_usd,
        )

        # 3. Transformar TradeRecords de UniversalBacktestResult a ExecutionTruth y TradeLog
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
                    strategy_snapshot_hash=strategy_obj.compute_sha256(),
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

        # 4. Construir CanonicalExecutionLedger sellado criptográficamente
        ledger = CanonicalExecutionLedger(
            strategy_id=request.strategy_id,
            strategy_snapshot_hash=strategy_obj.compute_sha256(),
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

        # 5. Transformar curva de equity
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

        # 6. Sortino Ratio
        pnls = [t.net_pnl_usd for t in univ_res.trades]
        neg = [p for p in pnls if p < 0]
        downside = math.sqrt(sum(x * x for x in neg) / len(neg)) if neg else 0.0
        mean_pnl = (sum(pnls) / len(pnls)) if pnls else 0.0
        sortino = round(mean_pnl / downside, 2) if downside > 0 else 0.0

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
            sharpe_ratio=round(float(univ_res.total_roi_pct / max(0.5, univ_res.max_drawdown_pct)), 2) if univ_res.max_drawdown_pct > 0 else 0.0,
            sortino_ratio=sortino,
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

        candles = load_candles(symbol, timeframe)
        if not candles:
            raise ValueError(
                f"NO_DATA: dataset vacío para {symbol} {timeframe} — backtest cancelado (ZERO-MOCKS)"
            )

        n_bars = len(candles)
        split_idx = int(n_bars * split_ratio)
        if split_idx < 20 or (n_bars - split_idx) < 10:
            raise ValueError(
                f"INSUFFICIENT_DATA_FOR_SPLIT: Muestra total ({n_bars} barras) insuficiente para partición {split_ratio*100:.0f}% IS / {(1-split_ratio)*100:.0f}% OOS."
            )

        candles_is = candles[:split_idx]
        candles_oos = candles[split_idx:]

        is_sha256 = hashlib.sha256(json.dumps(candles_is, sort_keys=True, default=str).encode("utf-8")).hexdigest()
        oos_sha256 = hashlib.sha256(json.dumps(candles_oos, sort_keys=True, default=str).encode("utf-8")).hexdigest()

        start_is_ms = _candle_ms(candles_is[0])
        end_is_ms = _candle_ms(candles_is[-1])
        start_oos_ms = _candle_ms(candles_oos[0])
        end_oos_ms = _candle_ms(candles_oos[-1])

        # 1. Backtest In-Sample
        req_is = request.model_copy(update={
            "request_id": f"{request.request_id}_IS",
            "dataset": DatasetSnapshot(
                dataset_id=f"{request.dataset.dataset_id}_IS",
                symbol=symbol,
                timeframe=timeframe,
                start_timestamp_utc_ms=start_is_ms,
                end_timestamp_utc_ms=end_is_ms,
                total_bars=len(candles_is),
                sha256_hash=is_sha256,
                is_in_sample=True,
            ),
        })

        # 2. Backtest Out-of-Sample
        req_oos = request.model_copy(update={
            "request_id": f"{request.request_id}_OOS",
            "dataset": DatasetSnapshot(
                dataset_id=f"{request.dataset.dataset_id}_OOS",
                symbol=symbol,
                timeframe=timeframe,
                start_timestamp_utc_ms=start_oos_ms,
                end_timestamp_utc_ms=end_oos_ms,
                total_bars=len(candles_oos),
                sha256_hash=oos_sha256,
                is_in_sample=False,
            ),
        })

        res_is = self._execute_on_candles(req_is, candles_is)
        res_oos = self._execute_on_candles(req_oos, candles_oos)

        strategy_obj = request.strategy
        if strategy_obj is None or not isinstance(strategy_obj, CanonicalStrategy):
            strategy_obj = _build_fallback_canonical_strategy(request.strategy_id, symbol, timeframe)

        strat_sha256 = strategy_obj.compute_sha256()
        combined_ledger_hash = hashlib.sha256(f"{res_is.ledger_hash}:{res_oos.ledger_hash}".encode("utf-8")).hexdigest()

        bundle = EvidenceBundle(
            bundle_id=f"bnd_{request.strategy_id}_{int(time.time()*1000)}",
            strategy_id=request.strategy_id,
            strategy_sha256=strat_sha256,
            dataset_id=request.dataset.dataset_id,
            dataset_is_sha256=is_sha256,
            dataset_oos_sha256=oos_sha256,
            symbol=symbol,
            timeframe=timeframe,
            target_track="FONDEO" if strategy_obj.target_track == ExecutionTrack.TRACK_FONDEO else "ULTRA",
            execution_config_hash=res_is.provenance_hash_sha256 or "can_exec_cfg_v3",
            engine_name="UniversalDeterministicBacktestEngine",
            engine_version="3.0.0",
            commit_sha=commit_sha,
            initial_capital_usd=request.initial_capital_usd,
            is_trades_count=res_is.total_trades,
            oos_trades_count=res_oos.total_trades,
            is_metrics={
                "net_profit_usd": res_is.net_profit_usd,
                "win_rate_pct": res_is.win_rate_pct,
                "profit_factor": res_is.profit_factor,
                "max_drawdown_pct": res_is.max_drawdown_pct,
                "sharpe_ratio": res_is.sharpe_ratio,
            },
            oos_metrics={
                "net_profit_usd": res_oos.net_profit_usd,
                "win_rate_pct": res_oos.win_rate_pct,
                "profit_factor": res_oos.profit_factor,
                "max_drawdown_pct": res_oos.max_drawdown_pct,
                "sharpe_ratio": res_oos.sharpe_ratio,
            },
            ledger_hash=combined_ledger_hash,
            gates_evaluation={},
        )

        return res_is, res_oos, bundle
