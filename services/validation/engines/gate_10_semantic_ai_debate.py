"""services/validation/engines/gate_10_semantic_ai_debate.py
Motor 10 de Validación: Deliberación Cualitativa & Debate Multi-Agente Semántico.
Ejecuta el panel deliberador de 5 agentes IA de riesgo (Interpreter, Critic, Improver, Regime, Adversarial).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List
from services.semantic_ai.semantic_engine import SemanticQuantEngine


@dataclass
class SemanticAIDebateResult:
    passed: bool
    consensus_verdict: str
    consensus_score: float
    agents_findings: List[Dict[str, Any]] = field(default_factory=list)
    error_reasons: List[str] = field(default_factory=list)


class SemanticAIDebateEngine:
    """Motor independiente para someter estrategias al comité deliberador de 5 agentes IA."""

    def __init__(self, min_consensus_score: float = 75.0) -> None:
        self.min_consensus_score = min_consensus_score
        self.engine = SemanticQuantEngine()

    def evaluate(
        self,
        strategy_id: str,
        name: str,
        symbol: str,
        timeframe: str,
        route: str,
        profit_factor_oos: float,
        max_dd_pct: float,
        win_rate: float,
    ) -> SemanticAIDebateResult:
        errors: List[str] = []
        debate_data = self.engine.debate_candidate(
            strategy_id=strategy_id,
            name=name,
            symbol=symbol,
            timeframe=timeframe,
            route=route,
            pf_oos=profit_factor_oos,
            max_dd_pct=max_dd_pct,
            win_rate=win_rate,
        )

        score = float(debate_data.get("consensus_score", 0.0))
        verdict = debate_data.get("consensus_verdict", "RECHAZADO")
        agents = debate_data.get("agents_debate", [])

        if score < self.min_consensus_score:
            errors.append(f"Puntuación de consenso semántico multi-agente insuficiente: {score:.1f} < {self.min_consensus_score:.1f}")

        if "RECHAZADO" in verdict:
            errors.append(f"Veredicto negativo del comité de agentes: {verdict}")

        passed = len(errors) == 0
        return SemanticAIDebateResult(
            passed=passed,
            consensus_verdict=verdict,
            consensus_score=round(score, 1),
            agents_findings=agents,
            error_reasons=errors,
        )
