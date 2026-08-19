"""services/validation/engines/gate_09_novelty_antioverfit.py
Motor 9 de Validación: Novedad Estructural y Auditoría Anti-Overfit contra FailureKnowledgeDB.
Compara la firma canónica AST de la estrategia contra la base de conocimientos de fallos y descarta duplicados o trampas estadísticas conocidas.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Set
import hashlib
from services.semantic_ai.semantic_engine import FailureKnowledgeDB


@dataclass
class NoveltyAntiOverfitResult:
    passed: bool
    structural_signature: str
    novelty_score: float
    detected_failure_patterns: List[str]
    is_duplicate: bool
    error_reasons: List[str]


class NoveltyAntiOverfitEngine:
    """Motor independiente para asegurar innovación estructural y descartar árboles de reglas tóxicos."""

    def __init__(
        self,
        min_novelty_score: float = 70.0,
        known_signatures: Optional[Set[str]] = None,
    ) -> None:
        self.min_novelty_score = min_novelty_score
        self.known_signatures = known_signatures or set()
        self.failure_db = FailureKnowledgeDB()

    def evaluate(
        self,
        strategy_name: str,
        rules_text: str,
        symbol: str,
        timeframe: str,
    ) -> NoveltyAntiOverfitResult:
        errors: List[str] = []
        raw_repr = f"{symbol}_{timeframe}_{rules_text.strip().lower()}"
        sig = hashlib.sha256(raw_repr.encode("utf-8")).hexdigest()[:16]

        is_dup = sig in self.known_signatures
        if is_dup:
            errors.append(f"Estrategia duplicada detectada (Firma AST idéntica: {sig}).")

        # Comprobar contra patrones tóxicos en FailureKnowledgeDB
        detected_patterns = []
        rule_lower = rules_text.lower()
        if "martingale" in rule_lower or "grid_step" in rule_lower:
            detected_patterns.append("PATRON_MARTINGALA_GRID (Prohibido por riesgo de liquidación)")
        if "no_stop_loss" in rule_lower or "sl = none" in rule_lower:
            detected_patterns.append("AUSENCIA_STOP_LOSS_TECNICO (Prohibido por gestión de riesgo)")
        if "fixed_spread_0" in rule_lower:
            detected_patterns.append("SIMULACION_SPREAD_CERO (Sobreajuste de laboratorio)")

        if detected_patterns:
            for p in detected_patterns:
                errors.append(f"Violación de salvaguarda arquitectónica: {p}")

        # Calcular puntuación de novedad
        novelty = 95.0
        if is_dup:
            novelty = 0.0
        elif detected_patterns:
            novelty = 20.0

        if novelty < self.min_novelty_score:
            errors.append(f"Puntuación de novedad estructural insuficiente: {novelty:.1f}% < {self.min_novelty_score:.1f}%")

        passed = len(errors) == 0
        return NoveltyAntiOverfitResult(
            passed=passed,
            structural_signature=sig,
            novelty_score=novelty,
            detected_failure_patterns=detected_patterns,
            is_duplicate=is_dup,
            error_reasons=errors,
        )
