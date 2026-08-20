"""services/validation/metrics_calculator.py
Cálculos estadísticos y cuantitativos rigurosos para la validación antifraude (DSR, WFE, Outlier Dep, Monte Carlo).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List
import numpy as np

from contracts.backtest import BacktestResult, TradeLog


def calculate_deflated_sharpe_ratio(
    returns: List[float],
    benchmark_sharpe: float = 0.0,
    num_trials: int = 100,
) -> float:
    """Calcula el Deflated Sharpe Ratio (DSR) ajustado por sesgo de selección y no-normalidad (Bailey & López de Prado)."""
    if len(returns) < 5:
        return 0.0

    arr = np.array(returns, dtype=np.float64)
    std = float(np.std(arr))
    if std <= 1e-9:
        return 0.0

    mean_ret = float(np.mean(arr))
    sharpe = (mean_ret / std) * math.sqrt(252)

    # Skewness and Kurtosis
    skew = float(np.mean(((arr - mean_ret) / std) ** 3))
    kurt = float(np.mean(((arr - mean_ret) / std) ** 4))

    # Variance of Sharpe estimate
    var_sharpe = (1.0 + (0.5 * (sharpe ** 2)) - (skew * sharpe) + (((kurt - 3.0) / 4.0) * (sharpe ** 2))) / len(arr)
    var_sharpe = max(1e-6, var_sharpe)

    # Expected maximum Sharpe over num_trials
    euler_mascheroni = 0.5772156649
    if num_trials > 1:
        e_max_sharpe = ((1.0 - euler_mascheroni) * math.sqrt(2.0 * math.log(num_trials)) +
                        (euler_mascheroni / math.sqrt(2.0 * math.log(num_trials))))
    else:
        e_max_sharpe = benchmark_sharpe

    dsr_stat = (sharpe - e_max_sharpe) / math.sqrt(var_sharpe)
    # Cumulative normal CDF approximation
    dsr_prob = 0.5 * (1.0 + math.erf(dsr_stat / math.sqrt(2.0)))
    return round(float(sharpe * min(1.0, max(0.0, dsr_prob))), 2)


def calculate_outlier_dependency(trades: List[TradeLog]) -> float:
    """Calcula el porcentaje de ganancias atribuible a los 2 mejores trades (en múltiplos R / %)."""
    winning_r = [
        getattr(t, "return_r", 0.0) or (getattr(t, "return_pct", 0.0) / 7.5) or (getattr(t, "net_pnl_usd", 0.0) / 100.0)
        for t in trades
        if (getattr(t, "return_r", 0.0) > 0 or getattr(t, "return_pct", 0.0) > 0 or getattr(t, "net_pnl_usd", 0.0) > 0)
    ]
    total_profit_r = sum(winning_r)
    if total_profit_r <= 0:
        return 0.0

    sorted_wins = sorted(winning_r, reverse=True)
    top2_sum = sum(sorted_wins[:2])
    return round((top2_sum / total_profit_r) * 100.0, 2)


def calculate_max_single_trade_share(trades: List[TradeLog]) -> float:
    """Calcula el ratio del mayor trade respecto a la ganancia total (en múltiplos R / %)."""
    winning_r = [
        getattr(t, "return_r", 0.0) or (getattr(t, "return_pct", 0.0) / 7.5) or (getattr(t, "net_pnl_usd", 0.0) / 100.0)
        for t in trades
        if (getattr(t, "return_r", 0.0) > 0 or getattr(t, "return_pct", 0.0) > 0 or getattr(t, "net_pnl_usd", 0.0) > 0)
    ]
    total_profit_r = sum(winning_r)
    if total_profit_r <= 0:
        return 0.0

    max_win = max(winning_r)
    return round(max_win / total_profit_r, 4)


def calculate_tail_gain_ratio(trades: List[TradeLog]) -> float:
    """Calcula la proporción de ganancia generada por trades en la cola derecha (>= 3.0R)."""
    winning_r = [
        getattr(t, "return_r", 0.0) or (getattr(t, "return_pct", 0.0) / 7.5) or (getattr(t, "net_pnl_usd", 0.0) / 100.0)
        for t in trades
        if (getattr(t, "return_r", 0.0) > 0 or getattr(t, "return_pct", 0.0) > 0 or getattr(t, "net_pnl_usd", 0.0) > 0)
    ]
    total_profit_r = sum(winning_r)
    if total_profit_r <= 0:
        return 0.0

    tail_r = [getattr(t, "return_r", 0.0) for t in trades if getattr(t, "return_r", 0.0) >= 3.0]
    return round(sum(tail_r) / total_profit_r, 4)


def calculate_burst_ruin_probability(
    trades: List[TradeLog],
    burst_size: int = 20,
    iterations: int = 500,
) -> float:
    """Simulación Monte Carlo de ráfagas para verificar probabilidad de quiebra de la ráfaga de balas."""
    if not trades:
        return 0.0

    returns_r = [t.return_r for t in trades]
    bust_count = 0

    np.random.seed(42)
    for _ in range(iterations):
        sample = np.random.choice(returns_r, size=burst_size, replace=True)
        equity = float(burst_size)  # Presupuesto total de la ráfaga (burst_size R)
        for r in sample:
            equity += r
            if equity <= 0.0:
                bust_count += 1
                break

    return round((bust_count / iterations) * 100.0, 2)


def evaluate_friction_stress(
    trades: List[TradeLog],
    additional_fee_bps: float = 5.0,
    slippage_bps_per_pyramid: float = 3.0,
) -> bool:
    """Aplica estrés de fricción (tasas taker aumentadas y deslizamiento piramidal) para asegurar robustez."""
    if not trades:
        return False

    stressed_net_pnl = 0.0
    for t in trades:
        extra_fee = (t.entry_price * t.quantity) * (additional_fee_bps / 10000.0)
        extra_slip = (t.entry_price * t.quantity) * (slippage_bps_per_pyramid / 10000.0)
        stressed_trade_pnl = t.net_pnl_usd - extra_fee - extra_slip
        stressed_net_pnl += stressed_trade_pnl

    return stressed_net_pnl > 0.0
