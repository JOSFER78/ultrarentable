"""services/semantic_ai/failure_knowledge.py
Memoria de Fallos (FailureKnowledgeDB) para el Semantic Quant Engine.
Captura estructurada de por qué falló cada estrategia para evitar repetir errores y mapear regímenes hostiles.
"""

from __future__ import annotations

import hashlib
import json
import time
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from contracts.canonical_strategy import CanonicalStrategy, RuleTree, RuleCondition
from contracts.validation_contracts import ValidationTrack


class FailureCategory(str, Enum):
    OVERFITTING_IS_OOS = "OVERFITTING_IS_OOS"
    OUTLIER_DEPENDENCY = "OUTLIER_DEPENDENCY"
    MAX_DRAWDOWN_EXCEEDED = "MAX_DRAWDOWN_EXCEEDED"
    DAILY_LOSS_VIOLATION = "DAILY_LOSS_VIOLATION"
    LOW_PAYOFF_RATIO = "LOW_PAYOFF_RATIO"
    LOW_EXPECTED_R = "LOW_EXPECTED_R"
    SKEWNESS_INSUFFICIENT = "SKEWNESS_INSUFFICIENT"
    VAULT_HARVEST_FAIL = "VAULT_HARVEST_FAIL"
    FRICTION_SENSITIVE = "FRICTION_SENSITIVE"
    BURST_RUIN_EXCEEDED = "BURST_RUIN_EXCEEDED"
    REGIME_MISMATCH = "REGIME_MISMATCH"


class FailureRecord(BaseModel):
    """Registro inmutable de fallo cuantitativo."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    failure_id: str
    strategy_id: str
    track: ValidationTrack
    category: FailureCategory
    rejection_reasons: List[str]
    failing_indicators: List[str] = Field(default_factory=list)
    market_regime: str = "UNKNOWN"
    metrics_snapshot: Dict[str, float] = Field(default_factory=dict)
    rule_signature_hash: str
    timestamp_utc_ms: int
    root_cause_summary: str


class FailureKnowledgeDB:
    """Base de conocimiento de fallos en memoria e indexada por patrones de reglas."""

    def __init__(self) -> None:
        self._records: List[FailureRecord] = []
        self._blacklisted_signatures: set[str] = set()
        self._indicator_failure_counts: Dict[str, int] = {}
        self._category_counts: Dict[FailureCategory, int] = {cat: 0 for cat in FailureCategory}

    def record_failure(
        self,
        strategy: CanonicalStrategy,
        track: ValidationTrack,
        category: FailureCategory,
        rejection_reasons: List[str],
        market_regime: str = "UNKNOWN",
        metrics_snapshot: Optional[Dict[str, float]] = None,
    ) -> FailureRecord:
        """Registra un nuevo fallo e indexa la firma de reglas en la lista de exclusión."""
        metrics_snapshot = metrics_snapshot or {}
        now_ms = int(time.time() * 1000)

        # Extraer indicadores de las reglas
        indicators = []
        for cond in strategy.rules.long_conditions + strategy.rules.short_conditions:
            indicators.append(cond.left_indicator.name)
            if cond.right_indicator:
                indicators.append(cond.right_indicator.name)

        sig_hash = self._compute_rule_signature(strategy.rules)
        fail_id = f"fail_{sig_hash[:12]}_{now_ms}"

        record = FailureRecord(
            failure_id=fail_id,
            strategy_id=strategy.strategy_id,
            track=track,
            category=category,
            rejection_reasons=rejection_reasons,
            failing_indicators=list(set(indicators)),
            market_regime=market_regime,
            metrics_snapshot=metrics_snapshot,
            rule_signature_hash=sig_hash,
            timestamp_utc_ms=now_ms,
            root_cause_summary=f"Rechazado en {track.value} por {category.value}: {', '.join(rejection_reasons[:2])}",
        )

        self._records.append(record)
        self._blacklisted_signatures.add(sig_hash)
        self._category_counts[category] = self._category_counts.get(category, 0) + 1

        for ind in indicators:
            self._indicator_failure_counts[ind] = self._indicator_failure_counts.get(ind, 0) + 1

        return record

    def is_rule_tree_blacklisted(self, rules: RuleTree) -> bool:
        """Comprueba si una combinación de reglas ya ha fallado sistemáticamente en el pasado."""
        sig = self._compute_rule_signature(rules)
        return sig in self._blacklisted_signatures

    def get_failure_statistics(self) -> Dict[str, Any]:
        """Devuelve un resumen analítico de los fallos registrados."""
        return {
            "total_failures_recorded": len(self._records),
            "blacklisted_patterns_count": len(self._blacklisted_signatures),
            "category_distribution": {k.value: v for k, v in self._category_counts.items() if v > 0},
            "top_failing_indicators": sorted(
                self._indicator_failure_counts.items(), key=lambda x: x[1], reverse=True
            )[:5],
        }

    def get_recent_failures(self, limit: int = 20) -> List[FailureRecord]:
        return self._records[-limit:]

    @staticmethod
    def _compute_rule_signature(rules: RuleTree) -> str:
        """Calcula una firma estructural invariante de las condiciones de entrada."""
        tokens = []
        for cond in rules.long_conditions:
            r_ind = cond.right_indicator.name if cond.right_indicator else str(cond.threshold_value)
            tokens.append(f"L:{cond.left_indicator.name}_{cond.left_indicator.period}:{cond.operator.value}:{r_ind}")
        for cond in rules.short_conditions:
            r_ind = cond.right_indicator.name if cond.right_indicator else str(cond.threshold_value)
            tokens.append(f"S:{cond.left_indicator.name}_{cond.left_indicator.period}:{cond.operator.value}:{r_ind}")
        raw = "|".join(sorted(tokens))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
