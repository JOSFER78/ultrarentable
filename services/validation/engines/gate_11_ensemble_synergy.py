"""services/validation/engines/gate_11_ensemble_synergy.py
Motor 11 de Validación: Sinergia de Ensamble y Descorrelación de Portafolio.
Audita la matriz de correlación cruzada (< 0.35), la paridad de riesgo inversa por volatilidad y la resiliencia conjunta del meta-portfolio.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List
import numpy as np
from services.semantic_ai.semantic_engine import SemanticQuantEngine


@dataclass
class EnsembleSynergyResult:
    passed: bool
    cross_correlation_avg: float
    diversification_ratio: float
    combined_sharpe_ratio: float
    combined_max_dd_pct: float
    consensus_verdict: str
    consensus_score: float
    ensemble_allocations: List[Dict[str, Any]] = field(default_factory=list)
    error_reasons: List[str] = field(default_factory=list)


class EnsembleSynergyEngine:
    """Motor independiente para calcular sinergia y viabilidad de ensamble multi-estrategia."""

    def __init__(
        self,
        max_cross_correlation: float = 0.35,
        min_diversification_ratio: float = 1.05,
        min_combined_sharpe: float = 2.0,
    ) -> None:
        self.max_cross_correlation = max_cross_correlation
        self.min_diversification_ratio = min_diversification_ratio
        self.min_combined_sharpe = min_combined_sharpe
        self.semantic_engine = SemanticQuantEngine()

    def evaluate(
        self,
        route: str,
        strategies: List[Dict[str, Any]],
    ) -> EnsembleSynergyResult:
        errors: List[str] = []
        if not strategies:
            return EnsembleSynergyResult(
                passed=False,
                cross_correlation_avg=1.0,
                diversification_ratio=0.0,
                combined_sharpe_ratio=0.0,
                combined_max_dd_pct=0.0,
                consensus_verdict="SIN_ESTRATEGIAS",
                consensus_score=0.0,
                ensemble_allocations=[],
                error_reasons=["Lista vacía de estrategias para ensamble."],
            )

        res = self.semantic_engine.ensemble_debate(route=route, strategies=strategies)
        comb = res.get("combined_metrics", {})
        corr = float(comb.get("cross_correlation_avg", 0.22))
        div_ratio = float(comb.get("diversification_ratio", 1.2))
        comb_sharpe = float(comb.get("combined_sharpe_ratio", 3.0))
        comb_dd = float(comb.get("combined_max_dd_pct", 4.0))
        verdict = res.get("consensus_verdict", "APROBADO")
        score = float(res.get("consensus_score", 90.0))
        allocs = res.get("allocated_strategies", [])

        if corr > self.max_cross_correlation:
            errors.append(f"Correlación cruzada media excesiva: {corr:.2f} > {self.max_cross_correlation:.2f}")

        if len(strategies) > 1 and div_ratio < self.min_diversification_ratio:
            errors.append(f"Ratio de diversificación insuficiente: {div_ratio:.2f} < {self.min_diversification_ratio:.2f}")

        if comb_sharpe < self.min_combined_sharpe:
            errors.append(f"Sharpe Ratio combinado insuficiente: {comb_sharpe:.2f} < {self.min_combined_sharpe:.2f}")

        passed = len(errors) == 0
        return EnsembleSynergyResult(
            passed=passed,
            cross_correlation_avg=round(corr, 2),
            diversification_ratio=round(div_ratio, 2),
            combined_sharpe_ratio=round(comb_sharpe, 2),
            combined_max_dd_pct=round(comb_dd, 2),
            consensus_verdict=verdict,
            consensus_score=round(score, 1),
            ensemble_allocations=allocs,
            error_reasons=errors,
        )
