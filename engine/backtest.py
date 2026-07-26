from typing import Any

import numpy as np
import pandas as pd

from dataclasses import dataclass
from engine.strategy.base import Strategy
from engine.data.loader import DataLoader
from datetime import date, datetime

import plotly.express as px
from plotly.graph_objs import Figure

@dataclass
class BacktestResult:
    """Stores backtest results including ROI curve, price curve, dates, metrics, and raw data."""
    roi_curve: Figure
    price_curve: Figure
    return_buyandhold: float
    dates: date
    metrics: dict[str, Any]
    df: pd.DataFrame
    

class Backtest:
    strategy: Strategy
    symbol: str
    loader: DataLoader
    start_date: str | date | datetime 
    end_date: str | date | datetime
    cash: float
    portfolio_value: list[float]
    shares: int

    def __init__(self, strategy: Strategy, symbol: str, start_date: date | datetime, end_date: date | datetime, cash: float):
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

        # 6. Generate plots
        roi_curve = px.line(
            x=df.index,
            y=roi,
            title="Return on Investment (ROI)",
            labels={"x": "Date", "y": "ROI (%)"},
        )
        price_curve = px.line(
            df,
            x=df.index,
            y="close",
            title="Price Curve",
            labels={"close": "Price ($)", "index": "Date"},
        )

        return BacktestResult(
            roi_curve=roi_curve, 
            price_curve=price_curve,
            return_buyandhold=return_buyandhold,
            dates=df.index, 
            metrics=None, 
            df=df
        )