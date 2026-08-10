from typing import Any

import numpy as np

from pandas import DataFrame

from dataclasses import dataclass
from engine.backtest_config import BacktestConfig
from engine.strategy.base import Strategy
from engine.data.loader import DataLoader
from datetime import date, datetime
from engine.metrics_calculator import MetricsCalculator

import plotly.express as px
from plotly.graph_objs import Figure

@dataclass
class BacktestResult:
    """Stores backtest results including ROI curve, price curve, market curve, dates, metrics, and raw data."""
    plot: Figure
    return_buyandhold: float
    dates: date
    metrics: dict[str, Any]
    df: DataFrame
    

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

        This method loads market data, applies the strategy signals, computes strategy returns,
        compares performance to the market, and builds a plot for visualization.
        """
        df = self.loader.load(symbol=self.symbol, start=self.start_date, end=self.end_date)
        signals = self.strategy.generate_signals(df)
        closing_prices = df['close']

        # Build a running position series from raw trading signals.
        # Treat 0 as no new signal and carry forward the most recent valid position.
        positions = signals.replace(0, np.nan).ffill().fillna(0).clip(-1, 1)

        # Compute daily asset returns from the close prices.
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

        # Calculate the buy-and-hold return for the same period.
        starting_price = closing_prices.iloc[0]
        final_price = closing_prices.iloc[-1]
        return_buyandhold = ((final_price / starting_price) - 1) * 100

        # Load market benchmark data and compute its cumulative return.
        market_df = self.loader.load("^GSPC", start=self.start_date, end=self.end_date)
        market_closing_prices = market_df['close']
        market_returns = market_closing_prices.pct_change().fillna(0)
        market_returns_log = np.log(1 + market_returns)
        market_returns_roi = (np.exp(market_returns_log.cumsum()) - 1) * 100

        # Returns from stock (%)
        stock_returns = (closing_prices / df['close'].iloc[0] - 1) * 100
        
        # Build a combined line chart for the strategy ROI and market benchmark.
        combined_fig = px.line(
            title="ROI, Price, and Market Comparison"
        )

        combined_fig.add_scatter(
            x=df.index,
            y=roi,
            name="Strategy ROI (%)",
            line=dict(color="blue")
        )
        combined_fig.add_scatter(
            x=market_df.index,
            y=market_returns_roi,
            name="S&P500",
            line=dict(color="red")
        )
        combined_fig.add_scatter(
            x=market_df.index,
            y=stock_returns,
            name="Stock ROI",
            line=dict(color="green")
        )

        metrics = self.calculate_metrics(
            daily_returns=strategy_returns,
            market_returns=market_returns,
            start_date=self.start_date,
            end_date=self.end_date,
        )

        return BacktestResult(
            plot=combined_fig,
            return_buyandhold=return_buyandhold,
            dates=df.index,
            metrics=metrics,
            df=df,
        )

    def calculate_metrics(self, daily_returns,
                          market_returns, 
                          start_date: str | date | datetime, 
                          end_date: str | date | datetime,) -> dict[str, Any]:
        """Compute standard performance metrics from strategy and benchmark returns."""
        metrics = {}
        metrics["cagr"] = MetricsCalculator.cagr(
            daily_returns=daily_returns,
            start_date=start_date,
            end_date=end_date,
        )
        metrics["sharpe"] = MetricsCalculator.sharpe(
            daily_returns=daily_returns,
            risk_free_rate=0.0
        )
        metrics["max_drawdown"] = MetricsCalculator.max_drawdown(daily_returns=daily_returns)
        metrics["alpha"] = MetricsCalculator.alpha(
            asset_returns=daily_returns,
            market_returns=market_returns,
            risk_free_rate=0.0
        )
        metrics["beta"] = MetricsCalculator.beta(
            asset_returns=daily_returns,
            market_returns=market_returns
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