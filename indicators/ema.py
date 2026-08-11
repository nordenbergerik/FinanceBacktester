import pandas as pd


def calculate_ema(prices: pd.Series, window: int) -> pd.Series:
    """
    Calculate an exponential moving average (EMA) over a fixed window.

    Args:
        prices: Price series used to calculate the EMA.
        window: Number of periods to use for the EMA.

    Returns:
        A pandas Series containing the EMA values.
    """
    if window <= 0:
        raise ValueError("Window must be a positive integer")

    return prices.ewm(span=window, adjust=False, min_periods=window).mean()
