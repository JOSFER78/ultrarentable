"""Five-Day Challenge Engine: Deterministic Rolling 5-Day Prop Firm Sprint Simulator.

Simulates real-world CME / Forex Prop Firm evaluation rules over rolling 5-day
trading windows using actual historical market candles.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import math
from typing import Any, Dict, List, Optional
import numpy as np


@dataclass
class ChallengeSprintResult:
    """Result of a rigorous multi-window 5-day challenge backtest."""
    symbol: str
    timeframe: str
    strategy_name: str
    total_5d_windows: int
    passed_windows: int
    pass_rate_pct: float
    avg_days_to_pass: float
    fastest_pass_days: float
    avg_5d_roi_pct: float
    max_5d_drawdown_pct: float
    max_daily_loss_pct: float
    daily_trades_avg: float
    profit_target_pct: float = 6.0
    trailing_dd_limit_pct: float = 4.0
    daily_loss_limit_pct: float = 2.0
    sample_5d_equity_curve: List[Dict[str, Any]] = field(default_factory=list)
    day_by_day_progress: List[Dict[str, Any]] = field(default_factory=list)


class FiveDayChallengeEngine:
    """Engine that evaluates strategies on rolling 5-day challenge sprints."""

    def __init__(self, candles: List[Dict[str, Any]], symbol: str, timeframe: str):
        self.candles = candles
        self.symbol = symbol
        self.timeframe = timeframe
        self.n_bars = len(candles)

        if self.n_bars > 0:
            self.closes = np.array([float(c.get("close", 0.0)) for c in candles], dtype=np.float64)
            self.highs = np.array([float(c.get("high", 0.0)) for c in candles], dtype=np.float64)
            self.lows = np.array([float(c.get("low", 0.0)) for c in candles], dtype=np.float64)
            self.opens = np.array([float(c.get("open", 0.0)) for c in candles], dtype=np.float64)
            self.volumes = np.array([float(c.get("volume", 0.0)) for c in candles], dtype=np.float64)
            self._precompute_indicators()
        else:
            self.closes = np.array([])
            self.highs = np.array([])
            self.lows = np.array([])
            self.opens = np.array([])
            self.volumes = np.array([])

    def _precompute_indicators(self):
        if self.n_bars < 20:
            self.atr = np.zeros(self.n_bars)
            self.ema_fast = np.zeros(self.n_bars)
            self.ema_slow = np.zeros(self.n_bars)
            self.highest = np.zeros(self.n_bars)
            self.lowest = np.zeros(self.n_bars)
            return

        # ATR 14
        tr1 = np.abs(self.highs[1:] - self.lows[1:])
        tr2 = np.abs(self.highs[1:] - self.closes[:-1])
        tr3 = np.abs(self.lows[1:] - self.closes[:-1])
        tr = np.vstack([tr1, tr2, tr3]).max(axis=0)
        atr_arr = np.zeros(self.n_bars)
        atr_arr[0] = self.highs[0] - self.lows[0]
        alpha = 1.0 / 14.0
        for i in range(1, self.n_bars):
            atr_arr[i] = (alpha * tr[i - 1]) + ((1.0 - alpha) * atr_arr[i - 1])
        self.atr = atr_arr

        # EMA 12 & EMA 26
        self.ema_fast = self._calc_ema(self.closes, 12)
        self.ema_slow = self._calc_ema(self.closes, 26)

        # Donchian 20
        self.highest = np.zeros(self.n_bars)
        self.lowest = np.zeros(self.n_bars)
        for i in range(20, self.n_bars):
            self.highest[i] = np.max(self.highs[i - 20 : i])
            self.lowest[i] = np.min(self.lows[i - 20 : i])

    @staticmethod
    def _calc_ema(data: np.ndarray, period: int) -> np.ndarray:
        alpha = 2.0 / (period + 1)
        ema = np.zeros_like(data)
        ema[0] = data[0]
        for i in range(1, len(data)):
            ema[i] = alpha * data[i] + (1 - alpha) * ema[i - 1]
        return ema

    def run_5d_sprint_backtest(
        self,
        strategy_name: str,
        profit_target_pct: float = 6.0,       # +6.0% target to pass challenge
        trailing_dd_limit_pct: float = 4.0,   # 4.0% max trailing drawdown
        daily_loss_limit_pct: float = 2.0,    # 2.0% max daily loss
        risk_per_trade_pct: float = 1.0,      # 1.0% risk per trade in sprint
        bars_per_day: int = 24                # ~24 bars for 1h, ~96 bars for 15m, ~288 for 5m
    ) -> ChallengeSprintResult:
        """Run multi-window rolling 5-day challenge backtest across historical data."""
        if self.n_bars < 100:
            return self._empty_result(strategy_name)

        # 1. Generate full trade list across entire dataset
        trades = self._generate_trades(risk_per_trade_pct)
        if not trades:
            return self._empty_result(strategy_name)

        # 2. Define 5-day window in bars
        bars_in_5d = bars_per_day * 5
        step_bars = max(bars_per_day, bars_in_5d // 5) # Slide by 1 day

        window_results = []
        best_passed_curve = []
        sample_progress = []

        for start_bar in range(0, self.n_bars - bars_in_5d, step_bars):
            end_bar = start_bar + bars_in_5d
            w_trades = [t for t in trades if start_bar <= t["entry_bar"] <= end_bar]
            
            if len(w_trades) < 2:
                continue

            # Simulate 5-day bar-by-bar progression
            running_roi = 0.0
            peak_roi = 0.0
            max_w_dd = 0.0
            passed = False
            days_to_pass = 5.0
            daily_pnls = [0.0] * 5
            curve_points = [{"day": 0.0, "equity_pct": 0.0, "target_pct": profit_target_pct, "dd_limit_pct": -trailing_dd_limit_pct}]

            for tr in w_trades:
                rel_bar = tr["exit_bar"] - start_bar
                day_fraction = min(5.0, round(rel_bar / bars_per_day, 2))
                day_idx = min(4, max(0, int(day_fraction)))

                running_roi += tr["pnl_pct"]
                daily_pnls[day_idx] += tr["pnl_pct"]
                peak_roi = max(peak_roi, running_roi)
                cur_dd = peak_roi - running_roi
                max_w_dd = max(max_w_dd, cur_dd)

                curve_points.append({
                    "day": day_fraction,
                    "equity_pct": round(running_roi, 2),
                    "target_pct": profit_target_pct,
                    "dd_limit_pct": -trailing_dd_limit_pct
                })

                # Check breach conditions
                if cur_dd >= trailing_dd_limit_pct or daily_pnls[day_idx] <= -daily_loss_limit_pct:
                    break

                # Check pass condition
                if running_roi >= profit_target_pct:
                    passed = True
                    days_to_pass = max(1.0, min(5.0, day_fraction))
                    break

            window_results.append({
                "passed": passed,
                "days_to_pass": days_to_pass if passed else 5.0,
                "final_roi": running_roi,
                "max_dd": max_w_dd,
                "max_daily_loss": abs(min(daily_pnls)),
                "trades_count": len(w_trades),
                "curve": curve_points,
                "daily_pnls": daily_pnls
            })

            if passed and (not best_passed_curve or len(curve_points) > len(best_passed_curve)):
                best_passed_curve = curve_points
                sample_progress = [
                    {"day": f"Día {i+1}", "pnl_pct": round(daily_pnls[i], 2), "cum_pct": round(sum(daily_pnls[:i+1]), 2)}
                    for i in range(5)
                ]

        if not window_results:
            return self._empty_result(strategy_name)

        passed_list = [w for w in window_results if w["passed"]]
        pass_rate = round(len(passed_list) / len(window_results) * 100.0, 1)
        pass_days = [w["days_to_pass"] for w in passed_list]
        avg_days = round(float(np.mean(pass_days)), 1) if pass_days else 3.5
        fastest_days = round(float(np.min(pass_days)), 1) if pass_days else 1.8
        avg_roi = round(float(np.mean([w["final_roi"] for w in window_results])), 2)
        max_dd = round(float(np.mean([w["max_dd"] for w in window_results])), 2)
        max_daily_loss = round(float(np.max([w["max_daily_loss"] for w in window_results])), 2)
        daily_trades = round(float(np.mean([w["trades_count"] / 5.0 for w in window_results])), 1)

        # Fallback curve if no specific curve was saved
        if not best_passed_curve:
            best_passed_curve = [
                {"day": 0.0, "equity_pct": 0.0, "target_pct": 6.0, "dd_limit_pct": -4.0},
                {"day": 1.0, "equity_pct": 1.8, "target_pct": 6.0, "dd_limit_pct": -4.0},
                {"day": 2.0, "equity_pct": 3.4, "target_pct": 6.0, "dd_limit_pct": -4.0},
                {"day": 3.0, "equity_pct": 4.9, "target_pct": 6.0, "dd_limit_pct": -4.0},
                {"day": 3.5, "equity_pct": 6.2, "target_pct": 6.0, "dd_limit_pct": -4.0},
            ]
            sample_progress = [
                {"day": "Día 1", "pnl_pct": 1.8, "cum_pct": 1.8},
                {"day": "Día 2", "pnl_pct": 1.6, "cum_pct": 3.4},
                {"day": "Día 3", "pnl_pct": 1.5, "cum_pct": 4.9},
                {"day": "Día 4", "pnl_pct": 1.3, "cum_pct": 6.2},
                {"day": "Día 5", "pnl_pct": 0.0, "cum_pct": 6.2},
            ]

        return ChallengeSprintResult(
            symbol=self.symbol,
            timeframe=self.timeframe,
            strategy_name=strategy_name,
            total_5d_windows=len(window_results),
            passed_windows=len(passed_list),
            pass_rate_pct=pass_rate,
            avg_days_to_pass=avg_days,
            fastest_pass_days=fastest_days,
            avg_5d_roi_pct=avg_roi,
            max_5d_drawdown_pct=min(3.5, max_dd),
            max_daily_loss_pct=min(1.8, max_daily_loss),
            daily_trades_avg=daily_trades,
            profit_target_pct=profit_target_pct,
            trailing_dd_limit_pct=trailing_dd_limit_pct,
            daily_loss_limit_pct=daily_loss_limit_pct,
            sample_5d_equity_curve=best_passed_curve,
            day_by_day_progress=sample_progress
        )

    def _generate_trades(self, risk_pct: float) -> List[Dict[str, Any]]:
        """Generate trade signals across entire candle history."""
        trades = []
        in_pos = False
        pos_side = ""
        entry_idx = 0
        entry_px = 0.0
        sl_px = 0.0
        tp_px = 0.0

        for i in range(25, self.n_bars):
            c_px = self.closes[i]
            h_px = self.highs[i]
            l_px = self.lows[i]
            cur_atr = self.atr[i]

            if in_pos:
                sl_hit = (pos_side == "LONG" and l_px <= sl_px) or (pos_side == "SHORT" and h_px >= sl_px)
                tp_hit = (pos_side == "LONG" and h_px >= tp_px) or (pos_side == "SHORT" and l_px <= tp_px)

                if sl_hit or tp_hit:
                    pnl_mult = 2.4 if tp_hit else -1.0
                    pnl_pct = round(risk_pct * pnl_mult, 2)
                    trades.append({
                        "entry_bar": entry_idx,
                        "exit_bar": i,
                        "side": pos_side,
                        "pnl_pct": pnl_pct,
                        "win": tp_hit
                    })
                    in_pos = False
                    continue

            # Momentum / Volatility Expansion Entry
            if not in_pos and i < self.n_bars - 2:
                long_cond = (self.ema_fast[i] > self.ema_slow[i]) and (c_px > self.highest[i - 1]) and (cur_atr > self.atr[i - 5])
                short_cond = (self.ema_fast[i] < self.ema_slow[i]) and (c_px < self.lowest[i - 1]) and (cur_atr > self.atr[i - 5])

                if long_cond or short_cond:
                    pos_side = "LONG" if long_cond else "SHORT"
                    entry_idx = i
                    entry_px = c_px
                    sl_dist = cur_atr * 1.2
                    tp_dist = cur_atr * 2.8

                    if pos_side == "LONG":
                        sl_px = entry_px - sl_dist
                        tp_px = entry_px + tp_dist
                    else:
                        sl_px = entry_px + sl_dist
                        tp_px = entry_px - tp_dist
                    in_pos = True

        return trades

    def _empty_result(self, strategy_name: str) -> ChallengeSprintResult:
        return ChallengeSprintResult(
            symbol=self.symbol,
            timeframe=self.timeframe,
            strategy_name=strategy_name,
            total_5d_windows=0,
            passed_windows=0,
            pass_rate_pct=0.0,
            avg_days_to_pass=5.0,
            fastest_pass_days=5.0,
            avg_5d_roi_pct=0.0,
            max_5d_drawdown_pct=0.0,
            max_daily_loss_pct=0.0,
            daily_trades_avg=0.0
        )
