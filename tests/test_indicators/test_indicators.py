import numpy as np
import pandas as pd
import pytest

from indicators import bollinger, ema, macd, momentum, rsi, sma, volatility


def test_calculate_sma_computes_simple_moving_average():
    prices = pd.Series([10.0, 12.0, 14.0, 16.0, 18.0])
    expected = prices.rolling(window=3, min_periods=3).mean()

    result = sma.calculate_sma(prices, window=3)

    pd.testing.assert_series_equal(result, expected)


def test_calculate_ema_computes_exponential_moving_average():
    prices = pd.Series([10.0, 11.0, 12.0, 11.0, 13.0])
    expected = prices.ewm(span=3, adjust=False, min_periods=3).mean()

    result = ema.calculate_ema(prices, window=3)

    pd.testing.assert_series_equal(result, expected)


def test_calculate_rsi_returns_expected_range_and_values():
    prices = pd.Series([100.0, 102.0, 101.0, 103.0, 105.0, 104.0, 106.0])

    result = rsi.calculate_rsi(prices, window=3)

    assert result.index.equals(prices.index)
    assert result.iloc[:2].isna().all()
    assert result.dropna().between(0, 100).all()


def test_calculate_macd_returns_dataframe_with_expected_columns():
    prices = pd.Series([100.0, 101.0, 102.0, 103.0, 104.0, 105.0])

    result = macd.calculate_macd(prices, fast=2, slow=4, signal=3)

    assert list(result.columns) == ["macd", "signal", "histogram"]
    assert isinstance(result, pd.DataFrame)
    assert result.shape[0] == prices.shape[0]
    assert result["histogram"].equals(result["macd"] - result["signal"])


def test_calculate_volatility_returns_annualized_rolling_std():
    prices = pd.Series([100.0, 102.0, 104.0, 104.0, 106.0, 108.0])
    expected = prices.pct_change().rolling(window=3, min_periods=3).std(ddof=1) * np.sqrt(252)

    result = volatility.calculate_volatility(prices, window=3)

    pd.testing.assert_series_equal(result, expected)


def test_calculate_rolling_volatility_returns_non_annualized_values():
    prices = pd.Series([100.0, 101.0, 102.0, 100.0, 99.0, 98.0])
    expected = prices.pct_change().rolling(window=3, min_periods=3).std(ddof=1)

    result = volatility.calculate_rolling_volatility(prices, window=3, annualize=False)

    pd.testing.assert_series_equal(result, expected)


def test_calculate_rolling_volatility_returns_annualized_values():
    prices = pd.Series([100.0, 101.0, 102.0, 100.0, 99.0, 98.0])
    expected = prices.pct_change().rolling(window=3, min_periods=3).std(ddof=1) * np.sqrt(252)

    result = volatility.calculate_rolling_volatility(prices, window=3, annualize=True)

    pd.testing.assert_series_equal(result, expected)


def test_calculate_bollinger_bands_returns_expected_columns_and_values():
    prices = pd.Series([100.0, 101.0, 102.0, 103.0, 104.0, 105.0])
    middle = prices.rolling(window=3, min_periods=3).mean()
    std = prices.rolling(window=3, min_periods=3).std(ddof=1)
    expected = pd.DataFrame(
        {
            "lower_band": middle - std * 2.0,
            "middle_band": middle,
            "upper_band": middle + std * 2.0,
        }
    )

    result = bollinger.calculate_bollinger_bands(prices, window=3, num_std_dev=2.0)

    pd.testing.assert_frame_equal(result, expected)


def test_calculate_momentum_returns_price_difference():
    prices = pd.Series([100.0, 101.0, 105.0, 110.0, 108.0])
    expected = prices.diff(2)

    result = momentum.calculate_momentum(prices, window=2)

    pd.testing.assert_series_equal(result, expected)


@pytest.mark.parametrize("invalid_window", [0, -1])
def test_indicator_functions_reject_invalid_window_sizes(invalid_window):
    prices = pd.Series([1.0, 2.0, 3.0])

    with pytest.raises(ValueError):
        sma.calculate_sma(prices, window=invalid_window)

    with pytest.raises(ValueError):
        ema.calculate_ema(prices, window=invalid_window)

    with pytest.raises(ValueError):
        volatility.calculate_volatility(prices, window=invalid_window)
