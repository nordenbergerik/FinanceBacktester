import numpy as np
import pandas as pd


def calculate_volatility(prices: pd.Series, window: int = 252) -> pd.Series:
    """
    Calculate annualized rolling volatility from a price series.

    Args:
        prices: Price series used to calculate volatility.
        window: Number of periods used for the rolling volatility calculation.

    Returns:
        A pandas Series containing annualized volatility values.
    """
    if window <= 0:
        raise ValueError("Window must be a positive integer")

    returns = prices.pct_change()
    return returns.rolling(window=window, min_periods=window).std(ddof=1) * np.sqrt(252)


def calculate_rolling_volatility(
    prices: pd.Series,
    window: int = 20,
    annualize: bool = False,
) -> pd.Series:
    """
    Calculate rolling volatility from a price series.

    Args:
        prices: Price series used to calculate volatility.
        window: Number of periods used for the rolling volatility calculation.
        annualize: Whether to scale the resulting volatility to an annual basis.

    Returns:
        A pandas Series containing rolling volatility values.
    """
    if window <= 0:
        raise ValueError("Window must be a positive integer")

    returns = prices.pct_change()
    rolling_vol = returns.rolling(window=window, min_periods=window).std(ddof=1)
    return rolling_vol * np.sqrt(252) if annualize else rolling_vol


