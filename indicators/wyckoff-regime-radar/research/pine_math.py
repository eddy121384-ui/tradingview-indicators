"""Small Pine-semantics helpers used by the Wyckoff research mirror.

These helpers deliberately model only the built-ins required by the frozen
v0.5.2.1 price-only path. Pine↔Python checkpoint parity remains the authority
for edge cases such as percentile-rank ties and initial warm-up behavior.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def safe_div(num, den):
    n = np.asarray(num, dtype=float)
    d = np.asarray(den, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        out = n / d
    out = np.where(~np.isfinite(n) | ~np.isfinite(d) | (d == 0.0), np.nan, out)
    return float(out) if np.ndim(out) == 0 else out


def clamp(x, lo: float, hi: float):
    return np.clip(x, lo, hi)


def gate(x, lo: float, hi: float):
    arr = np.asarray(x, dtype=float)
    if hi == lo:
        out = np.zeros_like(arr)
    else:
        out = np.clip((arr - lo) / (hi - lo), 0.0, 1.0)
        out = np.where(np.isfinite(arr), out, 0.0)
    return float(out) if np.ndim(out) == 0 else out


def weighted(*value_weight_pairs):
    values = value_weight_pairs[0::2]
    weights = np.asarray(value_weight_pairs[1::2], dtype=float)
    denom = weights.sum()
    arrays = [np.asarray(value, dtype=float) for value in values]
    if denom == 0.0:
        out = np.full_like(arrays[0], np.nan, dtype=float)
    else:
        out = sum(value * weight for value, weight in zip(arrays, weights)) / denom
    return float(out) if np.ndim(out) == 0 else out


def shift(values, periods: int = 1):
    arr = np.asarray(values)
    if periods <= 0:
        return arr.copy()
    if np.issubdtype(arr.dtype, np.bool_):
        out = np.zeros(arr.shape, dtype=bool)
    else:
        out = np.full(arr.shape, np.nan, dtype=float)
    if periods < len(arr):
        out[periods:] = arr[:-periods]
    return out


def rolling_sma(values, length: int):
    return pd.Series(values, dtype=float).rolling(length, min_periods=length).mean().to_numpy()


def rolling_std(values, length: int):
    # ta.stdev() defaults to the biased/population estimate.
    return pd.Series(values, dtype=float).rolling(length, min_periods=length).std(ddof=0).to_numpy()


def rolling_highest(values, length: int):
    return pd.Series(values, dtype=float).rolling(length, min_periods=length).max().to_numpy()


def rolling_lowest(values, length: int):
    return pd.Series(values, dtype=float).rolling(length, min_periods=length).min().to_numpy()


def ema(values, length: int):
    """Recursive EMA seeded with the first finite source value."""
    arr = np.asarray(values, dtype=float)
    out = np.full(arr.shape, np.nan, dtype=float)
    alpha = 2.0 / (length + 1.0)
    prev = np.nan
    for i, value in enumerate(arr):
        if not np.isfinite(value):
            continue
        prev = value if not np.isfinite(prev) else alpha * value + (1.0 - alpha) * prev
        out[i] = prev
    return out


def rma(values, length: int):
    """Wilder moving average used by ta.atr()."""
    arr = np.asarray(values, dtype=float)
    out = np.full(arr.shape, np.nan, dtype=float)
    seed = []
    prev = np.nan
    for i, value in enumerate(arr):
        if not np.isfinite(value):
            continue
        if not np.isfinite(prev):
            seed.append(value)
            if len(seed) == length:
                prev = float(np.mean(seed))
                out[i] = prev
        else:
            prev = (prev * (length - 1) + value) / length
            out[i] = prev
    return out


def true_range(high, low, close):
    high = np.asarray(high, dtype=float)
    low = np.asarray(low, dtype=float)
    close = np.asarray(close, dtype=float)
    out = np.full(close.shape, np.nan, dtype=float)
    for i in range(len(close)):
        if not (np.isfinite(high[i]) and np.isfinite(low[i])):
            continue
        if i == 0 or not np.isfinite(close[i - 1]):
            out[i] = high[i] - low[i]
        else:
            out[i] = max(
                high[i] - low[i],
                abs(high[i] - close[i - 1]),
                abs(low[i] - close[i - 1]),
            )
    return out


def atr(high, low, close, length: int):
    return rma(true_range(high, low, close), length)


def rolling_linreg_slope(values, length: int):
    """Slope implied by ta.linreg(src,len,0) - ta.linreg(src,len,1)."""
    arr = np.asarray(values, dtype=float)
    out = np.full(arr.shape, np.nan, dtype=float)
    x = np.arange(length, dtype=float)
    x_mean = x.mean()
    denom = np.sum((x - x_mean) ** 2)
    for i in range(length - 1, len(arr)):
        window = arr[i - length + 1 : i + 1]
        if np.isfinite(window).all():
            y_mean = window.mean()
            out[i] = np.sum((x - x_mean) * (window - y_mean)) / denom
    return out


def slope_z(values, length: int, vol):
    slope = rolling_linreg_slope(values, length)
    return safe_div(slope * length, np.asarray(vol, dtype=float) * np.sqrt(length))


def percentrank(values, length: int):
    """Mirror TradingView ``ta.percentrank()`` for the Wyckoff parity path.

    TradingView runtime checkpoints from Issue #66 D-1B show that the current
    observation is ranked against the *previous* ``length`` observations, not a
    ``length``-bar window that includes the current bar. Therefore the rank step
    is ``100 / length`` and the endpoints can map to 0 and 100.

    Tie handling remains strict ``<`` as in the original research mirror. The
    first D-1B capture had no tie case that distinguished ``<`` from ``<=``.
    """
    arr = np.asarray(values, dtype=float)
    out = np.full(arr.shape, np.nan, dtype=float)
    if length <= 0:
        return out
    for i in range(length, len(arr)):
        current = arr[i]
        history = arr[i - length : i]
        if np.isfinite(current) and np.isfinite(history).all():
            out[i] = np.count_nonzero(history < current) / length * 100.0
    return out


def barssince(condition):
    cond = np.asarray(condition, dtype=bool)
    out = np.full(cond.shape, np.nan, dtype=float)
    last_true = None
    for i, value in enumerate(cond):
        if value:
            last_true = i
            out[i] = 0.0
        elif last_true is not None:
            out[i] = float(i - last_true)
    return out


def recent(condition, bars: int):
    bs = barssince(condition)
    return np.isfinite(bs) & (bs <= bars)


def crossover(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    out = np.zeros(len(a), dtype=bool)
    valid = np.isfinite(a[1:]) & np.isfinite(a[:-1]) & np.isfinite(b[1:]) & np.isfinite(b[:-1])
    out[1:] = valid & (a[1:] > b[1:]) & (a[:-1] <= b[:-1])
    return out


def crossunder(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    out = np.zeros(len(a), dtype=bool)
    valid = np.isfinite(a[1:]) & np.isfinite(a[:-1]) & np.isfinite(b[1:]) & np.isfinite(b[:-1])
    out[1:] = valid & (a[1:] < b[1:]) & (a[:-1] >= b[:-1])
    return out
