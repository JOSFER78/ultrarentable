"""services/engine/metrics_engine.py
Forensic Mathematical Metrics Engine (v3.0.0).

DOCTRINA ZERO-MOCKS & ZERO-FAKE METRICS:
- Calculates all quantitative metrics strictly from physical trade records and bar equity ledgers.
- Never uses heuristic multipliers (e.g. Sortino = Sharpe * 1.15 is strictly forbidden).
- Returns NOT_COMPUTABLE whenever statistical requirements are not met (e.g. 0 losing trades, < 5 trades, missing trials_tested).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional
import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from contracts.universal_ledger import BarEquityRecord, TradeRecord


class MetricStatus(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    value: Optional[float] = None
    status: str = "VALID"  # "VALID" | "NOT_COMPUTABLE" | "NO_EVIDENCE"
    reason: Optional[str] = None


class ForensicPerformanceMetrics(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate_pct: float
    
    net_profit_usd: float
    total_roi_pct: float
    monthly_roi_pct: float
    annualized_roi_pct: float
    
    profit_factor: MetricStatus
    expectancy_r: MetricStatus
    sharpe_ratio: MetricStatus
    sortino_ratio: MetricStatus
    calmar_ratio: MetricStatus
    deflated_sharpe_ratio: MetricStatus
    
    max_drawdown_pct: float
    max_drawdown_duration_bars: int
    outlier_dependency_pct: MetricStatus
    tail_gain_ratio: MetricStatus
    hurst_exponent: MetricStatus
    shannon_entropy: MetricStatus


class UniversalMetricsEngine:
    """Motor forense de cálculo matemático exacto de métricas."""

    @classmethod
    def compute_all(
        cls,
        trades: List[TradeRecord],
        bar_ledger: List[BarEquityRecord],
        base_capital: float,
        trials_tested: Optional[int] = None,
        annualization_factor: float = 252.0,
    ) -> ForensicPerformanceMetrics:
        n_trades = len(trades)
        winning = [t for t in trades if t.net_pnl_usd > 0]
        losing = [t for t in trades if t.net_pnl_usd <= 0]
        win_count = len(winning)
        loss_count = len(losing)
        win_rate = (win_count / n_trades * 100.0) if n_trades > 0 else 0.0

        net_profit = sum(t.net_pnl_usd for t in trades)
        total_roi = (net_profit / max(1.0, base_capital)) * 100.0

        # Duración temporal
        if bar_ledger and len(bar_ledger) > 1:
            span_ms = max(1, bar_ledger[-1].timestamp_ms - bar_ledger[0].timestamp_ms)
            span_years = max(0.01, (span_ms / (1000.0 * 86400.0)) / 365.25)
        else:
            span_years = 1.0
        annual_roi = total_roi / span_years
        monthly_roi = annual_roi / 12.0

        # Profit Factor
        gross_wins = sum(t.net_pnl_usd for t in winning)
        gross_losses = abs(sum(t.net_pnl_usd for t in losing))
        if gross_losses > 0:
            pf_metric = MetricStatus(value=round(gross_wins / gross_losses, 2), status="VALID")
        elif gross_wins > 0:
            pf_metric = MetricStatus(value=None, status="NOT_COMPUTABLE", reason="NO_LOSING_TRADES")
        else:
            pf_metric = MetricStatus(value=0.0, status="VALID")

        # Expectancy R
        if n_trades > 0:
            exp_r = float(np.mean([t.return_r for t in trades]))
            exp_metric = MetricStatus(value=round(exp_r, 2), status="VALID")
        else:
            exp_metric = MetricStatus(value=None, status="NOT_COMPUTABLE", reason="NO_TRADES")

        # Returns vector
        trade_returns = np.array([t.return_pct / 100.0 for t in trades], dtype=np.float64) if n_trades > 0 else np.array([], dtype=np.float64)

        # Sharpe Ratio
        if n_trades >= 5 and np.std(trade_returns) > 1e-8:
            mean_ret = float(np.mean(trade_returns))
            std_ret = float(np.std(trade_returns))
            sharpe_val = (mean_ret / std_ret) * math.sqrt(annualization_factor)
            sharpe_metric = MetricStatus(value=round(sharpe_val, 2), status="VALID")
        else:
            sharpe_metric = MetricStatus(value=None, status="NOT_COMPUTABLE", reason="INSUFFICIENT_TRADE_SAMPLE_OR_ZERO_VARIANCE")

        # Sortino Ratio (Downside deviation)
        downside = trade_returns[trade_returns < 0]
        if len(downside) >= 2 and np.std(downside) > 1e-8:
            mean_ret = float(np.mean(trade_returns))
            downside_std = float(np.sqrt(np.mean(downside ** 2)))
            sortino_val = (mean_ret / downside_std) * math.sqrt(annualization_factor)
            sortino_metric = MetricStatus(value=round(sortino_val, 2), status="VALID")
        else:
            sortino_metric = MetricStatus(value=None, status="NOT_COMPUTABLE", reason="INSUFFICIENT_NEGATIVE_RETURNS_OR_ZERO_DOWNSIDE")

        # Max Drawdown
        if bar_ledger:
            equities = [b.equity_usd for b in bar_ledger]
            peak = equities[0]
            max_dd = 0.0
            max_dd_bars = 0
            curr_dd_bars = 0

            for eq in equities:
                if eq >= peak:
                    peak = eq
                    curr_dd_bars = 0
                else:
                    curr_dd_bars += 1
                    max_dd_bars = max(max_dd_bars, curr_dd_bars)
                    dd = ((peak - eq) / peak) * 100.0
                    max_dd = max(max_dd, dd)
            max_drawdown_pct = round(max_dd, 2)
            max_drawdown_duration = max_dd_bars
        else:
            max_drawdown_pct = 0.0
            max_drawdown_duration = 0

        # Calmar Ratio
        if max_drawdown_pct > 0.01:
            calmar_val = annual_roi / max_drawdown_pct
            calmar_metric = MetricStatus(value=round(calmar_val, 2), status="VALID")
        else:
            calmar_metric = MetricStatus(value=None, status="NOT_COMPUTABLE", reason="ZERO_DRAWDOWN")

        # Deflated Sharpe Ratio (DSR)
        if trials_tested is None:
            dsr_metric = MetricStatus(value=None, status="NOT_COMPUTABLE", reason="MISSING_TRIALS_TESTED_EVIDENCE")
        elif sharpe_metric.value is not None and n_trades >= 10:
            dsr_val = cls._calc_dsr(trade_returns, sharpe_metric.value, trials_tested)
            dsr_metric = MetricStatus(value=round(dsr_val, 3), status="VALID")
        else:
            dsr_metric = MetricStatus(value=None, status="NOT_COMPUTABLE", reason="INSUFFICIENT_SAMPLE_FOR_DSR")

        # Outlier Dependency (Top 2 trades % of total positive PnL)
        pos_pnls = sorted([t.net_pnl_usd for t in winning], reverse=True)
        tot_pos = sum(pos_pnls)
        if tot_pos > 0 and len(pos_pnls) >= 2:
            outlier_pct = (sum(pos_pnls[:2]) / tot_pos) * 100.0
            outlier_metric = MetricStatus(value=round(outlier_pct, 2), status="VALID")
        elif tot_pos > 0:
            outlier_metric = MetricStatus(value=100.0, status="VALID")
        else:
            outlier_metric = MetricStatus(value=0.0, status="VALID")

        # Tail Gain Ratio (trades >= 3R / total positive PnL)
        tail_pnls = sum(t.net_pnl_usd for t in winning if t.return_r >= 3.0)
        if tot_pos > 0:
            tail_ratio = tail_pnls / tot_pos
            tail_metric = MetricStatus(value=round(tail_ratio, 4), status="VALID")
        else:
            tail_metric = MetricStatus(value=0.0, status="VALID")

        # Hurst Exponent
        if bar_ledger and len(bar_ledger) >= 50:
            closes_arr = np.array([b.close_price for b in bar_ledger], dtype=np.float64)
            h_val = cls._calc_hurst(closes_arr)
            hurst_metric = MetricStatus(value=round(h_val, 3), status="VALID")
        else:
            hurst_metric = MetricStatus(value=None, status="NOT_COMPUTABLE", reason="INSUFFICIENT_BARS_FOR_HURST")

        # Shannon Entropy
        if n_trades >= 15:
            ent = cls._calc_shannon_entropy(trade_returns)
            entropy_metric = MetricStatus(value=round(ent, 3), status="VALID")
        else:
            entropy_metric = MetricStatus(value=None, status="NOT_COMPUTABLE", reason="INSUFFICIENT_TRADES_FOR_ENTROPY")

        return ForensicPerformanceMetrics(
            total_trades=n_trades,
            winning_trades=win_count,
            losing_trades=loss_count,
            win_rate_pct=round(win_rate, 2),
            net_profit_usd=round(net_profit, 2),
            total_roi_pct=round(total_roi, 2),
            monthly_roi_pct=round(monthly_roi, 2),
            annualized_roi_pct=round(annual_roi, 2),
            profit_factor=pf_metric,
            expectancy_r=exp_metric,
            sharpe_ratio=sharpe_metric,
            sortino_ratio=sortino_metric,
            calmar_ratio=calmar_metric,
            deflated_sharpe_ratio=dsr_metric,
            max_drawdown_pct=max_drawdown_pct,
            max_drawdown_duration_bars=max_drawdown_duration,
            outlier_dependency_pct=outlier_metric,
            tail_gain_ratio=tail_metric,
            hurst_exponent=hurst_metric,
            shannon_entropy=entropy_metric,
        )

    @staticmethod
    def _calc_dsr(returns: np.ndarray, sharpe: float, num_trials: int) -> float:
        n = len(returns)
        mean_ret = float(np.mean(returns))
        std_ret = float(np.std(returns))
        if std_ret < 1e-8 or n < 5:
            return 0.0

        skew = float(np.mean(((returns - mean_ret) / std_ret) ** 3))
        kurt = float(np.mean(((returns - mean_ret) / std_ret) ** 4))

        var_sharpe = (1.0 + (0.5 * (sharpe ** 2)) - (skew * sharpe) + (((kurt - 3.0) / 4.0) * (sharpe ** 2))) / float(n)
        var_sharpe = max(1e-6, var_sharpe)

        euler_mascheroni = 0.5772156649
        if num_trials > 1:
            e_max_sharpe = ((1.0 - euler_mascheroni) * math.sqrt(2.0 * math.log(num_trials)) +
                            (euler_mascheroni / math.sqrt(2.0 * math.log(num_trials))))
        else:
            e_max_sharpe = 0.0

        dsr_stat = (sharpe - e_max_sharpe) / math.sqrt(var_sharpe)
        dsr_prob = 0.5 * (1.0 + math.erf(dsr_stat / math.sqrt(2.0)))
        return float(dsr_prob)

    @staticmethod
    def _calc_hurst(series: np.ndarray) -> float:
        """Cálculo exacto del Exponente de Hurst mediante Rescaled Range (R/S)."""
        n = len(series)
        if n < 50:
            return 0.50
        lags = [10, 20, 40, 80, 160]
        lags = [lag for lag in lags if lag < n // 2]
        if len(lags) < 2:
            return 0.50

        rs_values = []
        for lag in lags:
            diff = np.diff(series)
            sub_diffs = [diff[i:i + lag] for i in range(0, len(diff) - lag + 1, lag)]
            sub_rs = []
            for sub in sub_diffs:
                if len(sub) < lag:
                    continue
                mean_sub = np.mean(sub)
                dev = sub - mean_sub
                cum_dev = np.cumsum(dev)
                r = np.max(cum_dev) - np.min(cum_dev)
                s = np.std(sub)
                if s > 1e-8:
                    sub_rs.append(r / s)
            if sub_rs:
                rs_values.append(np.mean(sub_rs))

        if len(rs_values) < 2:
            return 0.50

        poly = np.polyfit(np.log(lags[:len(rs_values)]), np.log(rs_values), 1)
        return float(min(1.0, max(0.0, poly[0])))

    @staticmethod
    def _calc_shannon_entropy(returns: np.ndarray, bins: int = 10) -> float:
        """Cálculo de la entropía de Shannon de la distribución de retornos."""
        hist, _ = np.histogram(returns, bins=bins, density=True)
        hist = hist[hist > 0]
        if len(hist) == 0:
            return 0.0
        prob = hist / np.sum(hist)
        return float(-np.sum(prob * np.log2(prob)))
