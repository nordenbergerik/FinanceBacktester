import pandas as pd

from .ema import calculate_ema


def calculate_macd(
    prices: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    """
    Calculate the MACD line, signal line, and histogram for a price series.

    Args:
        prices: Price series used to calculate MACD.
        fast: Fast EMA window.
        slow: Slow EMA window.
        signal: Signal line EMA window.

    Returns:
        A pandas DataFrame with columns `macd`, `signal`, and `histogram`.
    """
    if fast <= 0 or slow <= 0 or signal <= 0:
        raise ValueError("All window sizes must be positive integers")

    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)

    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False, min_periods=signal).mean()
    histogram = macd_line - signal_line

    return pd.DataFrame(
        {
            "macd": macd_line,
            "signal": signal_line,
            "histogram": histogram,
        }
    )
