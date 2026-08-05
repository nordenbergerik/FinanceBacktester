from engine.strategy.base import Strategy
import pandas as pd

class Mockstrategy(Strategy):
    """A simple example strategy that generates signals based on prior close price momentum."""

    def __init__(self):
        super().__init__() 
            
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """Generate long/short signals using a price momentum threshold.

        Positions are set to 1 when the previous close is significantly above the close two days ago,
        and -1 when price has dropped sharply.
        """
        signals = pd.Series(0, index=df.index)
        df['prev_close'] = df['close'].shift(1)
        df['prev_prev_close'] = df['close'].shift(2)
        threshold = 0.03
        signals[(df['prev_close'] > df['prev_prev_close'] * (1 + threshold))] = 1
        signals[(df['prev_close'] < df['prev_prev_close'] * (1 - threshold))] = -1
        return signals