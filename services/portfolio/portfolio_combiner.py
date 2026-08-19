"""services/portfolio/portfolio_combiner.py
Motor de Combinación de Portafolios Multi-Estrategia (Fase 7).
Calcula la matriz de covarianza real de retornos y drawdowns, agregando curvas punto a punto.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Literal, Optional
import numpy as np

from contracts.snapshots.strategy_snapshot import StrategySnapshot
from contracts.snapshots.portfolio_snapshot import PortfolioSnapshot, PortfolioStrategyAllocation
from services.validation.engine.event_backtest_engine import EventBacktestResult


class PortfolioCombiner:
    """Combina ejecuciones deterministas reales para generar un PortfolioSnapshot inmutable."""

    def combine_strategies(
        self,
        portfolio_id: str,
        backtest_results: List[EventBacktestResult],
        allocation_method: Literal["HRP", "EQUAL_WEIGHT", "INVERSE_VOLATILITY", "RISK_PARITY"] = "INVERSE_VOLATILITY",
        total_capital_usd: float = 100000.0,
    ) -> PortfolioSnapshot:
        if not backtest_results:
            return PortfolioSnapshot.create_and_hash(
                portfolio_id=portfolio_id,
                allocation_method=allocation_method,
                rebalance_frequency="DAILY",
                strategies=[],
                correlation_matrix={},
                drawdown_correlation_matrix={},
                total_capital_usd=total_capital_usd,
                combined_net_profit_usd=0.0,
                combined_profit_factor=0.0,
                combined_max_drawdown_pct=0.0,
                diversification_ratio=1.0,
                combined_equity_curve=[total_capital_usd],
            )

        n_strats = len(backtest_results)
        
        # Calcular ponderaciones por Inversa de Volatilidad
        vols = []
        for r in backtest_results:
            pnl_series = [t.net_pnl_usd for t in r.trades]
            std = float(np.std(pnl_series)) if len(pnl_series) > 1 else 1.0
            vols.append(max(1e-4, std))

        inv_vols = [1.0 / v for v in vols]
        sum_inv = sum(inv_vols)
        weights = [round(float(iv / sum_inv), 4) for iv in inv_vols]

        allocations = []
        for idx, r in enumerate(backtest_results):
            allocations.append(
                PortfolioStrategyAllocation(
                    strategy_id=r.strategy_id,
                    symbol=r.dataset_id.split("_")[2].upper() if "_" in r.dataset_id else "UNKNOWN",
                    weight=weights[idx],
                    canonical_hash=r.canonical_hash,
                )
            )

        # Matriz de Correlación
        corr_matrix: Dict[str, Dict[str, float]] = {}
        dd_corr_matrix: Dict[str, Dict[str, float]] = {}

        min_len = min(len(r.equity_curve) for r in backtest_results)
        eq_matrix = np.array([r.equity_curve[:min_len] for r in backtest_results])
        dd_matrix = np.array([r.drawdown_curve[:min_len] for r in backtest_results])

        for i, r_i in enumerate(backtest_results):
            corr_matrix[r_i.strategy_id] = {}
            dd_corr_matrix[r_i.strategy_id] = {}
            for j, r_j in enumerate(backtest_results):
                if i == j:
                    corr_matrix[r_i.strategy_id][r_j.strategy_id] = 1.0
                    dd_corr_matrix[r_i.strategy_id][r_j.strategy_id] = 1.0
                else:
                    c = float(np.corrcoef(eq_matrix[i], eq_matrix[j])[0, 1])
                    dd_c = float(np.corrcoef(dd_matrix[i], dd_matrix[j])[0, 1])
                    corr_matrix[r_i.strategy_id][r_j.strategy_id] = round(0.0 if math.isnan(c) else c, 4)
                    dd_corr_matrix[r_i.strategy_id][r_j.strategy_id] = round(0.0 if math.isnan(dd_c) else dd_c, 4)

        # Curva Combinada Ponderada
        combined_equity = [total_capital_usd]
        peak_combined = total_capital_usd
        max_comb_dd = 0.0

        for step in range(1, min_len):
            step_delta = sum(
                (eq_matrix[k][step] - eq_matrix[k][step - 1]) * weights[k]
                for k in range(n_strats)
            )
            new_eq = max(0.0, combined_equity[-1] + step_delta)
            combined_equity.append(round(new_eq, 2))
            peak_combined = max(peak_combined, new_eq)
            current_dd = ((peak_combined - new_eq) / max(1.0, peak_combined)) * 100.0
            max_comb_dd = max(max_comb_dd, current_dd)

        total_net_pnl = combined_equity[-1] - total_capital_usd
        all_gains = sum(max(0.0, combined_equity[k] - combined_equity[k-1]) for k in range(1, len(combined_equity)))
        all_losses = abs(sum(min(0.0, combined_equity[k] - combined_equity[k-1]) for k in range(1, len(combined_equity))))
        comb_pf = (all_gains / all_losses) if all_losses > 0 else (99.0 if all_gains > 0 else 0.0)

        # Diversification Ratio: Sum(w_i * vol_i) / vol_portfolio
        comb_vol = float(np.std(np.diff(combined_equity))) if len(combined_equity) > 2 else 1.0
        div_ratio = float(sum(weights[k] * vols[k] for k in range(n_strats)) / max(1e-4, comb_vol))

        return PortfolioSnapshot.create_and_hash(
            portfolio_id=portfolio_id,
            allocation_method=allocation_method,
            rebalance_frequency="DAILY",
            strategies=allocations,
            correlation_matrix=corr_matrix,
            drawdown_correlation_matrix=dd_corr_matrix,
            total_capital_usd=total_capital_usd,
            combined_net_profit_usd=round(total_net_pnl, 2),
            combined_profit_factor=round(comb_pf, 2),
            combined_max_drawdown_pct=round(max_comb_dd, 2),
            diversification_ratio=round(div_ratio, 2),
            combined_equity_curve=combined_equity,
        )
