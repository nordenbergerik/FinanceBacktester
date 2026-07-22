from engine.strategy.base import Strategy
import pandas as pd

class Mockstrategy(Strategy):
    def __init__(self):
        super().__init__() 

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        signals = pd.Series(0, index=df.index)
        df['prev_price'] = df['close'].shift(1)
        signals[df['close'] > df['prev_price']] = 1
        signals[df['close'] < df['prev_price']] = -1
        return signals