"""services/discovery/funding_discovery.py
Motor de Búsqueda y Descubrimiento Cuantitativo para la Ruta FONDEO (Fase 3).
Optimización de candidatos para superar pruebas de prop firms en <= 5 días sujeto a Trailing DD <= 4.5% y DLL.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from contracts.canonical_strategy import RuleTree, ExitModel, SizingAndRisk, IndicatorSpec, RuleCondition, ComparisonOperator, SessionWindow
from contracts.snapshots.strategy_snapshot import StrategySnapshot, StrategyRoute, PyramidingPolicy, MarginPolicy


class FundingSearchSpace(BaseModel):
    symbols: List[str] = Field(default_factory=lambda: ["NQ", "ES", "YM", "RTY", "CL", "GC", "EURUSD", "GBPUSD"])
    timeframes: List[str] = Field(default_factory=lambda: ["5m", "15m", "1h"])
    max_drawdown_ceiling_pct: float = Field(default=4.5, le=5.0)
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
        risk_per_trade_pct: float = 0.5,
        target_profit_ticks: int = 40,
        stop_loss_ticks: int = 20,
    ) -> StrategySnapshot:
        """Genera un StrategySnapshot inmutable con la configuración estricta para Fondeo."""
        entry_rules = RuleTree(
            long_conditions=[
                RuleCondition(
                    left_indicator=IndicatorSpec(name="EMA", timeframe=timeframe, period=9),
                    operator=ComparisonOperator.CROSSES_ABOVE,
                    right_indicator=IndicatorSpec(name="EMA", timeframe=timeframe, period=21),
                ),
                RuleCondition(
                    left_indicator=IndicatorSpec(name="RSI", timeframe=timeframe, period=14),
                    operator=ComparisonOperator.GREATER_THAN,
                    threshold_value=50.0,
                ),
            ],
            short_conditions=[
                RuleCondition(
                    left_indicator=IndicatorSpec(name="EMA", timeframe=timeframe, period=9),
                    operator=ComparisonOperator.CROSSES_BELOW,
                    right_indicator=IndicatorSpec(name="EMA", timeframe=timeframe, period=21),
                ),
                RuleCondition(
                    left_indicator=IndicatorSpec(name="RSI", timeframe=timeframe, period=14),
                    operator=ComparisonOperator.LESS_THAN,
                    threshold_value=50.0,
                ),
            ],
            logical_operator="AND",
        )

        exit_rules = ExitModel(
            stop_loss_ticks=stop_loss_ticks,
            take_profit_ticks=target_profit_ticks,
            break_even_atr_mult=1.0,
            max_bars_in_trade=24,
        )

        sizing = SizingAndRisk(
            base_risk_pct=risk_per_trade_pct,
            max_contracts_or_lots=5.0,
            base_leverage=1.0,
        )

        # En Fondeo NO se piramida (minimizar drawdown y varianza)
        pyramiding = PyramidingPolicy(enabled=False, max_tiers=1, tiers=[])

        margin_policy = MarginPolicy(
            margin_mode="CROSS_MARGIN",
            max_leverage_ceiling=3.0,
            liquidation_buffer_min_pct=50.0,
            reinvestment_rate_pct=0.0,
            vault_harvest_rate_pct=0.0,
        )

        session_window = SessionWindow(
            timezone="America/New_York",
            start_time="09:30",
            end_time="16:00",
            force_close_at_end=True,
        )

        return StrategySnapshot.create_and_hash(
            strategy_id=strategy_id,
            route=StrategyRoute.FONDEO,
            archetype="INTRADAY_MOMENTUM_PROP",
            symbol=symbol,
            timeframe=timeframe,
            entry_rules=entry_rules,
            exit_rules=exit_rules,
            sizing_and_risk=sizing,
            pyramiding_policy=pyramiding,
            margin_policy=margin_policy,
            session_window=session_window,
            dataset_id_reference=dataset_id,
            dataset_sha256_reference=dataset_sha256,
        )
