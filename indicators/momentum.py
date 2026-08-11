import pandas as pd


def calculate_momentum(prices: pd.Series, window: int = 1) -> pd.Series:
    """
    Calculate momentum as the price change over a fixed lookback period.

    Args:
        prices: Price series used to calculate momentum.
        window: Number of periods over which to measure momentum.

    Returns:
        A pandas Series containing momentum values.
    """
    if window <= 0:
        raise ValueError("Window must be a positive integer")

    return prices.diff(window)
