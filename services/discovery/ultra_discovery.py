"""services/discovery/ultra_discovery.py
Motor de Búsqueda y Descubrimiento Cuantitativo para la Ruta ULTRA (Fase 3).
Exploración agresiva de convexidad, apalancamiento dinámico, piramidación sobre beneficios y reciclaje de margen.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from contracts.canonical_strategy import RuleTree, ExitModel, SizingAndRisk, IndicatorSpec, RuleCondition, ComparisonOperator
from contracts.snapshots.strategy_snapshot import StrategySnapshot, StrategyRoute, PyramidingPolicy, PyramidingTier, MarginPolicy


class UltraSearchSpace(BaseModel):
    symbols: List[str] = Field(default_factory=lambda: ["BTCUSDT", "ETHUSDT", "SOLUSDT", "SUIUSDT", "DOGEUSDT"])
    timeframes: List[str] = Field(default_factory=lambda: ["1m", "5m", "15m", "1h", "4h"])
    leverage_tiers: List[float] = Field(default_factory=lambda: [10.0, 20.0, 50.0, 100.0])
    pyramiding_max_tiers: int = Field(default=3, ge=1, le=5)
    max_tolerated_drawdown_pct: float = Field(default=80.0, ge=50.0, le=85.0)


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
        leverage: float = 50.0,
        sl_atr_mult: float = 2.0,
        tp_atr_mult: float = 7.0,
        pyramiding_tiers_count: int = 3,
        ema_fast: int = 20,
        ema_slow: int = 50,
        rsi_period: int = 14,
        rsi_threshold_long: float = 52.0,
        rsi_threshold_short: float = 48.0,
    ) -> StrategySnapshot:
        """Genera un StrategySnapshot inmutable con la configuración completa para la ruta Ultra."""
        # Reglas de Entrada: Tendencia EMA y Filtro de Momentum RSI
        entry_rules = RuleTree(
            long_conditions=[
                RuleCondition(
                    left_indicator=IndicatorSpec(name="EMA", timeframe=timeframe, period=ema_fast),
                    operator=ComparisonOperator.GREATER_THAN,
                    right_indicator=IndicatorSpec(name="EMA", timeframe=timeframe, period=ema_slow),
                ),
                RuleCondition(
                    left_indicator=IndicatorSpec(name="RSI", timeframe=timeframe, period=rsi_period),
                    operator=ComparisonOperator.GREATER_THAN,
                    threshold_value=rsi_threshold_long,
                ),
            ],
            short_conditions=[
                RuleCondition(
                    left_indicator=IndicatorSpec(name="EMA", timeframe=timeframe, period=ema_fast),
                    operator=ComparisonOperator.LESS_THAN,
                    right_indicator=IndicatorSpec(name="EMA", timeframe=timeframe, period=ema_slow),
                ),
                RuleCondition(
                    left_indicator=IndicatorSpec(name="RSI", timeframe=timeframe, period=rsi_period),
                    operator=ComparisonOperator.LESS_THAN,
                    threshold_value=rsi_threshold_short,
                ),
            ],
            logical_operator="AND",
        )

        exit_rules = ExitModel(
            stop_loss_atr_mult=sl_atr_mult,
            take_profit_atr_mult=tp_atr_mult,
            trailing_stop_atr_mult=sl_atr_mult * 0.8,
            break_even_atr_mult=sl_atr_mult * 1.0,
        )

        sizing = SizingAndRisk(
            base_risk_pct=3.0,
            max_contracts_or_lots=100.0,
            base_leverage=leverage,
        )

        pyramiding = PyramidingPolicy(
            enabled=True,
            max_tiers=pyramiding_tiers_count,
            tiers=[
                PyramidingTier(trigger_pnl_atr_mult=1.5, added_size_mult=1.0, trail_stop_to_breakeven=True),
                PyramidingTier(trigger_pnl_atr_mult=3.0, added_size_mult=1.5, trail_stop_to_breakeven=True),
                PyramidingTier(trigger_pnl_atr_mult=5.0, added_size_mult=2.0, trail_stop_to_breakeven=True),
            ][:pyramiding_tiers_count],
        )

        margin_policy = MarginPolicy(
            margin_mode="CROSS_MARGIN",
            max_leverage_ceiling=leverage,
            liquidation_buffer_min_pct=3.0,
            reinvestment_rate_pct=50.0,
            vault_harvest_rate_pct=25.0,
        )

        return StrategySnapshot.create_and_hash(
            strategy_id=strategy_id,
            route=StrategyRoute.ULTRA,
            archetype="MOMENTUM_EXPANSION_PYRAMID",
            symbol=symbol,
            timeframe=timeframe,
            entry_rules=entry_rules,
            exit_rules=exit_rules,
            sizing_and_risk=sizing,
            pyramiding_policy=pyramiding,
            margin_policy=margin_policy,
            dataset_id_reference=dataset_id,
            dataset_sha256_reference=dataset_sha256,
        )
