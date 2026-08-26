from typing import Any

import numpy as np
import pandas as pd

from pandas import DataFrame

from dataclasses import dataclass
from engine.backtest_config import BacktestConfig
from engine.strategy.base import Strategy
from engine.data.loader import DataLoader
from datetime import date, datetime
from engine.metrics_calculator import MetricsCalculator
from indicators import sma

import plotly.express as px
from plotly.graph_objs import Figure

@dataclass
class BacktestResult:
    """Stores backtest results including dates, metrics, and raw data."""
    dates: date
    metrics: dict[str, Any]
    stock_df: DataFrame

class Backtest:
    config: BacktestConfig
    strategy: Strategy
    symbol: str
    loader: DataLoader
    start_date: str | date | datetime 
    end_date: str | date | datetime
    cash: float
    portfolio_value: list[float]
    shares: int

    def __init__(self, config: BacktestConfig):
        """Initialize a backtest with a trading strategy, symbol, date range, and starting capital.

        Args:
            strategy: Trading strategy used to generate buy/sell signals.
            symbol: Security ticker to backtest.
            start_date: Start date of the backtest, either date-like or YYYY-MM-DD string.
            end_date: End date of the backtest, either date-like or YYYY-MM-DD string.
            cash: Initial cash amount at the start of the backtest.
        """
        self.config = config
        self.strategy = config.strategy
        self.symbol = config.symbol
        self.loader = config.loader
        self.start_date = config.start_date
        self.end_date = config.end_date
        self.cash = config.cash
        self.portfolio_value = [config.cash]
        self.shares = config.shares
    
    def run(self) -> BacktestResult:
        """Run the backtest and produce a result object with performance data.

        This method loads benchmark data, applies the strategy signals, computes strategy returns,
        compares performance to the benchmark, and builds a plot for visualization.
        """

        # Load stock and marrket dataframes
        stock_df = self.loader.load(symbol=self.symbol, start=self.start_date, end=self.end_date)
        benchmark_df = self.loader.load("^GSPC", start=self.start_date, end=self.end_date)

        # Remove NaN values for both stock and benchmark dataframes
        cleaned_dataframes = self.clean_df_index(stock_df=stock_df, benchmark_df=benchmark_df)
        stock_df = cleaned_dataframes.get("stock_df")
        benchmark_df = cleaned_dataframes.get("benchmark_df")

        signals = self.strategy.generate_signals(stock_df)
        closing_prices = stock_df['adj close']

        # Build a running position series from raw trading signals.
        # Treat 0 as no new signal and carry forward the most recent valid position.
        positions = signals.replace(0, np.nan).ffill().fillna(0).clip(-1, 1)

        # Compute daily asset returns from adjusted close prices.
        price_returns = closing_prices.pct_change().fillna(0)

        # The strategy return uses the prior day's position, because today's return is realized
        # only when the position was held at the start of the day.
        strategy_returns = positions.shift(1).fillna(0) * price_returns

        # Reconstruct portfolio equity growth from the strategy returns.
        initial_value = self.cash
        portfolio_log_returns = np.log(1 + strategy_returns)
        self.portfolio_value = initial_value * np.exp(portfolio_log_returns.cumsum())
        roi = (np.exp(portfolio_log_returns.cumsum()) - 1) * 100

        # Convert daily strategy returns to percentage values for metric calculations.
        returns = strategy_returns.to_numpy() * 100

        # Compute benchmark return series from the already aligned benchmark data.
        benchmark_closing_prices = benchmark_df['adj close']
        benchmark_returns = benchmark_closing_prices.pct_change().fillna(0)
        benchmark_returns_log = np.log(1 + benchmark_returns)
        benchmark_returns_roi = (np.exp(benchmark_returns_log.cumsum()) - 1) * 100

        metrics = self.calculate_metrics(
            daily_returns=strategy_returns,
            benchmark_returns=benchmark_returns,
            start_date=self.start_date,
            end_date=self.end_date,
            closing_prices=closing_prices
        )

        return BacktestResult(
            dates=stock_df.index,
            metrics=metrics,
            stock_df=stock_df,
        )

    def clean_df_index(self, stock_df: pd.DataFrame, benchmark_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
        stock_df, benchmark_df = stock_df.align(benchmark_df, join="inner", axis=0)
        combined = pd.concat(
            [stock_df["adj close"], benchmark_df["adj close"]],
            axis=1,
            keys=["stock_close", "benchmark_close"]
        )
        cleaned = combined.dropna(subset=["stock_close", "benchmark_close"])
        stock_df = stock_df.loc[cleaned.index]
        benchmark_df = benchmark_df.loc[cleaned.index]
        dict = {}
        dict["stock_df"] = stock_df
        dict["benchmark_df"] = benchmark_df
        return dict

    def calculate_metrics(self, daily_returns,
                          benchmark_returns, 
                          start_date: str | date | datetime, 
                          end_date: str | date | datetime,
                          closing_prices: pd.Series) -> dict[str, Any]:
        """Compute standard performance metrics from strategy and benchmark returns."""
        metrics = {}
        metrics["buy_and_hold_return"] = MetricsCalculator.buy_and_hold_return(
            closing_prices
        )
        metrics["cagr"] = MetricsCalculator.cagr(
            daily_returns,
            start_date,
            end_date,
        )
        metrics["sharpe"] = MetricsCalculator.sharpe(
            daily_returns,
            risk_free_rate=0.0
        )
        metrics["max_drawdown"] = MetricsCalculator.max_drawdown(daily_returns)
        metrics["alpha"] = MetricsCalculator.alpha(
            daily_returns,
            benchmark_returns,
            risk_free_rate=0.0
        )
        metrics["beta"] = MetricsCalculator.beta(
            daily_returns,
            benchmark_returns
        )
        return metrics

    def set_start_date(self, start_date: str | date | datetime):
        """Update the backtest start date, validating string input if needed."""
        if isinstance(start_date, str):
            if Backtest.__validate_date_format__(start_date):
                self.start_date = start_date
            else:
                raise ValueError("Date string must be in YYYY-MM-DD format")
        else:
            self.start_date = start_date

    def set_end_date(self, end_date: str | date | datetime):
        """Update the backtest end date, validating string input if needed."""
        if isinstance(end_date, str):
            if Backtest.__validate_date_format__(end_date):
                self.end_date = end_date
            else:
                raise ValueError("Date string must be in YYYY-MM-DD format")
        else:
            self.end_date = end_date

    @staticmethod
    def __validate_date_format__(date: str) ->  bool:
        """Check whether a string is a valid YYYY-MM-DD date format."""
        try:
            datetime.strptime(date, "%Y-%m-%d")
            return True
        except Exception as e:
            print(f"Error parsing string to date: {e}")
            return False