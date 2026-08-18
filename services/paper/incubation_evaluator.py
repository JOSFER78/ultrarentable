"""services/paper/incubation_evaluator.py
Evaluador de Incubación de 14 Días y Detección de Degradación OOS.
Compara la ejecución en Paper Trading contra el baseline de Backtest y decide promoción a LIVE_ACTIVE o rechazo.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
import numpy as np

from contracts.backtest import BacktestResult, TradeLog
from contracts.canonical_strategy import CanonicalStrategy, StrategyLifecycleStatus
from services.validation.candidate_registry import CandidateRegistry


class IncubationVerdict(str, Enum):
    CONTINUE_INCUBATING = "CONTINUE_INCUBATING"
    PROMOTE_TO_LIVE = "PROMOTE_TO_LIVE"
    ABORT_AND_REJECT = "ABORT_AND_REJECT"


@dataclass(frozen=True)
class IncubationReport:
    strategy_id: str
    verdict: IncubationVerdict
    days_observed: float
    total_paper_trades: int
    paper_sharpe: float
    backtest_sharpe: float
    sharpe_drift_pct: float
    paper_max_dd_pct: float
    backtest_max_dd_pct: float
    max_dd_ratio: float
    reasons: List[str]


class IncubationEvaluator:
    """Evaluador de estabilidad estadística entre Paper Trading y Backtest."""

    def __init__(
        self,
        min_observation_days: float = 14.0,
        min_trades: int = 15,
        max_sharpe_drift_pct: float = 30.0,
        max_dd_expansion_ratio: float = 1.25,
    ) -> None:
        self.min_days = min_observation_days
        self.min_trades = min_trades
        self.max_sharpe_drift = max_sharpe_drift_pct
        self.max_dd_ratio = max_dd_expansion_ratio

    def evaluate(
        self,
        strategy: CanonicalStrategy,
        backtest_baseline: BacktestResult,
        paper_trades: List[TradeLog],
        observation_start_ms: int,
        current_time_ms: int,
        registry: Optional[CandidateRegistry] = None,
    ) -> IncubationReport:
        """Evalúa las métricas en vivo y actualiza la FSM si aplica."""
        days_observed = max(0.0, (current_time_ms - observation_start_ms) / (1000.0 * 86400.0))
        n_trades = len(paper_trades)
        reasons: List[str] = []

        if n_trades == 0:
            return IncubationReport(
                strategy_id=strategy.strategy_id,
                verdict=IncubationVerdict.CONTINUE_INCUBATING,
                days_observed=round(days_observed, 1),
                total_paper_trades=0,
                paper_sharpe=0.0,
                backtest_sharpe=backtest_baseline.sharpe_ratio,
                sharpe_drift_pct=0.0,
                paper_max_dd_pct=0.0,
                backtest_max_dd_pct=backtest_baseline.max_drawdown_pct,
                max_dd_ratio=0.0,
                reasons=["Sin operaciones ejecutadas aún en el sandbox"],
            )

        # 1. Calcular métricas de Paper Trading
        pnls = [t.net_pnl_usd for t in paper_trades]
        mean_pnl = float(np.mean(pnls))
        std_pnl = float(np.std(pnls)) if len(pnls) > 1 else 1.0
        paper_sharpe = float((mean_pnl / std_pnl) * math.sqrt(252)) if std_pnl > 0 else 0.0

        # Drawdown de Paper Trading
        equity = 10000.0 + np.cumsum([0.0] + pnls)
        peak = np.maximum.accumulate(equity)
        dds = (peak - equity) / peak * 100.0
        paper_max_dd = float(np.max(dds)) if len(dds) > 0 else 0.0

        # 2. Comparación contra Backtest Baseline
        bt_sharpe = max(0.1, backtest_baseline.sharpe_ratio)
        sharpe_drift_pct = abs(paper_sharpe - bt_sharpe) / bt_sharpe * 100.0

        bt_max_dd = max(0.5, backtest_baseline.max_drawdown_pct)
        dd_ratio = paper_max_dd / bt_max_dd

        # Degradación de Sharpe: solo penaliza si el rendimiento en vivo es inferior al backtest
        sharpe_degradation_pct = max(0.0, (bt_sharpe - paper_sharpe) / bt_sharpe * 100.0) if bt_sharpe > 0 else 0.0

        # 3. Comprobar condiciones de Aborto / Rechazo
        if dd_ratio > self.max_dd_ratio:
            reasons.append(f"Max DD en Paper ({paper_max_dd:.1f}%) excede {self.max_dd_ratio}x el Backtest ({bt_max_dd:.1f}%)")

        if paper_sharpe < 0:
            reasons.append(f"Sharpe negativo en Paper Trading ({paper_sharpe:.2f})")

        if sharpe_degradation_pct > self.max_sharpe_drift and paper_sharpe < bt_sharpe:
            reasons.append(f"Degradación de Sharpe excesiva ({sharpe_degradation_pct:.1f}% > {self.max_sharpe_drift:.1f}%)")

        if reasons:
            verdict = IncubationVerdict.ABORT_AND_REJECT
            if registry and strategy.strategy_id in registry._strategies:
                try:
                    registry.transition(strategy.strategy_id, StrategyLifecycleStatus.REJECTED, "; ".join(reasons))
                except Exception:
                    pass
        elif days_observed >= self.min_days and n_trades >= self.min_trades and sharpe_degradation_pct <= self.max_sharpe_drift:
            verdict = IncubationVerdict.PROMOTE_TO_LIVE
            if registry and strategy.strategy_id in registry._strategies:
                try:
                    registry.transition(strategy.strategy_id, StrategyLifecycleStatus.LIVE_ACTIVE, "Incubación de 14 días completada con éxito")
                except Exception:
                    pass
        else:
            verdict = IncubationVerdict.CONTINUE_INCUBATING
            reasons.append(f"En observación ({days_observed:.1f}/{self.min_days} días, {n_trades}/{self.min_trades} trades)")

        return IncubationReport(
            strategy_id=strategy.strategy_id,
            verdict=verdict,
            days_observed=round(days_observed, 1),
            total_paper_trades=n_trades,
            paper_sharpe=round(paper_sharpe, 2),
            backtest_sharpe=round(bt_sharpe, 2),
            sharpe_drift_pct=round(sharpe_drift_pct, 1),
            paper_max_dd_pct=round(paper_max_dd, 2),
            backtest_max_dd_pct=round(bt_max_dd, 2),
            max_dd_ratio=round(dd_ratio, 2),
            reasons=reasons,
        )
