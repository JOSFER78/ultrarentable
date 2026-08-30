"""Motor de Búsqueda y Descubrimiento Cuantitativo para la Ruta FONDEO."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from contracts.canonical_strategy import (
    RuleTree,
    ExitModel,
    StopLossType,
    TakeProfitType,
    SizingAndRisk,
    SizingType,
    IndicatorSpec,
    ConditionNode,
    ComparisonOp,
    LogicalOp,
    SessionWindow,
)
from contracts.snapshots.strategy_snapshot import StrategySnapshot, StrategyRoute, PyramidingPolicy, MarginPolicy


class FundingSearchSpace(BaseModel):
    symbols: List[str] = Field(
        default_factory=lambda: [
            "NQ", "ES", "YM", "RTY", "CL", "GC", "SI",
            "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD",
            "BTCUSDT", "ETHUSDT",
        ]
    )
    timeframes: List[str] = Field(default_factory=lambda: ["1m", "5m", "15m", "1h", "4h"])
    max_drawdown_ceiling_pct: float = Field(default=4.0, le=4.5)
    target_pass_days: int = Field(default=5, ge=1, le=20)


class FundingDiscoveryEngine:
    """Motor de generación y optimización para cuentas institucionales de Fondeo."""

    def __init__(self, search_space: Optional[FundingSearchSpace] = None):
        self.search_space = search_space or FundingSearchSpace()

    def generate_candidate_blueprint(
        self,
        strategy_id: str,
        symbol: str,
        timeframe: str,
        dataset_id: str,
        dataset_sha256: str,
        risk_per_trade_pct: float = 0.25,
        target_profit_ticks: float = 45.0,
        stop_loss_ticks: float = 15.0,
        sl_atr_mult: Optional[float] = None,
        tp_atr_mult: Optional[float] = None,
        ema_fast: int = 9,
        ema_slow: int = 21,
        rsi_period: int = 14,
        rsi_threshold_long: float = 50.0,
        rsi_threshold_short: float = 50.0,
        archetype: str = "INSTITUTIONAL_SESSION_MOMENTUM",
        time_stop_bars: int = 36,
        session_start_utc: str = "13:30",
        session_end_utc: str = "20:00",
        **kwargs: Any,
    ) -> StrategySnapshot:
        """Genera un StrategySnapshot con todos los parámetros del trial aplicados."""
        arch_upper = str(archetype).upper() if archetype else "INSTITUTIONAL_SESSION_MOMENTUM"
        ema_fast_spec = IndicatorSpec(name="EMA", params={"period": int(ema_fast)}, source_field="close", shift=0)
        ema_slow_spec = IndicatorSpec(name="EMA", params={"period": int(ema_slow)}, source_field="close", shift=0)
        rsi_spec = IndicatorSpec(name="RSI", params={"period": int(rsi_period)}, source_field="close", shift=0)

        if arch_upper in {"MEAN_REVERSION", "RSI_REVERSION"}:
            long_conditions = [
                ConditionNode(left=rsi_spec, op=ComparisonOp.LT, right=float(rsi_threshold_short)),
                ConditionNode(left=ema_fast_spec, op=ComparisonOp.GT, right=ema_slow_spec),
            ]
            short_conditions = [
                ConditionNode(left=rsi_spec, op=ComparisonOp.GT, right=float(rsi_threshold_long)),
                ConditionNode(left=ema_fast_spec, op=ComparisonOp.LT, right=ema_slow_spec),
            ]
        elif arch_upper in {"TREND_FOLLOWING", "EMA_CROSS"}:
            long_conditions = [ConditionNode(left=ema_fast_spec, op=ComparisonOp.CROSS_ABOVE, right=ema_slow_spec)]
            short_conditions = [ConditionNode(left=ema_fast_spec, op=ComparisonOp.CROSS_BELOW, right=ema_slow_spec)]
        elif arch_upper in {"RSI_MOMENTUM", "MOMENTUM_RSI"}:
            long_conditions = [
                ConditionNode(left=ema_fast_spec, op=ComparisonOp.GT, right=ema_slow_spec),
                ConditionNode(left=rsi_spec, op=ComparisonOp.GT, right=float(rsi_threshold_long)),
            ]
            short_conditions = [
                ConditionNode(left=ema_fast_spec, op=ComparisonOp.LT, right=ema_slow_spec),
                ConditionNode(left=rsi_spec, op=ComparisonOp.LT, right=float(rsi_threshold_short)),
            ]
        else:
            long_conditions = [
                ConditionNode(left=ema_fast_spec, op=ComparisonOp.CROSS_ABOVE, right=ema_slow_spec),
                ConditionNode(left=rsi_spec, op=ComparisonOp.GT, right=float(rsi_threshold_long)),
            ]
            short_conditions = [
                ConditionNode(left=ema_fast_spec, op=ComparisonOp.CROSS_BELOW, right=ema_slow_spec),
                ConditionNode(left=rsi_spec, op=ComparisonOp.LT, right=float(rsi_threshold_short)),
            ]

        entry_rules = RuleTree(
            logic=LogicalOp.AND,
            direction="BOTH",
            long_conditions=long_conditions,
            short_conditions=short_conditions,
        )

        if sl_atr_mult is not None and tp_atr_mult is not None:
            exit_rules = ExitModel(
                sl_type=StopLossType.ATR_MULTIPLE,
                sl_value=float(sl_atr_mult),
                tp_type=TakeProfitType.ATR_MULTIPLE,
                tp_value=float(tp_atr_mult),
                time_stop_bars=int(time_stop_bars),
            )
        else:
            exit_rules = ExitModel(
                sl_type=StopLossType.FIXED_POINTS,
                sl_value=float(stop_loss_ticks),
                tp_type=TakeProfitType.FIXED_POINTS,
                tp_value=float(target_profit_ticks),
                time_stop_bars=int(time_stop_bars),
            )

        sizing = SizingAndRisk(
            sizing_type=SizingType.RISK_PCT_EQUITY,
            risk_value=float(risk_per_trade_pct),
            max_open_positions=1,
            max_daily_loss_usd=float(kwargs.get("max_daily_loss_usd", 1000.0)),
        )
        session_window = SessionWindow(
            start_time_utc=session_start_utc,
            end_time_utc=session_end_utc,
            close_at_eod=True,
            allowed_days=[0, 1, 2, 3, 4],
        )
        return StrategySnapshot.create_and_hash(
            strategy_id=strategy_id,
            route=StrategyRoute.FONDEO,
            archetype=arch_upper,
            symbol=symbol,
            timeframe=timeframe,
            entry_rules=entry_rules,
            exit_rules=exit_rules,
            sizing_and_risk=sizing,
            dataset_id_reference=dataset_id,
            dataset_sha256_reference=dataset_sha256,
            pyramiding_policy=PyramidingPolicy(enabled=False),
            margin_policy=MarginPolicy(
                margin_mode="ISOLATED",
                max_leverage_ceiling=1.0,
                liquidation_buffer_min_pct=50.0,
                reinvestment_rate_pct=0.0,
                vault_harvest_rate_pct=0.0,
            ),
            session_window=session_window,
        )
