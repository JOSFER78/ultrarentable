"""services/semantic_ai/mutation_engine.py
Motor de optimización semántica y muestreo determinista de reglas AST para CanonicalStrategy.
Cumple estrictamente con la doctrina Zero-Mocks & Real-Only (Cero generadores sintéticos).
"""

from __future__ import annotations

import time

from contracts.canonical_strategy import (
    CanonicalStrategy,
    ComparisonOperator,
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


class SemanticMutationEngine:
    """Generador y mutador determinista de estrategias canónicas cuantitativas."""

    def generate_candidate(
        self,
        symbol: str,
        timeframe: str,
        track: ExecutionTrack = ExecutionTrack.TRACK_FONDEO,
        archetype_name: str = "VOLATILITY_EXPANSION",
    ) -> CanonicalStrategy:
        """Genera una instancia válida de CanonicalStrategy v2.0.0 de forma determinista."""
        strat_id = f"UR-CAND-{symbol.replace('-', '_')}-{timeframe}-{int(time.time() * 1000) % 100000}"
        
        # Selección determinista de parámetros según horizonte temporal y microestructura
        tf_rsi_map = {"1m": 21, "5m": 14, "15m": 14, "1h": 14, "4h": 10, "1d": 10}
        rsi_period = tf_rsi_map.get(timeframe.lower(), 14)
        rsi_thresh = 50.0 if "MOMENTUM" in archetype_name else 55.0

        is_cme = "USDT" not in symbol
        exchange = "CME" if is_cme else "BINGX"
        contract_type = "FUTURES" if is_cme else "PERPETUAL"
        point_val = 20.0 if symbol in ("NQ", "MNQ") else (50.0 if symbol in ("ES", "MES") else 1.0)
        tick_sz = 0.25 if is_cme else 0.01

        return CanonicalStrategy(
            strategy_id=strat_id,
            name=f"{symbol} {timeframe} {archetype_name}",
            target_track=track,
            status=StrategyLifecycleStatus.GENERATED,
            instrument=TargetInstrument(
                symbol=symbol,
                exchange=exchange,
                contract_type=contract_type,
                point_value=point_val,
                tick_size=tick_sz,
            ),
            timeframe=timeframe,
            session=SessionWindow(
                timezone="America/New_York" if is_cme else "UTC",
                start_time="09:30" if is_cme else "00:00",
                end_time="16:00" if is_cme else "23:59",
                force_close_at_end=is_cme,
            ),
            rules=RuleTree(
                long_conditions=[
                    RuleCondition(
                        left_indicator=IndicatorSpec(name="RSI", timeframe=timeframe, period=rsi_period),
                        operator=ComparisonOperator.GREATER_THAN,
                        threshold_value=rsi_thresh,
                    )
                ]
            ),
            exits=ExitModel(stop_loss_ticks=20, take_profit_ticks=60),
            sizing_and_risk=SizingAndRisk(
                base_risk_pct=1.0 if track == ExecutionTrack.TRACK_FONDEO else 5.0,
                max_contracts_or_lots=4.0,
                base_leverage=1.0 if track == ExecutionTrack.TRACK_FONDEO else 20.0,
            ),
            provenance=ProvenanceMetadata(
                source_engine="semantic_ai",
                project_name="Ultrarentable_Factory",
                databank_name="Candidates",
                build_id=f"ai_{strat_id}",
                created_timestamp_utc=int(time.time() * 1000),
                author_or_agent="SEMANTIC_AI_SEARCH",
            ),
        )
