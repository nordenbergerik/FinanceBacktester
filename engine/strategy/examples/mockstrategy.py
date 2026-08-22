from engine.strategy.base import Strategy
import pandas as pd

class Mockstrategy(Strategy):
    """A simple example strategy that generates signals from adjusted-close momentum."""

    def __init__(self):
        super().__init__() 
            
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """Generate long/short signals using a price momentum threshold.

        Positions are set to 1 when the previous adjusted close is significantly above the adjusted close two days ago,
        and -1 when price has dropped sharply.
        """
        signals = pd.Series(0, index=df.index)
        df['prev_adj_close'] = df['adj close'].shift(1)
        df['prev_prev_adj_close'] = df['adj close'].shift(2)
        threshold = 0.02
        signals[(df['prev_adj_close'] > df['prev_prev_adj_close'] * (1 + threshold))] = 1
        signals[(df['prev_adj_close'] < df['prev_prev_adj_close'] * (1 - threshold))] = -1
        return signals