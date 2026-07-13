from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Bar:
    """A single OHLCV price bar for one symbol at one point in time.
    Frozen (immutable) because bars represent historical fact — once
    loaded, nothing in the engine should be able to mutate them.
    """
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

    def __post_init__(self) -> None:
        if self.low > self.high:
            raise ValueError(
                f"{self.symbol} at {self.timestamp}: high ({self.high}) "
                f"cannot be less than low ({self.low})"
            )
        if not (self.low <= self.open <= self.high):
            raise ValueError(
                f"{self.symbol} at {self.timestamp}: open ({self.open}) "
                f"outside [low, high] range"
            )
        if not (self.low <= self.close <= self.high):
            raise ValueError(
                f"{self.symbol} at {self.timestamp}: close ({self.close}) "
                f"outside [low, high] range"
            )
        if self.volume < 0:
            raise ValueError(
                f"{self.symbol} at {self.timestamp}: volume cannot be negative"
            )

    @property
    def typical_price(self) -> float:
        return (self.high + self.low + self.close) / 3

    @property
    def is_bullish(self) -> bool:
        return self.close > self.open
    