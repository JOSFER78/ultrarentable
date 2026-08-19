"""services/validation/engines/gate_07_market_regime_coverage.py
Motor 7 de Validación: Cobertura Multi-Régimen de Mercado.
Verifica que la estrategia funcione armónicamente a través de regímenes de mercado alcistas (Bull), bajistas (Bear) y laterales/rango (Chop).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class MarketRegimeCoverageResult:
    passed: bool
    bull_regime_pnl: float
    bear_regime_pnl: float
    chop_regime_pnl: float
    regime_alignment_score: float
    catastrophic_regimes: List[str]
    error_reasons: List[str]


class MarketRegimeCoverageEngine:
    """Motor independiente para auditar la robustez de la estrategia frente a transiciones de régimen."""

    def __init__(
        self,
        min_alignment_score: float = 65.0,
        max_regime_loss_usd: float = -1000.0,
    ) -> None:
        self.min_alignment_score = min_alignment_score
        self.max_regime_loss_usd = max_regime_loss_usd

    def evaluate(
        self,
        regime_pnls: Dict[str, float],
    ) -> MarketRegimeCoverageResult:
        errors: List[str] = []
        bull_pnl = regime_pnls.get("BULL", 0.0)
        bear_pnl = regime_pnls.get("BEAR", 0.0)
        chop_pnl = regime_pnls.get("CHOP", 0.0)

        catastrophic: List[str] = []
        for regime, pnl in [("BULL", bull_pnl), ("BEAR", bear_pnl), ("CHOP", chop_pnl)]:
            if pnl < self.max_regime_loss_usd:
                catastrophic.append(regime)
                errors.append(f"Pérdida catastrófica en régimen {regime}: ${pnl:.2f} < ${self.max_regime_loss_usd:.2f}")

        # Puntuación de alineación: penaliza regímenes negativos
        positives = sum(1 for p in [bull_pnl, bear_pnl, chop_pnl] if p > 0)
        total_pnl = bull_pnl + bear_pnl + chop_pnl
        score = 50.0 + (positives * 15.0) + (10.0 if total_pnl > 0 else -20.0)
        score = max(0.0, min(100.0, score))

        if score < self.min_alignment_score:
            errors.append(f"Puntuación de cobertura de régimen insuficiente: {score:.1f}% < {self.min_alignment_score:.1f}%")

        passed = len(errors) == 0
        return MarketRegimeCoverageResult(
            passed=passed,
            bull_regime_pnl=round(bull_pnl, 2),
            bear_regime_pnl=round(bear_pnl, 2),
            chop_regime_pnl=round(chop_pnl, 2),
            regime_alignment_score=round(score, 1),
            catastrophic_regimes=catastrophic,
            error_reasons=errors,
        )
