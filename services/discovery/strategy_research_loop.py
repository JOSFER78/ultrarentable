"""Bounded real-only strategy research loop.

Coordinates generation, IS evaluation, semantic mutation and validation-set
ranking. Blind OOS remains untouched and belongs exclusively to final validation.
All evaluated hypotheses are compiled into the canonical executable engine.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from contracts.backtest import BacktestRequest, DatasetSnapshot
from contracts.canonical_strategy import (
    CanonicalStrategy,
    ProvenanceMetadata,
    StrategyLifecycleStatus,
)
from contracts.snapshots.strategy_snapshot import StrategySnapshot
from services.backtest.fast_engine_adapter import FastEngineAdapter
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
    total_trades_is: int
    profit_factor_is: float
    max_drawdown_is_pct: float
    net_profit_is_usd: float
    total_trades_validation: int
    profit_factor_validation: float
    max_drawdown_validation_pct: float
    net_profit_validation_usd: float
    research_score: float


class StrategyResearchLoop:
    """Generate/evolve real hypotheses and rank them using IS + held-out Validation."""

    def __init__(self, registry: StrategySearchRegistry, engine_version: str = "5.4.0") -> None:
        self.registry = registry
        self.engine_version = engine_version
        self.discovery = UltraDiscoveryEngine()
        self.fast_backtest = FastEngineAdapter()
        # Kept as a compatibility reference for callers that import this loop;
        # quantitative candidate evaluation is performed by the canonical adapter above.
        self.legacy_backtest = EventBacktestEngine()
        self.evolution = StrategyEvolutionEngine()

    @staticmethod
    def _score(is_result: Any, validation_result: Any) -> float:
        """Research ranking only. Never used for certification."""
        if is_result.total_trades <= 0 or validation_result.total_trades <= 0:
            return -1e9
        is_quality = max(0.01, is_result.profit_factor) * max(0.05, 1.0 - is_result.max_drawdown_pct / 100.0)
        val_quality = max(0.01, validation_result.profit_factor) * max(0.05, 1.0 - validation_result.max_drawdown_pct / 100.0)
        sample_factor = min(1.0, min(is_result.total_trades, validation_result.total_trades) / 30.0)
        return float((0.45 * is_quality + 0.55 * val_quality) * (1.0 + sample_factor))

    def _build_strategy(
        self,
        strategy_id: str,
        symbol: str,
        timeframe: str,
        dataset_id: str,
        dataset_sha256: str,
        params: Dict[str, Any],
        parent_strategy_id: Optional[str] = None,
        mutation_type: Optional[str] = None,
    ) -> StrategySnapshot:
        return self.discovery.generate_candidate_blueprint(
            strategy_id=strategy_id,
            symbol=symbol,
            timeframe=timeframe,
            dataset_id=dataset_id,
            dataset_sha256=dataset_sha256,
            ema_fast=int(params["ema_fast"]),
            ema_slow=int(params["ema_slow"]),
            rsi_period=int(params["rsi_period"]),
            rsi_threshold_long=float(params["rsi_threshold_long"]),
            rsi_threshold_short=float(params["rsi_threshold_short"]),
            sl_atr_mult=float(params.get("sl_atr_mult", 2.0)),
            tp_atr_mult=float(params.get("tp_atr_mult", 6.0)),
            pyramiding_tiers_count=int(params.get("pyramiding_tiers_count", 0)),
            archetype=str(params.get("archetype", "MOMENTUM_BREAKOUT")),
            volatility_filter=params.get("volatility_filter"),
            volume_confirmation=params.get("volume_confirmation"),
            breakout_confirmation=bool(params.get("breakout_confirmation", False)),
            breakout_lookback=int(params.get("breakout_lookback", 20)),
            exit_family=params.get("exit_family"),
            session_profile=params.get("session_profile"),
            time_stop_bars=int(params.get("time_stop_bars", 48)),
            rr_multiple=float(params.get("rr_multiple", 2.5)),
            trail_after_r=float(params.get("trail_after_r", 1.5)),
        )

    @staticmethod
    def _to_canonical_strategy(
        snapshot: StrategySnapshot,
        parent_strategy_id: Optional[str] = None,
        mutation_type: Optional[str] = None,
        engine_version: str = "5.4.0",
    ) -> CanonicalStrategy:
        """Bridge the immutable StrategySnapshot into the canonical executable AST."""
        if not snapshot.entry_rules or not snapshot.exit_rules or not snapshot.sizing_and_risk:
            raise ValueError(f"INCOMPLETE_STRATEGY_SNAPSHOT: {snapshot.strategy_id}")
        provenance = ProvenanceMetadata(
            author="StrategyResearchLoop",
            engine_version=engine_version,
            policy_version=engine_version,
            # Stable metadata so identical research inputs produce identical semantic hashes.
            created_at_utc="1970-01-01T00:00:00+00:00",
            parent_hash=parent_strategy_id,
            mutation_type=mutation_type,
        )
        return CanonicalStrategy.create_and_hash(
            strategy_id=snapshot.strategy_id,
            name=snapshot.strategy_id,
            version="1.0.0",
            symbol=snapshot.symbol,
            timeframe=snapshot.timeframe,
            route=snapshot.route.value,
            archetype=snapshot.archetype,
            provenance=provenance,
            entry_rules=snapshot.entry_rules,
            exit_rules=snapshot.exit_rules,
            sizing_and_risk=snapshot.sizing_and_risk,
            session_window=snapshot.session_window,
            status=StrategyLifecycleStatus.GENERATED,
        )

    def _run_canonical_backtest(
        self,
        strategy: StrategySnapshot,
        candles: List[Dict[str, Any]],
        dataset_id: str,
        dataset_sha256: str,
        initial_capital_usd: float,
        parent_strategy_id: Optional[str] = None,
        mutation_type: Optional[str] = None,
    ) -> Any:
        canonical = self._to_canonical_strategy(
            strategy,
            parent_strategy_id=parent_strategy_id,
            mutation_type=mutation_type,
            engine_version=self.engine_version,
        )
        dataset = DatasetSnapshot(
            dataset_id=dataset_id,
            symbol=strategy.symbol,
            timeframe=strategy.timeframe,
            start_timestamp_utc_ms=int(candles[0].get("time") or candles[0].get("timestamp") or 0),
            end_timestamp_utc_ms=int(candles[-1].get("time") or candles[-1].get("timestamp") or 0),
            total_bars=len(candles),
            sha256_hash=dataset_sha256,
            is_in_sample=True,
        )
        request = BacktestRequest(
            request_id=f"req_{strategy.strategy_id}_{dataset_id}",
            strategy_id=canonical.strategy_id,
            strategy=canonical,
            dataset=dataset,
            initial_capital_usd=initial_capital_usd,
        )
        return self.fast_backtest._execute_on_candles(request, candles)

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
        frontier: List[Tuple[str, Dict[str, Any], str, Optional[str], int]] = []
        history: List[ResearchCandidate] = []

        seed_archetypes = ["MOMENTUM_BREAKOUT", "TREND_FOLLOWING", "RSI_MOMENTUM", "MEAN_REVERSION"]
        for idx in range(max(1, int(seeds))):
            archetype = seed_archetypes[idx % len(seed_archetypes)]
            params = {
                "ema_fast": [8, 12, 20][idx % 3],
                "ema_slow": [30, 50, 80][idx % 3],
                "rsi_period": [10, 14, 21][idx % 3],
                "rsi_threshold_long": [52.0, 55.0, 60.0][idx % 3],
                "rsi_threshold_short": [48.0, 45.0, 40.0][idx % 3],
                "sl_atr_mult": [1.5, 2.0, 3.0][idx % 3],
                "tp_atr_mult": [4.0, 6.0, 8.0][idx % 3],
                "archetype": archetype,
                "pyramiding_tiers_count": 0,
            }
            frontier.append((f"seed_{idx:04d}", params, archetype, None, 1))

        for generation in range(1, max(1, int(generations)) + 1):
            evaluated: List[Tuple[float, str, Dict[str, Any], str, Optional[str], Any, Any]] = []
            for _, params, archetype, parent_strategy_id, _ in frontier:
                strategy_id = f"{run_id}_g{generation}_{len(evaluated):04d}"
                strategy = self._build_strategy(
                    strategy_id,
                    symbol,
                    timeframe,
                    path.name,
                    dataset_sha256,
                    params,
                    parent_strategy_id=parent_strategy_id,
                )
                is_result = self._run_canonical_backtest(
                    strategy,
                    candles_is,
                    path.name,
                    dataset_sha256,
                    initial_capital_usd,
                    parent_strategy_id=parent_strategy_id,
                )
                validation_result = self._run_canonical_backtest(
                    strategy,
                    candles_val,
                    path.name,
                    dataset_sha256,
                    initial_capital_usd,
                    parent_strategy_id=parent_strategy_id,
                )
                score = self._score(is_result, validation_result)

                self.registry.record_trial(
                    SearchTrialRecord(
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
                        in_sample_pf=is_result.profit_factor,
                        in_sample_dd_pct=is_result.max_drawdown_pct,
                    )
                )

                history.append(
                    ResearchCandidate(
                        strategy_id=strategy_id,
                        parent_strategy_id=parent_strategy_id,
                        generation=generation,
                        archetype=archetype,
                        parameters=params,
                        total_trades_is=is_result.total_trades,
                        profit_factor_is=is_result.profit_factor,
                        max_drawdown_is_pct=is_result.max_drawdown_pct,
                        net_profit_is_usd=is_result.net_profit_usd,
                        total_trades_validation=validation_result.total_trades,
                        profit_factor_validation=validation_result.profit_factor,
                        max_drawdown_validation_pct=validation_result.max_drawdown_pct,
                        net_profit_validation_usd=validation_result.net_profit_usd,
                        research_score=score,
                    )
                )
                evaluated.append(
                    (
                        score,
                        strategy_id,
                        params,
                        archetype,
                        strategy_id,
                        is_result,
                        validation_result,
                    )
                )

            evaluated.sort(key=lambda item: item[0], reverse=True)
            survivors = evaluated[: max(1, min(8, len(evaluated)))]
            if generation >= max(1, int(generations)):
                break

            frontier = []
            for _, strategy_id, params, archetype, _, _, _ in survivors:
                for proposal in self.evolution.propose(
                    parent_strategy_id=strategy_id,
                    parameters=params,
                    archetype=archetype,
                    limit=max(1, int(children_per_seed)),
                ):
                    child_params = proposal.parameters
                    child_archetype = str(child_params.get("archetype", archetype))
                    frontier.append(
                        (
                            proposal.mutation_id,
                            child_params,
                            child_archetype,
                            strategy_id,
                            generation + 1,
                        )
                    )

        final_preview = sorted(history, key=lambda c: c.research_score, reverse=True)[:20]
        return {
            "run_id": run_id,
            "dataset_id": path.name,
            "dataset_sha256": dataset_sha256,
            "generations": max(1, int(generations)),
            "history_count": len(history),
            "survivors_preview": [c.__dict__ for c in final_preview],
            "status": "RESEARCH_COMPLETE_NOT_CERTIFIED",
            "blind_oos_touched": False,
            "execution_engine": "FastEngineAdapter -> CanonicalCompiler -> UniversalDeterministicBacktestEngine",
        }
