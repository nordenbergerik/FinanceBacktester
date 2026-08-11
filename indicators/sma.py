import pandas as pd


def calculate_sma(prices: pd.Series, window: int) -> pd.Series:
    """
    Calculate a simple moving average (SMA) over a fixed window.

    Args:
        prices: Price series used to calculate the SMA.
        window: Number of periods to use for the moving average.

    Returns:
        A pandas Series containing the SMA values.
    """
    if window <= 0:
        raise ValueError("Window must be a positive integer")

    return prices.rolling(window=window, min_periods=window).mean()