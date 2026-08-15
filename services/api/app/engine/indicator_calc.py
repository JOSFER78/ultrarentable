"""Deterministic Indicator Calculator for FAST Engine."""
from __future__ import annotations

from typing import Sequence
import numpy as np


def compute_sma(values: Sequence[float], period: int) -> np.ndarray:
    """Simple Moving Average."""
    arr = np.asarray(values, dtype=np.float64)
    n = len(arr)
    result = np.full(n, np.nan, dtype=np.float64)
    if period <= 0 or period > n:
        return result
    kernel = np.ones(period, dtype=np.float64) / period
    convoluted = np.convolve(arr, kernel, mode="valid")
    result[period - 1 :] = convoluted
    return result


def compute_ema(values: Sequence[float], period: int) -> np.ndarray:
    """Exponential Moving Average."""
    arr = np.asarray(values, dtype=np.float64)
    n = len(arr)
    result = np.full(n, np.nan, dtype=np.float64)
    if period <= 0 or period > n:
        return result
    multiplier = 2.0 / (period + 1.0)
    sma_init = np.mean(arr[:period])
    result[period - 1] = sma_init
    for i in range(period, n):
        result[i] = (arr[i] - result[i - 1]) * multiplier + result[i - 1]
    return result


def compute_rsi(values: Sequence[float], period: int) -> np.ndarray:
    """Relative Strength Index."""
    arr = np.asarray(values, dtype=np.float64)
    n = len(arr)
    result = np.full(n, np.nan, dtype=np.float64)
    if period <= 0 or period >= n:
        return result
    deltas = np.diff(arr)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)

    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])

    if avg_loss == 0:
        result[period] = 100.0
    else:
        rs = avg_gain / avg_loss
        result[period] = 100.0 - (100.0 / (1.0 + rs))

    for i in range(period + 1, n):
        idx = i - 1
        avg_gain = (avg_gain * (period - 1) + gains[idx]) / period
        avg_loss = (avg_loss * (period - 1) + losses[idx]) / period
        if avg_loss == 0:
            result[i] = 100.0
        else:
            rs = avg_gain / avg_loss
            result[i] = 100.0 - (100.0 / (1.0 + rs))
    return result


def compute_atr(high: Sequence[float], low: Sequence[float], close: Sequence[float], period: int) -> np.ndarray:
    """Average True Range."""
    h = np.asarray(high, dtype=np.float64)
    l = np.asarray(low, dtype=np.float64)
    c = np.asarray(close, dtype=np.float64)
    n = len(c)
    result = np.full(n, np.nan, dtype=np.float64)
    if period <= 0 or period >= n:
        return result

    tr = np.zeros(n, dtype=np.float64)
    tr[0] = h[0] - l[0]
    for i in range(1, n):
        tr[i] = max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))

    result[period - 1] = np.mean(tr[:period])
    for i in range(period, n):
        result[i] = (result[i - 1] * (period - 1) + tr[i]) / period
    return result


def compute_highest(values: Sequence[float], period: int) -> np.ndarray:
    """Rolling Maximum."""
    arr = np.asarray(values, dtype=np.float64)
    n = len(arr)
    result = np.full(n, np.nan, dtype=np.float64)
    if period <= 0 or period > n:
        return result
    for i in range(period - 1, n):
        result[i] = np.max(arr[i - period + 1 : i + 1])
    return result


def compute_lowest(values: Sequence[float], period: int) -> np.ndarray:
    """Rolling Minimum."""
    arr = np.asarray(values, dtype=np.float64)
    n = len(arr)
    result = np.full(n, np.nan, dtype=np.float64)
    if period <= 0 or period > n:
        return result
    for i in range(period - 1, n):
        result[i] = np.min(arr[i - period + 1 : i + 1])
    return result


def compute_roc(values: Sequence[float], period: int) -> np.ndarray:
    """Rate of Change (% multiplier)."""
    arr = np.asarray(values, dtype=np.float64)
    n = len(arr)
    result = np.full(n, np.nan, dtype=np.float64)
    if period <= 0 or period >= n:
        return result
    for i in range(period, n):
        prev = arr[i - period]
        if prev != 0:
            result[i] = ((arr[i] - prev) / prev) * 100.0
    return result


def compute_stddev(values: Sequence[float], period: int) -> np.ndarray:
    """Rolling Standard Deviation."""
    arr = np.asarray(values, dtype=np.float64)
    n = len(arr)
    result = np.full(n, np.nan, dtype=np.float64)
    if period <= 0 or period > n:
        return result
    for i in range(period - 1, n):
        result[i] = np.std(arr[i - period + 1 : i + 1], ddof=0)
    return result


def compute_volume_ratio(volume: Sequence[float], period: int) -> np.ndarray:
    """Ratio of current volume to its rolling SMA."""
    vol = np.asarray(volume, dtype=np.float64)
    sma = compute_sma(vol, period)
    n = len(vol)
    result = np.full(n, np.nan, dtype=np.float64)
    for i in range(n):
        if not np.isnan(sma[i]) and sma[i] > 0:
            result[i] = vol[i] / sma[i]
    return result
