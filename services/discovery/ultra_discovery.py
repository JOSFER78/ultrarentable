"""services/discovery/ultra_discovery.py
Motor de Búsqueda y Descubrimiento Cuantitativo para la Ruta ULTRA (Fase 3).
Exploración de convexidad, apalancamiento controlado (1x-5x) y gestión de riesgo asimétrico.
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
)
from contracts.snapshots.strategy_snapshot import StrategySnapshot, StrategyRoute, PyramidingPolicy, MarginPolicy


class UltraSearchSpace(BaseModel):
    symbols: List[str] = Field(default_factory=lambda: ["BTCUSDT", "ETHUSDT", "SOLUSDT", "NQ", "GC"])
    timeframes: List[str] = Field(default_factory=lambda: ["15m", "1h", "4h"])
    leverage_tiers: List[float] = Field(default_factory=lambda: [1.0, 2.0, 3.0, 5.0])
    max_tolerated_drawdown_pct: float = Field(default=25.0, ge=10.0, le=30.0)


class UltraDiscoveryEngine:
    """Motor de generación y optimización para subcuentas bala Ultra ($1k USD)."""

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
    ) -> StrategySnapshot:
        """Genera un StrategySnapshot inmutable con la configuración completa para la ruta Ultra."""
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
            sl_value=sl_value,
            tp_type=TakeProfitType.FIXED_POINTS,
            tp_value=tp_value,
            time_stop_bars=48,
        )

        sizing = SizingAndRisk(
            sizing_type=SizingType.RISK_PCT_EQUITY,
            risk_value=risk_pct,
            max_open_positions=1,
            max_daily_loss_usd=250.0,
        )

        pyramiding = PyramidingPolicy(enabled=False)

        margin_policy = MarginPolicy(
            margin_mode="ISOLATED",
            max_leverage_ceiling=leverage,
            liquidation_buffer_min_pct=30.0,
            reinvestment_rate_pct=0.0,
            vault_harvest_rate_pct=0.0,
        )

        return StrategySnapshot.create_and_hash(
            strategy_id=strategy_id,
            route=StrategyRoute.ULTRA,
            archetype="MOMENTUM_BREAKOUT",
            symbol=symbol,
            timeframe=timeframe,
            entry_rules=entry_rules,
            exit_rules=exit_rules,
            sizing_and_risk=sizing,
            dataset_id_reference=dataset_id,
            dataset_sha256_reference=dataset_sha256,
            pyramiding_policy=pyramiding,
            margin_policy=margin_policy,
        )
