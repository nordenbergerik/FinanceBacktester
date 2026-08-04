from datetime import date, datetime
from typing import TypeVar

import numpy as np

from pandas import DataFrame


class MetricsCalculator:
    #daily_returns: Series[float]
    @staticmethod
    def cagr(daily_returns, start_date: str | date | datetime, end_date: str | date | datetime ) -> float:
        """
        Calculate Compound Annual Growth Rate (CAGR) from daily returns.

        Args:
            daily_returns: Series of daily returns (e.g., 0.01 for 1%)
            dates: DatetimeIndex of the period

        Returns:
            CAGR as a decimal (e.g., 0.1234 for 12.34%)
        """
        # Calculate cumulative return
        cumulative_return = np.exp(np.log(1 + daily_returns).cumsum())

        # Calculate number of years (accounting for partial years)
        if MetricsCalculator.__is_valid_date__(start_date) and MetricsCalculator.__is_valid_date__(end_date):
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            raise ValueError("Wrong formated string")
        total_days = (end - start).days
        num_years = total_days / 365.25  # 365.25 accounts for leap years

        # CAGR formula: (Ending Value / Beginning Value)^(1/n) - 1
        cagr = ((cumulative_return.iloc[-1] / cumulative_return.iloc[0]) ** (1 / num_years) - 1) * 100
        return float(cagr)  # Convert to Python float

    def __is_valid_date__(date_str: str) -> bool:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except Exception as e:
            print(f"Error parsing string to date: {e}")
            return False
        
    @staticmethod
    def sharpe(daily_returns, risk_free_rate: float = 0.0) -> float:
        """
        Calculate the Sharpe ratio from daily returns.

        Args:
            daily_returns: Series-like daily returns as decimals (e.g. 0.01 for 1%).
            risk_free_rate: Annual risk-free rate as a decimal.

        Returns:
            Sharpe ratio (annualized if daily returns are daily).
        """
        returns = np.asarray(daily_returns, dtype=float)
        if returns.size == 0:
            raise ValueError("daily_returns must contain at least one value")

        daily_risk_free = risk_free_rate / 252
        excess_returns = returns - daily_risk_free
        mean_excess = np.mean(excess_returns)
        std_excess = np.std(excess_returns, ddof=1)

        if std_excess == 0:
            return 0.0

        return float(mean_excess / std_excess)

    @staticmethod
    def max_drawdown(daily_returns):
        """
        Calculate Maximum Drawdown from a series of returns.

        Args:
            returns_series: Series of daily returns (e.g., 0.01 for 1%)

        Returns:
            Maximum drawdown as a decimal (e.g., 0.25 for 25%)
        """
        # Convert returns to cumulative product (price curve)
        cumulative_returns = (1 + daily_returns).cumprod()

        # Calculate running maximum
        running_max = cumulative_returns.expanding().max()

        # Calculate drawdown series
        drawdown = (cumulative_returns - running_max) / running_max

        # Find maximum drawdown
        max_drawdown = drawdown.min()

        return float(abs(max_drawdown))

    @staticmethod
    def alpha(asset_returns, market_returns, risk_free_rate=0.0):
        """
        Calculate Alpha of an asset.

        Args:
            asset_returns: Series of asset returns
            market_returns: Series of market returns
            risk_free_rate: Annualized risk-free rate (default: 0)

        Returns:
            Alpha coefficient
        """
        beta = MetricsCalculator.beta(asset_returns, market_returns)
        excess_market_return = market_returns - risk_free_rate
        excess_asset_return = asset_returns - risk_free_rate

        # Calculate predicted return based on CAPM
        predicted_return = risk_free_rate + beta * excess_market_return

        # Alpha is the difference between actual and predicted return
        alpha = (excess_asset_return - predicted_return).mean()
        return alpha

    @staticmethod
    def beta(asset_returns, market_returns):
        """
        Calculate Beta of an asset relative to a market benchmark.

        Args:
            asset_returns: Series of asset returns
            market_returns: Series of market returns

        Returns:
            Beta coefficient
        """
        # Calculate covariance and variance
        covariance = np.cov(asset_returns, market_returns)[0, 1]
        market_variance = np.var(market_returns, ddof=1)  # Sample variance

        beta = covariance / market_variance
        return beta
