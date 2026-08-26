"""services/discovery/funding_discovery.py
Motor de Búsqueda y Descubrimiento Cuantitativo para la Ruta FONDEO (Fase 3).
Optimización de candidatos para superar pruebas de prop firms en <= 5 días sujeto a Trailing DD <= 4.0% y DLL <= 2.0%.
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
from contracts.snapshots.strategy_snapshot import StrategySnapshot, StrategyRoute, PyramidingPolicy, MarginPolicy


class FundingSearchSpace(BaseModel):
    symbols: List[str] = Field(default_factory=lambda: ["NQ", "ES", "YM", "RTY", "CL", "GC", "EURUSD", "GBPUSD"])
    timeframes: List[str] = Field(default_factory=lambda: ["5m", "15m", "1h"])
    max_drawdown_ceiling_pct: float = Field(default=4.0, le=4.5)
    target_pass_days: int = Field(default=5, ge=1, le=20)


class FundingDiscoveryEngine:
    """Motor de generación y optimización para cuentas institucionales de Fondeo ($50k USD)."""

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
        ema_fast: int = 9,
        ema_slow: int = 21,
        rsi_period: int = 14,
        rsi_threshold_long: float = 50.0,
        rsi_threshold_short: float = 50.0,
        **kwargs: Any,
    ) -> StrategySnapshot:
        """Genera un StrategySnapshot inmutable con la configuración estricta para Fondeo."""
        entry_rules = RuleTree(
            logic=LogicalOp.AND,
            direction="BOTH",
            long_conditions=[
                ConditionNode(
                    left=IndicatorSpec(name="EMA", params={"period": ema_fast}, source_field="close", shift=0),
                    op=ComparisonOp.CROSS_ABOVE,
                    right=IndicatorSpec(name="EMA", params={"period": ema_slow}, source_field="close", shift=0),
                ),
                ConditionNode(
                    left=IndicatorSpec(name="RSI", params={"period": rsi_period}, source_field="close", shift=0),
                    op=ComparisonOp.GT,
                    right=rsi_threshold_long,
                ),
            ],
            short_conditions=[
                ConditionNode(
                    left=IndicatorSpec(name="EMA", params={"period": ema_fast}, source_field="close", shift=0),
                    op=ComparisonOp.CROSS_BELOW,
                    right=IndicatorSpec(name="EMA", params={"period": ema_slow}, source_field="close", shift=0),
                ),
                ConditionNode(
                    left=IndicatorSpec(name="RSI", params={"period": rsi_period}, source_field="close", shift=0),
                    op=ComparisonOp.LT,
                    right=rsi_threshold_short,
                ),
            ],
        )

        exit_rules = ExitModel(
            sl_type=StopLossType.FIXED_POINTS,
            sl_value=stop_loss_ticks,
            tp_type=TakeProfitType.FIXED_POINTS,
            tp_value=target_profit_ticks,
            time_stop_bars=36,
        )

        sizing = SizingAndRisk(
            sizing_type=SizingType.RISK_PCT_EQUITY,
            risk_value=risk_per_trade_pct,
            max_open_positions=1,
            max_daily_loss_usd=1000.0,
        )

        pyramiding = PyramidingPolicy(enabled=False)

        margin_policy = MarginPolicy(
            margin_mode="ISOLATED",
            max_leverage_ceiling=1.0,
            liquidation_buffer_min_pct=50.0,
            reinvestment_rate_pct=0.0,
            vault_harvest_rate_pct=0.0,
        )

        session_window = SessionWindow(
            start_time_utc="13:30",
            end_time_utc="20:00",
            close_at_eod=True,
            allowed_days=[0, 1, 2, 3, 4],
        )

        return StrategySnapshot.create_and_hash(
            strategy_id=strategy_id,
            route=StrategyRoute.FONDEO,
            archetype="INSTITUTIONAL_SESSION_MOMENTUM",
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
