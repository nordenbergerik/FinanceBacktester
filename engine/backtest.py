from typing import Any

import numpy as np

from pandas import DataFrame

from dataclasses import dataclass
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
    strategy: Strategy
    symbol: str
    loader: DataLoader
    start_date: date | datetime 
    end_date: date | datetime
    cash: float
    portfolio_value: list[float]
    shares: int

    def __init__(self, strategy: Strategy, symbol: str, start_date: str | date | datetime, end_date: str | date | datetime, cash: float):
        self.strategy = strategy
        self.symbol = symbol
        self.loader = DataLoader()
        self.start_date = start_date
        self.end_date = end_date
        self.cash = cash
        self.portfolio_value = [cash]
        self.shares = 0
    
    def run(self) -> BacktestResult:
        """Runs the backtest and returns results."""
        df = self.loader.load(symbol=self.symbol, start=self.start_date, end=self.end_date)
        signals = self.strategy.generate_signals(df)
        closing_prices = df['close']

        # 1. Forward-fill the signals to know your current market position at any given time
        # If your strategy outputs a signal only on the day of the trade, we need to track the "holding" state.
        # Let's assume 'position' is 1 when holding asset, 0 when in cash.
        # We can compute this by tracking the changes or accumulating the signals:
        positions = signals.cumsum().ffill().fillna(0)

        # 2. Calculate daily asset returns
        price_returns = closing_prices.pct_change().fillna(0)

        # 3. Your daily strategy return is your position from the *previous* day multiplied by today's asset return
        strategy_returns = positions.shift(1).fillna(0) * price_returns

        # 4. Reconstruct the portfolio value curve starting from your initial cash
        # (Assuming you put all your cash into the asset when long)
        initial_value = self.cash
        portfolio_log_returns = np.log(1 + strategy_returns)
        self.portfolio_value = initial_value * np.exp(portfolio_log_returns.cumsum())
        roi = (np.exp(portfolio_log_returns.cumsum()) - 1) * 100

        # 5. Calculate daily percentage returns for your output
        returns = strategy_returns.to_numpy() * 100

        # Generate buy and hold return
        starting_price = closing_prices.iloc[0]
        final_price = closing_prices.iloc[-1]
        return_buyandhold = ((final_price / starting_price) - 1) * 100

        # Generate market returns 
        market_df = self.loader.load("^GSPC", start=self.start_date, end=self.end_date)
        market_closing_prices = market_df['close']
        market_returns = market_closing_prices.pct_change().fillna(0)
        market_returns_log = np.log(1 + market_returns)
        market_returns_roi = (np.exp(market_returns_log.cumsum()) - 1) * 100
        


        # Generate plots
        combined_fig = px.line(
            title="ROI, Price, and Market Comparison"
        )

        # roi of strategy
        combined_fig.add_scatter(
            x=df.index,
            y=roi,
            name="ROI (%)",
            line=dict(color="blue")
        )
        # market returns
        combined_fig.add_scatter(
            x=market_df.index,
            y=market_returns_roi,
            name="S&P500",
            line=dict(color="red")
        )
        # combined_fig.add_scatter(
        #     x=df.index,
        #     y=df['close'],
        #     name="Price ($)",
        #     line=dict(color="green")
        # )

        # market_curve = px.line(
        #     x=market_df.index,
        #     y=market_returns_roi,
        #     title="S&P500",
        #     labels={"close": "Price ($)", "index": "Date"}
        # )

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