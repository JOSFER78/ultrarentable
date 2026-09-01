"""Real-only research loop specialized for FONDEO hypotheses.

Uses the FONDEO strategy builder, the canonical compiler/backtest adapter and
held-out validation. Blind OOS remains untouched.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from contracts.backtest import BacktestRequest, DatasetSnapshot
from contracts.canonical_strategy import CanonicalStrategy, ProvenanceMetadata, StrategyLifecycleStatus
from contracts.snapshots.strategy_snapshot import StrategySnapshot
from services.backtest.fast_engine_adapter import FastEngineAdapter
from services.discovery.funding_discovery import FundingDiscoveryEngine
from services.discovery.funding_evolution_engine import FundingEvolutionEngine
from services.discovery.research_objective import robust_research_score
from services.discovery.strategy_search_registry import SearchTrialRecord, StrategySearchRegistry
from services.engine_version import CURRENT_ENGINE_VERSION


class FundingResearchLoop:
    """Generate/evolve FONDEO hypotheses against real datasets only."""

    def __init__(self, registry: StrategySearchRegistry,
                engine_version: str = CURRENT_ENGINE_VERSION) -> None:
        # W4.2: el default ANTES estaba hardcodeado a "5.4.0" (motor vigente: ver
        # services/engine_version.py). Candidatas generadas por este loop sin pasar
        # engine_version explícito (p.ej. scripts/run_strategy_research.py) quedaban
        # estampadas con un motor viejo y is_version_stale() las descartaba SIEMPRE aguas
        # abajo (meta_ensemble_service.py, scripts/gobernanza_regla26.py), pase lo que pase
        # con el motor real usado para generarlas.
        self.registry = registry
        self.engine_version = engine_version
        self.discovery = FundingDiscoveryEngine()
        self.evolution = FundingEvolutionEngine()
        self.backtest = FastEngineAdapter()

    @staticmethod
    def _score(is_result: Any, validation_result: Any) -> float:
        is_returns = [float(t.return_pct) for t in getattr(is_result, "trades", [])]
        val_returns = [float(t.return_pct) for t in getattr(validation_result, "trades", [])]
        is_score = robust_research_score(
            profit_factor=is_result.profit_factor,
            max_drawdown_pct=is_result.max_drawdown_pct,
            trades=is_result.total_trades,
            initial_capital_usd=getattr(is_result, "initial_capital_usd", 50000.0),
            net_profit_usd=is_result.net_profit_usd,
            drawdown_ceiling_pct=4.0,
            returns_pct=is_returns,
        )
        val_score = robust_research_score(
            profit_factor=validation_result.profit_factor,
            max_drawdown_pct=validation_result.max_drawdown_pct,
            trades=validation_result.total_trades,
            initial_capital_usd=getattr(validation_result, "initial_capital_usd", 50000.0),
            net_profit_usd=validation_result.net_profit_usd,
            drawdown_ceiling_pct=4.0,
            reference_profit_factor=is_result.profit_factor,
            returns_pct=val_returns,
        )
        if is_score == float("-inf") or val_score == float("-inf"):
            return -1e9
        return float(0.35 * is_score + 0.65 * val_score)

    @staticmethod
    def _to_canonical(snapshot: StrategySnapshot, parent_strategy_id: Optional[str], engine_version: str) -> CanonicalStrategy:
        if not snapshot.entry_rules or not snapshot.exit_rules or not snapshot.sizing_and_risk:
            raise ValueError(f"INCOMPLETE_STRATEGY_SNAPSHOT: {snapshot.strategy_id}")
        provenance = ProvenanceMetadata(
            author="FundingResearchLoop",
            engine_version=engine_version,
            policy_version=engine_version,
            created_at_utc="1970-01-01T00:00:00+00:00",
            parent_hash=parent_strategy_id,
        )
        return CanonicalStrategy.create_and_hash(
            strategy_id=snapshot.strategy_id,
            name=snapshot.strategy_id,
            version="1.0.0",
            symbol=snapshot.symbol,
            timeframe=snapshot.timeframe,
            route="FONDEO",
            archetype=snapshot.archetype,
            provenance=provenance,
            entry_rules=snapshot.entry_rules,
            exit_rules=snapshot.exit_rules,
            sizing_and_risk=snapshot.sizing_and_risk,
            session_window=snapshot.session_window,
            status=StrategyLifecycleStatus.GENERATED,
        )

    def _build_strategy(self, strategy_id: str, symbol: str, timeframe: str, dataset_id: str, dataset_sha256: str, params: Dict[str, Any]) -> StrategySnapshot:
        return self.discovery.generate_candidate_blueprint(
            strategy_id=strategy_id,
            symbol=symbol,
            timeframe=timeframe,
            dataset_id=dataset_id,
            dataset_sha256=dataset_sha256,
            risk_per_trade_pct=float(params.get("risk_per_trade_pct", 0.25)),
            target_profit_ticks=float(params.get("target_profit_ticks", 45.0)),
            stop_loss_ticks=float(params.get("stop_loss_ticks", 15.0)),
            ema_fast=int(params["ema_fast"]),
            ema_slow=int(params["ema_slow"]),
            rsi_period=int(params["rsi_period"]),
            rsi_threshold_long=float(params["rsi_threshold_long"]),
            rsi_threshold_short=float(params["rsi_threshold_short"]),
            archetype=str(params.get("archetype", "INSTITUTIONAL_SESSION_MOMENTUM")),
            time_stop_bars=int(params.get("time_stop_bars", 36)),
            session_start_utc=str(params.get("session_start_utc", "13:30")),
            session_end_utc=str(params.get("session_end_utc", "20:00")),
            max_daily_loss_usd=float(params.get("max_daily_loss_usd", 1000.0)),
        )

    def _run_backtest(
        self,
        snapshot: StrategySnapshot,
        candles: List[Dict[str, Any]],
        dataset_id: str,
        dataset_sha256: str,
        initial_capital_usd: float,
        is_in_sample: bool,
        parent_strategy_id: Optional[str],
    ) -> Any:
        canonical = self._to_canonical(snapshot, parent_strategy_id, self.engine_version)
        dataset = DatasetSnapshot(
            dataset_id=dataset_id,
            symbol=snapshot.symbol,
            timeframe=snapshot.timeframe,
            start_timestamp_utc_ms=int(candles[0].get("time") or candles[0].get("timestamp") or 0),
            end_timestamp_utc_ms=int(candles[-1].get("time") or candles[-1].get("timestamp") or 0),
            total_bars=len(candles),
            sha256_hash=dataset_sha256,
            is_in_sample=is_in_sample,
        )
        request = BacktestRequest(
            request_id=f"req_{snapshot.strategy_id}_{dataset_id}_{'IS' if is_in_sample else 'VAL'}",
            strategy_id=canonical.strategy_id,
            strategy=canonical,
            dataset=dataset,
            initial_capital_usd=initial_capital_usd,
        )
        return self.backtest._execute_on_candles(request, candles)

    @staticmethod
    def _seed_params(idx: int) -> Dict[str, Any]:
        fasts = [5, 9, 13]
        slows = [21, 34, 55]
        rsis = [10, 14, 21]
        thresholds = [(50.0, 50.0), (52.0, 48.0), (55.0, 45.0)]
        stops = [10.0, 15.0, 20.0]
        targets = [20.0, 30.0, 45.0, 60.0]
        f = fasts[idx % len(fasts)]
        s = next(v for v in slows if v > f)
        r = rsis[(idx // len(fasts)) % len(rsis)]
        long_t, short_t = thresholds[(idx // 3) % len(thresholds)]
        stop = stops[(idx // 9) % len(stops)]
        target = next(v for v in targets if v > stop)
        return {
            "ema_fast": f,
            "ema_slow": s,
            "rsi_period": r,
            "rsi_threshold_long": long_t,
            "rsi_threshold_short": short_t,
            "stop_loss_ticks": stop,
            "target_profit_ticks": target,
            "risk_per_trade_pct": 0.25,
            "time_stop_bars": 36,
            "session_profile": "US_CORE",
            "session_start_utc": "13:30",
            "session_end_utc": "20:00",
            "archetype": "INSTITUTIONAL_SESSION_MOMENTUM",
        }

    def run(
        self,
        dataset_path: str,
        symbol: str,
        timeframe: str,
        generations: int = 2,
        seeds: int = 24,
        children_per_seed: int = 4,
        initial_capital_usd: float = 50000.0,
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
        candles_is, candles_val = candles[:split_is], candles[split_is:split_val]
        run_id = f"fondeo_research_{path.stem}_{dataset_sha256[:12]}"
        frontier: List[Tuple[str, Dict[str, Any], Optional[str], int]] = []
        history: List[Dict[str, Any]] = []

        for idx in range(max(1, int(seeds))):
            params = self._seed_params(idx)
            frontier.append((f"seed_{idx:04d}", params, None, 1))

        for generation in range(1, max(1, int(generations)) + 1):
            evaluated: List[Tuple[float, str, Dict[str, Any], Any, Any]] = []
            for _, params, parent_id, _ in frontier:
                strategy_id = f"{run_id}_g{generation}_{len(evaluated):04d}"
                snapshot = self._build_strategy(strategy_id, symbol, timeframe, path.name, dataset_sha256, params)
                is_result = self._run_backtest(snapshot, candles_is, path.name, dataset_sha256, initial_capital_usd, True, parent_id)
                val_result = self._run_backtest(snapshot, candles_val, path.name, dataset_sha256, initial_capital_usd, False, parent_id)
                score = self._score(is_result, val_result)
                self.registry.record_trial(SearchTrialRecord(
                    trial_id=strategy_id,
                    run_id=run_id,
                    generation=generation,
                    parent_trial_id=parent_id,
                    symbol=symbol,
                    timeframe=timeframe,
                    route="FONDEO",
                    archetype=str(params.get("archetype", "INSTITUTIONAL_SESSION_MOMENTUM")),
                    parameters=params,
                    rules_json=snapshot.entry_rules.model_dump_json(),
                    dataset_id=path.name,
                    dataset_sha256=dataset_sha256,
                    discovery_engine="FundingResearchLoop",
                    in_sample_pf=is_result.profit_factor,
                    in_sample_dd_pct=is_result.max_drawdown_pct,
                ))
                record = {
                    "strategy_id": strategy_id,
                    "parent_strategy_id": parent_id,
                    "generation": generation,
                    "parameters": params,
                    "profit_factor_is": is_result.profit_factor,
                    "max_drawdown_is_pct": is_result.max_drawdown_pct,
                    "trades_is": is_result.total_trades,
                    "profit_factor_validation": val_result.profit_factor,
                    "max_drawdown_validation_pct": val_result.max_drawdown_pct,
                    "trades_validation": val_result.total_trades,
                    "net_profit_validation_usd": val_result.net_profit_usd,
                    "research_score": score,
                }
                history.append(record)
                evaluated.append((score, strategy_id, params, is_result, val_result))

            evaluated.sort(key=lambda item: item[0], reverse=True)
            survivors = evaluated[: max(1, min(8, len(evaluated)))]
            if generation >= max(1, int(generations)):
                break
            frontier = []
            for _, strategy_id, params, _, _ in survivors:
                for proposal in self.evolution.propose(strategy_id, params, limit=max(1, int(children_per_seed))):
                    frontier.append((proposal.mutation_id, proposal.parameters, strategy_id, generation + 1))

        preview = sorted(history, key=lambda row: row["research_score"], reverse=True)[:20]
        return {
            "run_id": run_id,
            "dataset_id": path.name,
            "dataset_sha256": dataset_sha256,
            "route": "FONDEO",
            "history_count": len(history),
            "survivors_preview": preview,
            "status": "RESEARCH_COMPLETE_NOT_CERTIFIED",
            "blind_oos_touched": False,
            "execution_engine": "FastEngineAdapter -> CanonicalCompiler -> UniversalDeterministicBacktestEngine",
        }
