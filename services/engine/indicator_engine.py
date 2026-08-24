"""services/engine/indicator_engine.py
Dynamic Technical & Quantitative Indicator Engine (v3.0.0).

DOCTRINA ZERO-MOCKS & EXACT MATHEMATICS:
- Pure deterministic vector and recursive calculations for all indicators.
- Caches calculations by (indicator_type, period, params_hash) to avoid redundant passes.
"""

from __future__ import annotations

import math
from typing import Any, Dict, Optional
import numpy as np

from contracts.universal_strategy import IndicatorType


class DynamicIndicatorEngine:
    """Calculador dinámico determinista de indicadores técnicos y cuantitativos."""

    def __init__(self, opens: np.ndarray, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, volumes: Optional[np.ndarray] = None) -> None:
        self.opens = np.asarray(opens, dtype=np.float64)
        self.highs = np.asarray(highs, dtype=np.float64)
        self.lows = np.asarray(lows, dtype=np.float64)
        self.closes = np.asarray(closes, dtype=np.float64)
        self.volumes = np.asarray(volumes, dtype=np.float64) if volumes is not None else np.ones_like(self.closes)
        self.n = len(self.closes)
        self._cache: Dict[str, np.ndarray] = {}

    def get_series(self, indicator_type: IndicatorType, period: Optional[int] = None, params: Optional[Dict[str, Any]] = None) -> np.ndarray:
        """Obtiene o calcula la serie correspondiente de forma dinámica."""
        cache_key = f"{indicator_type.value}_{period}_{params}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        res = self._compute(indicator_type, period or 14, params or {})
        self._cache[cache_key] = res
        return res

    def _compute(self, ind: IndicatorType, p: int, params: Dict[str, Any]) -> np.ndarray:
        p = max(1, int(p))

        # Raw Price Series
        if ind == IndicatorType.PRICE_OPEN:
            return self.opens
        elif ind == IndicatorType.PRICE_HIGH:
            return self.highs
        elif ind == IndicatorType.PRICE_LOW:
            return self.lows
        elif ind == IndicatorType.PRICE_CLOSE:
            return self.closes
        elif ind == IndicatorType.PRICE_VOLUME:
            return self.volumes

        # Moving Averages
        elif ind == IndicatorType.SMA:
            return self.calc_sma(self.closes, p)
        elif ind == IndicatorType.EMA:
            return self.calc_ema(self.closes, p)
        elif ind == IndicatorType.WMA:
            return self.calc_wma(self.closes, p)
        elif ind == IndicatorType.HMA:
            return self.calc_hma(self.closes, p)
        elif ind == IndicatorType.DEMA:
            ema1 = self.calc_ema(self.closes, p)
            ema2 = self.calc_ema(ema1, p)
            return 2.0 * ema1 - ema2
        elif ind == IndicatorType.TEMA:
            ema1 = self.calc_ema(self.closes, p)
            ema2 = self.calc_ema(ema1, p)
            ema3 = self.calc_ema(ema2, p)
            return 3.0 * ema1 - 3.0 * ema2 + ema3
        elif ind == IndicatorType.VWAP:
            typical_price = (self.highs + self.lows + self.closes) / 3.0
            cum_vol_price = np.cumsum(typical_price * self.volumes)
            cum_vol = np.maximum(1e-6, np.cumsum(self.volumes))
            return cum_vol_price / cum_vol

        # Oscillators
        elif ind == IndicatorType.RSI:
            return self.calc_rsi(self.closes, p)
        elif ind == IndicatorType.ROC:
            return self.calc_roc(self.closes, p)
        elif ind == IndicatorType.CCI:
            return self.calc_cci(self.highs, self.lows, self.closes, p)
        elif ind == IndicatorType.WILLIAMS_R:
            return self.calc_williams_r(self.highs, self.lows, self.closes, p)
        elif ind in (IndicatorType.MACD_LINE, IndicatorType.MACD_SIGNAL, IndicatorType.MACD_HIST):
            fast = int(params.get("fast_period", 12))
            slow = int(params.get("slow_period", 26))
            signal = int(params.get("signal_period", 9))
            macd_line, sig_line, hist = self.calc_macd(self.closes, fast, slow, signal)
            if ind == IndicatorType.MACD_LINE:
                return macd_line
            elif ind == IndicatorType.MACD_SIGNAL:
                return sig_line
            else:
                return hist
        elif ind in (IndicatorType.STOCHASTIC_K, IndicatorType.STOCHASTIC_D):
            smooth_k = int(params.get("smooth_k", 3))
            smooth_d = int(params.get("smooth_d", 3))
            k, d = self.calc_stochastic(self.highs, self.lows, self.closes, p, smooth_k, smooth_d)
            return k if ind == IndicatorType.STOCHASTIC_K else d

        # Volatility & Bands
        elif ind == IndicatorType.ATR:
            return self.calc_atr(self.highs, self.lows, self.closes, p)
        elif ind == IndicatorType.STDDEV:
            return self.calc_stddev(self.closes, p)
        elif ind == IndicatorType.PARKINSON_VOLATILITY:
            return self.calc_parkinson_volatility(self.highs, self.lows, p)
        elif ind in (IndicatorType.BOLLINGER_UPPER, IndicatorType.BOLLINGER_MIDDLE, IndicatorType.BOLLINGER_LOWER, IndicatorType.BOLLINGER_WIDTH):
            k = float(params.get("std_dev_mult", 2.0))
            mid = self.calc_sma(self.closes, p)
            sd = self.calc_stddev(self.closes, p)
            upper = mid + (k * sd)
            lower = mid - (k * sd)
            if ind == IndicatorType.BOLLINGER_UPPER:
                return upper
            elif ind == IndicatorType.BOLLINGER_MIDDLE:
                return mid
            elif ind == IndicatorType.BOLLINGER_LOWER:
                return lower
            else:
                return np.where(mid > 0, (upper - lower) / mid, 0.0)
        elif ind in (IndicatorType.DONCHIAN_HIGH, IndicatorType.DONCHIAN_LOW, IndicatorType.DONCHIAN_MID):
            high_d, low_d, mid_d = self.calc_donchian(self.highs, self.lows, p)
            if ind == IndicatorType.DONCHIAN_HIGH:
                return high_d
            elif ind == IndicatorType.DONCHIAN_LOW:
                return low_d
            else:
                return mid_d

        # Extremes & Volume
        elif ind == IndicatorType.HIGHEST:
            return self.calc_highest(self.highs, p)
        elif ind == IndicatorType.LOWEST:
            return self.calc_lowest(self.lows, p)
        elif ind == IndicatorType.VOLUME_SMA:
            return self.calc_sma(self.volumes, p)
        elif ind == IndicatorType.VOLUME_RATIO:
            vol_sma = self.calc_sma(self.volumes, p)
            return np.where(vol_sma > 0, self.volumes / vol_sma, 1.0)

        # Fallback to closes if unknown
        return self.closes

    # === Mathematical Calculations ===
    @staticmethod
    def calc_sma(series: np.ndarray, period: int) -> np.ndarray:
        n = len(series)
        out = np.empty(n, dtype=np.float64)
        if period <= 1:
            return series.copy()
        cumsum = np.cumsum(np.insert(series, 0, 0.0))
        out[:period - 1] = series[:period - 1]
        out[period - 1:] = (cumsum[period:] - cumsum[:-period]) / float(period)
        return out

    @staticmethod
    def calc_ema(series: np.ndarray, period: int) -> np.ndarray:
        period = max(1, int(period))
        alpha = 2.0 / (period + 1.0)
        ema = np.empty_like(series, dtype=np.float64)
        ema[0] = series[0]
        for t in range(1, len(series)):
            ema[t] = alpha * series[t] + (1.0 - alpha) * ema[t - 1]
        return ema

    @staticmethod
    def calc_wma(series: np.ndarray, period: int) -> np.ndarray:
        period = max(1, int(period))
        weights = np.arange(1, period + 1, dtype=np.float64)
        sum_weights = weights.sum()
        out = np.empty_like(series, dtype=np.float64)
        for i in range(len(series)):
            if i < period - 1:
                out[i] = series[i]
            else:
                out[i] = np.dot(series[i - period + 1:i + 1], weights) / sum_weights
        return out

    @classmethod
    def calc_hma(cls, series: np.ndarray, period: int) -> np.ndarray:
        period = max(2, int(period))
        half_p = max(1, period // 2)
        sqrt_p = max(1, int(math.sqrt(period)))
        wma_half = cls.calc_wma(series, half_p)
        wma_full = cls.calc_wma(series, period)
        diff = 2.0 * wma_half - wma_full
        return cls.calc_wma(diff, sqrt_p)

    @staticmethod
    def calc_rsi(closes: np.ndarray, period: int) -> np.ndarray:
        period = max(2, int(period))
        n = len(closes)
        rsi = np.full(n, 50.0, dtype=np.float64)
        if n <= period:
            return rsi

        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0.0)
        losses = np.where(deltas < 0, -deltas, 0.0)

        avg_gain = float(np.mean(gains[:period]))
        avg_loss = float(np.mean(losses[:period]))

        rsi[period] = 100.0 if avg_loss == 0 else 100.0 - (100.0 / (1.0 + (avg_gain / avg_loss)))

        for i in range(period + 1, n):
            gain = gains[i - 1]
            loss = losses[i - 1]
            avg_gain = (avg_gain * (period - 1) + gain) / float(period)
            avg_loss = (avg_loss * (period - 1) + loss) / float(period)
            rsi[i] = 100.0 if avg_loss == 0 else 100.0 - (100.0 / (1.0 + (avg_gain / avg_loss)))
        return rsi

    @staticmethod
    def calc_atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int) -> np.ndarray:
        period = max(1, int(period))
        n = len(closes)
        tr = np.empty(n, dtype=np.float64)
        tr[0] = highs[0] - lows[0]
        for i in range(1, n):
            h_l = highs[i] - lows[i]
            h_cp = abs(highs[i] - closes[i - 1])
            l_cp = abs(lows[i] - closes[i - 1])
            tr[i] = max(h_l, h_cp, l_cp)

        atr = np.empty(n, dtype=np.float64)
        atr[:period] = np.mean(tr[:period]) if n >= period else tr.copy()
        alpha = 1.0 / float(period)
        for i in range(period, n):
            atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / float(period)
        return atr

    @staticmethod
    def calc_stddev(series: np.ndarray, period: int) -> np.ndarray:
        period = max(2, int(period))
        n = len(series)
        out = np.zeros(n, dtype=np.float64)
        if n < period:
            return out
        windows = np.lib.stride_tricks.sliding_window_view(series, period)
        out[period - 1:] = np.std(windows, axis=-1)
        return out

    @staticmethod
    def calc_highest(highs: np.ndarray, period: int) -> np.ndarray:
        period = max(1, int(period))
        n = len(highs)
        if period == 1:
            return highs.copy()
        out = np.empty(n, dtype=np.float64)
        if n < period:
            return np.maximum.accumulate(highs)
        out[:period - 1] = [np.max(highs[:i + 1]) for i in range(period - 1)]
        out[period - 1:] = np.lib.stride_tricks.sliding_window_view(highs, period).max(axis=-1)
        return out

    @staticmethod
    def calc_lowest(lows: np.ndarray, period: int) -> np.ndarray:
        period = max(1, int(period))
        n = len(lows)
        if period == 1:
            return lows.copy()
        out = np.empty(n, dtype=np.float64)
        if n < period:
            return np.minimum.accumulate(lows)
        out[:period - 1] = [np.min(lows[:i + 1]) for i in range(period - 1)]
        out[period - 1:] = np.lib.stride_tricks.sliding_window_view(lows, period).min(axis=-1)
        return out

    @classmethod
    def calc_donchian(cls, highs: np.ndarray, lows: np.ndarray, period: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        h = cls.calc_highest(highs, period)
        l = cls.calc_lowest(lows, period)
        m = (h + l) / 2.0
        return h, l, m

    @staticmethod
    def calc_roc(closes: np.ndarray, period: int) -> np.ndarray:
        period = max(1, int(period))
        n = len(closes)
        out = np.zeros(n, dtype=np.float64)
        for i in range(period, n):
            prev = closes[i - period]
            out[i] = ((closes[i] - prev) / prev) * 100.0 if prev != 0 else 0.0
        return out

    @staticmethod
    def calc_cci(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int) -> np.ndarray:
        period = max(2, int(period))
        tp = (highs + lows + closes) / 3.0
        n = len(tp)
        out = np.zeros(n, dtype=np.float64)
        if n < period:
            return out
        windows = np.lib.stride_tricks.sliding_window_view(tp, period)
        sma_tp = windows.mean(axis=-1)
        mean_dev = np.mean(np.abs(windows - sma_tp[:, None]), axis=-1)
        dev_denom = np.where(mean_dev != 0, 0.015 * mean_dev, 1e-8)
        out[period - 1:] = np.where(mean_dev != 0, (tp[period - 1:] - sma_tp) / dev_denom, 0.0)
        return out

    @staticmethod
    def calc_williams_r(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int) -> np.ndarray:
        period = max(1, int(period))
        n = len(closes)
        out = np.full(n, -50.0, dtype=np.float64)
        if n < period:
            return out
        hh = np.lib.stride_tricks.sliding_window_view(highs, period).max(axis=-1)
        ll = np.lib.stride_tricks.sliding_window_view(lows, period).min(axis=-1)
        denom = np.where(hh != ll, hh - ll, 1e-8)
        out[period - 1:] = np.where(hh != ll, ((hh - closes[period - 1:]) / denom) * -100.0, -50.0)
        return out

    @classmethod
    def calc_macd(cls, closes: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        ema_fast = cls.calc_ema(closes, fast)
        ema_slow = cls.calc_ema(closes, slow)
        macd_line = ema_fast - ema_slow
        sig_line = cls.calc_ema(macd_line, signal)
        hist = macd_line - sig_line
        return macd_line, sig_line, hist

    @classmethod
    def calc_stochastic(cls, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period_k: int = 14, smooth_k: int = 3, smooth_d: int = 3) -> tuple[np.ndarray, np.ndarray]:
        n = len(closes)
        raw_k = np.full(n, 50.0, dtype=np.float64)
        if n >= period_k:
            hh = np.lib.stride_tricks.sliding_window_view(highs, period_k).max(axis=-1)
            ll = np.lib.stride_tricks.sliding_window_view(lows, period_k).min(axis=-1)
            denom = np.where(hh != ll, hh - ll, 1e-8)
            raw_k[period_k - 1:] = np.where(hh != ll, ((closes[period_k - 1:] - ll) / denom) * 100.0, 50.0)
        k = cls.calc_sma(raw_k, smooth_k)
        d = cls.calc_sma(k, smooth_d)
        return k, d

    @staticmethod
    def calc_parkinson_volatility(highs: np.ndarray, lows: np.ndarray, period: int = 14) -> np.ndarray:
        period = max(2, int(period))
        n = len(highs)
        out = np.zeros(n, dtype=np.float64)
        if n < period:
            return out
        factor = 1.0 / (4.0 * math.log(2.0))
        log_hl = np.log(np.maximum(1e-8, highs / np.maximum(1e-8, lows))) ** 2
        windows = np.lib.stride_tricks.sliding_window_view(log_hl, period)
        sum_hl = windows.sum(axis=-1)
        out[period - 1:] = np.sqrt((factor / float(period)) * sum_hl)
        return out
