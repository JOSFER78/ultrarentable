"""Optuna Parameter Optimizer for Strategy Refinement."""
from __future__ import annotations

import copy
import random
from typing import Any, Callable


class OptunaOptimizer:
    """Parametric optimizer for tuning indicator periods and leverage."""

    def __init__(self, seed: int = 42):
        self.seed = seed

    def optimize_parameters(
        self,
        strategy_dict: dict[str, Any],
        eval_fn: Callable[[dict[str, Any]], float],
        n_trials: int = 10,
        max_leverage: int = 20,
    ) -> tuple[dict[str, Any], float]:
        """
        Tunes indicator periods and leverage using Optuna or deterministic grid/random search fallback.
        Returns (best_strategy_dict, best_fitness).
        """
        leverage_cap = min(500, max(1, int(max_leverage)))
        best_strat = copy.deepcopy(strategy_dict)
        best_fitness = eval_fn(best_strat)

        try:
            import optuna
            optuna.logging.set_verbosity(optuna.logging.WARNING)

            def objective(trial: optuna.Trial) -> float:
                candidate = copy.deepcopy(strategy_dict)
                # Find all indicator periods to tune
                periods_to_tune: list[dict[str, Any]] = []

                def _find_periods(node: Any) -> None:
                    if isinstance(node, dict):
                        if node.get("type") == "INDICATOR" and "params" in node and "period" in node["params"]:
                            periods_to_tune.append(node["params"])
                        for v in node.values():
                            _find_periods(v)
                    elif isinstance(node, list):
                        for item in node:
                            _find_periods(item)

                _find_periods(candidate["signals"])

                for idx, p_dict in enumerate(periods_to_tune):
                    curr = p_dict["period"]
                    low = max(2, curr - 20)
                    high = min(500, curr + 20)
                    p_dict["period"] = trial.suggest_int(f"period_{idx}", low, high)

                lev = trial.suggest_int("leverage", 1, leverage_cap)
                candidate["position"]["leverage"] = lev

                try:
                    return eval_fn(candidate)
                except Exception:
                    return -9999.0

            study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=self.seed))
            study.optimize(objective, n_trials=n_trials, timeout=30)

            if study.best_value > best_fitness:
                best_fitness = study.best_value
                # Reconstruct best strategy
                best_params = study.best_params
                best_strat = copy.deepcopy(strategy_dict)
                periods_to_tune = []

                def _find_periods_2(node: Any) -> None:
                    if isinstance(node, dict):
                        if node.get("type") == "INDICATOR" and "params" in node and "period" in node["params"]:
                            periods_to_tune.append(node["params"])
                        for v in node.values():
                            _find_periods_2(v)
                    elif isinstance(node, list):
                        for item in node:
                            _find_periods_2(item)

                _find_periods_2(best_strat["signals"])
                for idx, p_dict in enumerate(periods_to_tune):
                    if f"period_{idx}" in best_params:
                        p_dict["period"] = best_params[f"period_{idx}"]

                if "leverage" in best_params:
                    best_strat["position"]["leverage"] = best_params["leverage"]

        except ImportError:
            # Fallback random local search
            rng = random.Random(self.seed)
            for _ in range(n_trials):
                cand = copy.deepcopy(strategy_dict)
                cand["position"]["leverage"] = rng.randint(1, leverage_cap)
                score = eval_fn(cand)
                if score > best_fitness:
                    best_fitness = score
                    best_strat = cand

        best_strat["metadata"]["name"] = f"Opt_{best_strat['metadata'].get('name', 'Strat')}"
        return best_strat, best_fitness
