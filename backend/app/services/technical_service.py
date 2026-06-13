"""Technical analysis calculations for stock K-line data."""
import pandas as pd
import numpy as np
from typing import Optional

def _to_float(v):
    """Convert a numpy value to a native Python float."""
    if v is None:
        return None
    try:
        return float(v) if not np.isnan(v) else None
    except (TypeError, ValueError):
        return None

def _to_str(v):
    """Convert value to string safely."""
    if v is None:
        return "flat"
    return str(v)

async def get_technical_analysis(df: pd.DataFrame) -> dict:
    """Compute technical indicators from OHLCV DataFrame."""
    if df is None or df.empty:
        return {"error": "no data"}
    close = df["close"].values.astype(float)
    high = df["high"].values.astype(float) if "high" in df else close
    low = df["low"].values.astype(float) if "low" in df else close
    volume = df["volume"].values.astype(float) if "volume" in df else np.zeros_like(close)

    current_price = _to_float(close[-1])

    ma5_arr = _ma(close, 5)
    ma20_arr = _ma(close, 20)
    ma60_arr = _ma(close, 60)

    rsi_arr = _rsi(close, 14)
    macd_line, signal, histogram = _macd(close)
    k, d, j = _kdj(close, high, low, 9)

    ma5_val = _to_float(ma5_arr[-1]) if ma5_arr is not None and len(ma5_arr) > 0 else None
    ma20_val = _to_float(ma20_arr[-1]) if ma20_arr is not None and len(ma20_arr) > 0 else None
    ma60_val = _to_float(ma60_arr[-1]) if ma60_arr is not None and len(ma60_arr) > 0 else None

    rsi_val = _to_float(rsi_arr[-1]) if rsi_arr is not None and len(rsi_arr) > 0 else 50.0

    macd_v = _to_float(macd_line[-1]) if macd_line is not None and len(macd_line) > 0 else 0
    signal_v = _to_float(signal[-1]) if signal is not None and len(signal) > 0 else 0
    hist_v = _to_float(histogram[-1]) if histogram is not None and len(histogram) > 0 else 0

    # Bollinger
    bb_mid = ma20_val
    if len(close) >= 20:
        bb_std = float(np.std(close[-20:])) * 2
    else:
        bb_std = 0
    bb_upper = _to_float(bb_mid + bb_std) if bb_mid is not None else None
    bb_lower = _to_float(bb_mid - bb_std) if bb_mid is not None else None

    # Volume
    vol_ma5_arr = _ma(volume, 5)
    vol_ma5_val = _to_float(vol_ma5_arr[-1]) if vol_ma5_arr is not None and len(vol_ma5_arr) > 0 else 0

    return {
        "current_price": current_price,
        "ma5": ma5_val,
        "ma20": ma20_val,
        "ma60": ma60_val,
        "ma5_trend": _trend_str(ma5_arr, 3) if ma5_arr is not None else "flat",
        "ma20_trend": _trend_str(ma20_arr, 3) if ma20_arr is not None else "flat",
        "rsi": rsi_val,
        "rsi_trend": _trend_str(rsi_arr, 3) if rsi_arr is not None else "flat",
        "macd": {
            "macd": macd_v,
            "signal": signal_v,
            "histogram": hist_v,
            "golden_cross": _golden_cross(macd_line, signal) if macd_line is not None and signal is not None else False,
            "dead_cross": _dead_cross(macd_line, signal) if macd_line is not None and signal is not None else False,
        },
        "bollinger": {
            "upper": bb_upper,
            "mid": bb_mid,
            "lower": bb_lower,
            "position": _bb_position(current_price, bb_upper, bb_lower) if current_price and bb_upper and bb_lower else "unknown",
        },
        "kdj": {
            "k": _to_float(k[-1]) if k is not None and len(k) > 0 else 50.0,
            "d": _to_float(d[-1]) if d is not None and len(d) > 0 else 50.0,
            "j": _to_float(j[-1]) if j is not None and len(j) > 0 else 50.0,
        },
        "volume_ma5": vol_ma5_val,
        "price_change_pct": _to_float((close[-1] / close[0] - 1) * 100) if len(close) > 0 else 0,
        "high_52w": _to_float(np.max(close)),
        "low_52w": _to_float(np.min(close)),
    }

def _ma(arr: np.ndarray, window: int) -> Optional[np.ndarray]:
    if len(arr) < window:
        return None
    return np.convolve(arr, np.ones(window) / window, mode="valid")

def _rsi(close: np.ndarray, period: int = 14) -> Optional[np.ndarray]:
    if len(close) < period + 1:
        return None
    deltas = np.diff(close)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.zeros_like(close)
    avg_loss = np.zeros_like(close)
    avg_gain[period] = np.mean(gains[:period])
    avg_loss[period] = np.mean(losses[:period])
    for i in range(period + 1, len(close)):
        avg_gain[i] = (avg_gain[i - 1] * (period - 1) + gains[i - 1]) / period
        avg_loss[i] = (avg_loss[i - 1] * (period - 1) + losses[i - 1]) / period
    rs = np.where(avg_loss[period:] != 0, avg_gain[period:] / avg_loss[period:], 100)
    rsi_arr = 100 - (100 / (1 + rs))
    result = np.full(len(close), 50.0)
    result[period:] = rsi_arr
    return result

def _macd(close: np.ndarray, fast=12, slow=26, signal=9):
    if len(close) < slow + signal:
        return None, None, None
    ema_fast = _ema(close, fast)
    ema_slow = _ema(close, slow)
    macd_line = ema_fast - ema_slow
    signal_line = _ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def _ema(arr: np.ndarray, period: int) -> np.ndarray:
    result = np.zeros_like(arr)
    multiplier = 2 / (period + 1)
    result[0] = arr[0]
    for i in range(1, len(arr)):
        result[i] = (arr[i] - result[i - 1]) * multiplier + result[i - 1]
    return result

def _kdj(close, high, low, n=9):
    if len(close) < n:
        return None, None, None
    lowest = np.zeros_like(close)
    highest = np.zeros_like(close)
    for i in range(n - 1, len(close)):
        lowest[i] = np.min(low[i - n + 1:i + 1])
        highest[i] = np.max(high[i - n + 1:i + 1])
    rsv = np.where(highest - lowest != 0, (close - lowest) / (highest - lowest) * 100, 50)
    k = np.zeros_like(close)
    d = np.zeros_like(close)
    for i in range(len(close)):
        if i == 0:
            k[i] = 50; d[i] = 50
        else:
            k[i] = 2 / 3 * k[i - 1] + 1 / 3 * rsv[i]
            d[i] = 2 / 3 * d[i - 1] + 1 / 3 * k[i]
    j = 3 * k - 2 * d
    return k, d, j

def _trend_str(arr: np.ndarray, lookback: int) -> str:
    if arr is None or len(arr) < lookback:
        return "flat"
    recent = arr[-lookback:]
    if all(recent[i] < recent[i + 1] for i in range(lookback - 1)):
        return "up"
    elif all(recent[i] > recent[i + 1] for i in range(lookback - 1)):
        return "down"
    return "flat"

def _golden_cross(macd, signal) -> bool:
    if macd is None or signal is None or len(macd) < 3:
        return False
    return float(macd[-2]) < float(signal[-2]) and float(macd[-1]) > float(signal[-1])

def _dead_cross(macd, signal) -> bool:
    if macd is None or signal is None or len(macd) < 3:
        return False
    return float(macd[-2]) > float(signal[-2]) and float(macd[-1]) < float(signal[-1])

def _bb_position(price, upper, lower) -> str:
    if not upper or not lower or upper == lower:
        return "unknown"
    ratio = (price - lower) / (upper - lower)
    if ratio > 0.9:
        return "above_upper"
    elif ratio > 0.7:
        return "upper_band"
    elif ratio < 0.1:
        return "below_lower"
    elif ratio < 0.3:
        return "lower_band"
    return "middle"