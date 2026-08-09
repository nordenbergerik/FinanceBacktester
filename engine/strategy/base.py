import pandas as pd
from abc import ABC, abstractmethod

class Strategy(ABC):
    """Abstract base class for trading strategies that generate entry/exit signals."""

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """Return a series of trading signals for the provided market data."""
        pass