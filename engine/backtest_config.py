from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

from engine.data.loader import DataLoader
from engine.strategy.base import Strategy

class BacktestConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    strategy: Strategy
    symbol: str
    loader: DataLoader = DataLoader()
    start_date: str | date | datetime 
    end_date: str | date | datetime
    cash: float
    shares: int = 0

    @field_validator("start_date", "end_date", mode="before")
    def parse_date(cls, value):
        if isinstance(value, str):
            try:
                return datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format")
        return value

