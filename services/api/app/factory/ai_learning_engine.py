"""AI Pattern Memory & Adaptive Learning Engine for Strategy Discovery.

Implements Bayesian-inspired reinforcement weighting and parameter mutation memory:
- Tracks historical success rates of strategy archetypes, indicators, stop/target ratios, and timeframes.
- Adapts sampling probabilities so that parameter spaces with higher OOS & WFO pass rates are explored more intensely.
- Introduces controlled exploration entropy to prevent local optima stagnation.
"""

from __future__ import annotations

import json
import logging
import math
import random
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("ai_learning_engine")

STATE_FILE = Path("/home/ubuntu/.local/state/ultrarentable/ai_learning_state.json")


@dataclass
class ParameterGene:
    name: str
    value: Any
    category: str
    trials: int = 0
    passed_is: int = 0
    passed_oos: int = 0
    passed_wfo: int = 0
    approved: int = 0
    weight: float = 1.0


class AILearningEngine:
    """Adaptive AI Parameter Memory & Mutation Optimizer."""

    def __init__(self, state_file: Path = STATE_FILE):
        self.state_file = state_file
        self.generation: int = 1
        self.total_evaluations: int = 0
        self.total_approved: int = 0
        self.exploration_rate: float = 0.20  # 20% random exploration vs 80% exploitation
        
        # Knowledge Base of Parameter Genes
        self.genes: Dict[str, Dict[str, ParameterGene]] = {
            "atr_stop_mult": {
                "1.0": ParameterGene("atr_stop_mult", 1.0, "risk"),
                "1.2": ParameterGene("atr_stop_mult", 1.2, "risk"),
                "1.5": ParameterGene("atr_stop_mult", 1.5, "risk"),
                "1.8": ParameterGene("atr_stop_mult", 1.8, "risk"),
                "2.0": ParameterGene("atr_stop_mult", 2.0, "risk"),
                "2.5": ParameterGene("atr_stop_mult", 2.5, "risk"),
                "3.0": ParameterGene("atr_stop_mult", 3.0, "risk"),
            },
            "atr_tp_mult": {
                "2.0": ParameterGene("atr_tp_mult", 2.0, "reward"),
                "2.5": ParameterGene("atr_tp_mult", 2.5, "reward"),
                "3.0": ParameterGene("atr_tp_mult", 3.0, "reward"),
                "4.0": ParameterGene("atr_tp_mult", 4.0, "reward"),
                "5.0": ParameterGene("atr_tp_mult", 5.0, "reward"),
                "6.0": ParameterGene("atr_tp_mult", 6.0, "reward"),
                "8.0": ParameterGene("atr_tp_mult", 8.0, "reward"),
            },
            "archetype": {
                "MOMENTUM_BREAKOUT": ParameterGene("archetype", "MOMENTUM_BREAKOUT", "pattern"),
                "VOLATILITY_EXPANSION": ParameterGene("archetype", "VOLATILITY_EXPANSION", "pattern"),
                "MEAN_REVERSION": ParameterGene("archetype", "MEAN_REVERSION", "pattern"),
                "TREND_FOLLOWING_EMA": ParameterGene("archetype", "TREND_FOLLOWING_EMA", "pattern"),
                "RSI_DIVERGENCE": ParameterGene("archetype", "RSI_DIVERGENCE", "pattern"),
                "DONCHIAN_CHANNEL": ParameterGene("archetype", "DONCHIAN_CHANNEL", "pattern"),
            },
            "timeframe": {
                "1m": ParameterGene("timeframe", "1m", "timeframe"),
                "5m": ParameterGene("timeframe", "5m", "timeframe"),
                "15m": ParameterGene("timeframe", "15m", "timeframe"),
                "1h": ParameterGene("timeframe", "1h", "timeframe"),
                "4h": ParameterGene("timeframe", "4h", "timeframe"),
            }
        }
        self._load_state()

    def _load_state(self) -> None:
        if not self.state_file.exists():
            return
        try:
            with open(self.state_file, "r") as f:
                data = json.load(f)
                self.generation = data.get("generation", 1)
                self.total_evaluations = data.get("total_evaluations", 0)
                self.total_approved = data.get("total_approved", 0)
                self.exploration_rate = data.get("exploration_rate", 0.20)
                
                raw_genes = data.get("genes", {})
                for cat, genes_dict in raw_genes.items():
                    if cat not in self.genes:
                        self.genes[cat] = {}
                    for k, g_data in genes_dict.items():
                        self.genes[cat][k] = ParameterGene(**g_data)
        except Exception as e:
            logger.warning(f"Error loading AI learning state: {e}")

    def save_state(self) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = {
                "generation": self.generation,
                "total_evaluations": self.total_evaluations,
                "total_approved": self.total_approved,
                "exploration_rate": self.exploration_rate,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "genes": {
                    cat: {k: asdict(gene) for k, gene in genes_dict.items()}
                    for cat, genes_dict in self.genes.items()
                }
            }
            with open(self.state_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving AI learning state: {e}")

    def sample_parameters(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """Sample strategy parameters using learned weights and epsilon-greedy exploration."""
        self.total_evaluations += 1
        
        # Epsilon-greedy exploration
        is_exploring = random.random() < self.exploration_rate
        
        sampled = {}
        for category, genes_dict in self.genes.items():
            if category == "timeframe":
                continue  # Timeframe given by cell or requested
            
            keys = list(genes_dict.keys())
            if is_exploring:
                chosen_key = random.choice(keys)
            else:
                weights = [max(0.1, gene.weight) for gene in genes_dict.values()]
                total_w = sum(weights)
                probs = [w / total_w for w in weights]
                chosen_key = random.choices(keys, weights=probs, k=1)[0]
                
            sampled[category] = genes_dict[chosen_key].value
            
        sampled["symbol"] = symbol
        sampled["timeframe"] = timeframe
        return sampled

    def register_feedback(
        self,
        params: Dict[str, Any],
        passed_is: bool,
        passed_oos: bool,
        passed_wfo: bool,
        approved: bool,
        profit_factor: float = 1.0,
        max_dd_pct: float = 5.0
    ) -> None:
        """Update gene reinforcement weights based on backtest & robustness gate results."""
        for category, val in params.items():
            str_val = str(val)
            if category in self.genes and str_val in self.genes[category]:
                gene = self.genes[category][str_val]
                gene.trials += 1
                if passed_is:
                    gene.passed_is += 1
                if passed_oos:
                    gene.passed_oos += 1
                if passed_wfo:
                    gene.passed_wfo += 1
                if approved:
                    gene.approved += 1
                    self.total_approved += 1

                # Bayesian Weight Update Formula:
                success_rate = (gene.approved * 3.0 + gene.passed_wfo * 1.5 + gene.passed_oos * 1.0 + gene.passed_is * 0.5) / max(1, gene.trials)
                pf_bonus = max(0.5, min(2.5, profit_factor)) if approved else 1.0
                dd_penalty = 1.0 / max(1.0, max_dd_pct / 5.0)
                
                # Smoothed moving weight
                target_weight = max(0.2, min(5.0, (success_rate * pf_bonus * dd_penalty) + 0.5))
                gene.weight = round(0.85 * gene.weight + 0.15 * target_weight, 3)

        # Decay exploration rate slowly as knowledge accumulates
        if self.total_evaluations % 100 == 0:
            self.generation += 1
            self.exploration_rate = max(0.08, self.exploration_rate * 0.98)
            self.save_state()

    def get_summary_metrics(self) -> Dict[str, Any]:
        """Return human and UI friendly learning stats."""
        top_patterns = sorted(
            self.genes.get("archetype", {}).values(),
            key=lambda g: g.weight,
            reverse=True
        )
        top_stops = sorted(
            self.genes.get("atr_stop_mult", {}).values(),
            key=lambda g: g.weight,
            reverse=True
        )
        top_tps = sorted(
            self.genes.get("atr_tp_mult", {}).values(),
            key=lambda g: g.weight,
            reverse=True
        )
        
        return {
            "generation": self.generation,
            "total_evaluations": self.total_evaluations,
            "total_approved": self.total_approved,
            "acceptance_rate_pct": round((self.total_approved / max(1, self.total_evaluations)) * 100, 2),
            "exploration_rate_pct": round(self.exploration_rate * 100, 1),
            "top_archetypes": [{"name": g.name, "value": g.value, "weight": g.weight, "approved": g.approved} for g in top_patterns],
            "top_stop_multipliers": [{"value": g.value, "weight": g.weight} for g in top_stops[:3]],
            "top_tp_multipliers": [{"value": g.value, "weight": g.weight} for g in top_tps[:3]],
        }


# Singleton Instance
ai_learning_engine = AILearningEngine()
