import pandas as pd


def calculate_bollinger_bands(
    prices: pd.Series,
    window: int = 20,
    num_std_dev: float = 2.0,
) -> pd.DataFrame:
    """
    Calculate Bollinger Bands for a price series.

    Args:
        prices: Price series used to calculate the bands.
        window: Number of periods used for the moving average and standard deviation.
        num_std_dev: Number of standard deviations to offset the upper and lower bands.

    Returns:
        A pandas DataFrame containing `lower_band`, `middle_band`, and `upper_band`.
    """
    if window <= 0:
        raise ValueError("Window must be a positive integer")
    if num_std_dev <= 0:
        raise ValueError("num_std_dev must be a positive number")

    middle_band = prices.rolling(window=window, min_periods=window).mean()
    rolling_std = prices.rolling(window=window, min_periods=window).std(ddof=1)
    upper_band = middle_band + rolling_std * num_std_dev
    lower_band = middle_band - rolling_std * num_std_dev

    return pd.DataFrame(
        {
            "lower_band": lower_band,
            "middle_band": middle_band,
            "upper_band": upper_band,
        }
    )
