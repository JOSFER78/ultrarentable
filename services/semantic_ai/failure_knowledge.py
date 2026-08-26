"""services/semantic_ai/failure_knowledge.py
Fachada de compatibilidad para FailureKnowledgeDB con backend persistente LearningStore.
Captura estructurada de por qué falló cada estrategia para evitar repetir errores y mapear regímenes hostiles.
"""

from __future__ import annotations

import hashlib
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from contracts.canonical_strategy import CanonicalStrategy, RuleTree
from contracts.validation_contracts import ValidationTrack
from contracts.learning_contracts import (
    FailureCategory,
    FailureRecordEntity,
    LearningPatternRecord,
)
from services.semantic_ai.learning_store import learning_store, LearningStore


class FailureRecord(BaseModel):
    """Registro inmutable de fallo cuantitativo (compatibilidad legacy)."""
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
    """Base de conocimiento persistente de fallos respaldada por SQLite WAL (LearningStore)."""

    def __init__(self, store: Optional[LearningStore] = None) -> None:
        self._store = store or learning_store

    def record_failure(
        self,
        strategy: CanonicalStrategy,
        track: ValidationTrack,
        category: FailureCategory,
        rejection_reasons: List[str],
        market_regime: str = "UNKNOWN",
        metrics_snapshot: Optional[Dict[str, float]] = None,
    ) -> FailureRecord:
        """Registra un nuevo fallo en el LearningStore persistente."""
        metrics_snapshot = metrics_snapshot or {}
        now_ms = int(time.time() * 1000)
        now_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_ms / 1000.0))

        indicators = []
        rules = getattr(strategy, "entry_rules", None)
        if rules:
            for cond in (getattr(rules, "long_conditions", None) or []) + (getattr(rules, "short_conditions", None) or []):
                _ln = getattr(cond, "left", None)
                if _ln is not None and hasattr(_ln, "name"):
                    indicators.append(_ln.name)

        sig_hash = self._compute_rule_signature(rules) if rules else hashlib.sha256(strategy.strategy_id.encode()).hexdigest()
        fail_id = f"fail_{sig_hash[:12]}_{now_ms}"

        strat_hash = getattr(strategy, "strategy_hash", f"hash_{strategy.strategy_id}")

        # Persistir en LearningStore durable
        entity = FailureRecordEntity(
            failure_id=fail_id,
            strategy_hash=strat_hash,
            strategy_id=strategy.strategy_id,
            track=track.value if hasattr(track, "value") else str(track),
            gate_name=rejection_reasons[0] if rejection_reasons else "GENERIC_GATE",
            category=category,
            market_regime=market_regime,
            metrics_snapshot=metrics_snapshot,
            rejection_reasons=rejection_reasons,
            failing_indicators=list(set(indicators)),
            rule_signature_hash=sig_hash,
            root_cause_summary=f"Rechazado en {track} por {category.value}: {', '.join(rejection_reasons[:2])}",
            created_at_utc=now_utc,
            is_verified=True,
        )
        self._store.record_failure(entity)

        return FailureRecord(
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
            root_cause_summary=entity.root_cause_summary,
        )

    def is_rule_tree_blacklisted(self, rules: RuleTree) -> bool:
        """Comprueba si una combinación de reglas ya ha fallado sistemáticamente en el LearningStore."""
        sig = self._compute_rule_signature(rules)
        return self._store.is_rule_tree_blacklisted(sig)

    def get_failure_statistics(self) -> Dict[str, Any]:
        """Devuelve un resumen analítico de los fallos registrados desde el LearningStore durable."""
        stats = self._store.get_failure_statistics()
        return {
            "total_failures_recorded": stats.get("total_failures_recorded", 0),
            "blacklisted_patterns_count": stats.get("total_learning_patterns", 0),
            "category_distribution": stats.get("category_distribution", {}),
            "top_failing_gates": stats.get("top_failing_gates", []),
            "total_strategy_versions": stats.get("total_strategy_versions", 0),
            "total_validation_snapshots": stats.get("total_validation_snapshots", 0),
        }

    def get_cluster_stats(self) -> Dict[str, Any]:
        """Alias para telemetría."""
        return self.get_failure_statistics()

    @staticmethod
    def _compute_rule_signature(rules: RuleTree) -> str:
        """Calcula una firma estructural invariante de las condiciones de entrada."""
        if not rules:
            return hashlib.sha256(b"empty_rules").hexdigest()
        tokens = []
        for cond in (getattr(rules, "long_conditions", None) or []):
            r_node = getattr(cond, "right", None)
            r_ind = r_node.name if hasattr(r_node, "name") else str(r_node if r_node is not None else "")
            l_node = getattr(cond, "left", None)
            l_name = l_node.name if hasattr(l_node, "name") else str(l_node)
            l_per = (getattr(l_node, "params", {}) or {}).get("period", 0)
            op = cond.op.value if hasattr(getattr(cond, "op", None), "value") else str(getattr(cond, "op", getattr(cond, "operator", "")))
            tokens.append(f"L:{l_name}_{l_per}:{op}:{r_ind}")
        for cond in (getattr(rules, "short_conditions", None) or []):
            r_node = getattr(cond, "right", None)
            r_ind = r_node.name if hasattr(r_node, "name") else str(r_node if r_node is not None else "")
            l_node = getattr(cond, "left", None)
            l_name = l_node.name if hasattr(l_node, "name") else str(l_node)
            l_per = (getattr(l_node, "params", {}) or {}).get("period", 0)
            op = cond.op.value if hasattr(getattr(cond, "op", None), "value") else str(getattr(cond, "op", getattr(cond, "operator", "")))
            tokens.append(f"S:{l_name}_{l_per}:{op}:{r_ind}")
        raw = "|".join(sorted(tokens))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# Instancia singleton
failure_db = FailureKnowledgeDB()
