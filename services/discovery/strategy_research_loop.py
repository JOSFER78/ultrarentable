"""Bounded real-only strategy research loop.

This module coordinates generation, semantic mutation and deterministic backtesting.
It deliberately stops before blind OOS certification: the existing validation fabric
remains the only authority for certification.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from services.discovery.strategy_evolution_engine import StrategyEvolutionEngine
from services.discovery.strategy_search_registry import SearchTrialRecord, StrategySearchRegistry
from services.discovery.ultra_discovery import UltraDiscoveryEngine
from services.validation.engine.event_backtest_engine import EventBacktestEngine


@dataclass(frozen=True)
class ResearchCandidate:
    strategy_id: str
    parent_strategy_id: Optional[str]
    generation: int
    archetype: str
    parameters: Dict[str, Any]
    total_trades: int
    profit_factor: float
    max_drawdown_pct: float
    net_profit_usd: float


class StrategyResearchLoop:
    """Generate and evolve real hypotheses without declaring them profitable prematurely."""

    def __init__(self, registry: StrategySearchRegistry, engine_version: str = "5.4.0") -> None:
        self.registry = registry
        self.engine_version = engine_version
        self.discovery = UltraDiscoveryEngine()
        self.backtest = EventBacktestEngine()
        self.evolution = StrategyEvolutionEngine()

    @staticmethod
    def _score(result: Any) -> float:
        """Research ranking only; never used as a certification decision."""
        if result.total_trades <= 0 or result.profit_factor <= 0:
            return -1e9
        dd_factor = max(0.05, 1.0 - result.max_drawdown_pct / 100.0)
        sample_factor = min(1.0, result.total_trades / 30.0)
        return float(result.profit_factor * dd_factor * (1.0 + sample_factor))

    def run(
        self,
        dataset_path: str,
        symbol: str,
        timeframe: str,
        generations: int = 2,
        seeds: int = 24,
        children_per_seed: int = 6,
        initial_capital_usd: float = 1000.0,
    ) -> Dict[str, Any]:
        path = Path(dataset_path)
        if not path.is_file():
            raise FileNotFoundError(f"Real dataset not found: {path}")

        dataset_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        candles = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(candles, list) or len(candles) < 200:
            raise ValueError("Dataset must contain at least 200 real bars")

        split_is = int(len(candles) * 0.60)
        split_val = int(len(candles) * 0.80)
        candles_is = candles[:split_is]
        candles_val = candles[split_is:split_val]

        run_id = f"research_{path.stem}_{dataset_sha256[:12]}"
        candidates: List[ResearchCandidate] = []
        frontier: List[Tuple[float, str, Dict[str, Any], str, Optional[str], int]] = []

        seed_archetypes = [
            "MOMENTUM_BREAKOUT",
            "TREND_FOLLOWING",
            "RSI_MOMENTUM",
            "MEAN_REVERSION",
        ]
        for idx in range(max(1, int(seeds))):
            params = {
                "ema_fast": [8, 12, 20][idx % 3],
                "ema_slow": [30, 50, 80][idx % 3],
                "rsi_period": [10, 14, 21][idx % 3],
                "rsi_threshold_long": [52.0, 55.0, 60.0][idx % 3],
                "rsi_threshold_short": [48.0, 45.0, 40.0][idx % 3],
                "sl_atr_mult": [1.5, 2.0, 3.0][idx % 3],
                "tp_atr_mult": [4.0, 6.0, 8.0][idx % 3],
                "archetype": seed_archetypes[idx % len(seed_archetypes)],
                "pyramiding_tiers_count": 0,
            }
            frontier.append((0.0, f"seed_{idx:04d}", params, params["archetype"], None, 1))

        history: List[ResearchCandidate] = []

        for generation in range(1, max(1, int(generations)) + 1):
            evaluated: List[Tuple[float, str, Dict[str, Any], str, Optional[str], int, Any]] = []
            for _, parent_id, params, archetype, parent_strategy_id, _ in frontier:
                strategy_id = f"{run_id}_g{generation}_{len(evaluated):04d}"
                strategy = self.discovery.generate_candidate_blueprint(
                    strategy_id=strategy_id,
                    symbol=symbol,
                    timeframe=timeframe,
                    dataset_id=path.name,
                    dataset_sha256=dataset_sha256,
                    ema_fast=int(params["ema_fast"]),
                    ema_slow=int(params["ema_slow"]),
                    rsi_period=int(params["rsi_period"]),
                    rsi_threshold_long=float(params["rsi_threshold_long"]),
                    rsi_threshold_short=float(params["rsi_threshold_short"]),
                    sl_atr_mult=float(params["sl_atr_mult"]),
                    tp_atr_mult=float(params["tp_atr_mult"]),
                    pyramiding_tiers_count=int(params.get("pyramiding_tiers_count", 0)),
                    archetype=archetype,
                )
                result = self.backtest.run_backtest(strategy, candles_is, initial_capital_usd=initial_capital_usd)
                score = self._score(result)
                self.registry.record_trial(SearchTrialRecord(
                    trial_id=strategy_id,
                    run_id=run_id,
                    generation=generation,
                    parent_trial_id=parent_strategy_id,
                    symbol=symbol,
                    timeframe=timeframe,
                    route="ULTRA",
                    archetype=archetype,
                    parameters=params,
                    rules_json=strategy.entry_rules.model_dump_json(),
                    dataset_id=path.name,
                    dataset_sha256=dataset_sha256,
                    discovery_engine="StrategyResearchLoop",
                    in_sample_pf=result.profit_factor,
                    in_sample_dd_pct=result.max_drawdown_pct,
                ))
                candidate = ResearchCandidate(
                    strategy_id=strategy_id,
                    parent_strategy_id=parent_strategy_id,
                    generation=generation,
                    archetype=archetype,
                    parameters=params,
                    total_trades=result.total_trades,
                    profit_factor=result.profit_factor,
                    max_drawdown_pct=result.max_drawdown_pct,
                    net_profit_usd=result.net_profit_usd,
                )
                history.append(candidate)
                evaluated.append((score, strategy_id, params, archetype, strategy_id, generation, result))

            evaluated.sort(key=lambda item: item[0], reverse=True)
            survivors = evaluated[: max(1, min(8, len(evaluated)))]
            if generation >= max(1, int(generations)):
                break

            frontier = []
            for score, strategy_id, params, archetype, _, gen, _ in survivors:
                proposals = self.evolution.propose(
                    parent_strategy_id=strategy_id,
                    parameters=params,
                    archetype=archetype,
                    limit=max(1, int(children_per_seed)),
                )
                for proposal in proposals:
                    frontier.append((score, proposal.mutation_id, proposal.parameters, proposal.parameters.get("archetype", archetype), strategy_id, gen + 1))

        # Validation set is intentionally used only for diagnostics/ranking of survivors;
        # Blind OOS is not touched here and must remain owned by the validation pipeline.
        final_preview = sorted(
            history,
            key=lambda c: (c.profit_factor, c.total_trades, -c.max_drawdown_pct),
            reverse=True,
        )[:20]
        return {
            "run_id": run_id,
            "dataset_id": path.name,
            "dataset_sha256": dataset_sha256,
            "generations": max(1, int(generations)),
            "history_count": len(history),
            "survivors_preview": [c.__dict__ for c in final_preview],
            "status": "RESEARCH_COMPLETE_NOT_CERTIFIED",
            "blind_oos_touched": False,
        }
