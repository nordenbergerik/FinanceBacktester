import pandas as pd


def calculate_rsi(prices: pd.Series, window: int = 14) -> pd.Series:
    """
    Calculate the Relative Strength Index (RSI) for a price series.

    Args:
        prices: Price series used to calculate RSI.
        window: Number of periods to use for RSI smoothing.

    Returns:
        A pandas Series containing RSI values between 0 and 100.
    """
    if window <= 0:
        raise ValueError("Window must be a positive integer")

    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    average_gain = gain.rolling(window=window, min_periods=window).mean()
    average_loss = loss.rolling(window=window, min_periods=window).mean()

    rs = average_gain / average_loss
    rsi = 100 - (100 / (1 + rs))

    rsi = rsi.where(average_loss != 0, 100)
    rsi = rsi.mask((average_gain == 0) & (average_loss == 0), 50)

    return rsi
