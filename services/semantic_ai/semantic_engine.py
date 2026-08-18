"""services/semantic_ai/semantic_engine.py
Semantic Quant Engine: Orquestación multi-agente de generación, mutación y crítica de estrategias canónicas.
Garantiza la Regla Absoluta de Gobernanza: 'La IA propone, el Evidence Gate aprueba'.
"""

from __future__ import annotations

import random
import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

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
from services.semantic_ai.failure_knowledge import (
    FailureCategory,
    FailureKnowledgeDB,
    FailureRecord,
)


class MarketRegime(str, Enum):
    TRENDING_BULL = "TRENDING_BULL"
    TRENDING_BEAR = "TRENDING_BEAR"
    VOLATILITY_EXPANSION = "VOLATILITY_EXPANSION"
    LOW_VOLATILITY_CHOP = "LOW_VOLATILITY_CHOP"


class InterpreterAgent:
    """Traduce parámetros numéricos y AST a taxonomía semántica y estructural."""

    def describe_strategy(self, strategy: CanonicalStrategy) -> Dict[str, Any]:
        long_rules_desc = [
            f"{c.left_indicator.name}({c.left_indicator.period}) {c.operator.value} "
            f"{c.right_indicator.name if c.right_indicator else c.threshold_value}"
            for c in strategy.rules.long_conditions
        ]
        short_rules_desc = [
            f"{c.left_indicator.name}({c.left_indicator.period}) {c.operator.value} "
            f"{c.right_indicator.name if c.right_indicator else c.threshold_value}"
            for c in strategy.rules.short_conditions
        ]

        style = "MOMENTUM_TREND" if any("EMA" in d or "RSI" in d for d in long_rules_desc) else "VOLATILITY_BREAKOUT"
        return {
            "strategy_id": strategy.strategy_id,
            "track": strategy.target_track.value,
            "instrument": strategy.instrument.symbol,
            "style": style,
            "long_rules": long_rules_desc,
            "short_rules": short_rules_desc,
            "sl_ticks": strategy.exits.stop_loss_ticks,
            "tp_ticks": strategy.exits.take_profit_ticks,
        }


class CriticAgent:
    """Audita candidatos contra la Memoria de Fallos y detecta debilidades estructurales."""

    def __init__(self, failure_db: FailureKnowledgeDB) -> None:
        self.failure_db = failure_db

    def critique(self, strategy: CanonicalStrategy) -> Tuple[bool, List[str]]:
        warnings: List[str] = []

        # 1. Comprobar lista negra en FailureKnowledgeDB
        if self.failure_db.is_rule_tree_blacklisted(strategy.rules):
            return False, ["Patrón de reglas idéntico a una combinación fallida en FailureKnowledgeDB"]

        # 2. Chequeo de Stop Loss obligatorio
        if not strategy.exits.stop_loss_ticks and not strategy.exits.stop_loss_atr_mult:
            warnings.append("Falta Stop Loss explícito (Riesgo ilimitado)")

        # 3. Chequeo de Sesión para Track Fondeo
        if strategy.target_track == ExecutionTrack.TRACK_FONDEO and not strategy.session.force_close_at_end:
            warnings.append("Track Fondeo requiere forzar cierre de posiciones al fin de sesión")

        # 4. Chequeo de piramidación en Track Fondeo (prohibida)
        if strategy.target_track == ExecutionTrack.TRACK_FONDEO and strategy.sizing_and_risk.pyramiding_max_layers > 0:
            warnings.append("Piramidación no permitida en Track Fondeo por reglas de prop firms")

        passed = len([w for w in warnings if "Riesgo ilimitado" in w or "FailureKnowledgeDB" in w]) == 0
        return passed, warnings


class ImproverAgent:
    """Motor genético y semántico de mutación que recombina y mejora estrategias."""

    def __init__(self, failure_db: FailureKnowledgeDB) -> None:
        self.failure_db = failure_db

    def mutate(
        self,
        base_strategy: CanonicalStrategy,
        max_attempts: int = 10,
    ) -> CanonicalStrategy:
        """Genera una mutación válida que NO colisione con patrones fallidos conocidos."""
        current_rules = base_strategy.rules
        mutated_rules = current_rules

        for _ in range(max_attempts):
            # Mutar período de indicador o umbral
            new_longs = []
            for cond in current_rules.long_conditions:
                new_period = max(5, cond.left_indicator.period + random.choice([-2, -1, 1, 2, 5]))
                new_threshold = cond.threshold_value + random.choice([-5.0, -2.0, 2.0, 5.0]) if cond.threshold_value else None
                new_longs.append(
                    RuleCondition(
                        left_indicator=IndicatorSpec(
                            name=cond.left_indicator.name,
                            timeframe=cond.left_indicator.timeframe,
                            period=new_period,
                        ),
                        operator=cond.operator,
                        threshold_value=new_threshold,
                    )
                )

            candidate_tree = RuleTree(
                long_conditions=new_longs,
                short_conditions=current_rules.short_conditions,
                logical_operator=current_rules.logical_operator,
            )

            # Verificar que la mutación no esté en la lista negra
            if not self.failure_db.is_rule_tree_blacklisted(candidate_tree):
                mutated_rules = candidate_tree
                break

        # Adaptar salidas y apalancamiento
        new_sl = base_strategy.exits.stop_loss_ticks
        new_tp = base_strategy.exits.take_profit_ticks
        if new_sl:
            new_sl = max(10, new_sl + random.choice([-2, 2, 5]))
        if new_tp:
            new_tp = max(20, new_tp + random.choice([-5, 5, 10]))

        now_ms = int(time.time() * 1000)
        u_suffix = uuid.uuid4().hex[:6].upper()
        new_id = f"UR-SEM-{base_strategy.instrument.symbol}-{u_suffix}"

        return CanonicalStrategy(
            schema_version="2.0.0",
            strategy_id=new_id,
            name=f"Mutant {base_strategy.name} {u_suffix}",
            target_track=base_strategy.target_track,
            status=StrategyLifecycleStatus.GENERATED,
            instrument=base_strategy.instrument,
            timeframe=base_strategy.timeframe,
            session=base_strategy.session,
            rules=mutated_rules,
            exits=ExitModel(stop_loss_ticks=new_sl, take_profit_ticks=new_tp),
            sizing_and_risk=base_strategy.sizing_and_risk,
            provenance=ProvenanceMetadata(
                source_engine="semantic_ai",
                created_timestamp_utc=now_ms,
                author_or_agent="SEMANTIC_IMPROVER_AGENT",
            ),
            metadata={"parent_strategy_id": base_strategy.strategy_id},
        )


class SemanticQuantEngine:
    """Orquestador Maestro de IA Semántica para Ultrarentable V2."""

    def __init__(self, failure_db: Optional[FailureKnowledgeDB] = None) -> None:
        self.failure_db = failure_db or FailureKnowledgeDB()
        self.interpreter = InterpreterAgent()
        self.critic = CriticAgent(self.failure_db)
        self.improver = ImproverAgent(self.failure_db)

    def generate_candidate(
        self,
        symbol: str = "NQ",
        timeframe: str = "1h",
        track: ExecutionTrack = ExecutionTrack.TRACK_FONDEO,
    ) -> CanonicalStrategy:
        """Crea un candidato canónico inicial estructurado."""
        now_ms = int(time.time() * 1000)
        u_suffix = uuid.uuid4().hex[:6].upper()
        strat_id = f"UR-SEM-{symbol}-{u_suffix}"

        exchange = "CME" if symbol in ("NQ", "ES", "MES", "MNQ", "CL") else "BINGX"
        contract_type = "FUTURES" if exchange == "CME" else "PERPETUAL"
        point_val = 20.0 if symbol in ("NQ", "MNQ") else (50.0 if symbol in ("ES", "MES") else 1.0)
        tick_sz = 0.25 if symbol in ("NQ", "ES", "MES", "MNQ") else 0.1

        long_cond = RuleCondition(
            left_indicator=IndicatorSpec(name="RSI", timeframe=timeframe, period=14),
            operator=ComparisonOperator.GREATER_THAN,
            threshold_value=52.0,
        )

        return CanonicalStrategy(
            schema_version="2.0.0",
            strategy_id=strat_id,
            name=f"Semantic {symbol} {timeframe.upper()} {track.value}",
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
                timezone="America/New_York",
                start_time="09:30",
                end_time="16:00",
                force_close_at_end=(track == ExecutionTrack.TRACK_FONDEO),
            ),
            rules=RuleTree(long_conditions=[long_cond]),
            exits=ExitModel(stop_loss_ticks=25, take_profit_ticks=75),
            sizing_and_risk=SizingAndRisk(
                base_risk_pct=1.0 if track == ExecutionTrack.TRACK_FONDEO else 5.0,
                max_contracts_or_lots=4.0 if track == ExecutionTrack.TRACK_FONDEO else 10.0,
                base_leverage=1.0 if track == ExecutionTrack.TRACK_FONDEO else 20.0,
                pyramiding_max_layers=0 if track == ExecutionTrack.TRACK_FONDEO else 3,
            ),
            provenance=ProvenanceMetadata(
                source_engine="semantic_ai",
                created_timestamp_utc=now_ms,
                author_or_agent="SEMANTIC_GENERATOR_AGENT",
            ),
        )

    def improve_candidate(self, strategy: CanonicalStrategy) -> Optional[CanonicalStrategy]:
        """Audita, muta y retorna una versión mejorada del candidato."""
        mutant = self.improver.mutate(strategy)
        passed, warnings = self.critic.critique(mutant)
        return mutant if passed else None
