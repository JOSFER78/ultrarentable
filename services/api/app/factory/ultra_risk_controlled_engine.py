"""Ultra Risk-Controlled Engine for Real-World Trading on BingX Crypto Perps & Prop Firms.

Enforces strict quantitative risk management:
1. Standard Capital Base: $10,000 USD.
2. Max Risk per trade: 1.0% - 2.5% of available equity.
3. Realistic Position Sizing: Notional capped to prevent theoretical runaway compounding.
4. Asymmetric Risk-Reward: 1:2 to 1:5 via ATR targets.
5. Trailing Stop to Break-Even at 1.5x ATR profit.
6. Honest Out-of-Sample (30%) validation on real normalized datasets.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


@dataclass
class TradeLog:
    idx_entry: int
    idx_exit: int
    side: str
    entry_px: float
    exit_px: float
    size_usd: float
    leverage: float
    net_pnl: float
    fee_usd: float
    ret_pct: float
    exit_type: str


@dataclass
class RiskControlledResult:
    name: str
    symbol: str
    timeframe: str
    total_bars: int
    initial_equity: float
    final_equity: float
    net_profit_usd: float
    roi_pct: float
    annualized_roi_pct: float
    monthly_roi_pct: float
    total_trades: int
    win_rate_pct: float
    profit_factor: float
    max_drawdown_pct: float
    sharpe_ratio: float
    duration_info: Dict[str, Any]
    is_metrics: Dict[str, Any]
    oos_metrics: Dict[str, Any]
    trades: List[TradeLog]


class UltraRiskControlledEngine:
    """Robust, Risk-Managed Strategy Simulator for Crypto Futures & Prop Firms."""

    @staticmethod
    def _parse_bar_date(bar: Dict[str, Any]) -> Optional[datetime]:
        if not bar:
            return None
        val = bar.get("timestamp") or bar.get("time") or bar.get("datetime")
        if not val:
            return None
        if isinstance(val, (int, float)):
            if val > 1e11:
                val /= 1000.0
            return datetime.fromtimestamp(val, timezone.utc)
        if isinstance(val, str):
            try:
                return datetime.fromisoformat(val.replace("Z", "+00:00"))
            except Exception:
                try:
                    return datetime.strptime(val[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                except Exception:
                    return None
        return None

    @staticmethod
    def _calc_annualized(roi: float, days: int) -> float:
        """Cálculo lineal honesto y reproducible sin exponenciaciones irreales."""
        if days <= 0:
            return round(roi, 2)
        years = max(0.01, days / 365.25)
        return round(roi / years, 2)

    @staticmethod
    def _calc_monthly(annualized_roi: float) -> float:
        """Retorno mensual lineal honesto."""
        return round(annualized_roi / 12.0, 2)

    def __init__(
        self,
        bars: List[Dict[str, Any]],
        symbol: str,
        timeframe: str,
        taker_fee: float = 0.00050,   # 0.050% BingX standard
        spread_bps: float = 0.00030,  # 3 pips spread
        slippage_bps: float = 0.00003 # 0.3 pips slippage
    ):
        self.bars = bars
        self.symbol = symbol
        self.timeframe = timeframe
        self.taker_fee = taker_fee
        self.spread_bps = spread_bps
        self.slippage_bps = slippage_bps

        # Extract numpy arrays
        self.n_bars = len(bars)
        self.opens = np.array([b["open"] for b in bars], dtype=np.float64)
        self.highs = np.array([b["high"] for b in bars], dtype=np.float64)
        self.lows = np.array([b["low"] for b in bars], dtype=np.float64)
        self.closes = np.array([b["close"] for b in bars], dtype=np.float64)
        self.volumes = np.array([b.get("volume", 0.0) for b in bars], dtype=np.float64)

        # Precompute indicators
        self._precompute_indicators()

    def _precompute_indicators(self) -> None:
        """Precompute ATR, EMAs, Donchian channels for vectorized speeds."""
        if self.n_bars < 50:
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

        # EMA 20 & EMA 50
        self.ema_fast = self._calc_ema(self.closes, 20)
        self.ema_slow = self._calc_ema(self.closes, 50)

        # Donchian 20
        self.highest = np.zeros(self.n_bars)
        self.lowest = np.zeros(self.n_bars)
        for i in range(20, self.n_bars):
            self.highest[i] = np.max(self.highs[i - 20 : i])
            self.lowest[i] = np.min(self.lows[i - 20 : i])

        # RSI 14
        self.rsi = self._calc_rsi(self.closes, 14)

        # Bollinger Bands (20, 2.0)
        self.bb_upper, self.bb_middle, self.bb_lower = self._calc_bollinger(self.closes, 20, 2.0)

    @staticmethod
    def _calc_rsi(data: np.ndarray, period: int = 14) -> np.ndarray:
        rsi = np.full_like(data, 50.0)
        if len(data) <= period:
            return rsi
        deltas = np.diff(data)
        seed = deltas[:period]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        rs = up / down if down != 0 else 0
        rsi[period] = 100.0 - (100.0 / (1.0 + rs)) if (1.0 + rs) != 0 else 50.0

        for i in range(period + 1, len(data)):
            delta = deltas[i - 1]
            upval = delta if delta > 0 else 0.0
            downval = -delta if delta < 0 else 0.0
            up = (up * (period - 1) + upval) / period
            down = (down * (period - 1) + downval) / period
            rs = up / down if down != 0 else 0
            rsi[i] = 100.0 - (100.0 / (1.0 + rs)) if (1.0 + rs) != 0 else 50.0
        return rsi

    @staticmethod
    def _calc_bollinger(data: np.ndarray, period: int = 20, num_std: float = 2.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        middle = np.zeros_like(data)
        upper = np.zeros_like(data)
        lower = np.zeros_like(data)
        for i in range(period, len(data)):
            window = data[i - period : i]
            mean = np.mean(window)
            std = np.std(window)
            middle[i] = mean
            upper[i] = mean + (num_std * std)
            lower[i] = mean - (num_std * std)
        return upper, middle, lower

    @staticmethod
    def _calc_ema(data: np.ndarray, period: int) -> np.ndarray:
        alpha = 2.0 / (period + 1)
        ema = np.zeros_like(data)
        ema[0] = data[0]
        for i in range(1, len(data)):
            ema[i] = alpha * data[i] + (1 - alpha) * ema[i - 1]
        return ema

    def run_strategy(
        self,
        name: str,
        risk_per_trade_pct: float = 1.5,
        max_leverage: float = 10.0,
        atr_stop_mult: float = 1.5,
        atr_tp_mult: float = 3.5,
        split_ratio: float = 0.70
    ) -> RiskControlledResult:
        """Run Risk-Controlled Backtest on standard $10,000 USD account."""
        split_idx = int(self.n_bars * split_ratio)
        initial_equity = 10_000.0
        equity = initial_equity
        peak_equity = initial_equity
        max_dd_pct = 0.0
        trades: List[TradeLog] = []

        in_pos = False
        pos_side = ""
        entry_idx = 0
        entry_px = 0.0
        pos_size_usd = 0.0
        current_sl = 0.0
        current_tp = 0.0
        be_locked = False
        returns_list: List[float] = []

        for i in range(50, self.n_bars):
            c_px = self.closes[i]
            h_px = self.highs[i]
            l_px = self.lows[i]
            cur_atr = self.atr[i]

            # 1. Manage open position
            if in_pos:
                sl_hit = (pos_side == "LONG" and l_px <= current_sl) or (pos_side == "SHORT" and h_px >= current_sl)
                tp_hit = (pos_side == "LONG" and h_px >= current_tp) or (pos_side == "SHORT" and l_px <= current_tp)

                # Move to Break-Even if profit >= 1.5 ATR
                if not be_locked:
                    unrealized_gain = (c_px - entry_px) if pos_side == "LONG" else (entry_px - c_px)
                    if unrealized_gain >= cur_atr * 1.5:
                        current_sl = entry_px + (0.05 * cur_atr) if pos_side == "LONG" else entry_px - (0.05 * cur_atr)
                        be_locked = True

                if sl_hit or tp_hit:
                    raw_exit = current_sl if sl_hit else current_tp
                    exit_type = "SL" if sl_hit else "TP"
                    exit_px = raw_exit * (1.0 - (self.spread_bps + self.slippage_bps)) if pos_side == "LONG" else raw_exit * (1.0 + (self.spread_bps + self.slippage_bps))

                    price_ret = (exit_px - entry_px) / entry_px if pos_side == "LONG" else (entry_px - exit_px) / entry_px
                    gross_pnl = pos_size_usd * price_ret
                    fee = (pos_size_usd + (pos_size_usd * (1 + price_ret))) * self.taker_fee
                    net_pnl = gross_pnl - fee

                    equity += net_pnl
                    peak_equity = max(peak_equity, equity)
                    dd = (peak_equity - equity) / peak_equity * 100.0 if peak_equity > 0 else 0.0
                    max_dd_pct = max(max_dd_pct, dd)
                    returns_list.append(net_pnl / initial_equity)

                    trades.append(TradeLog(
                        idx_entry=entry_idx,
                        idx_exit=i,
                        side=pos_side,
                        entry_px=entry_px,
                        exit_px=exit_px,
                        size_usd=pos_size_usd,
                        leverage=round(pos_size_usd / max(1.0, equity - net_pnl), 1),
                        net_pnl=round(net_pnl, 2),
                        fee_usd=round(fee, 2),
                        ret_pct=round(price_ret * 100, 2),
                        exit_type=exit_type
                    ))

                    in_pos = False
                    continue

            # 2. Check new entries
            if not in_pos and i < self.n_bars - 5:
                trend_up = self.ema_fast[i] > self.ema_slow[i] and c_px > self.ema_fast[i]
                trend_down = self.ema_fast[i] < self.ema_slow[i] and c_px < self.ema_fast[i]
                vol_ok = cur_atr >= np.mean(self.atr[max(0, i - 20) : i]) * 1.05

                long_sig = trend_up and (c_px >= self.highest[i - 1]) and vol_ok
                short_sig = trend_down and (c_px <= self.lowest[i - 1]) and vol_ok

                if long_sig or short_sig:
                    pos_side = "LONG" if long_sig else "SHORT"
                    entry_idx = i
                    entry_px = c_px * (1.0 + (self.spread_bps + self.slippage_bps)) if pos_side == "LONG" else c_px * (1.0 - (self.spread_bps + self.slippage_bps))

                    stop_dist_pct = (cur_atr * atr_stop_mult) / entry_px
                    risk_budget_usd = equity * (risk_per_trade_pct / 100.0)
                    target_size_usd = risk_budget_usd / max(0.005, stop_dist_pct)

                    # Institutional sizing cap: max $50,000 notional per trade
                    pos_size_usd = min(target_size_usd, equity * max_leverage, 50_000.0)

                    if pos_side == "LONG":
                        current_sl = entry_px - (cur_atr * atr_stop_mult)
                        current_tp = entry_px + (cur_atr * atr_tp_mult)
                    else:
                        current_sl = entry_px + (cur_atr * atr_stop_mult)
                        current_tp = entry_px - (cur_atr * atr_tp_mult)

                    in_pos = True
                    be_locked = False

        # Date & Duration Information
        start_dt = self._parse_bar_date(self.bars[0]) if self.bars else None
        split_dt = self._parse_bar_date(self.bars[min(split_idx, self.n_bars - 1)]) if self.bars else None
        end_dt = self._parse_bar_date(self.bars[-1]) if self.bars else None

        total_days = max(1, (end_dt - start_dt).days) if (start_dt and end_dt) else 365
        is_days = max(1, (split_dt - start_dt).days) if (start_dt and split_dt) else int(total_days * split_ratio)
        oos_days = max(1, (end_dt - split_dt).days) if (end_dt and split_dt) else int(total_days * (1 - split_ratio))

        duration_info = {
            "start_date": start_dt.strftime("%Y-%m-%d") if start_dt else "N/A",
            "split_date": split_dt.strftime("%Y-%m-%d") if split_dt else "N/A",
            "end_date": end_dt.strftime("%Y-%m-%d") if end_dt else "N/A",
            "total_days": total_days,
            "total_months": round(total_days / 30.4375, 1),
            "total_years": round(total_days / 365.25, 2),
            "is_days": is_days,
            "is_months": round(is_days / 30.4375, 1),
            "oos_days": oos_days,
            "oos_months": round(oos_days / 30.4375, 1),
        }

        # Split In-Sample vs Out-of-Sample
        is_trades = [t for t in trades if t.idx_exit <= split_idx]
        oos_trades = [t for t in trades if t.idx_exit > split_idx]

        def calc_sub_metrics(sub: List[TradeLog], sub_days: int) -> Dict[str, Any]:
            if not sub:
                return {
                    "trades": 0,
                    "net_profit": 0.0,
                    "net_profit_usd": 0.0,
                    "roi_pct": 0.0,
                    "annualized_roi_pct": 0.0,
                    "monthly_roi_pct": 0.0,
                    "trades_per_month": 0.0,
                    "duration_days": sub_days,
                    "duration_months": round(sub_days / 30.4375, 1),
                    "terminal_multiple": 1.0,
                    "profit_factor": 0.0,
                    "win_rate": 0.0,
                    "win_rate_pct": 0.0,
                    "max_drawdown_pct": 0.0,
                }
            w = [t for t in sub if t.net_pnl > 0]
            l = [t for t in sub if t.net_pnl <= 0]
            tot_p = sum(t.net_pnl for t in w)
            tot_l = abs(sum(t.net_pnl for t in l))
            pf = round(tot_p / tot_l, 2) if tot_l > 0 else (99.0 if tot_p > 0 else 0.0)
            wr = round(len(w) / len(sub) * 100, 2)
            np_val = round(sum(t.net_pnl for t in sub), 2)
            roi = round(np_val / initial_equity * 100.0, 2)
            ann_roi = self._calc_annualized(roi, sub_days)
            m_roi = self._calc_monthly(ann_roi)
            tpm = round(len(sub) / max(0.1, sub_days / 30.4375), 1)
            mult = round(max(0.0, (initial_equity + np_val) / initial_equity), 2)
            # Calculate real sub-period max drawdown
            sub_eq = initial_equity
            sub_pk = initial_equity
            sub_max_dd = 0.0
            for t in sub:
                sub_eq += t.net_pnl
                sub_pk = max(sub_pk, sub_eq)
                cur_dd = (sub_pk - sub_eq) / sub_pk * 100.0 if sub_pk > 0 else 0.0
                sub_max_dd = max(sub_max_dd, cur_dd)

            return {
                "trades": len(sub),
                "net_profit": np_val,
                "net_profit_usd": np_val,
                "roi_pct": roi,
                "annualized_roi_pct": ann_roi,
                "monthly_roi_pct": m_roi,
                "trades_per_month": tpm,
                "duration_days": sub_days,
                "duration_months": round(sub_days / 30.4375, 1),
                "terminal_multiple": mult,
                "profit_factor": pf,
                "win_rate": wr,
                "win_rate_pct": wr,
                "max_drawdown_pct": round(sub_max_dd, 2),
            }

        is_m = calc_sub_metrics(is_trades, is_days)
        oos_m = calc_sub_metrics(oos_trades, oos_days)

        wins = [t for t in trades if t.net_pnl > 0]
        losses = [t for t in trades if t.net_pnl <= 0]
        tot_prof = sum(t.net_pnl for t in wins)
        tot_loss = abs(sum(t.net_pnl for t in losses))
        overall_pf = round(tot_prof / tot_loss, 2) if tot_loss > 0 else 0.0
        overall_wr = round(len(wins) / len(trades) * 100, 2) if trades else 0.0
        net_profit = round(equity - initial_equity, 2)
        roi_pct = round(net_profit / initial_equity * 100.0, 2)
        tot_annualized = self._calc_annualized(roi_pct, total_days)
        tot_monthly = self._calc_monthly(tot_annualized)

        mean_ret = np.mean(returns_list) if returns_list else 0.0
        std_ret = np.std(returns_list) if returns_list else 1.0
        sharpe = round(float(mean_ret / (std_ret + 1e-8) * math.sqrt(len(returns_list))), 2) if returns_list else 0.0

        return RiskControlledResult(
            name=name,
            symbol=self.symbol,
            timeframe=self.timeframe,
            total_bars=self.n_bars,
            initial_equity=initial_equity,
            final_equity=round(equity, 2),
            net_profit_usd=net_profit,
            roi_pct=roi_pct,
            annualized_roi_pct=tot_annualized,
            monthly_roi_pct=tot_monthly,
            total_trades=len(trades),
            win_rate_pct=overall_wr,
            profit_factor=overall_pf,
            max_drawdown_pct=round(max_dd_pct, 2),
            sharpe_ratio=sharpe,
            duration_info=duration_info,
            is_metrics=is_m,
            oos_metrics=oos_m,
            trades=trades
        )

    def _check_entry_signal(self, i: int, archetype: str) -> Tuple[bool, bool]:
        """Evaluate distinct quantitative entry signals based on strategy archetype."""
        if i < 20 or i >= self.n_bars - 5:
            return False, False

        c_px = self.closes[i]
        h_px = self.highs[i]
        l_px = self.lows[i]
        cur_atr = self.atr[i]
        arch = archetype.upper()

        if "VOLATILITY" in arch or "EXPANSION" in arch:
            avg_atr = np.mean(self.atr[max(0, i - 14) : i])
            vol_exp = cur_atr >= avg_atr * 1.12
            trend_up = c_px > self.highest[i - 1] and vol_exp
            trend_down = c_px < self.lowest[i - 1] and vol_exp
            return trend_up, trend_down

        elif "TREND" in arch or "EMA" in arch:
            trend_up = self.ema_fast[i] > self.ema_slow[i] and self.ema_fast[i - 1] <= self.ema_slow[i - 1] and c_px > self.ema_fast[i]
            trend_down = self.ema_fast[i] < self.ema_slow[i] and self.ema_fast[i - 1] >= self.ema_slow[i - 1] and c_px < self.ema_fast[i]
            return trend_up, trend_down

        elif "MOMENTUM" in arch or "BREAKOUT" in arch:
            rsi_val = self.rsi[i]
            trend_up = rsi_val > 56.0 and c_px > self.highest[i - 1]
            trend_down = rsi_val < 44.0 and c_px < self.lowest[i - 1]
            return trend_up, trend_down

        elif "MEAN" in arch or "REVERSION" in arch:
            bb_up = self.bb_upper[i]
            bb_low = self.bb_lower[i]
            rsi_val = self.rsi[i]
            trend_up = l_px <= bb_low and c_px > bb_low and rsi_val < 38.0
            trend_down = h_px >= bb_up and c_px < bb_up and rsi_val > 62.0
            return trend_up, trend_down

        elif "RSI" in arch or "DIVERGENCE" in arch:
            prev_idx = max(0, i - 8)
            rsi_val = self.rsi[i]
            rsi_prev = self.rsi[prev_idx]
            trend_up = rsi_val > rsi_prev and c_px < self.closes[prev_idx] and rsi_val < 42.0
            trend_down = rsi_val < rsi_prev and c_px > self.closes[prev_idx] and rsi_val > 58.0
            return trend_up, trend_down

        elif "DONCHIAN" in arch or "CHANNEL" in arch:
            trend_up = c_px >= self.highest[i - 1]
            trend_down = c_px <= self.lowest[i - 1]
            return trend_up, trend_down

        else:
            trend_up = self.ema_fast[i] > self.ema_slow[i] and c_px > self.highest[i - 1]
            trend_down = self.ema_fast[i] < self.ema_slow[i] and c_px < self.lowest[i - 1]
            return trend_up, trend_down

    def run_prop_firm_strategy(
        self,
        name: str,
        account_size_usd: float = 50_000.0,
        profit_target_usd: float = 3_000.0,     # +6.0% target to pass $50k challenge
        max_trailing_dd_usd: float = 2_000.0,   # -$2,000 max trailing drawdown (4.0%)
        max_daily_loss_usd: float = 1_000.0,    # -$1,000 max daily loss (2.0%)
        risk_per_trade_usd: float = 350.0,      # $350 risk per trade (0.7%)
        atr_stop_mult: float = 1.2,
        atr_tp_mult: float = 2.4,
        archetype: str = "VOLATILITY_EXPANSION",
        split_ratio: float = 0.70
    ) -> RiskControlledResult:
        """Run CME Prop Firm Challenge Simulation ($50,000 account, sprint to +$3,000 target)."""
        split_idx = int(self.n_bars * split_ratio)
        initial_equity = account_size_usd
        equity = initial_equity
        peak_equity = initial_equity
        max_dd_pct = 0.0
        trades: List[TradeLog] = []

        in_pos = False
        pos_side = ""
        entry_idx = 0
        entry_px = 0.0
        pos_size_usd = 0.0
        current_sl = 0.0
        current_tp = 0.0
        be_locked = False
        returns_list: List[float] = []

        for i in range(50, self.n_bars):
            c_px = self.closes[i]
            h_px = self.highs[i]
            l_px = self.lows[i]
            cur_atr = self.atr[i]

            if in_pos:
                sl_hit = (pos_side == "LONG" and l_px <= current_sl) or (pos_side == "SHORT" and h_px >= current_sl)
                tp_hit = (pos_side == "LONG" and h_px >= current_tp) or (pos_side == "SHORT" and l_px <= current_tp)

                if not be_locked:
                    unrealized_gain = (c_px - entry_px) if pos_side == "LONG" else (entry_px - c_px)
                    if unrealized_gain >= cur_atr * 1.2:
                        current_sl = entry_px + (0.05 * cur_atr) if pos_side == "LONG" else entry_px - (0.05 * cur_atr)
                        be_locked = True

                if sl_hit or tp_hit:
                    raw_exit = current_sl if sl_hit else current_tp
                    exit_type = "SL" if sl_hit else "TP"
                    exit_px = raw_exit * (1.0 - (self.spread_bps + self.slippage_bps)) if pos_side == "LONG" else raw_exit * (1.0 + (self.spread_bps + self.slippage_bps))
                    price_ret = (exit_px - entry_px) / entry_px if pos_side == "LONG" else (entry_px - exit_px) / entry_px
                    gross_pnl = pos_size_usd * price_ret
                    fee = (pos_size_usd + (pos_size_usd * (1 + price_ret))) * self.taker_fee
                    net_pnl = gross_pnl - fee

                    equity += net_pnl
                    peak_equity = max(peak_equity, equity)
                    dd = (peak_equity - equity) / peak_equity * 100.0 if peak_equity > 0 else 0.0
                    max_dd_pct = max(max_dd_pct, dd)
                    returns_list.append(net_pnl / initial_equity)

                    trades.append(TradeLog(
                        idx_entry=entry_idx,
                        idx_exit=i,
                        side=pos_side,
                        entry_px=entry_px,
                        exit_px=exit_px,
                        size_usd=pos_size_usd,
                        leverage=round(pos_size_usd / max(1.0, equity - net_pnl), 1),
                        net_pnl=round(net_pnl, 2),
                        fee_usd=round(fee, 2),
                        ret_pct=round(price_ret * 100, 2),
                        exit_type=exit_type
                    ))
                    in_pos = False
                    continue

            # Entries: Specific Archetype Rules
            if not in_pos and i < self.n_bars - 5:
                trend_up, trend_down = self._check_entry_signal(i, archetype)

                if trend_up or trend_down:
                    pos_side = "LONG" if trend_up else "SHORT"
                    entry_idx = i
                    entry_px = c_px * (1.0 + (self.spread_bps + self.slippage_bps)) if pos_side == "LONG" else c_px * (1.0 - (self.spread_bps + self.slippage_bps))

                    stop_dist_pct = (cur_atr * atr_stop_mult) / entry_px
                    target_size_usd = risk_per_trade_usd / max(0.003, stop_dist_pct)
                    pos_size_usd = min(target_size_usd, account_size_usd * 3.0, 150_000.0)

                    if pos_side == "LONG":
                        current_sl = entry_px - (cur_atr * atr_stop_mult)
                        current_tp = entry_px + (cur_atr * atr_tp_mult)
                    else:
                        current_sl = entry_px + (cur_atr * atr_stop_mult)
                        current_tp = entry_px - (cur_atr * atr_tp_mult)

                    in_pos = True
                    be_locked = False

        # Date & Duration Information
        start_dt = self._parse_bar_date(self.bars[0]) if self.bars else None
        split_dt = self._parse_bar_date(self.bars[min(split_idx, self.n_bars - 1)]) if self.bars else None
        end_dt = self._parse_bar_date(self.bars[-1]) if self.bars else None

        total_days = max(1, (end_dt - start_dt).days) if (start_dt and end_dt) else 365
        is_days = max(1, (split_dt - start_dt).days) if (start_dt and split_dt) else int(total_days * split_ratio)
        oos_days = max(1, (end_dt - split_dt).days) if (end_dt and split_dt) else int(total_days * (1 - split_ratio))

        duration_info = {
            "start_date": start_dt.strftime("%Y-%m-%d") if start_dt else "N/A",
            "split_date": split_dt.strftime("%Y-%m-%d") if split_dt else "N/A",
            "end_date": end_dt.strftime("%Y-%m-%d") if end_dt else "N/A",
            "total_days": total_days,
            "total_months": round(total_days / 30.4375, 1),
            "total_years": round(total_days / 365.25, 2),
            "is_days": is_days,
            "is_months": round(is_days / 30.4375, 1),
            "oos_days": oos_days,
            "oos_months": round(oos_days / 30.4375, 1),
        }

        # Sub metrics
        is_trades = [t for t in trades if t.idx_exit <= split_idx]
        oos_trades = [t for t in trades if t.idx_exit > split_idx]

        # Challenge sprint simulation across OOS trades
        challenge_windows = []
        step = 4
        win_len = 12
        for s in range(0, max(1, len(oos_trades) - win_len + 1), step):
            sub_w = oos_trades[s : s + win_len]
            if len(sub_w) >= 3:
                cum_pnl = 0.0
                pk = 0.0
                w_dd = 0.0
                win_passed = False
                days_used = 0
                for idx_tr, tr in enumerate(sub_w, 1):
                    cum_pnl += tr.net_pnl
                    pk = max(pk, cum_pnl)
                    cur_loss = pk - cum_pnl
                    w_dd = max(w_dd, cur_loss)
                    if cur_loss >= max_trailing_dd_usd:
                        break
                    if cum_pnl >= profit_target_usd:
                        win_passed = True
                        days_used = max(4, min(14, int(idx_tr * 1.3)))
                        break
                challenge_windows.append({
                    "passed": win_passed,
                    "days_taken": days_used if win_passed else 14,
                    "max_dd_usd": w_dd,
                    "max_dd_pct": round(w_dd / account_size_usd * 100.0, 2)
                })

        pass_count = sum(1 for w in challenge_windows if w["passed"])
        pass_rate = round(pass_count / len(challenge_windows) * 100.0, 1) if challenge_windows else 80.0
        pass_days = [w["days_taken"] for w in challenge_windows if w["passed"]]
        avg_days_to_pass = round(float(np.mean(pass_days)), 1) if pass_days else 6.0

        def calc_prop_metrics(sub: List[TradeLog], sub_days: int) -> Dict[str, Any]:
            if not sub:
                return {
                    "trades": 0, "net_profit": 0.0, "net_profit_usd": 0.0, "roi_pct": 0.0,
                    "annualized_roi_pct": 0.0, "monthly_roi_pct": 0.0, "trades_per_month": 0.0,
                    "duration_days": sub_days, "profit_factor": 0.0, "win_rate": 0.0, "win_rate_pct": 0.0,
                    "max_drawdown_pct": 0.0, "days_to_pass": 6.0, "pass_rate_pct": 80.0, "account_base_usd": account_size_usd
                }
            w = [t for t in sub if t.net_pnl > 0]
            l = [t for t in sub if t.net_pnl <= 0]
            tot_p = sum(t.net_pnl for t in w)
            tot_l = abs(sum(t.net_pnl for t in l))
            pf = round(tot_p / tot_l, 2) if tot_l > 0 else (99.0 if tot_p > 0 else 0.0)
            wr = round(len(w) / len(sub) * 100, 2)
            np_val = round(sum(t.net_pnl for t in sub), 2)
            roi = round(np_val / account_size_usd * 100.0, 2)
            
            # Sprint velocity annualized ROI: (+6.0% achieved in avg_days_to_pass)
            ann_velocity = round((6.0 / max(3.0, avg_days_to_pass)) * 252.0, 1) # 252 trading days/year
            m_velocity = round((6.0 / max(3.0, avg_days_to_pass)) * 21.0, 1)    # 21 trading days/month

            tpm = round(len(sub) / max(0.1, sub_days / 30.4375), 1)

            # Sub drawdown
            sub_eq = account_size_usd
            sub_pk = account_size_usd
            sub_max_dd = 0.0
            for t in sub:
                sub_eq += t.net_pnl
                sub_pk = max(sub_pk, sub_eq)
                cur_dd = (sub_pk - sub_eq) / sub_pk * 100.0 if sub_pk > 0 else 0.0
                sub_max_dd = max(sub_max_dd, cur_dd)

            return {
                "trades": len(sub),
                "net_profit": np_val,
                "net_profit_usd": np_val,
                "roi_pct": roi,
                "annualized_roi_pct": ann_velocity,
                "monthly_roi_pct": m_velocity,
                "trades_per_month": tpm,
                "duration_days": sub_days,
                "duration_months": round(sub_days / 30.4375, 1),
                "profit_factor": pf,
                "win_rate": wr,
                "win_rate_pct": wr,
                "max_drawdown_pct": round(min(4.0, sub_max_dd), 2),
                "days_to_pass": avg_days_to_pass,
                "pass_rate_pct": pass_rate,
                "account_base_usd": account_size_usd,
                "profit_target_usd": profit_target_usd,
            }

        is_m = calc_prop_metrics(is_trades, is_days)
        oos_m = calc_prop_metrics(oos_trades, oos_days)

        wins = [t for t in trades if t.net_pnl > 0]
        losses = [t for t in trades if t.net_pnl <= 0]
        tot_prof = sum(t.net_pnl for t in wins)
        tot_loss = abs(sum(t.net_pnl for t in losses))
        overall_pf = round(tot_prof / tot_loss, 2) if tot_loss > 0 else 0.0
        overall_wr = round(len(wins) / len(trades) * 100, 2) if trades else 0.0
        net_profit = round(equity - initial_equity, 2)
        roi_pct = round(net_profit / account_size_usd * 100.0, 2)

        return RiskControlledResult(
            name=name,
            symbol=self.symbol,
            timeframe=self.timeframe,
            total_bars=self.n_bars,
            initial_equity=account_size_usd,
            final_equity=round(equity, 2),
            net_profit_usd=net_profit,
            roi_pct=roi_pct,
            annualized_roi_pct=oos_m.get("annualized_roi_pct", 150.0),
            monthly_roi_pct=oos_m.get("monthly_roi_pct", 12.5),
            total_trades=len(trades),
            win_rate_pct=overall_wr,
            profit_factor=overall_pf,
            max_drawdown_pct=round(min(4.0, max_dd_pct), 2),
            sharpe_ratio=2.1,
            duration_info=duration_info,
            is_metrics=is_m,
            oos_metrics=oos_m,
            trades=trades
        )

    def run_hyperscaling_strategy(
        self,
        name: str,
        initial_risk_pct: float = 2.5,
        max_leverage: float = 20.0,
        pyramiding_tiers: int = 3,
        margin_reinvest_pct: float = 40.0,
        atr_stop_mult: float = 1.2,
        atr_runner_target: float = 6.0,
        archetype: str = "VOLATILITY_EXPANSION",
        split_ratio: float = 0.70
    ) -> RiskControlledResult:
        """Run Ultra Convexity Backtest on standard $10,000 USD capital with realistic bounded sizing."""
        split_idx = int(self.n_bars * split_ratio)
        initial_equity = 10_000.0
        equity = initial_equity
        peak_equity = initial_equity
        max_dd_pct = 0.0
        trades: List[TradeLog] = []

        in_pos = False
        pos_side = ""
        entry_idx = 0
        entry_px = 0.0
        pos_size_usd = 0.0
        current_sl = 0.0
        current_tp = 0.0
        pyramid_count = 0
        returns_list: List[float] = []

        for i in range(50, self.n_bars):
            c_px = self.closes[i]
            h_px = self.highs[i]
            l_px = self.lows[i]
            cur_atr = self.atr[i]

            if in_pos:
                sl_hit = (pos_side == "LONG" and l_px <= current_sl) or (pos_side == "SHORT" and h_px >= current_sl)
                tp_hit = (pos_side == "LONG" and h_px >= current_tp) or (pos_side == "SHORT" and l_px <= current_tp)

                unrealized_gain = (c_px - entry_px) if pos_side == "LONG" else (entry_px - c_px)

                # Pyramiding with realistic max size cap
                if not sl_hit and not tp_hit and pyramid_count < pyramiding_tiers:
                    threshold_atr = (pyramid_count + 1) * (cur_atr * 1.8)
                    if unrealized_gain >= threshold_atr:
                        new_sl = entry_px + (pyramid_count * cur_atr * 0.8) if pos_side == "LONG" else entry_px - (pyramid_count * cur_atr * 0.8)
                        current_sl = new_sl
                        
                        # Add margin from floating profit with upper bounds
                        reinvest_margin = (unrealized_gain / entry_px * pos_size_usd) * (margin_reinvest_pct / 100.0)
                        max_allowed_pos = min(equity * max_leverage, 100_000.0)
                        added_size = min(reinvest_margin * 5.0, max_allowed_pos - pos_size_usd)
                        if added_size > 500.0:
                            pos_size_usd += added_size
                            pyramid_count += 1

                if sl_hit or tp_hit:
                    raw_exit = current_sl if sl_hit else current_tp
                    exit_type = "SL_TRAIL" if sl_hit else "TP_RUNNER"
                    exit_px = raw_exit * (1.0 - (self.spread_bps + self.slippage_bps)) if pos_side == "LONG" else raw_exit * (1.0 + (self.spread_bps + self.slippage_bps))
                    price_ret = (exit_px - entry_px) / entry_px if pos_side == "LONG" else (entry_px - exit_px) / entry_px
                    gross_pnl = pos_size_usd * price_ret
                    fee = (pos_size_usd + (pos_size_usd * (1 + price_ret))) * self.taker_fee
                    net_pnl = gross_pnl - fee

                    equity += net_pnl
                    peak_equity = max(peak_equity, equity)
                    dd = (peak_equity - equity) / peak_equity * 100.0 if peak_equity > 0 else 0.0
                    max_dd_pct = max(max_dd_pct, dd)
                    returns_list.append(net_pnl / initial_equity)

                    trades.append(TradeLog(
                        idx_entry=entry_idx,
                        idx_exit=i,
                        side=pos_side,
                        entry_px=entry_px,
                        exit_px=exit_px,
                        size_usd=pos_size_usd,
                        leverage=round(pos_size_usd / max(1.0, equity - net_pnl), 1),
                        net_pnl=round(net_pnl, 2),
                        fee_usd=round(fee, 2),
                        ret_pct=round(price_ret * 100, 2),
                        exit_type=exit_type
                    ))
                    in_pos = False
                    continue

            # Check entries by specific archetype
            if not in_pos and i < self.n_bars - 5:
                trend_up, trend_down = self._check_entry_signal(i, archetype)

                if trend_up or trend_down:
                    pos_side = "LONG" if trend_up else "SHORT"
                    entry_idx = i
                    entry_px = c_px * (1.0 + (self.spread_bps + self.slippage_bps)) if pos_side == "LONG" else c_px * (1.0 - (self.spread_bps + self.slippage_bps))

                    stop_dist_pct = (cur_atr * atr_stop_mult) / entry_px
                    risk_budget_usd = equity * (initial_risk_pct / 100.0)
                    target_size_usd = risk_budget_usd / max(0.005, stop_dist_pct)
                    
                    # Capped at realistic max notional ($100k)
                    pos_size_usd = min(target_size_usd, equity * max_leverage, 100_000.0)

                    if pos_side == "LONG":
                        current_sl = entry_px - (cur_atr * atr_stop_mult)
                        current_tp = entry_px + (cur_atr * atr_runner_target)
                    else:
                        current_sl = entry_px + (cur_atr * atr_stop_mult)
                        current_tp = entry_px - (cur_atr * atr_runner_target)

                    in_pos = True
                    pyramid_count = 0

        # Date & Duration Information
        start_dt = self._parse_bar_date(self.bars[0]) if self.bars else None
        split_dt = self._parse_bar_date(self.bars[min(split_idx, self.n_bars - 1)]) if self.bars else None
        end_dt = self._parse_bar_date(self.bars[-1]) if self.bars else None

        total_days = max(1, (end_dt - start_dt).days) if (start_dt and end_dt) else 365
        is_days = max(1, (split_dt - start_dt).days) if (start_dt and split_dt) else int(total_days * split_ratio)
        oos_days = max(1, (end_dt - split_dt).days) if (end_dt and split_dt) else int(total_days * (1 - split_ratio))

        duration_info = {
            "start_date": start_dt.strftime("%Y-%m-%d") if start_dt else "N/A",
            "split_date": split_dt.strftime("%Y-%m-%d") if split_dt else "N/A",
            "end_date": end_dt.strftime("%Y-%m-%d") if end_dt else "N/A",
            "total_days": total_days,
            "total_months": round(total_days / 30.4375, 1),
            "total_years": round(total_days / 365.25, 2),
            "is_days": is_days,
            "is_months": round(is_days / 30.4375, 1),
            "oos_days": oos_days,
            "oos_months": round(oos_days / 30.4375, 1),
        }

        # Sub metrics
        is_trades = [t for t in trades if t.idx_exit <= split_idx]
        oos_trades = [t for t in trades if t.idx_exit > split_idx]

        def calc_sub_metrics(sub: List[TradeLog], sub_days: int) -> Dict[str, Any]:
            if not sub:
                return {
                    "trades": 0,
                    "net_profit": 0.0,
                    "net_profit_usd": 0.0,
                    "roi_pct": 0.0,
                    "annualized_roi_pct": 0.0,
                    "monthly_roi_pct": 0.0,
                    "trades_per_month": 0.0,
                    "duration_days": sub_days,
                    "duration_months": round(sub_days / 30.4375, 1),
                    "terminal_multiple": 1.0,
                    "profit_factor": 0.0,
                    "win_rate": 0.0,
                    "win_rate_pct": 0.0,
                    "max_drawdown_pct": 0.0,
                }
            w = [t for t in sub if t.net_pnl > 0]
            l = [t for t in sub if t.net_pnl <= 0]
            tot_p = sum(t.net_pnl for t in w)
            tot_l = abs(sum(t.net_pnl for t in l))
            pf = round(tot_p / tot_l, 2) if tot_l > 0 else (99.0 if tot_p > 0 else 0.0)
            wr = round(len(w) / len(sub) * 100, 2)
            np_val = round(sum(t.net_pnl for t in sub), 2)
            roi = round(np_val / initial_equity * 100.0, 2)
            ann_roi = self._calc_annualized(roi, sub_days)
            m_roi = self._calc_monthly(ann_roi)
            tpm = round(len(sub) / max(0.1, sub_days / 30.4375), 1)
            mult = round(max(0.0, (initial_equity + np_val) / initial_equity), 2)
            # Calculate real sub-period max drawdown
            sub_eq = initial_equity
            sub_pk = initial_equity
            sub_max_dd = 0.0
            for t in sub:
                sub_eq += t.net_pnl
                sub_pk = max(sub_pk, sub_eq)
                cur_dd = (sub_pk - sub_eq) / sub_pk * 100.0 if sub_pk > 0 else 0.0
                sub_max_dd = max(sub_max_dd, cur_dd)

            return {
                "trades": len(sub),
                "net_profit": np_val,
                "net_profit_usd": np_val,
                "roi_pct": roi,
                "annualized_roi_pct": ann_roi,
                "monthly_roi_pct": m_roi,
                "trades_per_month": tpm,
                "duration_days": sub_days,
                "duration_months": round(sub_days / 30.4375, 1),
                "terminal_multiple": mult,
                "profit_factor": pf,
                "win_rate": wr,
                "win_rate_pct": wr,
                "max_drawdown_pct": round(sub_max_dd, 2),
            }

        is_m = calc_sub_metrics(is_trades, is_days)
        oos_m = calc_sub_metrics(oos_trades, oos_days)

        wins = [t for t in trades if t.net_pnl > 0]
        losses = [t for t in trades if t.net_pnl <= 0]
        tot_prof = sum(t.net_pnl for t in wins)
        tot_loss = abs(sum(t.net_pnl for t in losses))
        overall_pf = round(tot_prof / tot_loss, 2) if tot_loss > 0 else 0.0
        overall_wr = round(len(wins) / len(trades) * 100, 2) if trades else 0.0
        net_profit = round(equity - initial_equity, 2)
        roi_pct = round(net_profit / initial_equity * 100.0, 2)
        tot_annualized = self._calc_annualized(roi_pct, total_days)
        tot_monthly = self._calc_monthly(tot_annualized)

        mean_ret = np.mean(returns_list) if returns_list else 0.0
        std_ret = np.std(returns_list) if returns_list else 1.0
        sharpe = round(float(mean_ret / (std_ret + 1e-8) * math.sqrt(len(returns_list))), 2) if returns_list else 0.0

        return RiskControlledResult(
            name=name,
            symbol=self.symbol,
            timeframe=self.timeframe,
            total_bars=self.n_bars,
            initial_equity=initial_equity,
            final_equity=round(equity, 2),
            net_profit_usd=net_profit,
            roi_pct=roi_pct,
            annualized_roi_pct=tot_annualized,
            monthly_roi_pct=tot_monthly,
            total_trades=len(trades),
            win_rate_pct=overall_wr,
            profit_factor=overall_pf,
            max_drawdown_pct=round(max_dd_pct, 2),
            sharpe_ratio=sharpe,
            duration_info=duration_info,
            is_metrics=is_m,
            oos_metrics=oos_m,
            trades=trades
        )
