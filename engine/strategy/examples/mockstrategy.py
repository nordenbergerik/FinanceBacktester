from engine.strategy.base import Strategy
import pandas as pd

class Mockstrategy(Strategy):
    def __init__(self):
        super().__init__() 
            
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        signals = pd.Series(0, index=df.index)
        df['prev_close'] = df['close'].shift(1)
        df['prev_prev_close'] = df['close'].shift(2)
        threshold = 0.03
        signals[(df['prev_close'] > df['prev_prev_close'] * (1 + threshold))] = 1
        signals[(df['prev_close'] < df['prev_prev_close'] * (1 - threshold))] = -1
        return signals