"""Motor de Búsqueda y Descubrimiento Cuantitativo para la Ruta ULTRA.
ZERO-MOCKS · REAL-ONLY · MERKLE PROVENANCE
"""

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
from contracts.snapshots.strategy_snapshot import (
    StrategySnapshot,
    StrategyRoute,
    PyramidingPolicy,
    MarginPolicy,
    PyramidingTier,
)


class UltraSearchSpace(BaseModel):
    symbols: List[str] = Field(default_factory=lambda: ["BTCUSDT", "ETHUSDT", "SOLUSDT", "NQ", "GC"])
    timeframes: List[str] = Field(default_factory=lambda: ["15m", "1h", "4h"])
    leverage_tiers: List[float] = Field(default_factory=lambda: [1.0, 2.0, 3.0, 5.0])
    max_tolerated_drawdown_pct: float = Field(default=25.0, ge=10.0, le=30.0)


class UltraDiscoveryEngine:
    """Motor de generación y optimización para subcuentas bala Ultra."""

    def __init__(self, search_space: Optional[UltraSearchSpace] = None):
        self.search_space = search_space or UltraSearchSpace()

    def generate_candidate_blueprint(
        self,
        strategy_id: str,
        symbol: str,
        timeframe: str,
        dataset_id: str,
        dataset_sha256: str,
        leverage: float = 3.0,
        risk_pct: float = 1.5,
        sl_value: float = 20.0,
        tp_value: float = 60.0,
        ema_fast: int = 20,
        ema_slow: int = 50,
        rsi_period: int = 14,
        rsi_threshold_long: float = 52.0,
        rsi_threshold_short: float = 48.0,
        sl_atr_mult: Optional[float] = None,
        tp_atr_mult: Optional[float] = None,
        pyramiding_tiers_count: Optional[int] = None,
        archetype: Optional[str] = None,
        volatility_filter: Optional[str] = None,
        volume_confirmation: Optional[str] = None,
        breakout_confirmation: bool = False,
        breakout_lookback: int = 20,
        exit_family: Optional[str] = None,
        session_profile: Optional[str] = None,
        **kwargs: Any,
    ) -> StrategySnapshot:
        """Genera un Snapshot canónico; las mutaciones admitidas cambian reglas ejecutables reales."""
        archetype = str(archetype).upper() if archetype else "MOMENTUM_BREAKOUT"
        ema_fast_spec = IndicatorSpec(name="EMA", params={"period": int(ema_fast)}, source_field="close", shift=0)
        ema_slow_spec = IndicatorSpec(name="EMA", params={"period": int(ema_slow)}, source_field="close", shift=0)
        rsi_spec = IndicatorSpec(name="RSI", params={"period": int(rsi_period)}, source_field="close", shift=0)

        if archetype in {"MEAN_REVERSION", "RSI_REVERSION"}:
            long_conditions = [
                ConditionNode(left=rsi_spec, op=ComparisonOp.LT, right=float(rsi_threshold_short)),
                ConditionNode(left=ema_fast_spec, op=ComparisonOp.GT, right=ema_slow_spec),
            ]
            short_conditions = [
                ConditionNode(left=rsi_spec, op=ComparisonOp.GT, right=float(rsi_threshold_long)),
                ConditionNode(left=ema_fast_spec, op=ComparisonOp.LT, right=ema_slow_spec),
            ]
        elif archetype in {"TREND_FOLLOWING", "EMA_CROSS"}:
            long_conditions = [ConditionNode(left=ema_fast_spec, op=ComparisonOp.CROSS_ABOVE, right=ema_slow_spec)]
            short_conditions = [ConditionNode(left=ema_fast_spec, op=ComparisonOp.CROSS_BELOW, right=ema_slow_spec)]
        elif archetype in {"RSI_MOMENTUM", "MOMENTUM_RSI"}:
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

        if volatility_filter == "ATR_REGIME":
            atr_fast = IndicatorSpec(name="ATR", params={"period": 14}, source_field="close", shift=0)
            atr_slow = IndicatorSpec(name="ATR", params={"period": 50}, source_field="close", shift=0)
            long_conditions.append(ConditionNode(left=atr_fast, op=ComparisonOp.GT, right=atr_slow))
            short_conditions.append(ConditionNode(left=atr_fast, op=ComparisonOp.GT, right=atr_slow))

        if volume_confirmation == "RELATIVE_VOLUME":
            volume_now = IndicatorSpec(name="VOLUME", params={}, source_field="volume", shift=0)
            volume_avg = IndicatorSpec(name="SMA", params={"period": 20}, source_field="volume", shift=0)
            long_conditions.append(ConditionNode(left=volume_now, op=ComparisonOp.GT, right=volume_avg))
            short_conditions.append(ConditionNode(left=volume_now, op=ComparisonOp.GT, right=volume_avg))

        if breakout_confirmation:
            lookback = max(2, int(breakout_lookback))
            # Shift=1 means the Donchian reference excludes the current decision bar.
            high_break = IndicatorSpec(name="DONCHIAN_HIGH", params={"period": lookback}, source_field="high", shift=1)
            low_break = IndicatorSpec(name="DONCHIAN_LOW", params={"period": lookback}, source_field="low", shift=1)
            close_spec = IndicatorSpec(name="PRICE_CLOSE", params={}, source_field="close", shift=0)
            long_conditions.append(ConditionNode(left=close_spec, op=ComparisonOp.GT, right=high_break))
            short_conditions.append(ConditionNode(left=close_spec, op=ComparisonOp.LT, right=low_break))

        entry_rules = RuleTree(
            logic=LogicalOp.AND,
            direction="BOTH",
            long_conditions=long_conditions,
            short_conditions=short_conditions,
        )

        if exit_family == "RR_DYNAMIC":
            final_sl_type = StopLossType.ATR_MULTIPLE
            final_sl_val = float(sl_atr_mult if sl_atr_mult is not None else 2.0)
            final_tp_type = TakeProfitType.RR_MULTIPLE
            final_tp_val = float(kwargs.get("rr_multiple", 2.5))
            trail_after_r = None
        elif exit_family == "TIME_DECAY":
            final_sl_type = StopLossType.ATR_MULTIPLE
            final_sl_val = float(sl_atr_mult if sl_atr_mult is not None else 2.0)
            final_tp_type = TakeProfitType.ATR_MULTIPLE
            final_tp_val = float(tp_atr_mult if tp_atr_mult is not None else 6.0)
            trail_after_r = None
        elif exit_family == "TRAILING_PROFIT":
            final_sl_type = StopLossType.ATR_MULTIPLE
            final_sl_val = float(sl_atr_mult if sl_atr_mult is not None else 2.0)
            final_tp_type = TakeProfitType.ATR_MULTIPLE
            final_tp_val = float(tp_atr_mult if tp_atr_mult is not None else 6.0)
            trail_after_r = float(kwargs.get("trail_after_r", 1.5))
        else:
            final_sl_type = StopLossType.ATR_MULTIPLE if sl_atr_mult is not None else StopLossType.FIXED_POINTS
            final_sl_val = float(sl_atr_mult) if sl_atr_mult is not None else float(sl_value)
            final_tp_type = TakeProfitType.ATR_MULTIPLE if tp_atr_mult is not None else TakeProfitType.FIXED_POINTS
            final_tp_val = float(tp_atr_mult) if tp_atr_mult is not None else float(tp_value)
            trail_after_r = None

        time_stop = int(kwargs.get("time_stop_bars", 48))
        if exit_family == "TIME_DECAY":
            time_stop = min(time_stop, 24)

        exit_rules = ExitModel(
            sl_type=final_sl_type,
            sl_value=final_sl_val,
            tp_type=final_tp_type,
            tp_value=final_tp_val,
            trail_after_r=trail_after_r,
            time_stop_bars=time_stop,
        )
        sizing = SizingAndRisk(
            sizing_type=SizingType.RISK_PCT_EQUITY,
            risk_value=float(risk_pct),
            max_open_positions=1,
            max_daily_loss_usd=float(kwargs.get("max_daily_loss_usd", 250.0)),
        )
        tier_count = int(pyramiding_tiers_count or 0)
        tiers_list = [
            PyramidingTier(
                trigger_pnl_atr_mult=float(i * 1.5),
                added_size_mult=0.5,
                trail_stop_to_breakeven=True,
            )
            for i in range(1, tier_count + 1)
        ]
        pyramiding = PyramidingPolicy(
            enabled=tier_count > 0,
            max_tiers=tier_count if tier_count > 0 else 3,
            tiers=tiers_list,
        )
        session_window = None
        if session_profile == "LIQUIDITY_CORE":
            session_window = SessionWindow(
                start_time_utc="13:30",
                end_time_utc="20:00",
                close_at_eod=True,
                allowed_days=[0, 1, 2, 3, 4],
            )
        margin_policy = MarginPolicy(
            margin_mode="ISOLATED",
            max_leverage_ceiling=float(leverage),
            liquidation_buffer_min_pct=30.0,
            reinvestment_rate_pct=0.0,
            vault_harvest_rate_pct=0.0,
        )
        return StrategySnapshot.create_and_hash(
            strategy_id=strategy_id,
            route=StrategyRoute.ULTRA,
            archetype=archetype,
            symbol=symbol,
            timeframe=timeframe,
            entry_rules=entry_rules,
            exit_rules=exit_rules,
            sizing_and_risk=sizing,
            dataset_id_reference=dataset_id,
            dataset_sha256_reference=dataset_sha256,
            pyramiding_policy=pyramiding,
            margin_policy=margin_policy,
            session_window=session_window,
        )
